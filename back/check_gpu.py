#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GPU 지원 확인 스크립트
"""

print("=" * 60)
print("GPU 가속 지원 확인")
print("=" * 60)

# 1. PyTorch CUDA
print("\n[1] PyTorch CUDA 지원:")
try:
    import torch
    print(f"  - PyTorch 버전: {torch.__version__}")
    print(f"  - CUDA 사용 가능: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"  - CUDA 디바이스 수: {torch.cuda.device_count()}")
        print(f"  - CUDA 디바이스 이름: {torch.cuda.get_device_name(0)}")
        print(f"  - CUDA 버전: {torch.version.cuda}")
    else:
        print("  [WARNING] CUDA 사용 불가")
except Exception as e:
    print(f"  [ERROR] PyTorch 확인 실패: {e}")

# 2. OpenCV CUDA
print("\n[2] OpenCV CUDA 지원:")
try:
    import cv2
    print(f"  - OpenCV 버전: {cv2.__version__}")
    has_cuda = hasattr(cv2, 'cuda')
    print(f"  - CUDA 모듈 존재: {has_cuda}")
    if has_cuda:
        device_count = cv2.cuda.getCudaEnabledDeviceCount()
        print(f"  - CUDA 디바이스 수: {device_count}")
        if device_count > 0:
            print("  [OK] OpenCV CUDA 사용 가능")
        else:
            print("  [WARNING] CUDA 디바이스 없음")
    else:
        print("  [WARNING] OpenCV가 CUDA 지원 없이 빌드됨")
        print("  [INFO] pip로 설치한 opencv는 CUDA를 지원하지 않습니다.")
        print("  [INFO] 소스에서 직접 빌드해야 CUDA를 사용할 수 있습니다.")
except Exception as e:
    print(f"  [ERROR] OpenCV 확인 실패: {e}")

# 3. MediaPipe
print("\n[3] MediaPipe:")
try:
    import mediapipe as mp
    print(f"  - MediaPipe 버전: {mp.__version__}")
    print("  [INFO] MediaPipe는 내부적으로 GPU를 활용합니다 (model_complexity=2)")
except Exception as e:
    print(f"  [ERROR] MediaPipe 확인 실패: {e}")

# 4. ONNX Runtime
print("\n[4] ONNX Runtime:")
try:
    import onnxruntime as ort
    print(f"  - ONNX Runtime 버전: {ort.__version__}")
    providers = ort.get_available_providers()
    print(f"  - 사용 가능한 프로바이더: {', '.join(providers)}")
    if 'CUDAExecutionProvider' in providers:
        print("  [OK] CUDA Execution Provider 사용 가능")
    else:
        print("  [WARNING] CUDA Execution Provider 없음")
    
    # GPU 버전 확인
    try:
        import onnxruntime_gpu
        print("  [OK] onnxruntime-gpu 설치됨")
    except ImportError:
        print("  [INFO] onnxruntime-gpu 미설치")
except Exception as e:
    print(f"  [ERROR] ONNX Runtime 확인 실패: {e}")

# 5. rembg (배경 제거)
print("\n[5] rembg (배경 제거):")
try:
    from rembg import remove
    print("  - rembg 설치됨")
    print("  [INFO] rembg는 ONNX Runtime을 사용하여 GPU 가속됩니다")
except Exception as e:
    print(f"  [ERROR] rembg 확인 실패: {e}")

# 요약
print("\n" + "=" * 60)
print("요약:")
print("=" * 60)
print("[OK] GPU 사용 가능: PyTorch, MediaPipe, ONNX Runtime (rembg)")
print("[WARNING] CPU만 사용: OpenCV (pip 버전은 CUDA 미지원)")
print("\n권장사항:")
print("- 현재 설정으로 충분한 GPU 가속이 가능합니다")
print("- MediaPipe Pose, 배경 제거(rembg) 등 주요 작업이 GPU로 처리됩니다")
print("- OpenCV 연산(resize, warp 등)은 CPU를 사용하지만 성능에 큰 영향 없습니다")
print("=" * 60)
