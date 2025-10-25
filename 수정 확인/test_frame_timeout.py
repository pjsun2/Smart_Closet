"""
프레임 타임아웃 최적화 테스트 (프레임 보간 ON/OFF 비교)
- 프레임 타임아웃: 배치 수집 대기 시간
- 프레임 보간: 추론 결과 사이의 부드러운 전환
"""

import cv2
import numpy as np
import time
import sys
import os
import matplotlib.pyplot as plt
from collections import defaultdict
import threading
import matplotlib.font_manager as fm

# 현재 디렉토리를 sys.path에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from virtual_fitting import RTMPoseVirtualFitting

# 한글 폰트 설정 (matplotlib)
def setup_korean_font():
    """matplotlib 한글 폰트 설정"""
    try:
        # Windows 기본 한글 폰트 사용
        plt.rcParams['font.family'] = 'Malgun Gothic'  # 맑은 고딕
        plt.rcParams['axes.unicode_minus'] = False  # 마이너스 기호 깨짐 방지
        print("[폰트 설정] 한글 폰트 적용: 맑은 고딕")
    except Exception as e:
        try:
            # 맑은 고딕이 없으면 다른 한글 폰트 시도
            plt.rcParams['font.family'] = 'NanumGothic'
            plt.rcParams['axes.unicode_minus'] = False
            print("[폰트 설정] 한글 폰트 적용: 나눔고딕")
        except Exception as e2:
            print(f"[폰트 설정] 한글 폰트 설정 실패: {e2}")
            print("[폰트 설정] 기본 폰트 사용 (한글이 깨질 수 있음)")

# 한글 폰트 설정 실행
setup_korean_font()

# GPU 통계 수집 (nvidia-smi)
def get_gpu_stats():
    """GPU 사용률, 메모리, 온도 수집"""
    try:
        import subprocess
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=utilization.gpu,memory.used,temperature.gpu', 
             '--format=csv,noheader,nounits'],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0:
            stats = result.stdout.strip().split(',')
            return {
                'gpu_util': float(stats[0].strip()),
                'gpu_memory': float(stats[1].strip()),
                'gpu_temp': float(stats[2].strip())
            }
    except Exception as e:
        print(f"[WARNING] GPU 통계 수집 실패: {e}")
    
    return {'gpu_util': 0, 'gpu_memory': 0, 'gpu_temp': 0}

class GPUMonitor:
    """백그라운드 GPU 모니터링"""
    def __init__(self):
        self.running = False
        self.thread = None
        self.stats = []
        
    def start(self):
        self.running = True
        self.stats = []
        self.thread = threading.Thread(target=self._monitor, daemon=True)
        self.thread.start()
    
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
    
    def _monitor(self):
        while self.running:
            stats = get_gpu_stats()
            stats['timestamp'] = time.time()
            self.stats.append(stats)
            time.sleep(0.1)  # 100ms 간격
    
    def get_average_stats(self):
        if not self.stats:
            return {'gpu_util': 0, 'gpu_memory': 0, 'gpu_temp': 0}
        
        return {
            'gpu_util': np.mean([s['gpu_util'] for s in self.stats]),
            'gpu_memory': np.mean([s['gpu_memory'] for s in self.stats]),
            'gpu_temp': np.mean([s['gpu_temp'] for s in self.stats])
        }

