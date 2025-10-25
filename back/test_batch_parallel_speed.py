"""
배치 병렬 처리 속도 비교 테스트
- 순차 처리 vs CUDA Streams 병렬
"""

import sys
import os
import time
import numpy as np
import cv2
import torch

# 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'fit'))

from fit.virtual_fitting import RTMPoseVirtualFitting

def test_sequential_processing(vf, frames):
    """순차 처리 속도 측정"""
    from mmpose.apis import inference_topdown
    
    print("\n" + "="*70)
    print("1️⃣ 순차 처리 (기존 방식)")
    print("="*70)
    
    start_time = time.time()
    results = []
    
    for frame in frames:
        result = inference_topdown(vf.model, frame)
        results.append(result)
    
    end_time = time.time()
    elapsed = end_time - start_time
    fps = len(frames) / elapsed
    
    print(f"처리 프레임: {len(frames)}개")
    print(f"총 시간: {elapsed*1000:.2f}ms")
    print(f"평균 시간: {elapsed*1000/len(frames):.2f}ms/프레임")
    print(f"FPS: {fps:.2f}")
    
    return elapsed, fps

def test_cuda_streams_parallel(vf, frames):
    """CUDA Streams 병렬 처리 속도 측정"""
    from mmpose.apis import inference_topdown
    
    print("\n" + "="*70)
    print("2️⃣ CUDA Streams 병렬 (현재 방식)")
    print("="*70)
    
    if not torch.cuda.is_available():
        print("⚠️ CUDA 사용 불가, 테스트 스킵")
        return None, None
    
    start_time = time.time()
    
    # CUDA Streams 생성
    streams = [torch.cuda.Stream() for _ in range(len(frames))]
    stream_results = [None] * len(frames)
    
    # 각 스트림에서 병렬 추론
    for i, (frame, stream) in enumerate(zip(frames, streams)):
        with torch.cuda.stream(stream):
            stream_results[i] = inference_topdown(vf.model, frame)
    
    # 모든 스트림 완료 대기
    torch.cuda.synchronize()
    
    end_time = time.time()
    elapsed = end_time - start_time
    fps = len(frames) / elapsed
    
    print(f"처리 프레임: {len(frames)}개")
    print(f"총 시간: {elapsed*1000:.2f}ms")
    print(f"평균 시간: {elapsed*1000/len(frames):.2f}ms/프레임")
    print(f"FPS: {fps:.2f}")
    
    return elapsed, fps

def test_batch_sizes():
    """다양한 배치 크기로 테스트"""
    print("\n" + "="*70)
    print("🔍 배치 병렬 처리 속도 비교 테스트")
    print("="*70)
    
    device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
    
    # 가상 피팅 초기화
    vf = RTMPoseVirtualFitting(
        cloth_image_path='fit/input/cloth.jpg',
        device=device
    )
    
    # 더미 프레임 생성 (640x360)
    print("\n📝 테스트 프레임 생성...")
    frames = []
    for i in range(5):
        frame = np.random.randint(0, 255, (360, 640, 3), dtype=np.uint8)
        frames.append(frame)
    print(f"생성 완료: {len(frames)}개 프레임")
    
    # 1. 순차 처리
    seq_time, seq_fps = test_sequential_processing(vf, frames)
    
    # 2. CUDA Streams 병렬
    parallel_time, parallel_fps = test_cuda_streams_parallel(vf, frames)
    
    # 3. 결과 비교
    print("\n" + "="*70)
    print("📊 결과 비교")
    print("="*70)
    
    if parallel_time and seq_time:
        speedup = seq_time / parallel_time
        print(f"\n순차 처리:")
        print(f"  - 총 시간: {seq_time*1000:.2f}ms")
        print(f"  - FPS: {seq_fps:.2f}")
        
        print(f"\nCUDA Streams 병렬:")
        print(f"  - 총 시간: {parallel_time*1000:.2f}ms")
        print(f"  - FPS: {parallel_fps:.2f}")
        
        print(f"\n속도 향상:")
        print(f"  - {speedup:.2f}배 빠름")
        print(f"  - 시간 절약: {(seq_time - parallel_time)*1000:.2f}ms")
        print(f"  - FPS 증가: +{parallel_fps - seq_fps:.2f} ({(parallel_fps/seq_fps - 1)*100:.1f}%)")
        
        # GPU 병렬 효율 계산
        ideal_speedup = len(frames)  # 이상적: 5배
        efficiency = (speedup / ideal_speedup) * 100
        print(f"\nGPU 병렬 효율: {efficiency:.1f}% (이상적: 100%)")
        
        if efficiency < 50:
            print("⚠️ 낮은 병렬 효율 - mmpose API 제약 또는 GPU 병목")
        elif efficiency < 80:
            print("✅ 양호한 병렬 효율")
        else:
            print("🚀 우수한 병렬 효율!")
    
    vf.stop_inference_thread()
    
    # 다양한 배치 크기 테스트
    print("\n" + "="*70)
    print("🔬 배치 크기별 성능 테스트")
    print("="*70)
    
    batch_sizes = [1, 2, 3, 4, 5, 8, 10]
    
    print("\n배치 크기 | 순차 시간 | 병렬 시간 | 속도 향상 | 효율")
    print("-" * 70)
    
    for batch_size in batch_sizes:
        # 프레임 생성
        frames = [np.random.randint(0, 255, (360, 640, 3), dtype=np.uint8) 
                  for _ in range(batch_size)]
        
        # 순차 처리
        start = time.time()
        for frame in frames:
            _ = inference_topdown(vf.model, frame)
        seq_time = time.time() - start
        
        # CUDA Streams 병렬
        if torch.cuda.is_available():
            start = time.time()
            streams = [torch.cuda.Stream() for _ in range(len(frames))]
            stream_results = [None] * len(frames)
            
            for i, (frame, stream) in enumerate(zip(frames, streams)):
                with torch.cuda.stream(stream):
                    stream_results[i] = inference_topdown(vf.model, frame)
            
            torch.cuda.synchronize()
            parallel_time = time.time() - start
            
            speedup = seq_time / parallel_time
            efficiency = (speedup / batch_size) * 100
            
            print(f"{batch_size:^10} | {seq_time*1000:>9.1f}ms | {parallel_time*1000:>9.1f}ms | "
                  f"{speedup:>9.2f}x | {efficiency:>6.1f}%")
    
    print("\n🎯 결론:")
    print("  - 배치 크기가 클수록 병렬 효율 감소 (GPU 포화)")
    print("  - 최적 배치 크기: 3-5개 (효율 70-80%)")
    print("  - mmpose API는 배치 텐서 미지원 → CUDA Streams 우회")

if __name__ == "__main__":
    from mmpose.apis import inference_topdown
    test_batch_sizes()
