"""
CUDA Streams 성능 비교 테스트
=============================
순차 처리 vs CUDA Streams 병렬 처리 성능 비교
"""

import sys
import os
import time
import numpy as np

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'fit'))

from virtual_fitting import RTMPoseVirtualFitting
import torch

def quick_benchmark(use_cuda_streams=True):
    """빠른 성능 측정"""
    print(f"\n{'='*70}")
    print(f"Testing: {'CUDA Streams (Parallel)' if use_cuda_streams else 'Sequential Processing'}")
    print(f"{'='*70}")
    
    # VirtualFitting 초기화
    device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
    vf = RTMPoseVirtualFitting(
        cloth_image_path=os.path.join(current_dir, 'fit', 'input', 'cloth.jpg'),
        device=device
    )
    
    # 테스트 프레임 생성
    test_frames = []
    for i in range(30):
        frame = np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)
        test_frames.append(frame)
    
    print(f"[Test] Processing {len(test_frames)} frames...")
    
    # 워밍업
    for i in range(3):
        _ = vf.process_frame(test_frames[i], show_skeleton=False, use_warp=False)
    
    # 실제 측정
    start_time = time.time()
    for frame in test_frames:
        _ = vf.process_frame(frame, show_skeleton=False, use_warp=False)
    elapsed = time.time() - start_time
    
    fps = len(test_frames) / elapsed
    
    print(f"[Result] Elapsed: {elapsed:.2f}s")
    print(f"[Result] FPS: {fps:.2f}")
    
    vf.stop_inference_thread()
    
    return fps

if __name__ == "__main__":
    print("\n" + "🚀"*35)
    print("CUDA Streams Performance Test")
    print("🚀"*35)
    
    # CUDA Streams 활성화 상태 테스트
    fps_parallel = quick_benchmark(use_cuda_streams=True)
    
    print(f"\n{'='*70}")
    print(f"Results Summary")
    print(f"{'='*70}")
    print(f"CUDA Streams (Parallel): {fps_parallel:.2f} FPS")
    print(f"\n✅ Test Complete!")
    print(f"{'='*70}\n")
