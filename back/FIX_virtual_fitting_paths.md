# Virtual Fitting Path Fix

## Problems Fixed

### 1. Model Path Error
**Error**: `[Errno 2] No such file or directory: 'models/rtmpose-s_8xb256-420e_aic-coco-256x192.py'`

**Cause**: 상대 경로 사용으로 인해 다른 디렉토리에서 실행 시 모델 파일을 찾지 못함

**Solution**: 
- `virtual_fitting.py`의 `__init__` 메서드에서 절대 경로 사용
- `current_dir = os.path.dirname(os.path.abspath(__file__))`
- 모델 파일 경로: `os.path.join(current_dir, 'models', 'rtmpose-s_8xb256-420e_aic-coco-256x192.py')`
- 파일 존재 여부 사전 검증 추가

### 2. Cloth Image Path Error
**Issue**: 옷 이미지 경로도 상대 경로로 인한 문제 가능성

**Solution**:
- `cloth_image_path`를 절대 경로로 변환
- `load_cloth()` 메서드에서 output 디렉토리도 절대 경로 사용

### 3. Handle Error (WinError 6)
**Error**: `[WinError 6] 핸들이 잘못되었습니다`

**Cause**: VirtualFitting 인스턴스가 제대로 생성되지 않았을 때 process_frame 호출

**Solution**:
- `get_virtual_fitting()`에서 더 상세한 로깅 추가
- 옷 이미지 파일 존재 여부 사전 확인
- `process_frame()` 호출을 try-except로 감싸서 에러 세부사항 출력
- None 체크 후 명확한 에러 메시지 반환

## Changes Made

### File: `back/fit/virtual_fitting.py`

1. **`__init__` 메서드**:
```python
# Before
config_file = 'models/rtmpose-s_8xb256-420e_aic-coco-256x192.py'

# After
current_dir = os.path.dirname(os.path.abspath(__file__))
config_file = os.path.join(current_dir, 'models', 'rtmpose-s_8xb256-420e_aic-coco-256x192.py')

# 파일 존재 검증
if not os.path.exists(config_file):
    raise FileNotFoundError(f"Config file not found: {config_file}")
```

2. **`load_cloth` 메서드**:
```python
# Before
output_dir = 'output'

# After
current_dir = os.path.dirname(os.path.abspath(__file__))
output_dir = os.path.join(current_dir, 'output')
```

### File: `back/routes/clothes.py`

1. **`get_virtual_fitting` 함수**:
- 절대 경로로 cloth_image_path 생성
- 이미지 파일 존재 여부 확인 및 경고 메시지
- 상세한 디버깅 로그 추가

2. **`process_fit_frame` 함수**:
- `process_frame()` 호출을 별도 try-except로 감싸기
- 명확한 에러 메시지와 HTTP 상태 코드 반환

## Testing

서버 재시작 후 테스트:

```bash
# 서버 재시작
stop_servers.bat
start_backend.bat

# 또는
Ctrl+C (현재 서버 중지)
python back/server.py
```

## Expected Results

1. 모델 파일 로딩 성공 로그:
```
[RTMPose] 모델 로딩 중... (device: cuda:0)
[RTMPose] Config: C:\Users\parkj\Desktop\Smart_Closet\back\fit\models\rtmpose-s_8xb256-420e_aic-coco-256x192.py
[RTMPose] Checkpoint: C:\Users\parkj\Desktop\Smart_Closet\back\fit\models\rtmpose-s_simcc-aic-coco_pt-aic-coco_420e-256x192-fcb2599b_20230126.pth
[RTMPose] 모델 로딩 완료
```

2. VirtualFitting 인스턴스 생성 성공:
```
[clothes.py] RTMPoseVirtualFitting 인스턴스 생성 완료
```

3. 프레임 처리 정상 동작 (WinError 6 해결)

## Files Modified
- `back/fit/virtual_fitting.py`
- `back/routes/clothes.py`

---
**작성일**: 2025-10-24
**해결 이슈**: 모델 경로 오류, 핸들 오류