def test_frame_timeout(video_path, timeout_ms, interpolation_enabled, cloth_path='input/cloth.jpg'):
    """
    특정 프레임 타임아웃으로 가상 피팅 테스트
    
    Args:
        video_path: 테스트 비디오 경로
        timeout_ms: 프레임 타임아웃 (밀리초)
        interpolation_enabled: 프레임 보간 활성화 여부
        cloth_path: 옷 이미지 경로
    
    Returns:
        성능 메트릭 딕셔너리
    """
    print(f"\n{'='*80}")
    print(f"[테스트 시작] 프레임 타임아웃: {timeout_ms}ms, 보간: {'ON' if interpolation_enabled else 'OFF'}")
    print(f"{'='*80}")
    
    # GPU 모니터 시작
    gpu_monitor = GPUMonitor()
    gpu_monitor.start()
    
    # RTMPose 가상 피팅 초기화
    try:
        vf = RTMPoseVirtualFitting(cloth_image_path=cloth_path, device='cuda:0')
        
        # 프레임 타임아웃 설정 (배치 수집 대기 시간, 밀리초 → 초)
        vf.frame_timeout = timeout_ms / 1000.0
        
        # 프레임 보간 설정
        vf.interpolation_enabled = interpolation_enabled
        
        # 스트리밍 시작
        vf.start_streaming()
        
    except Exception as e:
        print(f"[ERROR] 가상 피팅 초기화 실패: {e}")
        gpu_monitor.stop()
        return None
    
    # 비디오 캡처
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"[ERROR] 비디오 열기 실패: {video_path}")
        gpu_monitor.stop()
        return None
    
    # 비디오 정보
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    duration = total_frames / fps
    
    print(f"[비디오 정보] 프레임: {total_frames}, FPS: {fps:.2f}, 길이: {duration:.2f}초")
    
    # 성능 측정 변수
    frame_times = []
    processing_times = []
    frame_count = 0
    
    start_time = time.time()
    
    # 프레임 처리
    while cap.isOpened():
        frame_start = time.time()
        
        ret, frame = cap.read()
        if not ret:
            break
        
        # 가상 피팅 처리
        process_start = time.time()
        result_frame = vf.process_frame(frame, show_skeleton=False, use_warp=True)
        process_end = time.time()
        
        processing_time = (process_end - process_start) * 1000  # ms
        processing_times.append(processing_time)
        
        frame_end = time.time()
        frame_time = frame_end - frame_start
        frame_times.append(frame_time)
        
        frame_count += 1
        
        # 진행률 표시
        if frame_count % 30 == 0:
            avg_fps = frame_count / (time.time() - start_time)
            print(f"[진행중] 프레임: {frame_count}/{total_frames}, FPS: {avg_fps:.2f}")
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # GPU 모니터 종료
    gpu_monitor.stop()
    gpu_stats = gpu_monitor.get_average_stats()
    
    # 가상 피팅 종료
    vf.stop_streaming()
    vf.stop_inference_thread()
    cap.release()
    
    # 성능 메트릭 계산
    actual_fps = frame_count / total_time
    avg_processing_time = np.mean(processing_times)
    p50_processing_time = np.percentile(processing_times, 50)
    p95_processing_time = np.percentile(processing_times, 95)
    p99_processing_time = np.percentile(processing_times, 99)
    
    metrics = {
        'timeout_ms': timeout_ms,
        'interpolation': interpolation_enabled,
        'frame_count': frame_count,
        'total_time': total_time,
        'actual_fps': actual_fps,
        'avg_processing_time': avg_processing_time,
        'p50_processing_time': p50_processing_time,
        'p95_processing_time': p95_processing_time,
        'p99_processing_time': p99_processing_time,
        'gpu_util': gpu_stats['gpu_util'],
        'gpu_memory': gpu_stats['gpu_memory'],
        'gpu_temp': gpu_stats['gpu_temp'],
        'frame_times': frame_times,
        'processing_times': processing_times
    }
    
    print(f"\n[테스트 완료]")
    print(f"  - 처리 프레임: {frame_count}")
    print(f"  - 총 시간: {total_time:.2f}초")
    print(f"  - 실제 FPS: {actual_fps:.2f}")
    print(f"  - 평균 처리 시간: {avg_processing_time:.2f}ms")
    print(f"  - P50 처리 시간: {p50_processing_time:.2f}ms")
    print(f"  - P95 처리 시간: {p95_processing_time:.2f}ms")
    print(f"  - GPU 사용률: {gpu_stats['gpu_util']:.1f}%")
    print(f"  - GPU 메모리: {gpu_stats['gpu_memory']:.0f}MB")
    print(f"  - GPU 온도: {gpu_stats['gpu_temp']:.1f}°C")
    
    return metrics

