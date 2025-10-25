"""
Virtual Fitting Performance Benchmark
=====================================
자동으로 다양한 파라미터를 테스트하고 성능을 측정하여 시각화 보고서를 생성합니다.

측정 항목:
1. Batch Size (1~8)
2. Inference Interval (0.03~0.1)
3. Inference Scale (0.3~1.0)
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # GUI 없이 저장만
import time
import os
import sys
from datetime import datetime
import json

# 한글 폰트 설정 (Windows)
try:
    plt.rcParams['font.family'] = 'Malgun Gothic'
    plt.rcParams['axes.unicode_minus'] = False
except:
    pass

# fit 디렉토리 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
fit_dir = os.path.join(current_dir, 'fit')
if fit_dir not in sys.path:
    sys.path.insert(0, fit_dir)

from fit.virtual_fitting import RTMPoseVirtualFitting

class PerformanceBenchmark:
    """성능 벤치마크 클래스"""
    
    def __init__(self, output_dir='benchmark_results'):
        """
        Args:
            output_dir: 결과 저장 디렉토리
        """
        self.output_dir = os.path.join(current_dir, output_dir)
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 타임스탬프
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 테스트 비디오 (웹캠 대신 샘플 프레임 생성)
        self.test_frames = self._generate_test_frames()
        
        print("="*70)
        print("Virtual Fitting Performance Benchmark")
        print("="*70)
        print(f"Output Directory: {self.output_dir}")
        print(f"Timestamp: {self.timestamp}")
        print(f"Test Frames: {len(self.test_frames)}")
        print("="*70 + "\n")
    
    def _generate_test_frames(self, count=100, width=1280, height=720):
        """테스트용 프레임 생성 (실제 카메라 대신)"""
        print("[Benchmark] Generating test frames...")
        frames = []
        for i in range(count):
            # 간단한 테스트 이미지 생성
            frame = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
            frames.append(frame)
        print(f"[Benchmark] Generated {count} test frames ({width}x{height})")
        return frames
    
    def benchmark_batch_size(self, batch_sizes=[1, 2, 3, 4, 5, 6, 7, 8]):
        """
        배치 크기에 따른 성능 측정
        
        Args:
            batch_sizes: 테스트할 배치 크기 리스트
        
        Returns:
            dict: {batch_size: fps}
        """
        print("\n" + "="*70)
        print("Benchmark 1: Batch Size Impact")
        print("="*70)
        
        results = {}
        
        for batch_size in batch_sizes:
            print(f"\n[Test] Batch Size = {batch_size}")
            
            try:
                # VirtualFitting 인스턴스 생성
                import torch
                device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
                
                vf = RTMPoseVirtualFitting(
                    cloth_image_path=os.path.join(fit_dir, 'input', 'cloth.jpg'),
                    device=device
                )
                
                # 파라미터 설정
                vf.batch_size = batch_size
                vf.use_batch_inference = True
                
                # 성능 측정
                fps = self._measure_fps(vf, num_frames=50)
                results[batch_size] = fps
                
                print(f"[Result] Batch Size {batch_size}: {fps:.2f} FPS")
                
                # 메모리 정리
                vf.stop_inference_thread()
                del vf
                
            except Exception as e:
                print(f"[Error] Batch Size {batch_size} failed: {e}")
                results[batch_size] = 0
        
        return results
    
    def benchmark_inference_interval(self, intervals=None):
        """
        추론 간격에 따른 성능 측정
        
        Args:
            intervals: 테스트할 간격 리스트 (초)
        
        Returns:
            dict: {interval: fps}
        """
        if intervals is None:
            intervals = [0.03, 0.04, 0.05, 0.067, 0.08, 0.1]
        
        print("\n" + "="*70)
        print("Benchmark 2: Inference Interval Impact")
        print("="*70)
        
        results = {}
        
        for interval in intervals:
            print(f"\n[Test] Inference Interval = {interval:.3f}s ({1/interval:.1f} FPS)")
            
            try:
                import torch
                device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
                
                vf = RTMPoseVirtualFitting(
                    cloth_image_path=os.path.join(fit_dir, 'input', 'cloth.jpg'),
                    device=device
                )
                
                # 파라미터 설정
                vf.inference_interval = interval
                vf.use_time_based_inference = True
                
                # 성능 측정
                fps = self._measure_fps(vf, num_frames=50)
                results[interval] = fps
                
                print(f"[Result] Interval {interval:.3f}s: {fps:.2f} FPS")
                
                # 메모리 정리
                vf.stop_inference_thread()
                del vf
                
            except Exception as e:
                print(f"[Error] Interval {interval} failed: {e}")
                results[interval] = 0
        
        return results
    
    def benchmark_inference_scale(self, scales=[0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]):
        """
        추론 해상도 스케일에 따른 성능 측정
        
        Args:
            scales: 테스트할 스케일 리스트
        
        Returns:
            dict: {scale: fps}
        """
        print("\n" + "="*70)
        print("Benchmark 3: Inference Scale Impact")
        print("="*70)
        
        results = {}
        
        for scale in scales:
            print(f"\n[Test] Inference Scale = {scale:.1f} ({int(scale*100)}%)")
            
            try:
                import torch
                device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
                
                vf = RTMPoseVirtualFitting(
                    cloth_image_path=os.path.join(fit_dir, 'input', 'cloth.jpg'),
                    device=device
                )
                
                # 파라미터 설정
                vf.inference_scale = scale
                vf.use_inference_downscale = True
                
                # 성능 측정
                fps = self._measure_fps(vf, num_frames=50)
                results[scale] = fps
                
                print(f"[Result] Scale {scale:.1f}: {fps:.2f} FPS")
                
                # 메모리 정리
                vf.stop_inference_thread()
                del vf
                
            except Exception as e:
                print(f"[Error] Scale {scale} failed: {e}")
                results[scale] = 0
        
        return results
    
    def _measure_fps(self, vf, num_frames=50):
        """
        실제 FPS 측정
        
        Args:
            vf: VirtualFitting 인스턴스
            num_frames: 측정할 프레임 수
        
        Returns:
            float: 측정된 FPS
        """
        # 워밍업 (처음 몇 프레임은 느림)
        for i in range(5):
            frame = self.test_frames[i % len(self.test_frames)]
            _ = vf.process_frame(frame, show_skeleton=False, use_warp=True)
        
        # 실제 측정
        start_time = time.time()
        
        for i in range(num_frames):
            frame = self.test_frames[i % len(self.test_frames)]
            _ = vf.process_frame(frame, show_skeleton=False, use_warp=True)
        
        elapsed_time = time.time() - start_time
        fps = num_frames / elapsed_time
        
        return fps
    
    def plot_results(self, results_dict, title, xlabel, ylabel, filename):
        """
        결과를 그래프로 시각화
        
        Args:
            results_dict: {x: y} 형태의 결과 딕셔너리
            title: 그래프 제목
            xlabel: X축 라벨
            ylabel: Y축 라벨
            filename: 저장할 파일명
        """
        plt.figure(figsize=(12, 7))
        
        x_values = list(results_dict.keys())
        y_values = list(results_dict.values())
        
        # 막대 그래프
        bars = plt.bar(range(len(x_values)), y_values, color='steelblue', alpha=0.8, edgecolor='black')
        
        # 값 표시
        for i, (bar, value) in enumerate(zip(bars, y_values)):
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{value:.2f}',
                    ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        plt.xlabel(xlabel, fontsize=12, fontweight='bold')
        plt.ylabel(ylabel, fontsize=12, fontweight='bold')
        plt.title(title, fontsize=14, fontweight='bold', pad=20)
        plt.xticks(range(len(x_values)), [str(x) for x in x_values], rotation=45)
        plt.grid(axis='y', alpha=0.3, linestyle='--')
        plt.tight_layout()
        
        # 저장
        filepath = os.path.join(self.output_dir, f"{self.timestamp}_{filename}")
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"[Saved] {filepath}")
    
    def plot_comparison(self, all_results, filename="comparison_chart.png"):
        """
        모든 벤치마크 결과를 하나의 그래프로 비교
        
        Args:
            all_results: {'Test Name': {param: fps}} 형태
            filename: 저장할 파일명
        """
        plt.figure(figsize=(16, 10))
        
        num_tests = len(all_results)
        
        for i, (test_name, results) in enumerate(all_results.items(), 1):
            plt.subplot(2, 2, i)
            
            x_values = list(results.keys())
            y_values = list(results.values())
            
            bars = plt.bar(range(len(x_values)), y_values, color='coral', alpha=0.7, edgecolor='black')
            
            # 값 표시
            for bar, value in zip(bars, y_values):
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height,
                        f'{value:.1f}',
                        ha='center', va='bottom', fontsize=9)
            
            plt.title(test_name, fontsize=12, fontweight='bold')
            plt.xlabel('Parameter', fontsize=10)
            plt.ylabel('FPS', fontsize=10)
            plt.xticks(range(len(x_values)), [str(x) for x in x_values], rotation=45)
            plt.grid(axis='y', alpha=0.3)
        
        plt.suptitle('Virtual Fitting Performance Benchmark - All Tests', 
                     fontsize=16, fontweight='bold', y=1.02)
        plt.tight_layout()
        
        # 저장
        filepath = os.path.join(self.output_dir, f"{self.timestamp}_{filename}")
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"[Saved] {filepath}")
    
    def generate_report(self, all_results):
        """
        텍스트 보고서 생성
        
        Args:
            all_results: 모든 벤치마크 결과
        """
        report_path = os.path.join(self.output_dir, f"{self.timestamp}_report.txt")
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write("Virtual Fitting Performance Benchmark Report\n")
            f.write("="*70 + "\n")
            f.write(f"Timestamp: {self.timestamp}\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*70 + "\n\n")
            
            for test_name, results in all_results.items():
                f.write(f"\n{test_name}\n")
                f.write("-"*70 + "\n")
                
                for param, fps in results.items():
                    f.write(f"{param:20} : {fps:8.2f} FPS\n")
                
                # 최고 성능
                best_param = max(results, key=results.get)
                best_fps = results[best_param]
                f.write(f"\nBest Performance: {best_param} ({best_fps:.2f} FPS)\n")
                f.write("-"*70 + "\n")
        
        print(f"[Saved] {report_path}")
        
        # JSON 형태로도 저장
        json_path = os.path.join(self.output_dir, f"{self.timestamp}_results.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=4)
        
        print(f"[Saved] {json_path}")
    
    def run_all_benchmarks(self):
        """모든 벤치마크 실행"""
        all_results = {}
        
        # 1. Batch Size
        print("\n" + "🔥"*35)
        batch_results = self.benchmark_batch_size([1, 2, 3, 4, 5, 6, 7, 8])
        all_results['Batch Size Impact'] = batch_results
        self.plot_results(
            batch_results,
            'Batch Size Impact on FPS',
            'Batch Size',
            'FPS (Frames Per Second)',
            'batch_size_benchmark.png'
        )
        
        # 2. Inference Interval
        print("\n" + "🔥"*35)
        interval_results = self.benchmark_inference_interval([0.03, 0.04, 0.05, 0.067, 0.08, 0.1])
        all_results['Inference Interval Impact'] = interval_results
        self.plot_results(
            interval_results,
            'Inference Interval Impact on FPS',
            'Inference Interval (seconds)',
            'FPS (Frames Per Second)',
            'inference_interval_benchmark.png'
        )
        
        # 3. Inference Scale
        print("\n" + "🔥"*35)
        scale_results = self.benchmark_inference_scale([0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
        all_results['Inference Scale Impact'] = scale_results
        self.plot_results(
            scale_results,
            'Inference Scale Impact on FPS',
            'Inference Scale (Resolution %)',
            'FPS (Frames Per Second)',
            'inference_scale_benchmark.png'
        )
        
        # 비교 차트
        print("\n" + "🔥"*35)
        self.plot_comparison(all_results)
        
        # 보고서 생성
        print("\n" + "🔥"*35)
        self.generate_report(all_results)
        
        print("\n" + "="*70)
        print("✅ All benchmarks completed!")
        print(f"📁 Results saved to: {self.output_dir}")
        print("="*70)
        
        return all_results


def main():
    """메인 실행"""
    print("\n")
    print("🚀 Starting Virtual Fitting Performance Benchmark...")
    print("\n")
    
    benchmark = PerformanceBenchmark()
    results = benchmark.run_all_benchmarks()
    
    print("\n")
    print("🎉 Benchmark Complete!")
    print(f"📊 Check the results in: {benchmark.output_dir}")
    print("\n")


if __name__ == "__main__":
    main()
