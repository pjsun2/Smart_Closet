"""
Quick Performance Test
======================
빠른 성능 측정 (실시간 FPS 표시)
"""

import cv2
import time
import os
import sys

# fit 디렉토리 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
fit_dir = os.path.join(current_dir, 'fit')
if fit_dir not in sys.path:
    sys.path.insert(0, fit_dir)

from fit.virtual_fitting import RTMPoseVirtualFitting

def quick_test():
    """빠른 FPS 테스트"""
    print("\n" + "="*70)
    print("Quick FPS Test")
    print("="*70 + "\n")
    
    # VirtualFitting 초기화
    import torch
    device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
    
    print(f"[Init] Device: {device}")
    print(f"[Init] Loading model...")
    
    vf = RTMPoseVirtualFitting(
        cloth_image_path=os.path.join(fit_dir, 'input', 'cloth.jpg'),
        device=device
    )
    
    print(f"\n[Config] Batch Size: {vf.batch_size}")
    print(f"[Config] Inference Interval: {vf.inference_interval:.3f}s ({1/vf.inference_interval:.1f} FPS)")
    print(f"[Config] Inference Scale: {vf.inference_scale:.1f} ({int(vf.inference_scale*100)}%)")
    print(f"[Config] Output FPS: {vf.output_fps}")
    
    # 웹캠 열기
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("[Error] Cannot open camera")
        return
    
    print("\n[Start] Press 'q' to quit")
    print("="*70 + "\n")
    
    # FPS 카운터
    frame_count = 0
    start_time = time.time()
    fps_display = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # 프레임 처리
        result = vf.process_frame(frame, show_skeleton=True, use_warp=True)
        
        # FPS 계산 (1초마다)
        frame_count += 1
        elapsed = time.time() - start_time
        
        if elapsed >= 1.0:
            fps_display = frame_count / elapsed
            frame_count = 0
            start_time = time.time()
            print(f"[FPS] {fps_display:.2f} FPS", end='\r')
        
        # FPS 표시
        cv2.putText(result, f"FPS: {fps_display:.1f}", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        cv2.putText(result, f"Batch: {vf.batch_size} | Interval: {vf.inference_interval:.3f}s", 
                   (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # 화면 표시
        cv2.imshow('Quick FPS Test', result)
        
        # 종료
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    vf.stop_inference_thread()
    
    print("\n\n[Done] Test complete!")


if __name__ == "__main__":
    quick_test()
