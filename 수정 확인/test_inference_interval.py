"""
추론 간격(Inference Interval) 최적화 테스트
- 추론 간격을 0.02초 ~ 0.1초까지 변경하며 테스트
- FPS, GPU 사용률, 레이턴시 측정
- 실제 virtual_fitting.py 사용
"""

import cv2
import numpy as np
import time
import sys
import os
import subprocess
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc

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

# virtual_fitting import
from virtual_fitting import RTMPoseVirtualFitting
import torch


class InferenceIntervalTester:
    """추론 간격 최적화 테스터"""
    
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
    
    def get_gpu_stats(self):
        """GPU 사용률 및 메모리 측정"""
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=utilization.gpu,memory.used,temperature.gpu', 
                 '--format=csv,noheader,nounits'],
                capture_output=True,
                text=True,
                timeout=1
            )
            
            if result.returncode == 0:
                output = result.stdout.strip()
                gpu_util, mem_used, temp = output.split(', ')
                return {
                    'gpu_utilization': float(gpu_util),
                    'memory_used': float(mem_used),
                    'temperature': float(temp)
                }
        except Exception as e:
            pass
        
        return None
    
    def test_single_interval(self, inference_interval):
        """단일 추론 간격 테스트"""
        print(f"\n{'='*70}")
        print(f"[테스트] 추론 간격 {inference_interval*1000:.0f}ms ({1/inference_interval:.1f} FPS) 테스트")
        print(f"{'='*70}")
        
        # Virtual Fitting 인스턴스 생성 (새로운 설정으로)
        print("[테스트] Virtual Fitting 초기화 중...")
        try:
            vf = RTMPoseVirtualFitting(
                cloth_image_path='input/cloth.jpg',
                device=self.device
            )
        except Exception as e:
            print(f"[테스트] [ERROR] Virtual Fitting 초기화 실패: {e}")
            import traceback
            traceback.print_exc()
            return None
        
        # 추론 간격 변경
        vf.inference_interval = inference_interval
        vf.actual_inference_interval = inference_interval
        
        # 스트리밍 활성화
        vf.start_streaming()
        
        print(f"[테스트] 설정 완료:")
        print(f"  - 추론 간격: {inference_interval*1000:.0f}ms")
        print(f"  - 배치 크기: {vf.batch_size}")
        print(f"  - 큐 크기: {vf.inference_queue.maxsize}")
        print(f"  - 추론 해상도: {int(vf.inference_scale*100)}%")
        
        # 성능 측정 변수
        frames_processed = 0
        process_times = []
        gpu_stats_samples = []
        
        test_start_time = time.time()
        
        # 비디오 읽기
        cap = cv2.VideoCapture(self.video_path)
        
        if not cap.isOpened():
            print(f"[테스트] [ERROR] 비디오 열기 실패")
            vf.stop_streaming()
            vf.stop_inference_thread()
            return None
        
        frame_count = 0
        video_start_time = time.time()
        
        # GPU 모니터링 시작
        last_gpu_check = time.time()
        gpu_check_interval = 0.2  # 200ms마다 GPU 체크
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # 시간 체크
            elapsed = time.time() - video_start_time
            if elapsed >= self.video_duration:
                break
            
            # 프레임 처리
            process_start = time.time()
            result_frame = vf.process_frame(frame, show_skeleton=False, use_warp=True)
            process_end = time.time()
            
            process_time = process_end - process_start
            process_times.append(process_time)
            frames_processed += 1
            frame_count += 1
            
            # GPU 통계 수집
            current_time = time.time()
            if current_time - last_gpu_check >= gpu_check_interval:
                stats = self.get_gpu_stats()
                if stats:
                    gpu_stats_samples.append(stats)
                last_gpu_check = current_time
        
        # 정리
        cap.release()
        vf.stop_streaming()
        vf.stop_inference_thread()
        
        # 결과 계산
        test_elapsed = time.time() - test_start_time
        actual_fps = frames_processed / test_elapsed if test_elapsed > 0 else 0
        
        avg_process_time = np.mean(process_times) * 1000 if process_times else 0
        p50_process_time = np.percentile(process_times, 50) * 1000 if process_times else 0
        p95_process_time = np.percentile(process_times, 95) * 1000 if process_times else 0
        p99_process_time = np.percentile(process_times, 99) * 1000 if process_times else 0
        
        # GPU 통계
        avg_gpu_util = 0
        avg_gpu_mem = 0
        avg_gpu_temp = 0
        
        if gpu_stats_samples:
            avg_gpu_util = np.mean([s['gpu_utilization'] for s in gpu_stats_samples])
            avg_gpu_mem = np.mean([s['memory_used'] for s in gpu_stats_samples])
            avg_gpu_temp = np.mean([s['temperature'] for s in gpu_stats_samples])
        
        print(f"\n[테스트] 결과:")
        print(f"  📊 처리량:")
        print(f"    - 처리 프레임: {frames_processed}")
        print(f"    - 실제 FPS: {actual_fps:.2f}")
        print(f"    - 테스트 시간: {test_elapsed:.2f}초")
        
        print(f"\n  ⏱️ 프레임 처리 시간:")
        print(f"    - 평균: {avg_process_time:.2f}ms")
        print(f"    - P50: {p50_process_time:.2f}ms")
        print(f"    - P95: {p95_process_time:.2f}ms")
        print(f"    - P99: {p99_process_time:.2f}ms")
        
        if gpu_stats_samples:
            print(f"\n  🎮 GPU 사용률:")
            print(f"    - 평균 사용률: {avg_gpu_util:.1f}%")
            print(f"    - 평균 메모리: {avg_gpu_mem:.0f}MB")
            print(f"    - 평균 온도: {avg_gpu_temp:.1f}°C")
        
        # GPU 메모리 정리
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        # 약간 대기 (다음 테스트를 위해)
        time.sleep(1.0)
        
        return {
            'inference_interval': inference_interval,
            'target_fps': 1 / inference_interval,
            'frames_processed': frames_processed,
            'actual_fps': actual_fps,
            'avg_process_time': avg_process_time,
            'p50_process_time': p50_process_time,
            'p95_process_time': p95_process_time,
            'p99_process_time': p99_process_time,
            'gpu_util': avg_gpu_util,
            'gpu_mem': avg_gpu_mem,
            'gpu_temp': avg_gpu_temp,
            'process_times': process_times,
            'gpu_stats': gpu_stats_samples
        }
    
    def run_interval_test(self):
        """추론 간격 테스트 실행"""
        print(f"\n{'='*70}")
        print("[테스트] 추론 간격 최적화 테스트 시작")
        print(f"{'='*70}\n")
        
        # 테스트할 추론 간격들 (초 단위)
        # 0.02초 (50 FPS) ~ 0.1초 (10 FPS)
        intervals = [
            0.02,   # 50 FPS
            0.025,  # 40 FPS
            0.03,   # 33 FPS
            0.04,   # 25 FPS (현재 설정)
            0.05,   # 20 FPS
            0.067,  # 15 FPS
            0.1,    # 10 FPS
        ]
        
        results = []
        
        for interval in intervals:
            try:
                result = self.test_single_interval(interval)
                if result:
                    results.append(result)
            except Exception as e:
                print(f"[테스트] [ERROR] 간격 {interval*1000:.0f}ms 테스트 실패: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        if not results:
            print("[테스트] [ERROR] 테스트 결과가 없습니다.")
            return None
        
        # 최종 결과 출력
        print(f"\n{'='*70}")
        print("[테스트] 종합 결과 비교")
        print(f"{'='*70}")
        
        print(f"\n{'간격(ms)':<10} | {'목표FPS':<10} | {'실제FPS':<10} | {'처리시간(P95)':<15} | {'GPU사용률':<10}")
        print(f"{'-'*70}")
        
        for r in results:
            print(f"{r['inference_interval']*1000:<10.0f} | {r['target_fps']:<10.1f} | "
                  f"{r['actual_fps']:<10.2f} | {r['p95_process_time']:<14.2f}ms | {r['gpu_util']:<9.1f}%")
        
        # 최적 간격 찾기 (FPS가 가장 높은 것)
        best_result = max(results, key=lambda x: x['actual_fps'])
        print(f"\n[테스트] 🏆 최적 추론 간격: {best_result['inference_interval']*1000:.0f}ms "
              f"({best_result['target_fps']:.1f} FPS)")
        print(f"  - 실제 FPS: {best_result['actual_fps']:.2f}")
        print(f"  - GPU 사용률: {best_result['gpu_util']:.1f}%")
        
        return results
    
    def visualize_results(self, results):
        """결과 시각화"""
        print(f"\n[테스트] 결과 시각화 중...")
        
        if not results:
            print("[테스트] 시각화할 데이터가 없습니다.")
            return
        
        intervals_ms = [r['inference_interval'] * 1000 for r in results]
        target_fps_values = [r['target_fps'] for r in results]
        actual_fps_values = [r['actual_fps'] for r in results]
        p95_times = [r['p95_process_time'] for r in results]
        gpu_utils = [r['gpu_util'] for r in results]
        gpu_mems = [r['gpu_mem'] for r in results]
        
        # Figure 생성 (6개 서브플롯)
        fig = plt.figure(figsize=(18, 12))
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        # 1. FPS 비교 (목표 vs 실제)
        ax1 = fig.add_subplot(gs[0, 0])
        x = np.arange(len(intervals_ms))
        width = 0.35
        ax1.bar(x - width/2, target_fps_values, width, label='목표 FPS', color='lightblue', alpha=0.7)
        ax1.bar(x + width/2, actual_fps_values, width, label='실제 FPS', color='orange', alpha=0.7)
        ax1.set_xlabel('추론 간격 (ms)', fontsize=11)
        ax1.set_ylabel('FPS', fontsize=11)
        ax1.set_title('목표 FPS vs 실제 FPS', fontsize=12, fontweight='bold')
        ax1.set_xticks(x)
        ax1.set_xticklabels([f'{int(i)}' for i in intervals_ms])
        ax1.legend()
        ax1.grid(True, alpha=0.3, axis='y')
        
        # 2. 실제 FPS (선 그래프)
        ax2 = fig.add_subplot(gs[0, 1])
        ax2.plot(intervals_ms, actual_fps_values, 'o-', linewidth=2, markersize=8, color='green')
        max_fps_idx = actual_fps_values.index(max(actual_fps_values))
        ax2.plot(intervals_ms[max_fps_idx], actual_fps_values[max_fps_idx], 
                'r*', markersize=20, label=f'최고 ({actual_fps_values[max_fps_idx]:.2f} FPS)')
        ax2.axhline(y=30, color='blue', linestyle='--', alpha=0.5, label='목표 (30 FPS)')
        ax2.set_xlabel('추론 간격 (ms)', fontsize=11)
        ax2.set_ylabel('실제 FPS', fontsize=11)
        ax2.set_title('추론 간격별 실제 FPS', fontsize=12, fontweight='bold')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. GPU 사용률
        ax3 = fig.add_subplot(gs[0, 2])
        colors_gpu = ['orange' if g < 70 else 'green' if g < 90 else 'red' for g in gpu_utils]
        ax3.bar(intervals_ms, gpu_utils, color=colors_gpu, alpha=0.7)
        ax3.axhline(y=85, color='green', linestyle='--', alpha=0.5, label='목표 (85%)')
        ax3.set_xlabel('추론 간격 (ms)', fontsize=11)
        ax3.set_ylabel('GPU 사용률 (%)', fontsize=11)
        ax3.set_title('추론 간격별 GPU 사용률', fontsize=12, fontweight='bold')
        ax3.legend()
        ax3.grid(True, alpha=0.3, axis='y')
        
        # 4. 프레임 처리 시간 (P95)
        ax4 = fig.add_subplot(gs[1, 0])
        ax4.plot(intervals_ms, p95_times, 'o-', linewidth=2, markersize=8, color='purple')
        ax4.set_xlabel('추론 간격 (ms)', fontsize=11)
        ax4.set_ylabel('처리 시간 (ms)', fontsize=11)
        ax4.set_title('프레임 처리 시간 (P95)', fontsize=12, fontweight='bold')
        ax4.grid(True, alpha=0.3)
        
        # 5. GPU 메모리 사용량
        ax5 = fig.add_subplot(gs[1, 1])
        ax5.bar(intervals_ms, gpu_mems, color='purple', alpha=0.7)
        ax5.set_xlabel('추론 간격 (ms)', fontsize=11)
        ax5.set_ylabel('GPU 메모리 (MB)', fontsize=11)
        ax5.set_title('추론 간격별 GPU 메모리', fontsize=12, fontweight='bold')
        ax5.grid(True, alpha=0.3, axis='y')
        
        # 6. 효율성 점수 (FPS / GPU 사용률)
        ax6 = fig.add_subplot(gs[1, 2])
        efficiency = [fps / max(gpu, 1) * 100 for fps, gpu in zip(actual_fps_values, gpu_utils)]
        ax6.bar(intervals_ms, efficiency, color='teal', alpha=0.7)
        max_eff_idx = efficiency.index(max(efficiency))
        ax6.bar(intervals_ms[max_eff_idx], efficiency[max_eff_idx], color='gold', alpha=0.9, 
                label=f'최고 효율 ({intervals_ms[max_eff_idx]:.0f}ms)')
        ax6.set_xlabel('추론 간격 (ms)', fontsize=11)
        ax6.set_ylabel('효율성 점수', fontsize=11)
        ax6.set_title('효율성 점수 (FPS/GPU사용률 × 100)', fontsize=12, fontweight='bold')
        ax6.legend()
        ax6.grid(True, alpha=0.3, axis='y')
        
        # 7. 처리 시간 분포 (박스플롯)
        ax7 = fig.add_subplot(gs[2, 0])
        process_time_data = [r['process_times'] for r in results if r['process_times']]
        if process_time_data:
            process_time_data_ms = [[t * 1000 for t in times] for times in process_time_data]
            bp = ax7.boxplot(process_time_data_ms, labels=[f'{int(i)}' for i in intervals_ms], 
                            patch_artist=True)
            for patch in bp['boxes']:
                patch.set_facecolor('lightgreen')
            ax7.set_xlabel('추론 간격 (ms)', fontsize=11)
            ax7.set_ylabel('처리 시간 (ms)', fontsize=11)
            ax7.set_title('처리 시간 분포', fontsize=12, fontweight='bold')
            ax7.grid(True, alpha=0.3, axis='y')
        
        # 8. FPS 달성률 (실제/목표)
        ax8 = fig.add_subplot(gs[2, 1])
        achievement_rate = [actual / target * 100 for actual, target in zip(actual_fps_values, target_fps_values)]
        colors_ach = ['green' if a >= 90 else 'orange' if a >= 70 else 'red' for a in achievement_rate]
        ax8.bar(intervals_ms, achievement_rate, color=colors_ach, alpha=0.7)
        ax8.axhline(y=100, color='green', linestyle='--', alpha=0.5, label='100% 달성')
        ax8.set_xlabel('추론 간격 (ms)', fontsize=11)
        ax8.set_ylabel('달성률 (%)', fontsize=11)
        ax8.set_title('FPS 목표 달성률', fontsize=12, fontweight='bold')
        ax8.legend()
        ax8.grid(True, alpha=0.3, axis='y')
        
        # 9. 종합 점수 (레이더 차트)
        ax9 = fig.add_subplot(gs[2, 2], projection='polar')
        
        # 정규화된 점수 계산
        max_fps = max(actual_fps_values)
        max_gpu = max(gpu_utils)
        
        # 각 간격별 점수
        selected_indices = [0, 3, 6]  # 50 FPS, 25 FPS, 10 FPS
        categories = ['FPS', 'GPU활용', '효율성', '안정성']
        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        angles += angles[:1]
        
        for idx in selected_indices:
            if idx < len(results):
                r = results[idx]
                fps_score = r['actual_fps'] / max_fps * 100
                gpu_score = r['gpu_util']
                efficiency_score = efficiency[idx] / max(efficiency) * 100
                stability_score = 100 - (r['p95_process_time'] - r['p50_process_time']) / r['p95_process_time'] * 100
                
                values = [fps_score, gpu_score, efficiency_score, stability_score]
                values += values[:1]
                
                label = f"{r['inference_interval']*1000:.0f}ms"
                ax9.plot(angles, values, 'o-', linewidth=2, label=label)
                ax9.fill(angles, values, alpha=0.15)
        
        ax9.set_xticks(angles[:-1])
        ax9.set_xticklabels(categories, fontsize=10)
        ax9.set_ylim(0, 100)
        ax9.set_title('종합 성능 비교', fontsize=12, fontweight='bold', pad=20)
        ax9.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
        ax9.grid(True)
        
        plt.suptitle('추론 간격(Inference Interval) 최적화 테스트 결과', 
                    fontsize=16, fontweight='bold')
        
        # 저장
        output_path = os.path.join(current_dir, 'inference_interval_optimization_result.png')
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
    tester = InferenceIntervalTester(video_path, device=device)
    results = tester.run_interval_test()
    
    if results:
        print(f"\n[테스트] 테스트 완료! {len(results)}개 간격 테스트됨")
        
        # 시각화
        graph_path = tester.visualize_results(results)
        print(f"\n[테스트] 시각화 완료: {graph_path}")


if __name__ == "__main__":
    main()
