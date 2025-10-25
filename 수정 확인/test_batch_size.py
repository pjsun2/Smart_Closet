"""
배치 크기 최적화 테스트 스크립트
- 배치 크기 1부터 시작하여 최적값 자동 탐색
- 각 배치 크기당 영상 전체 길이만큼 테스트
- FPS가 5회 연속 감소하면 테스트 종료
"""

import cv2
import numpy as np
import time
import sys
import os
import threading
import queue
import torch
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc

# 한글 폰트 설정
try:
    # Windows 한글 폰트
    plt.rcParams['font.family'] = 'Malgun Gothic'
    plt.rcParams['axes.unicode_minus'] = False
except:
    pass

# 현재 디렉토리를 sys.path에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from mmpose.apis import init_model, inference_topdown

class BatchSizeTester:
    """배치 크기 최적화 테스터"""
    
    def __init__(self, video_path, device='cuda:0'):
        self.video_path = video_path
        self.device = device
        
        # 비디오 길이 확인
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise FileNotFoundError(f"비디오 파일을 열 수 없습니다: {video_path}")
        
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        video_duration = total_frames / video_fps if video_fps > 0 else 0
        cap.release()
        
        print(f"[테스트] 비디오 정보:")
        print(f"  - 총 프레임: {total_frames}")
        print(f"  - FPS: {video_fps:.2f}")
        print(f"  - 길이: {video_duration:.2f}초")
        
        # RTMPose 모델 초기화
        config_file = os.path.join(current_dir, 'models', 'rtmpose-s_8xb256-420e_aic-coco-256x192.py')
        checkpoint_file = os.path.join(current_dir, 'models', 'rtmpose-s_simcc-aic-coco_pt-aic-coco_420e-256x192-fcb2599b_20230126.pth')
        
        print(f"[테스트] 모델 로딩 중... (device: {device})")
        self.model = init_model(config_file, checkpoint_file, device=device)
        self.model.eval()
        
        # GPU 워밍업
        if torch.cuda.is_available() and 'cuda' in device:
            print("[테스트] GPU 워밍업 중...")
            torch.backends.cudnn.benchmark = True
            torch.backends.cuda.matmul.allow_tf32 = True
            torch.backends.cudnn.allow_tf32 = True
            
            # 더미 이미지로 워밍업 (실제 추론 사용)
            dummy_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            with torch.no_grad():
                _ = inference_topdown(self.model, dummy_image)
            torch.cuda.empty_cache()
            print("[테스트] GPU 워밍업 완료")
        
        # 테스트 설정
        self.queue_size = 22  # 고정 (이전 테스트 최적값)
        self.inference_scale = 0.65  # 고정
        self.test_duration = video_duration  # 영상 길이만큼 테스트
        
        print(f"\n[테스트] 테스트 설정:")
        print(f"  - 큐 크기: {self.queue_size} (고정)")
        print(f"  - 추론 해상도: {int(self.inference_scale*100)}%")
        print(f"  - 테스트 시간: {self.test_duration:.2f}초 (영상 전체 길이)")
        print(f"  - 비디오: {video_path}")
    
    def test_single_batch_size(self, batch_size):
        """단일 배치 크기 테스트"""
        print(f"\n{'='*70}")
        print(f"[테스트] 배치 크기 {batch_size} 테스트 시작")
        print(f"{'='*70}")
        
        # 큐 초기화
        inference_queue = queue.Queue(maxsize=self.queue_size)
        result_queue = queue.Queue(maxsize=max(4, self.queue_size // 2))
        running = True
        
        # 성능 카운터
        frames_processed = 0
        total_inference_time = 0
        test_start_time = time.time()
        
        # 추론 워커 스레드
        def inference_worker():
            nonlocal frames_processed, total_inference_time
            
            while running:
                try:
                    # 배치 수집
                    batch_frames = []
                    frame_timeout = 0.015  # 15ms
                    
                    for i in range(batch_size):
                        try:
                            timeout = frame_timeout if i == 0 else frame_timeout * 0.5
                            frame_data = inference_queue.get(timeout=timeout)
                            
                            if frame_data is None:
                                return
                            
                            frame, original_w, original_h = frame_data
                            batch_frames.append(frame)
                        except queue.Empty:
                            break
                    
                    if not batch_frames:
                        continue
                    
                    # 배치 추론
                    inference_start = time.time()
                    
                    try:
                        results_batch = []
                        if torch.cuda.is_available() and 'cuda' in self.device:
                            streams = [torch.cuda.Stream() for _ in range(len(batch_frames))]
                            stream_results = [None] * len(batch_frames)
                            
                            with torch.no_grad():
                                for i, (frame, stream) in enumerate(zip(batch_frames, streams)):
                                    with torch.cuda.stream(stream):
                                        stream_results[i] = inference_topdown(self.model, frame)
                            
                            torch.cuda.synchronize()
                            results_batch = stream_results
                        else:
                            with torch.no_grad():
                                for frame in batch_frames:
                                    result = inference_topdown(self.model, frame)
                                    results_batch.append(result)
                        
                        inference_end = time.time()
                        inference_time = inference_end - inference_start
                        
                        frames_processed += len(batch_frames)
                        total_inference_time += inference_time
                        
                        # 결과 저장 (큐가 가득 차면 오래된 것 버림)
                        try:
                            result_queue.put_nowait(results_batch)
                        except queue.Full:
                            try:
                                result_queue.get_nowait()
                                result_queue.put_nowait(results_batch)
                            except:
                                pass
                    
                    except Exception as e:
                        print(f"[테스트] 추론 에러: {e}")
                        continue
                
                except Exception as e:
                    if running:
                        print(f"[테스트] 워커 에러: {e}")
                    continue
        
        # 워커 스레드 시작
        worker_thread = threading.Thread(target=inference_worker, daemon=True)
        worker_thread.start()
        
        # 비디오 읽기 및 프레임 전송
        cap = cv2.VideoCapture(self.video_path)
        
        if not cap.isOpened():
            print(f"[테스트] [ERROR] 비디오 열기 실패: {self.video_path}")
            running = False
            return 0, 0
        
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        print(f"[테스트] 비디오 정보: {total_frames} 프레임, {video_fps:.2f} FPS")
        
        frame_count = 0
        frames_sent = 0
        video_start_time = time.time()
        
        while running:
            ret, frame = cap.read()
            
            if not ret:
                # 비디오 끝나면 종료
                break
            
            frame_count += 1
            
            # 현재 시간 체크
            elapsed = time.time() - video_start_time
            if elapsed >= self.test_duration:
                break
            
            # 프레임 다운스케일
            original_h, original_w = frame.shape[:2]
            inference_w = int(original_w * self.inference_scale)
            inference_h = int(original_h * self.inference_scale)
            inference_frame = cv2.resize(frame, (inference_w, inference_h), interpolation=cv2.INTER_LINEAR)
            
            # 큐에 프레임 추가
            try:
                inference_queue.put_nowait((inference_frame, original_w, original_h))
                frames_sent += 1
            except queue.Full:
                pass  # 큐가 가득 차면 프레임 드롭
        
        # 정리
        running = False
        
        # 종료 신호
        try:
            inference_queue.put(None, timeout=0.1)
        except:
            pass
        
        worker_thread.join(timeout=1.0)
        cap.release()
        
        # 결과 계산
        test_elapsed = time.time() - test_start_time
        actual_fps = frames_processed / test_elapsed if test_elapsed > 0 else 0
        avg_batch_time = total_inference_time / (frames_processed / batch_size) if frames_processed > 0 else 0
        
        # GPU 메모리 사용량
        gpu_memory = 0
        if torch.cuda.is_available():
            gpu_memory = torch.cuda.memory_allocated() / 1024**3  # GB
        
        print(f"\n[테스트] 배치 크기 {batch_size} 결과:")
        print(f"  - 처리 프레임: {frames_processed} / {frames_sent} (전송됨)")
        print(f"  - 실제 FPS: {actual_fps:.2f}")
        print(f"  - 평균 배치 추론 시간: {avg_batch_time*1000:.2f}ms")
        print(f"  - GPU 메모리: {gpu_memory:.2f} GB")
        print(f"  - 테스트 시간: {test_elapsed:.2f}초")
        
        # 큐 정리
        while not inference_queue.empty():
            try:
                inference_queue.get_nowait()
            except:
                break
        
        while not result_queue.empty():
            try:
                result_queue.get_nowait()
            except:
                break
        
        return actual_fps, gpu_memory
    
    def run_optimization_test(self):
        """배치 크기 최적화 테스트 실행"""
        print(f"\n{'='*70}")
        print("[테스트] 배치 크기 최적화 테스트 시작")
        print("[테스트] FPS가 5회 연속 감소하면 테스트 종료")
        print(f"{'='*70}\n")
        
        results = []
        consecutive_decreases = 0
        max_batch_size = 20  # 최대 테스트 크기
        
        for batch_size in range(1, max_batch_size + 1):
            fps, gpu_memory = self.test_single_batch_size(batch_size)
            results.append((batch_size, fps, gpu_memory))
            
            # FPS 감소 체크
            if len(results) >= 2:
                prev_fps = results[-2][1]
                current_fps = results[-1][1]
                
                if current_fps < prev_fps:
                    consecutive_decreases += 1
                    print(f"[테스트] FPS 감소 감지 ({consecutive_decreases}/5): {prev_fps:.2f} → {current_fps:.2f}")
                else:
                    consecutive_decreases = 0
                    print(f"[테스트] FPS 증가: {prev_fps:.2f} → {current_fps:.2f}")
            
            # 5회 연속 감소하면 종료
            if consecutive_decreases >= 5:
                print(f"\n[테스트] ⚠️ FPS가 5회 연속 감소하여 테스트 종료")
                break
            
            # 다음 테스트 전 잠시 대기 (GPU 안정화)
            time.sleep(0.5)
        
        # 결과 저장 (시각화를 위해)
        self.test_results = results
        
        # 최종 결과 출력
        print(f"\n{'='*70}")
        print("[테스트] 최종 결과")
        print(f"{'='*70}")
        print(f"{'배치 크기':<10} | {'FPS':<10} | {'GPU 메모리(GB)':<15} | {'성능 변화':<15}")
        print(f"{'-'*60}")
        
        max_fps = 0
        optimal_batch_size = 1
        
        for i, (batch_size, fps, gpu_mem) in enumerate(results):
            if i == 0:
                change = "기준"
            else:
                prev_fps = results[i-1][1]
                diff = fps - prev_fps
                if prev_fps > 0:
                    change = f"{diff:+.2f} ({diff/prev_fps*100:+.1f}%)"
                else:
                    change = f"{diff:+.2f} (N/A)"
            
            marker = ""
            if fps > max_fps:
                max_fps = fps
                optimal_batch_size = batch_size
                marker = " ⭐ 최고"
            
            print(f"{batch_size:<10} | {fps:<10.2f} | {gpu_mem:<15.2f} | {change:<15} {marker}")
        
        print(f"\n{'='*70}")
        print(f"[테스트] 🏆 최적 배치 크기: {optimal_batch_size} (FPS: {max_fps:.2f})")
        print(f"{'='*70}\n")
        
        # 권장 설정 출력
        print("[테스트] 권장 설정:")
        print(f"""
# virtual_fitting.py에 적용:
self.batch_size = {optimal_batch_size}
self.inference_queue = queue.Queue(maxsize={self.queue_size})
self.result_queue = queue.Queue(maxsize={max(4, self.queue_size // 2)})
        """)
        
        return optimal_batch_size, max_fps, results
    
    def visualize_results(self, results):
        """결과 시각화"""
        print(f"\n[테스트] 결과 시각화 중...")
        
        batch_sizes = [r[0] for r in results]
        fps_values = [r[1] for r in results]
        gpu_memory = [r[2] for r in results]
        
        # 최적값 찾기
        max_fps = max(fps_values)
        optimal_idx = fps_values.index(max_fps)
        optimal_batch_size = batch_sizes[optimal_idx]
        
        # Figure 생성 (4개 서브플롯)
        fig, axes = plt.subplots(4, 1, figsize=(14, 16))
        fig.suptitle('배치 크기 최적화 테스트 결과', fontsize=16, fontweight='bold')
        
        # 1. FPS vs 배치 크기 (선 그래프)
        ax1 = axes[0]
        ax1.plot(batch_sizes, fps_values, 'b-', linewidth=2, marker='o', label='FPS')
        ax1.plot(optimal_batch_size, max_fps, 'r*', markersize=20, label=f'최적값 (배치={optimal_batch_size}, FPS={max_fps:.2f})')
        ax1.axhline(y=max_fps, color='r', linestyle='--', alpha=0.3)
        ax1.axvline(x=optimal_batch_size, color='r', linestyle='--', alpha=0.3)
        ax1.set_xlabel('배치 크기', fontsize=12)
        ax1.set_ylabel('FPS', fontsize=12)
        ax1.set_title('FPS vs 배치 크기', fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.legend(fontsize=10)
        
        # 2. GPU 메모리 사용량 (막대 그래프)
        ax2 = axes[1]
        colors_mem = ['orange' if mem < 4 else 'red' if mem > 6 else 'yellow' for mem in gpu_memory]
        ax2.bar(batch_sizes, gpu_memory, color=colors_mem, alpha=0.6)
        ax2.axhline(y=4, color='orange', linestyle='--', alpha=0.5, label='4GB (권장 최소)')
        ax2.axhline(y=6, color='red', linestyle='--', alpha=0.5, label='6GB (권장 최대)')
        ax2.set_xlabel('배치 크기', fontsize=12)
        ax2.set_ylabel('GPU 메모리 (GB)', fontsize=12)
        ax2.set_title('배치 크기별 GPU 메모리 사용량', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3, axis='y')
        ax2.legend(fontsize=10)
        
        # 3. 성능 변화율 (막대 그래프)
        ax3 = axes[2]
        changes = [0]  # 첫 번째는 기준
        for i in range(1, len(fps_values)):
            if fps_values[i-1] > 0:
                change = (fps_values[i] - fps_values[i-1]) / fps_values[i-1] * 100
            else:
                change = 0  # 이전 FPS가 0이면 변화율도 0
            changes.append(change)
        
        colors = ['green' if c >= 0 else 'red' for c in changes]
        ax3.bar(batch_sizes, changes, color=colors, alpha=0.6)
        ax3.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax3.set_xlabel('배치 크기', fontsize=12)
        ax3.set_ylabel('성능 변화율 (%)', fontsize=12)
        ax3.set_title('이전 배치 크기 대비 성능 변화율', fontsize=14, fontweight='bold')
        ax3.grid(True, alpha=0.3, axis='y')
        
        # 4. 누적 성능 개선 (영역 그래프)
        ax4 = axes[3]
        baseline_fps = fps_values[0]
        cumulative_improvement = [(fps - baseline_fps) / baseline_fps * 100 for fps in fps_values]
        
        ax4.fill_between(batch_sizes, 0, cumulative_improvement, alpha=0.3, color='blue')
        ax4.plot(batch_sizes, cumulative_improvement, 'b-', linewidth=2, marker='o')
        ax4.plot(optimal_batch_size, cumulative_improvement[optimal_idx], 'r*', markersize=20)
        ax4.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax4.axhline(y=cumulative_improvement[optimal_idx], color='r', linestyle='--', alpha=0.3)
        ax4.set_xlabel('배치 크기', fontsize=12)
        ax4.set_ylabel('누적 성능 개선 (%)', fontsize=12)
        ax4.set_title(f'배치 크기 1 대비 누적 성능 개선 (최대: {cumulative_improvement[optimal_idx]:.1f}%)', 
                     fontsize=14, fontweight='bold')
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # 저장
        output_path = os.path.join(current_dir, 'batch_size_optimization_result.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"[테스트] 그래프 저장: {output_path}")
        
        # 표시
        plt.show()
        
        return output_path


def main():
    """메인 함수"""
    video_path = r"C:\Users\parkj\Desktop\ponggwi\source\basic.mp4"
    
    # 비디오 파일 확인
    if not os.path.exists(video_path):
        print(f"[ERROR] 비디오 파일을 찾을 수 없습니다: {video_path}")
        return
    
    # GPU 확인
    device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
    print(f"[테스트] Device: {device}")
    
    if device == 'cpu':
        print("[WARNING] GPU를 사용할 수 없습니다. CPU 모드로 실행합니다.")
    
    # 테스터 생성 및 실행
    tester = BatchSizeTester(video_path, device=device)
    optimal_size, max_fps, results = tester.run_optimization_test()
    
    print(f"\n[테스트] 완료! 최적 배치 크기: {optimal_size}, 최대 FPS: {max_fps:.2f}")
    
    # 시각화
    graph_path = tester.visualize_results(results)
    print(f"\n[테스트] 시각화 완료: {graph_path}")


if __name__ == "__main__":
    main()