def visualize_results(all_results):
    """
    테스트 결과 시각화 (12개 차트)
    
    Args:
        all_results: 모든 테스트 결과 리스트
    """
    print("\n[시각화 생성 중...]")
    
    # 보간 ON/OFF로 분리
    results_interp_on = [r for r in all_results if r['interpolation']]
    results_interp_off = [r for r in all_results if not r['interpolation']]
    
    # Figure 생성 (4행 3열)
    fig = plt.figure(figsize=(20, 24))
    
    # 색상 정의
    color_on = '#2ecc71'  # 녹색 (보간 ON)
    color_off = '#e74c3c'  # 빨강 (보간 OFF)
    
    # === 1. FPS 비교 (보간 ON) ===
    ax1 = plt.subplot(4, 3, 1)
    timeouts_on = [r['timeout_ms'] for r in results_interp_on]
    fps_on = [r['actual_fps'] for r in results_interp_on]
    ax1.plot(timeouts_on, fps_on, 'o-', color=color_on, linewidth=2, markersize=8, label='보간 ON')
    ax1.set_xlabel('프레임 타임아웃 (ms)', fontsize=12)
    ax1.set_ylabel('실제 FPS', fontsize=12)
    ax1.set_title('1. FPS vs 프레임 타임아웃 (보간 ON)', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=10)
    
    # === 2. FPS 비교 (보간 OFF) ===
    ax2 = plt.subplot(4, 3, 2)
    timeouts_off = [r['timeout_ms'] for r in results_interp_off]
    fps_off = [r['actual_fps'] for r in results_interp_off]
    ax2.plot(timeouts_off, fps_off, 's-', color=color_off, linewidth=2, markersize=8, label='보간 OFF')
    ax2.set_xlabel('프레임 타임아웃 (ms)', fontsize=12)
    ax2.set_ylabel('실제 FPS', fontsize=12)
    ax2.set_title('2. FPS vs 프레임 타임아웃 (보간 OFF)', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.legend(fontsize=10)
    
    # === 3. FPS 비교 (보간 ON vs OFF) ===
    ax3 = plt.subplot(4, 3, 3)
    ax3.plot(timeouts_on, fps_on, 'o-', color=color_on, linewidth=2, markersize=8, label='보간 ON')
    ax3.plot(timeouts_off, fps_off, 's-', color=color_off, linewidth=2, markersize=8, label='보간 OFF')
    ax3.set_xlabel('프레임 타임아웃 (ms)', fontsize=12)
    ax3.set_ylabel('실제 FPS', fontsize=12)
    ax3.set_title('3. FPS 비교 (보간 ON vs OFF)', fontsize=14, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    ax3.legend(fontsize=10)
    
    # === 4. 처리 시간 비교 (평균) ===
    ax4 = plt.subplot(4, 3, 4)
    proc_time_on = [r['avg_processing_time'] for r in results_interp_on]
    proc_time_off = [r['avg_processing_time'] for r in results_interp_off]
    ax4.plot(timeouts_on, proc_time_on, 'o-', color=color_on, linewidth=2, markersize=8, label='보간 ON')
    ax4.plot(timeouts_off, proc_time_off, 's-', color=color_off, linewidth=2, markersize=8, label='보간 OFF')
    ax4.set_xlabel('프레임 타임아웃 (ms)', fontsize=12)
    ax4.set_ylabel('평균 처리 시간 (ms)', fontsize=12)
    ax4.set_title('4. 평균 처리 시간 비교', fontsize=14, fontweight='bold')
    ax4.grid(True, alpha=0.3)
    ax4.legend(fontsize=10)
    
    # === 5. 처리 시간 분포 (P50, P95, P99 - 보간 ON) ===
    ax5 = plt.subplot(4, 3, 5)
    p50_on = [r['p50_processing_time'] for r in results_interp_on]
    p95_on = [r['p95_processing_time'] for r in results_interp_on]
    p99_on = [r['p99_processing_time'] for r in results_interp_on]
    ax5.plot(timeouts_on, p50_on, 'o-', color='#3498db', linewidth=2, markersize=8, label='P50')
    ax5.plot(timeouts_on, p95_on, 's-', color='#f39c12', linewidth=2, markersize=8, label='P95')
    ax5.plot(timeouts_on, p99_on, '^-', color='#e74c3c', linewidth=2, markersize=8, label='P99')
    ax5.set_xlabel('프레임 타임아웃 (ms)', fontsize=12)
    ax5.set_ylabel('처리 시간 (ms)', fontsize=12)
    ax5.set_title('5. 처리 시간 분포 (보간 ON)', fontsize=14, fontweight='bold')
    ax5.grid(True, alpha=0.3)
    ax5.legend(fontsize=10)
    
    # === 6. 처리 시간 분포 (P50, P95, P99 - 보간 OFF) ===
    ax6 = plt.subplot(4, 3, 6)
    p50_off = [r['p50_processing_time'] for r in results_interp_off]
    p95_off = [r['p95_processing_time'] for r in results_interp_off]
    p99_off = [r['p99_processing_time'] for r in results_interp_off]
    ax6.plot(timeouts_off, p50_off, 'o-', color='#3498db', linewidth=2, markersize=8, label='P50')
    ax6.plot(timeouts_off, p95_off, 's-', color='#f39c12', linewidth=2, markersize=8, label='P95')
    ax6.plot(timeouts_off, p99_off, '^-', color='#e74c3c', linewidth=2, markersize=8, label='P99')
    ax6.set_xlabel('프레임 타임아웃 (ms)', fontsize=12)
    ax6.set_ylabel('처리 시간 (ms)', fontsize=12)
    ax6.set_title('6. 처리 시간 분포 (보간 OFF)', fontsize=14, fontweight='bold')
    ax6.grid(True, alpha=0.3)
    ax6.legend(fontsize=10)
    
    # === 7. GPU 사용률 비교 ===
    ax7 = plt.subplot(4, 3, 7)
    gpu_util_on = [r['gpu_util'] for r in results_interp_on]
    gpu_util_off = [r['gpu_util'] for r in results_interp_off]
    ax7.plot(timeouts_on, gpu_util_on, 'o-', color=color_on, linewidth=2, markersize=8, label='보간 ON')
    ax7.plot(timeouts_off, gpu_util_off, 's-', color=color_off, linewidth=2, markersize=8, label='보간 OFF')
    ax7.set_xlabel('프레임 타임아웃 (ms)', fontsize=12)
    ax7.set_ylabel('GPU 사용률 (%)', fontsize=12)
    ax7.set_title('7. GPU 사용률 비교', fontsize=14, fontweight='bold')
    ax7.grid(True, alpha=0.3)
    ax7.legend(fontsize=10)
    
    # === 8. GPU 메모리 사용량 비교 ===
    ax8 = plt.subplot(4, 3, 8)
    gpu_mem_on = [r['gpu_memory'] for r in results_interp_on]
    gpu_mem_off = [r['gpu_memory'] for r in results_interp_off]
    ax8.plot(timeouts_on, gpu_mem_on, 'o-', color=color_on, linewidth=2, markersize=8, label='보간 ON')
    ax8.plot(timeouts_off, gpu_mem_off, 's-', color=color_off, linewidth=2, markersize=8, label='보간 OFF')
    ax8.set_xlabel('프레임 타임아웃 (ms)', fontsize=12)
    ax8.set_ylabel('GPU 메모리 (MB)', fontsize=12)
    ax8.set_title('8. GPU 메모리 사용량 비교', fontsize=14, fontweight='bold')
    ax8.grid(True, alpha=0.3)
    ax8.legend(fontsize=10)
    
    # === 9. 효율성 비교 (FPS / GPU 사용률) ===
    ax9 = plt.subplot(4, 3, 9)
    efficiency_on = [fps / max(gpu, 1) for fps, gpu in zip(fps_on, gpu_util_on)]
    efficiency_off = [fps / max(gpu, 1) for fps, gpu in zip(fps_off, gpu_util_off)]
    ax9.plot(timeouts_on, efficiency_on, 'o-', color=color_on, linewidth=2, markersize=8, label='보간 ON')
    ax9.plot(timeouts_off, efficiency_off, 's-', color=color_off, linewidth=2, markersize=8, label='보간 OFF')
    ax9.set_xlabel('프레임 타임아웃 (ms)', fontsize=12)
    ax9.set_ylabel('효율성 (FPS/GPU%)', fontsize=12)
    ax9.set_title('9. 처리 효율성 비교', fontsize=14, fontweight='bold')
    ax9.grid(True, alpha=0.3)
    ax9.legend(fontsize=10)
    
    # === 10. 처리 시간 히스토그램 (최적 타임아웃 - 보간 ON) ===
    ax10 = plt.subplot(4, 3, 10)
    if results_interp_on:
        best_result_on = max(results_interp_on, key=lambda x: x['actual_fps'])
        ax10.hist(best_result_on['processing_times'], bins=50, color=color_on, alpha=0.7, edgecolor='black')
        ax10.set_xlabel('처리 시간 (ms)', fontsize=12)
        ax10.set_ylabel('빈도', fontsize=12)
        ax10.set_title(f'10. 처리 시간 분포 (보간 ON, 최적: {best_result_on["timeout_ms"]}ms)', 
                      fontsize=14, fontweight='bold')
        ax10.axvline(best_result_on['avg_processing_time'], color='red', linestyle='--', 
                    linewidth=2, label=f'평균: {best_result_on["avg_processing_time"]:.2f}ms')
        ax10.legend(fontsize=10)
        ax10.grid(True, alpha=0.3)
    
    # === 11. 처리 시간 히스토그램 (최적 타임아웃 - 보간 OFF) ===
    ax11 = plt.subplot(4, 3, 11)
    if results_interp_off:
        best_result_off = max(results_interp_off, key=lambda x: x['actual_fps'])
        ax11.hist(best_result_off['processing_times'], bins=50, color=color_off, alpha=0.7, edgecolor='black')
        ax11.set_xlabel('처리 시간 (ms)', fontsize=12)
        ax11.set_ylabel('빈도', fontsize=12)
        ax11.set_title(f'11. 처리 시간 분포 (보간 OFF, 최적: {best_result_off["timeout_ms"]}ms)', 
                      fontsize=14, fontweight='bold')
        ax11.axvline(best_result_off['avg_processing_time'], color='red', linestyle='--', 
                    linewidth=2, label=f'평균: {best_result_off["avg_processing_time"]:.2f}ms')
        ax11.legend(fontsize=10)
        ax11.grid(True, alpha=0.3)
    
    # === 12. 레이더 차트 (최적 설정 비교) ===
    ax12 = plt.subplot(4, 3, 12, projection='polar')
    if results_interp_on and results_interp_off:
        best_on = max(results_interp_on, key=lambda x: x['actual_fps'])
        best_off = max(results_interp_off, key=lambda x: x['actual_fps'])
        
        categories = ['FPS', 'GPU 효율', '응답성\n(낮을수록 좋음)', '안정성']
        
        # 정규화 (0-1)
        max_fps = max(best_on['actual_fps'], best_off['actual_fps'])
        max_eff = max(best_on['actual_fps'] / max(best_on['gpu_util'], 1),
                     best_off['actual_fps'] / max(best_off['gpu_util'], 1))
        max_p95 = max(best_on['p95_processing_time'], best_off['p95_processing_time'])
        max_p99 = max(best_on['p99_processing_time'], best_off['p99_processing_time'])
        
        values_on = [
            best_on['actual_fps'] / max_fps,
            (best_on['actual_fps'] / max(best_on['gpu_util'], 1)) / max_eff,
            1 - (best_on['p95_processing_time'] / max_p95),  # 낮을수록 좋음
            1 - (best_on['p99_processing_time'] / max_p99)   # 낮을수록 좋음
        ]
        
        values_off = [
            best_off['actual_fps'] / max_fps,
            (best_off['actual_fps'] / max(best_off['gpu_util'], 1)) / max_eff,
            1 - (best_off['p95_processing_time'] / max_p95),
            1 - (best_off['p99_processing_time'] / max_p99)
        ]
        
        angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
        values_on += values_on[:1]
        values_off += values_off[:1]
        angles += angles[:1]
        
        ax12.plot(angles, values_on, 'o-', color=color_on, linewidth=2, markersize=8, label='보간 ON')
        ax12.fill(angles, values_on, color=color_on, alpha=0.25)
        ax12.plot(angles, values_off, 's-', color=color_off, linewidth=2, markersize=8, label='보간 OFF')
        ax12.fill(angles, values_off, color=color_off, alpha=0.25)
        
        ax12.set_xticks(angles[:-1])
        ax12.set_xticklabels(categories, fontsize=10)
        ax12.set_ylim(0, 1)
        ax12.set_title('12. 최적 설정 종합 비교', fontsize=14, fontweight='bold', pad=20)
        ax12.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=10)
        ax12.grid(True)
    
    plt.tight_layout()
    
    # 저장
    output_path = os.path.join(current_dir, 'frame_timeout_optimization_result.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"[시각화 저장] {output_path}")
    
    plt.close()

def main():
    """메인 실행 함수"""
    # 테스트 설정
    video_path = r"C:\Users\parkj\Desktop\ponggwi\source\basic.mp4"
    cloth_path = os.path.join(current_dir, 'input', 'cloth.jpg')
    
    # 프레임 타임아웃 테스트 범위 (밀리초)
    # 배치 수집 대기 시간: 짧을수록 빠른 수집, 길수록 배치 크기 증가
    timeout_values = [5, 10, 15, 20, 30, 40, 50]  # 7가지
    
    print("="*80)
    print("프레임 타임아웃 최적화 테스트 (프레임 보간 ON/OFF 비교)")
    print("="*80)
    print(f"테스트 비디오: {video_path}")
    print(f"옷 이미지: {cloth_path}")
    print(f"프레임 타임아웃 범위: {timeout_values} ms")
    print(f"총 테스트 수: {len(timeout_values) * 2} (보간 ON: {len(timeout_values)}, OFF: {len(timeout_values)})")
    print("="*80)
    
    # 비디오 파일 확인
    if not os.path.exists(video_path):
        print(f"[ERROR] 비디오 파일이 없습니다: {video_path}")
        return
    
    # 옷 이미지 확인
    if not os.path.exists(cloth_path):
        print(f"[ERROR] 옷 이미지가 없습니다: {cloth_path}")
        return
    
    all_results = []
    
    # 프레임 보간 ON 테스트
    print(f"\n{'='*80}")
    print(f"[1단계] 프레임 보간 ON 테스트 ({len(timeout_values)}개)")
    print(f"{'='*80}")
    
    for i, timeout in enumerate(timeout_values, 1):
        print(f"\n[{i}/{len(timeout_values)}] 타임아웃: {timeout}ms, 보간: ON")
        
        result = test_frame_timeout(video_path, timeout, interpolation_enabled=True, cloth_path=cloth_path)
        
        if result:
            all_results.append(result)
        
        # 테스트 간 대기 (GPU 쿨다운)
        if i < len(timeout_values):
            print("[대기] 다음 테스트 준비 중... (5초)")
            time.sleep(5)
    
    # 프레임 보간 OFF 테스트
    print(f"\n{'='*80}")
    print(f"[2단계] 프레임 보간 OFF 테스트 ({len(timeout_values)}개)")
    print(f"{'='*80}")
    
    for i, timeout in enumerate(timeout_values, 1):
        print(f"\n[{i}/{len(timeout_values)}] 타임아웃: {timeout}ms, 보간: OFF")
        
        result = test_frame_timeout(video_path, timeout, interpolation_enabled=False, cloth_path=cloth_path)
        
        if result:
            all_results.append(result)
        
        # 테스트 간 대기 (GPU 쿨다운)
        if i < len(timeout_values):
            print("[대기] 다음 테스트 준비 중... (5초)")
            time.sleep(5)
    
    # 결과 시각화
    if all_results:
        print(f"\n{'='*80}")
        print(f"[최종 결과] 총 {len(all_results)}개 테스트 완료")
        print(f"{'='*80}")
        
        # 최고 성능 찾기
        results_interp_on = [r for r in all_results if r['interpolation']]
        results_interp_off = [r for r in all_results if not r['interpolation']]
        
        if results_interp_on:
            best_on = max(results_interp_on, key=lambda x: x['actual_fps'])
            print(f"\n[최고 성능 - 보간 ON]")
            print(f"  타임아웃: {best_on['timeout_ms']}ms")
            print(f"  FPS: {best_on['actual_fps']:.2f}")
            print(f"  평균 처리 시간: {best_on['avg_processing_time']:.2f}ms")
            print(f"  P95 처리 시간: {best_on['p95_processing_time']:.2f}ms")
            print(f"  GPU 사용률: {best_on['gpu_util']:.1f}%")
        
        if results_interp_off:
            best_off = max(results_interp_off, key=lambda x: x['actual_fps'])
            print(f"\n[최고 성능 - 보간 OFF]")
            print(f"  타임아웃: {best_off['timeout_ms']}ms")
            print(f"  FPS: {best_off['actual_fps']:.2f}")
            print(f"  평균 처리 시간: {best_off['avg_processing_time']:.2f}ms")
            print(f"  P95 처리 시간: {best_off['p95_processing_time']:.2f}ms")
            print(f"  GPU 사용률: {best_off['gpu_util']:.1f}%")
        
        # 시각화
        visualize_results(all_results)
        
        print(f"\n{'='*80}")
        print(f"[완료] 모든 테스트 및 시각화 완료")
        print(f"{'='*80}")
    else:
        print("\n[ERROR] 테스트 결과가 없습니다")

if __name__ == "__main__":
    main()
