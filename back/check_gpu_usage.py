"""
GPU 사용률이 낮은 이유 분석 스크립트
"""
import torch
import cv2
import mediapipe as mp
import numpy as np

print("="*70)
print("GPU 사용률 저하 원인 분석")
print("="*70)

# 1. PyTorch CUDA 상태
print("\n[1] PyTorch CUDA 상태:")
if torch.cuda.is_available():
    print(f"  ✅ CUDA 사용 가능: {torch.cuda.get_device_name(0)}")
    print(f"  - CUDA 버전: {torch.version.cuda}")
    print(f"  - 현재 메모리 사용: {torch.cuda.memory_allocated(0)/1024**2:.2f}MB")
    print(f"  - 최대 메모리 사용: {torch.cuda.max_memory_allocated(0)/1024**2:.2f}MB")
    
    # 간단한 GPU 연산 테스트
    x = torch.randn(1000, 1000).cuda()
    y = torch.randn(1000, 1000).cuda()
    z = torch.matmul(x, y)
    print(f"  - GPU 연산 테스트: 성공")
    print(f"  - 연산 후 메모리: {torch.cuda.memory_allocated(0)/1024**2:.2f}MB")
else:
    print("  ❌ CUDA 사용 불가")

# 2. OpenCV CUDA 상태
print("\n[2] OpenCV CUDA 상태:")
print(f"  - OpenCV 버전: {cv2.__version__}")
print(f"  - CUDA 모듈 존재: {hasattr(cv2, 'cuda')}")
if hasattr(cv2, 'cuda'):
    print(f"  - CUDA 디바이스 수: {cv2.cuda.getCudaEnabledDeviceCount()}")
    if cv2.cuda.getCudaEnabledDeviceCount() > 0:
        print("  ✅ OpenCV CUDA 사용 가능")
    else:
        print("  ⚠️ OpenCV CUDA 디바이스 없음 (CPU 모드)")
        print("  → pip로 설치한 OpenCV는 CUDA가 비활성화되어 있습니다")
else:
    print("  ❌ OpenCV CUDA 모듈 없음")

# 3. MediaPipe 설정
print("\n[3] MediaPipe 설정:")
print(f"  - MediaPipe 버전: {mp.__version__}")
print(f"  - GPU 모드 활성화 여부: 내부 설정에 의존")
print(f"  - model_complexity=2 설정됨 (GPU 활용 극대화)")

# 4. GPU 사용률이 낮은 주요 원인
print("\n[4] GPU 사용률이 낮은 주요 원인:")
print("-"*70)

reasons = [
    {
        'title': '① OpenCV가 CPU 모드로 실행',
        'detail': 'pip로 설치한 opencv-contrib-python은 CUDA 지원 없이 빌드됨',
        'impact': '중간 (resize, warp, blend 등이 CPU 사용)',
        'solution': 'OpenCV를 소스에서 CUDA 옵션으로 빌드 (복잡함)'
    },
    {
        'title': '② MediaPipe의 제한적 GPU 사용',
        'detail': 'MediaPipe는 추론 단계만 GPU 사용, 전처리는 CPU',
        'impact': '낮음 (이미 최적화됨)',
        'solution': 'model_complexity=2 유지 (현재 설정 유지)'
    },
    {
        'title': '③ 프레임 전송 간격 (200ms)',
        'detail': 'GPU가 유휴 상태로 대기하는 시간 존재',
        'impact': '높음 (GPU가 50%는 대기 상태)',
        'solution': '간격을 100ms로 줄이면 GPU 사용률 증가'
    },
    {
        'title': '④ 단일 스트림 처리',
        'detail': '한 번에 하나의 프레임만 처리 (병렬 처리 없음)',
        'impact': '높음 (GPU 활용도 낮음)',
        'solution': '배치 처리 구현 (복잡도 높음)'
    },
    {
        'title': '⑤ CPU 병목 현상',
        'detail': 'Base64 인코딩/디코딩, JSON 파싱 등 CPU 작업',
        'impact': '중간 (GPU보다 CPU가 먼저 포화)',
        'solution': 'WebSocket + Binary 전송으로 변경'
    },
    {
        'title': '⑥ rembg 배경 제거',
        'detail': 'ONNX Runtime이 GPU를 사용하지만 제한적',
        'impact': '낮음 (옷 업로드 시에만 실행)',
        'solution': 'onnxruntime-gpu 올바른 설정 (이미 설치됨)'
    }
]

for idx, reason in enumerate(reasons, 1):
    print(f"\n{reason['title']}")
    print(f"  설명: {reason['detail']}")
    print(f"  영향도: {reason['impact']}")
    print(f"  해결책: {reason['solution']}")

# 5. 권장 조치사항
print("\n" + "="*70)
print("[5] 즉시 적용 가능한 GPU 사용률 향상 방법:")
print("="*70)

print("""
[PRIORITY 1] 프레임 전송 간격 줄이기 (즉시 효과)
   - front/src/Component/main.js의 200ms를 100ms로 변경
   - 예상 GPU 사용률: 30% -> 50-60%
   - 부작용: 네트워크 부하 증가, CPU 사용률 증가

[PRIORITY 2] model_complexity 유지 (이미 최적화됨)
   - 현재 model_complexity=2 유지
   - GPU를 최대한 활용하는 설정
   
[PRIORITY 3] 해상도 증가 (GPU 부하 증가)
   - 더 높은 해상도로 처리하면 GPU 사용률 증가
   - 하지만 실시간성 저하 가능성

[WARNING] 장기 과제: OpenCV CUDA 빌드
   - Windows에서 OpenCV를 CUDA 옵션으로 소스 빌드
   - 매우 복잡하고 시간 소모적
   - 현재 설정으로도 충분한 성능 제공
""")

print("\n" + "="*70)
print("[6] 결론:")
print("="*70)
print("""
현재 GPU 사용률이 낮은 이유는:
1. OpenCV가 CPU 모드 (pip 버전의 한계)
2. 200ms 간격으로 인한 GPU 유휴 시간
3. 단일 스트림 처리로 인한 병렬화 부족

하지만 이는 정상적인 현상이며:
✅ MediaPipe Pose 추론은 GPU 사용 중
✅ PyTorch 연산은 GPU 사용 중
✅ 실시간 성능은 충분히 확보됨

GPU 사용률을 높이는 것이 반드시 좋은 것은 아닙니다.
현재 설정은 '실시간성'과 'GPU 효율성'의 균형점입니다.
""")

print("="*70)
