"""
가상 피팅 시스템 종합 성능 테스트
- 해상도별 성능 비교 (480p, 720p, 1080p)
- GPU 사용률 및 메모리 측정
- 레이턴시 (지연 시간) 분석
- 프레임 드롭률 측정
- 처리 시간 분포 (추론, 렌더링, 전체)
"""

import cv2
import numpy as np
import time
import sys
import os
import threading
import queue
import torch
import subprocess
import json
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc
from collections import defaultdict

# 한글 폰트 설정
try:
    plt.rcParams['font.family'] = 'Malgun Gothic'
    plt.rcParams['axes.unicode_minus'] = False
except:
    pass

# 현재 디렉토리를 sys.path에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from mmpose.apis import init_model, inference_topdown

class ComprehensivePerformanceTester:
    """종합 성능 테스터"""
    
    def __init__(self, video_path, device='cuda:0'):
        self.video_path = video_path
        self.device = device
        
        # 비디오 정보
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise FileNotFoundError(f"비디오 파일을 열 수 없습니다: {video_path}")
        
        self.video_fps = cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.video_duration = self.total_frames / self.video_fps if self.video_fps > 0 else 0
        cap.release()
        
        print(f"[테스트] 비디오 정보:")
        print(f"  - 총 프레임: {self.total_frames}")
        print(f"  - FPS: {self.video_fps:.2f}")
        print(f"  - 길이: {self.video_duration:.2f}초")
        
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
            
            dummy_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            with torch.no_grad():
                _ = inference_topdown(self.model, dummy_image)
            torch.cuda.empty_cache()
            print("[테스트] GPU 워밍업 완료")
        
        # 최적 설정 (이전 테스트 결과)
        self.batch_size = 10
        self.queue_size = 22
        self.inference_scale = 0.65
        
        print(f"\n[테스트] 현재 설정:")
        print(f"  - 배치 크기: {self.batch_size}")
        print(f"  - 큐 크기: {self.queue_size}")
        print(f"  - 추론 해상도: {int(self.inference_scale*100)}%")
    
    def get_gpu_stats(self):
        """GPU 사용률 및 메모리 측정 (nvidia-smi)"""
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu', 
                 '--format=csv,noheader,nounits'],
                capture_output=True,
                text=True,
                timeout=1
            )
            
            if result.returncode == 0:
                output = result.stdout.strip()
                gpu_util, mem_used, mem_total, temp = output.split(', ')
                return {
                    'gpu_utilization': float(gpu_util),
                    'memory_used': float(mem_used),
                    'memory_total': float(mem_total),
                    'temperature': float(temp)
                }
        except Exception as e:
            pass
        
        return None
    
    def test_resolution_performance(self, resolution_name, target_width, target_height):
        """특정 해상도에서 성능 테스트"""
        print(f"\n{'='*70}")
        print(f"[테스트] {resolution_name} ({target_width}x{target_height}) 테스트 시작")
        print(f"{'='*70}")
        
        # 큐 초기화
        inference_queue = queue.Queue(maxsize=self.queue_size)
        result_queue = queue.Queue(maxsize=self.queue_size // 2)
        running = True
        
        # 성능 측정 변수
        frames_sent = 0
        frames_processed = 0
        frames_dropped = 0
        
        inference_times = []
        total_times = []
        gpu_stats_samples = []
        
        latencies = []  # 프레임 전송 → 결과 수신 시간
        frame_timestamps = {}  # 프레임 ID → 전송 시각
        
        test_start_time = time.time()
        
        # 추론 워커 스레드
        def inference_worker():
            nonlocal frames_processed, inference_times
            
            while running:
                try:
                    batch_frames = []
                    frame_ids = []
                    frame_timeout = 0.015
                    
                    for i in range(self.batch_size):
                        try:
                            timeout = frame_timeout if i == 0 else frame_timeout * 0.5
                            frame_data = inference_queue.get(timeout=timeout)
                            
                            if frame_data is None:
                                return
                            
                            frame, frame_id = frame_data
                            batch_frames.append(frame)
                            frame_ids.append(frame_id)
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
                        inference_times.append(inference_time)
                        
                        frames_processed += len(batch_frames)
                        
                        # 결과 저장 및 레이턴시 계산
                        result_timestamp = time.time()
                        for frame_id in frame_ids:
                            if frame_id in frame_timestamps:
                                latency = result_timestamp - frame_timestamps[frame_id]
                                latencies.append(latency)
                        
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
        
        # GPU 모니터링 스레드
        def gpu_monitor():
            while running:
                stats = self.get_gpu_stats()
                if stats:
                    gpu_stats_samples.append(stats)
                time.sleep(0.1)  # 100ms마다 샘플링
        
        # 워커 스레드 시작
        worker_thread = threading.Thread(target=inference_worker, daemon=True)
        worker_thread.start()
        
        if torch.cuda.is_available():
            gpu_thread = threading.Thread(target=gpu_monitor, daemon=True)
            gpu_thread.start()
        
        # 비디오 읽기 및 프레임 전송
        cap = cv2.VideoCapture(self.video_path)
        
        if not cap.isOpened():
            print(f"[테스트] [ERROR] 비디오 열기 실패")
            running = False
            return None
        
        frame_id = 0
        video_start_time = time.time()
        
        while running:
            loop_start = time.time()
            
            ret, frame = cap.read()
            if not ret:
                break
            
            # 현재 시간 체크
            elapsed = time.time() - video_start_time
            if elapsed >= self.video_duration:
                break
            
            # 해상도 조정
            resized_frame = cv2.resize(frame, (target_width, target_height), interpolation=cv2.INTER_LINEAR)
            
            # 추론용 다운스케일
            inference_w = int(target_width * self.inference_scale)
            inference_h = int(target_height * self.inference_scale)
            inference_frame = cv2.resize(resized_frame, (inference_w, inference_h), interpolation=cv2.INTER_LINEAR)
            
            # 큐에 프레임 추가
            frame_timestamps[frame_id] = time.time()
            try:
                inference_queue.put_nowait((inference_frame, frame_id))
                frames_sent += 1
            except queue.Full:
                frames_dropped += 1
            
            frame_id += 1
            
            # 전체 루프 시간 측정
            loop_time = time.time() - loop_start
            total_times.append(loop_time)
        
        # 정리
        running = False
        
        try:
            inference_queue.put(None, timeout=0.1)
        except:
            pass
        
        worker_thread.join(timeout=1.0)
        cap.release()
        
        # 결과 계산
        test_elapsed = time.time() - test_start_time
        actual_fps = frames_processed / test_elapsed if test_elapsed > 0 else 0
        drop_rate = (frames_dropped / frames_sent * 100) if frames_sent > 0 else 0
        
        # GPU 통계
        avg_gpu_util = 0
        avg_gpu_mem = 0
        avg_gpu_temp = 0
        
        if gpu_stats_samples:
            avg_gpu_util = np.mean([s['gpu_utilization'] for s in gpu_stats_samples])
            avg_gpu_mem = np.mean([s['memory_used'] for s in gpu_stats_samples])
            avg_gpu_temp = np.mean([s['temperature'] for s in gpu_stats_samples])
        
        # 레이턴시 통계
        avg_latency = np.mean(latencies) * 1000 if latencies else 0
        p50_latency = np.percentile(latencies, 50) * 1000 if latencies else 0
        p95_latency = np.percentile(latencies, 95) * 1000 if latencies else 0
        p99_latency = np.percentile(latencies, 99) * 1000 if latencies else 0
        
        # 추론 시간 통계
        avg_inference = np.mean(inference_times) * 1000 if inference_times else 0
        p50_inference = np.percentile(inference_times, 50) * 1000 if inference_times else 0
        p95_inference = np.percentile(inference_times, 95) * 1000 if inference_times else 0
        p99_inference = np.percentile(inference_times, 99) * 1000 if inference_times else 0
        
        print(f"\n[테스트] {resolution_name} 결과:")
        print(f"  📊 처리량:")
        print(f"    - 전송 프레임: {frames_sent}")
        print(f"    - 처리 프레임: {frames_processed}")
        print(f"    - 드롭 프레임: {frames_dropped} ({drop_rate:.1f}%)")
        print(f"    - 실제 FPS: {actual_fps:.2f}")
        
        print(f"\n  ⏱️ 레이턴시 (프레임 전송 → 결과 수신):")
        print(f"    - 평균: {avg_latency:.2f}ms")
        print(f"    - P50: {p50_latency:.2f}ms")
        print(f"    - P95: {p95_latency:.2f}ms")
        print(f"    - P99: {p99_latency:.2f}ms")
        
        print(f"\n  🔧 추론 시간 (배치 처리):")
        print(f"    - 평균: {avg_inference:.2f}ms")
        print(f"    - P50: {p50_inference:.2f}ms")
        print(f"    - P95: {p95_inference:.2f}ms")
        print(f"    - P99: {p99_inference:.2f}ms")
        
        if gpu_stats_samples:
            print(f"\n  🎮 GPU 사용률:")
            print(f"    - 평균 사용률: {avg_gpu_util:.1f}%")
            print(f"    - 평균 메모리: {avg_gpu_mem:.0f}MB / {gpu_stats_samples[0]['memory_total']:.0f}MB")
            print(f"    - 평균 온도: {avg_gpu_temp:.1f}°C")
        
        return {
            'resolution': resolution_name,
            'width': target_width,
            'height': target_height,
            'frames_sent': frames_sent,
            'frames_processed': frames_processed,
            'frames_dropped': frames_dropped,
            'drop_rate': drop_rate,
            'fps': actual_fps,
            'latency_avg': avg_latency,
            'latency_p50': p50_latency,
            'latency_p95': p95_latency,
            'latency_p99': p99_latency,
            'inference_avg': avg_inference,
            'inference_p50': p50_inference,
            'inference_p95': p95_inference,
            'inference_p99': p99_inference,
            'gpu_util': avg_gpu_util,
            'gpu_mem': avg_gpu_mem,
            'gpu_temp': avg_gpu_temp,
            'latencies': latencies,
            'inference_times': inference_times,
            'gpu_stats': gpu_stats_samples
        }
    
    def run_comprehensive_test(self):
        """종합 성능 테스트 실행"""
        print(f"\n{'='*70}")
        print("[테스트] 종합 성능 테스트 시작")
        print(f"{'='*70}\n")
        
        # 테스트할 해상도들
        resolutions = [
            ('480p', 854, 480),
            ('720p', 1280, 720),
            ('1080p', 1920, 1080),
        ]
        
        results = []
        
        for res_name, width, height in resolutions:
            result = self.test_resolution_performance(res_name, width, height)
            if result:
                results.append(result)
            
            # 다음 테스트 전 GPU 안정화
            time.sleep(1.0)
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        
        # 최종 결과 출력
        print(f"\n{'='*70}")
        print("[테스트] 종합 결과 비교")
        print(f"{'='*70}")
        
        print(f"\n{'해상도':<10} | {'FPS':<8} | {'드롭률':<8} | {'레이턴시(P95)':<12} | {'GPU 사용률':<10}")
        print(f"{'-'*70}")
        
        for r in results:
            print(f"{r['resolution']:<10} | {r['fps']:<8.2f} | {r['drop_rate']:<7.1f}% | "
                  f"{r['latency_p95']:<11.2f}ms | {r['gpu_util']:<9.1f}%")
        
        return results
    
    def visualize_comprehensive_results(self, results):
        """종합 결과 시각화"""
        print(f"\n[테스트] 결과 시각화 중...")
        
        if not results:
            print("[테스트] 시각화할 데이터가 없습니다.")
            return
        
        fig = plt.figure(figsize=(18, 12))
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        resolutions = [r['resolution'] for r in results]
        
        # 1. FPS 비교 (막대 그래프)
        ax1 = fig.add_subplot(gs[0, 0])
        fps_values = [r['fps'] for r in results]
        colors = ['green' if fps > 25 else 'orange' if fps > 15 else 'red' for fps in fps_values]
        ax1.bar(resolutions, fps_values, color=colors, alpha=0.7)
        ax1.axhline(y=30, color='green', linestyle='--', alpha=0.5, label='목표 FPS (30)')
        ax1.set_ylabel('FPS', fontsize=11)
        ax1.set_title('해상도별 FPS', fontsize=12, fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3, axis='y')
        
        # 2. 드롭률 비교 (막대 그래프)
        ax2 = fig.add_subplot(gs[0, 1])
        drop_rates = [r['drop_rate'] for r in results]
        colors_drop = ['green' if d < 5 else 'orange' if d < 15 else 'red' for d in drop_rates]
        ax2.bar(resolutions, drop_rates, color=colors_drop, alpha=0.7)
        ax2.axhline(y=5, color='green', linestyle='--', alpha=0.5, label='허용 범위 (5%)')
        ax2.set_ylabel('드롭률 (%)', fontsize=11)
        ax2.set_title('해상도별 프레임 드롭률', fontsize=12, fontweight='bold')
        ax2.legend()
        ax2.grid(True, alpha=0.3, axis='y')
        
        # 3. GPU 사용률 비교 (막대 그래프)
        ax3 = fig.add_subplot(gs[0, 2])
        gpu_utils = [r['gpu_util'] for r in results]
        colors_gpu = ['orange' if g < 70 else 'green' if g < 90 else 'red' for g in gpu_utils]
        ax3.bar(resolutions, gpu_utils, color=colors_gpu, alpha=0.7)
        ax3.axhline(y=85, color='green', linestyle='--', alpha=0.5, label='목표 사용률 (85%)')
        ax3.set_ylabel('GPU 사용률 (%)', fontsize=11)
        ax3.set_title('해상도별 GPU 사용률', fontsize=12, fontweight='bold')
        ax3.legend()
        ax3.grid(True, alpha=0.3, axis='y')
        
        # 4. 레이턴시 분포 (박스플롯)
        ax4 = fig.add_subplot(gs[1, 0])
        latency_data = [r['latencies'] for r in results if r['latencies']]
        if latency_data:
            latency_data_ms = [[l * 1000 for l in latencies] for latencies in latency_data]
            bp = ax4.boxplot(latency_data_ms, labels=resolutions, patch_artist=True)
            for patch in bp['boxes']:
                patch.set_facecolor('lightblue')
            ax4.axhline(y=100, color='green', linestyle='--', alpha=0.5, label='목표 레이턴시 (100ms)')
            ax4.set_ylabel('레이턴시 (ms)', fontsize=11)
            ax4.set_title('레이턴시 분포 (전송→수신)', fontsize=12, fontweight='bold')
            ax4.legend()
            ax4.grid(True, alpha=0.3, axis='y')
        
        # 5. 추론 시간 분포 (박스플롯)
        ax5 = fig.add_subplot(gs[1, 1])
        inference_data = [r['inference_times'] for r in results if r['inference_times']]
        if inference_data:
            inference_data_ms = [[t * 1000 for t in times] for times in inference_data]
            bp2 = ax5.boxplot(inference_data_ms, labels=resolutions, patch_artist=True)
            for patch in bp2['boxes']:
                patch.set_facecolor('lightgreen')
            ax5.set_ylabel('추론 시간 (ms)', fontsize=11)
            ax5.set_title('추론 시간 분포 (배치)', fontsize=12, fontweight='bold')
            ax5.grid(True, alpha=0.3, axis='y')
        
        # 6. GPU 메모리 사용량 (막대 그래프)
        ax6 = fig.add_subplot(gs[1, 2])
        gpu_mems = [r['gpu_mem'] for r in results]
        ax6.bar(resolutions, gpu_mems, color='purple', alpha=0.7)
        ax6.set_ylabel('GPU 메모리 (MB)', fontsize=11)
        ax6.set_title('해상도별 GPU 메모리 사용량', fontsize=12, fontweight='bold')
        ax6.grid(True, alpha=0.3, axis='y')
        
        # 7. 레이턴시 P95/P99 비교 (그룹 막대)
        ax7 = fig.add_subplot(gs[2, 0])
        x = np.arange(len(resolutions))
        width = 0.35
        p95_values = [r['latency_p95'] for r in results]
        p99_values = [r['latency_p99'] for r in results]
        ax7.bar(x - width/2, p95_values, width, label='P95', color='orange', alpha=0.7)
        ax7.bar(x + width/2, p99_values, width, label='P99', color='red', alpha=0.7)
        ax7.set_ylabel('레이턴시 (ms)', fontsize=11)
        ax7.set_title('레이턴시 P95/P99 비교', fontsize=12, fontweight='bold')
        ax7.set_xticks(x)
        ax7.set_xticklabels(resolutions)
        ax7.legend()
        ax7.grid(True, alpha=0.3, axis='y')
        
        # 8. 추론 시간 P95/P99 비교 (그룹 막대)
        ax8 = fig.add_subplot(gs[2, 1])
        inf_p95_values = [r['inference_p95'] for r in results]
        inf_p99_values = [r['inference_p99'] for r in results]
        ax8.bar(x - width/2, inf_p95_values, width, label='P95', color='lightblue', alpha=0.7)
        ax8.bar(x + width/2, inf_p99_values, width, label='P99', color='darkblue', alpha=0.7)
        ax8.set_ylabel('추론 시간 (ms)', fontsize=11)
        ax8.set_title('추론 시간 P95/P99 비교', fontsize=12, fontweight='bold')
        ax8.set_xticks(x)
        ax8.set_xticklabels(resolutions)
        ax8.legend()
        ax8.grid(True, alpha=0.3, axis='y')
        
        # 9. 종합 점수 (레이더 차트)
        ax9 = fig.add_subplot(gs[2, 2], projection='polar')
        
        # 정규화된 점수 계산 (0-100)
        metrics = []
        for r in results:
            fps_score = min(r['fps'] / 30 * 100, 100)  # 30 FPS 기준
            drop_score = max(100 - r['drop_rate'] * 10, 0)  # 드롭률 낮을수록 좋음
            latency_score = max(100 - r['latency_p95'] / 2, 0)  # 200ms 기준
            gpu_score = r['gpu_util']  # 이미 0-100
            
            metrics.append([fps_score, drop_score, latency_score, gpu_score])
        
        categories = ['FPS', '안정성', '응답성', 'GPU활용']
        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        angles += angles[:1]
        
        for i, (res, metric) in enumerate(zip(resolutions, metrics)):
            values = metric + metric[:1]
            ax9.plot(angles, values, 'o-', linewidth=2, label=res)
            ax9.fill(angles, values, alpha=0.15)
        
        ax9.set_xticks(angles[:-1])
        ax9.set_xticklabels(categories, fontsize=10)
        ax9.set_ylim(0, 100)
        ax9.set_title('종합 성능 점수', fontsize=12, fontweight='bold', pad=20)
        ax9.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
        ax9.grid(True)
        
        plt.suptitle('가상 피팅 시스템 종합 성능 분석', fontsize=16, fontweight='bold')
        
        # 저장
        output_path = os.path.join(current_dir, 'comprehensive_performance_result.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"[테스트] 그래프 저장: {output_path}")
        
        plt.show()
        
        return output_path


def main():
    """메인 함수"""
    video_path = r"C:\Users\parkj\Desktop\ponggwi\source\basic.mp4"
    
    if not os.path.exists(video_path):
        print(f"[ERROR] 비디오 파일을 찾을 수 없습니다: {video_path}")
        return
    
    device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
    print(f"[테스트] Device: {device}")
    
    if device == 'cpu':
        print("[WARNING] GPU를 사용할 수 없습니다. CPU 모드로 실행합니다.")
    
    # 테스터 생성 및 실행
    tester = ComprehensivePerformanceTester(video_path, device=device)
    results = tester.run_comprehensive_test()
    
    if results:
        print(f"\n[테스트] 테스트 완료! {len(results)}개 해상도 테스트됨")
        
        # 시각화
        graph_path = tester.visualize_comprehensive_results(results)
        print(f"\n[테스트] 시각화 완료: {graph_path}")
        
        # JSON 저장
        json_path = os.path.join(current_dir, 'comprehensive_performance_result.json')
        
        # JSON 직렬화를 위해 numpy 배열 제거
        results_for_json = []
        for r in results:
            r_copy = r.copy()
            r_copy.pop('latencies', None)
            r_copy.pop('inference_times', None)
            r_copy.pop('gpu_stats', None)
            results_for_json.append(r_copy)
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results_for_json, f, indent=2, ensure_ascii=False)
        
        print(f"[테스트] JSON 저장: {json_path}")


if __name__ == "__main__":
    main()
