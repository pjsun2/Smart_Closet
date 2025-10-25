import cv2
import numpy as np
from rembg import remove
from PIL import Image
import io
import os
import mediapipe as mp

# MediaPipe 초기화
mp_pose = mp.solutions.pose
mp_selfie_segmentation = mp.solutions.selfie_segmentation

# GPU 가속 옵션
# 주의: pip로 설치한 opencv-contrib-python은 CUDA 지원 없이 빌드되어 있습니다.
# 하지만 PyTorch, MediaPipe, ONNX Runtime GPU는 여전히 GPU를 활용합니다.
USE_GPU_ACCELERATION = True
OPENCV_CUDA_AVAILABLE = hasattr(cv2, 'cuda') and cv2.cuda.getCudaEnabledDeviceCount() > 0

print(f"[Cloth Processor] OpenCV CUDA 사용 가능: {OPENCV_CUDA_AVAILABLE}")
if not OPENCV_CUDA_AVAILABLE:
    print("[Cloth Processor] OpenCV CUDA 미지원. CPU 모드로 실행됩니다.")
    print("[Cloth Processor] PyTorch, MediaPipe, rembg는 여전히 GPU를 사용합니다.")

# 세그멘테이션 모델 초기화 (전역, 한 번만 초기화)
_segmentation_model = None

def get_segmentation_model():
    """세그멘테이션 모델 싱글톤"""
    global _segmentation_model
    if _segmentation_model is None:
        _segmentation_model = mp_selfie_segmentation.SelfieSegmentation(model_selection=1)
        print("[Cloth Processor] 세그멘테이션 모델 초기화 완료")
    return _segmentation_model

def use_gpu_mat(img):
    """
    가능한 경우 GPU 메모리로 이미지 업로드
    
    Args:
        img: numpy array 이미지
    
    Returns:
        GpuMat 또는 원본 이미지
    """
    if OPENCV_CUDA_AVAILABLE:
        try:
            gpu_img = cv2.cuda_GpuMat()
            gpu_img.upload(img)
            return gpu_img
        except:
            return img
    return img

def download_from_gpu(gpu_img):
    """
    GPU 메모리에서 이미지 다운로드
    
    Args:
        gpu_img: GpuMat 또는 numpy array
    
    Returns:
        numpy array
    """
    if OPENCV_CUDA_AVAILABLE and hasattr(gpu_img, 'download'):
        return gpu_img.download()
    return gpu_img

def remove_background(cloth_image_path, output_path):
    """
    옷 이미지의 배경을 투명하게 제거합니다. (GPU 가속)
    
    Args:
        cloth_image_path: 입력 옷 이미지 경로
        output_path: 출력 이미지 경로 (PNG)
    
    Returns:
        배경이 제거된 이미지 (numpy array, RGBA)
    """
    print(f"[Cloth Processor] 배경 제거 시작: {cloth_image_path}")
    
    try:
        # 이미지 읽기
        with open(cloth_image_path, 'rb') as f:
            input_image = f.read()
        
        # rembg로 배경 제거 (ONNX Runtime GPU 사용)
        # onnxruntime-gpu가 설치되어 있으면 자동으로 GPU 사용
        output_image = remove(input_image)
        
        # PIL Image로 변환
        img_pil = Image.open(io.BytesIO(output_image))
        
        # PNG로 저장
        img_pil.save(output_path, 'PNG')
        print(f"[Cloth Processor] 배경 제거 완료: {output_path}")
        
        # numpy array로 변환 (RGBA)
        img_array = np.array(img_pil)
        
        return img_array
        
    except Exception as e:
        print(f"[Cloth Processor] 배경 제거 실패: {e}")
        # 실패 시 원본 이미지 반환
        img = cv2.imread(cloth_image_path, cv2.IMREAD_UNCHANGED)
        if img is None:
            raise FileNotFoundError(f"이미지를 찾을 수 없습니다: {cloth_image_path}")
        
        # BGR을 BGRA로 변환
        if img.shape[2] == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
        
        return img

def resize_cloth_to_body(cloth_img, shoulder_width, body_height):
    """
    감지된 어깨 너비와 상체 높이에 맞게 옷 이미지 크기 조정
    
    Args:
        cloth_img: 배경이 제거된 옷 이미지 (RGBA)
        shoulder_width: 어깨 너비 (픽셀)
        body_height: 상체 높이 (픽셀)
    
    Returns:
        크기 조정된 옷 이미지
    """
    h, w = cloth_img.shape[:2]
    
    # 옷의 가로세로 비율 유지하면서 크기 조정
    scale = shoulder_width / w
    new_w = int(w * scale)
    new_h = int(h * scale)
    
    # 높이가 너무 크면 높이 기준으로 조정
    if new_h > body_height:
        scale = body_height / h
        new_w = int(w * scale)
        new_h = int(h * scale)
    
    # 리사이즈 (OpenCV CUDA는 pip 버전에서 사용 불가)
    resized = cv2.resize(cloth_img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    
    return resized

def overlay_cloth_on_body(frame, cloth_img, position=None, alpha=1.0):
    """
    프레임에 옷 이미지를 오버레이합니다.
    RTMPose 스타일의 알파 채널 기반 합성 사용 - 완전 불투명
    
    Args:
        frame: 원본 비디오 프레임 (BGR)
        cloth_img: 배경이 제거된 옷 이미지 (RGBA) - 프레임과 동일한 크기여야 함
        position: (사용 안 함 - 이미 변형된 이미지 사용)
        alpha: 추가 투명도 조정 (0.0 ~ 1.0, 기본값 1.0 = 완전 불투명)
    
    Returns:
        옷이 오버레이된 프레임
    """
    h_frame, w_frame = frame.shape[:2]
    h_cloth, w_cloth = cloth_img.shape[:2]
    
    # 프레임과 옷 이미지 크기가 다르면 경고
    if h_frame != h_cloth or w_frame != w_cloth:
        print(f"[Cloth Processor] 경고: 프레임({h_frame}x{w_frame})과 옷({h_cloth}x{w_cloth}) 크기 불일치")
        # 옷 이미지를 프레임 크기에 맞춤
        cloth_img = cv2.resize(cloth_img, (w_frame, h_frame), interpolation=cv2.INTER_LINEAR)
    
    # RGBA를 BGR과 Alpha로 분리
    if cloth_img.shape[2] == 4:
        cloth_bgr = cloth_img[:, :, :3]
        cloth_alpha_channel = cloth_img[:, :, 3]
    else:
        # 알파 채널이 없으면 완전 불투명으로 처리
        cloth_bgr = cloth_img
        cloth_alpha_channel = np.ones((h_cloth, w_cloth), dtype=np.uint8) * 255
    
    # 알파 값 정규화 (0.0 ~ 1.0)
    alpha_normalized = (cloth_alpha_channel / 255.0) * alpha
    
    # RTMPose 스타일 알파 블렌딩 (채널별 처리)
    result = frame.copy()
    for c in range(3):  # BGR 각 채널
        result[:, :, c] = (
            frame[:, :, c] * (1 - alpha_normalized) + 
            cloth_bgr[:, :, c] * alpha_normalized
        ).astype(np.uint8)
    
    return result

def detect_cloth_keypoints_advanced(cloth_nobg_path):
    """
    배경이 제거된 옷 이미지에서 어깨 관절을 정확하게 감지합니다.
    
    Args:
        cloth_nobg_path: 배경 제거된 옷 이미지 경로 (RGBA)
    
    Returns:
        dict: 옷의 주요 키포인트 좌표
            - left_shoulder, right_shoulder (어깨)
            - shoulder_width (어깨 너비)
            - cloth_center (옷 중심)
            - neck_point (목 위치)
    """
    print(f"[Cloth Processor] 고급 옷 키포인트 감지 시작: {cloth_nobg_path}")
    
    # RGBA 이미지 읽기
    img = cv2.imread(cloth_nobg_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        print("[Cloth Processor] 이미지를 읽을 수 없습니다")
        return None
    
    h, w = img.shape[:2]
    
    # 알파 채널로 마스크 생성
    if img.shape[2] == 4:
        alpha = img[:, :, 3]
        mask = (alpha > 0).astype(np.uint8) * 255
    else:
        # RGBA가 아닌 경우 그레이스케일로 변환
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY)
    
    # 윤곽선 찾기
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        print("[Cloth Processor] 윤곽선을 찾을 수 없습니다")
        return None
    
    # 가장 큰 윤곽선 선택 (옷 본체)
    main_contour = max(contours, key=cv2.contourArea)
    
    # 바운딩 박스
    x, y, w_box, h_box = cv2.boundingRect(main_contour)
    
    # 1. 상단 영역에서 어깨 찾기 (상위 20% 영역)
    top_region = int(h_box * 0.2)
    top_y = y + top_region
    
    # 상단 영역의 마스크
    top_mask = np.zeros_like(mask)
    top_mask[y:top_y, x:x+w_box] = mask[y:top_y, x:x+w_box]
    
    # 각 행에서 좌우 끝점 찾기
    shoulder_candidates = []
    for row in range(y, top_y):
        row_pixels = np.where(top_mask[row, :] > 0)[0]
        if len(row_pixels) > 0:
            left_x = row_pixels[0]
            right_x = row_pixels[-1]
            width = right_x - left_x
            shoulder_candidates.append({
                'row': row,
                'left_x': left_x,
                'right_x': right_x,
                'width': width
            })
    
    if not shoulder_candidates:
        print("[Cloth Processor] 어깨 후보를 찾을 수 없습니다. 기본 추정 사용")
        return estimate_cloth_keypoints_from_contour_simple(img, x, y, w_box, h_box)
    
    # 가장 넓은 부분을 어깨로 판단
    widest = max(shoulder_candidates, key=lambda c: c['width'])
    
    left_shoulder = (widest['left_x'], widest['row'])
    right_shoulder = (widest['right_x'], widest['row'])
    shoulder_width = widest['width']
    
    # 2. 목 위치 추정 (어깨보다 위쪽 중앙)
    neck_search_start = max(0, widest['row'] - int(h_box * 0.15))
    neck_x = (left_shoulder[0] + right_shoulder[0]) // 2
    
    # 목 부근에서 중앙 픽셀이 있는 가장 위쪽 점 찾기
    neck_y = widest['row']
    for row in range(widest['row'], neck_search_start, -1):
        if mask[row, neck_x] > 0:
            neck_y = row
        else:
            break
    
    neck_point = (neck_x, neck_y)
    
    # 3. 옷 중심점 계산
    M = cv2.moments(main_contour)
    if M['m00'] != 0:
        cloth_center_x = int(M['m10'] / M['m00'])
        cloth_center_y = int(M['m01'] / M['m00'])
        cloth_center = (cloth_center_x, cloth_center_y)
    else:
        cloth_center = (x + w_box // 2, y + h_box // 2)
    
    # 4. 엘보우와 힙 추정 (옷 형태 기반)
    elbow_y = y + int(h_box * 0.4)  # 상위 40% 지점
    left_elbow = (int(left_shoulder[0] - w_box * 0.05), elbow_y)
    right_elbow = (int(right_shoulder[0] + w_box * 0.05), elbow_y)
    
    hip_y = y + int(h_box * 0.85)  # 하위 15% 지점
    hip_width_ratio = 0.7  # 엉덩이는 어깨보다 좁음
    left_hip = (int(cloth_center[0] - shoulder_width * hip_width_ratio / 2), hip_y)
    right_hip = (int(cloth_center[0] + shoulder_width * hip_width_ratio / 2), hip_y)
    
    keypoints = {
        'left_shoulder': left_shoulder,
        'right_shoulder': right_shoulder,
        'shoulder_width': shoulder_width,
        'neck_point': neck_point,
        'cloth_center': cloth_center,
        'left_elbow': left_elbow,
        'right_elbow': right_elbow,
        'left_hip': left_hip,
        'right_hip': right_hip,
        'bounding_box': (x, y, w_box, h_box)
    }
    
    print(f"[Cloth Processor] 어깨 감지 완료: 너비={shoulder_width}px, 위치=({left_shoulder}, {right_shoulder})")
    return keypoints

def estimate_cloth_keypoints_from_contour_simple(img, x, y, w_box, h_box):
    """
    간단한 윤곽선 기반 키포인트 추정 (폴백)
    
    Args:
        img: 옷 이미지
        x, y, w_box, h_box: 바운딩 박스 정보
    
    Returns:
        dict: 기본 키포인트
    """
    keypoints = {
        'left_shoulder': (x + int(w_box * 0.15), y + int(h_box * 0.1)),
        'right_shoulder': (x + int(w_box * 0.85), y + int(h_box * 0.1)),
        'shoulder_width': int(w_box * 0.7),
        'neck_point': (x + w_box // 2, y + int(h_box * 0.05)),
        'cloth_center': (x + w_box // 2, y + h_box // 2),
        'left_elbow': (x + int(w_box * 0.1), y + int(h_box * 0.4)),
        'right_elbow': (x + int(w_box * 0.9), y + int(h_box * 0.4)),
        'left_hip': (x + int(w_box * 0.3), y + int(h_box * 0.85)),
        'right_hip': (x + int(w_box * 0.7), y + int(h_box * 0.85)),
        'bounding_box': (x, y, w_box, h_box)
    }
    
    print("[Cloth Processor] 기본 추정 키포인트 사용")
    return keypoints

def detect_cloth_keypoints(cloth_image_path):
    """
    옷 이미지에서 관절(키포인트) 위치를 감지합니다.
    (하위 호환성을 위해 유지, 새로운 함수 사용 권장)
    
    Args:
        cloth_image_path: 옷 이미지 경로
    
    Returns:
        dict: 옷의 주요 키포인트 좌표
    """
    # cloth_nobg.png가 있으면 고급 감지 사용
    nobg_path = cloth_image_path.replace('cloth.jpg', '../output/cloth_nobg.png').replace('input/', 'fit/')
    if os.path.exists(nobg_path):
        print(f"[Cloth Processor] 배경 제거 이미지 사용: {nobg_path}")
        return detect_cloth_keypoints_advanced(nobg_path)
    
    print(f"[Cloth Processor] 옷 키포인트 감지 시작: {cloth_image_path}")
    
    # 이미지 읽기
    img = cv2.imread(cloth_image_path)
    if img is None:
        print("[Cloth Processor] 이미지를 읽을 수 없습니다")
        return None
    
    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    h, w = img.shape[:2]
    
    # MediaPipe Pose로 옷의 형태 감지
    with mp_pose.Pose(
        static_image_mode=True,
        model_complexity=2,
        enable_segmentation=False,
        min_detection_confidence=0.3
    ) as pose:
        results = pose.process(rgb_img)
        
        if not results.pose_landmarks:
            print("[Cloth Processor] 옷에서 키포인트를 감지하지 못했습니다. 대안 방법 사용")
            # 대안: 이미지 윤곽선 기반 키포인트 추정
            return estimate_cloth_keypoints_from_contour(img)
        
        landmarks = results.pose_landmarks.landmark
        
        keypoints = {
            'left_shoulder': (landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].x * w,
                            landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER].y * h),
            'right_shoulder': (landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].x * w,
                             landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER].y * h),
            'left_elbow': (landmarks[mp_pose.PoseLandmark.LEFT_ELBOW].x * w,
                          landmarks[mp_pose.PoseLandmark.LEFT_ELBOW].y * h),
            'right_elbow': (landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW].x * w,
                           landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW].y * h),
            'left_hip': (landmarks[mp_pose.PoseLandmark.LEFT_HIP].x * w,
                        landmarks[mp_pose.PoseLandmark.LEFT_HIP].y * h),
            'right_hip': (landmarks[mp_pose.PoseLandmark.RIGHT_HIP].x * w,
                         landmarks[mp_pose.PoseLandmark.RIGHT_HIP].y * h),
        }
        
        print("[Cloth Processor] 옷 키포인트 감지 완료")
        return keypoints

def estimate_cloth_keypoints_from_contour(img):
    """
    윤곽선 기반으로 옷의 키포인트를 추정합니다.
    
    Args:
        img: 옷 이미지 (BGR)
    
    Returns:
        dict: 추정된 키포인트
    """
    h, w = img.shape[:2]
    
    # 그레이스케일 변환
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 이진화
    _, binary = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY)
    
    # 윤곽선 찾기
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        print("[Cloth Processor] 윤곽선을 찾을 수 없습니다. 기본값 사용")
        return get_default_cloth_keypoints(w, h)
    
    # 가장 큰 윤곽선 선택
    main_contour = max(contours, key=cv2.contourArea)
    
    # 바운딩 박스
    x, y, w_box, h_box = cv2.boundingRect(main_contour)
    
    # 키포인트 추정 (옷의 일반적인 형태 기반)
    keypoints = {
        'left_shoulder': (x + w_box * 0.25, y + h_box * 0.15),
        'right_shoulder': (x + w_box * 0.75, y + h_box * 0.15),
        'left_elbow': (x + w_box * 0.15, y + h_box * 0.45),
        'right_elbow': (x + w_box * 0.85, y + h_box * 0.45),
        'left_hip': (x + w_box * 0.30, y + h_box * 0.85),
        'right_hip': (x + w_box * 0.70, y + h_box * 0.85),
    }
    
    print("[Cloth Processor] 윤곽선 기반 키포인트 추정 완료")
    return keypoints

def get_default_cloth_keypoints(w, h):
    """기본 키포인트 반환 (정면 티셔츠 형태 가정)"""
    return {
        'left_shoulder': (w * 0.25, h * 0.15),
        'right_shoulder': (w * 0.75, h * 0.15),
        'left_elbow': (w * 0.15, h * 0.45),
        'right_elbow': (w * 0.85, h * 0.45),
        'left_hip': (w * 0.30, h * 0.85),
        'right_hip': (w * 0.70, h * 0.85),
    }

def get_body_segmentation_mask(frame, body_keypoints=None):
    """
    MediaPipe를 사용하여 신체 세그멘테이션 마스크 생성
    
    Args:
        frame: 입력 프레임 (BGR)
        body_keypoints: 신체 키포인트 (옵션, 상체만 마스크하는데 사용)
    
    Returns:
        binary_mask: 신체 영역 마스크 (0 또는 255)
    """
    try:
        segmentation = get_segmentation_model()
        
        # RGB로 변환
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 세그멘테이션 수행
        results = segmentation.process(frame_rgb)
        
        if results.segmentation_mask is None:
            return None
        
        # 마스크를 이진화 (threshold: 0.5)
        mask = results.segmentation_mask
        binary_mask = (mask > 0.5).astype(np.uint8) * 255
        
        # 상체 영역만 추출 (body_keypoints가 있는 경우)
        if body_keypoints and 'left_shoulder' in body_keypoints and 'right_shoulder' in body_keypoints:
            h, w = frame.shape[:2]
            
            # 어깨 위치 기준으로 상체 영역 정의
            left_shoulder = body_keypoints['left_shoulder']
            right_shoulder = body_keypoints['right_shoulder']
            
            # 상체 영역: 어깨 위 20% ~ 엉덩이 아래 (또는 프레임 하단)
            shoulder_y = int((left_shoulder[1] + right_shoulder[1]) / 2)
            top_y = max(0, shoulder_y - int(h * 0.2))
            
            # 엉덩이가 있으면 그 위치, 없으면 어깨 아래 60%
            if 'left_hip' in body_keypoints and 'right_hip' in body_keypoints:
                hip_y = int((body_keypoints['left_hip'][1] + body_keypoints['right_hip'][1]) / 2)
                bottom_y = min(h, hip_y + int(h * 0.1))
            else:
                bottom_y = min(h, shoulder_y + int(h * 0.6))
            
            # 마스크 생성 (상체 영역만)
            torso_mask = np.zeros_like(binary_mask)
            torso_mask[top_y:bottom_y, :] = binary_mask[top_y:bottom_y, :]
            
            return torso_mask
        
        return binary_mask
    
    except Exception as e:
        print(f"[Cloth Processor] 세그멘테이션 실패: {e}")
        return None

def refine_cloth_with_segmentation(warped_cloth, frame, body_keypoints):
    """
    세그멘테이션 마스크를 사용하여 옷을 신체 윤곽에 맞게 정제
    
    Args:
        warped_cloth: 변형된 옷 이미지 (RGBA, 프레임과 동일한 크기)
        frame: 원본 프레임 (BGR)
        body_keypoints: 신체 키포인트
    
    Returns:
        refined_cloth: 세그멘테이션으로 정제된 옷 이미지 (RGBA)
    """
    try:
        # 신체 세그멘테이션 마스크 생성
        body_mask = get_body_segmentation_mask(frame, body_keypoints)
        
        if body_mask is None:
            print("[Cloth Processor] 세그멘테이션 마스크 생성 실패, 원본 사용")
            return warped_cloth
        
        # 옷의 알파 채널 추출
        if warped_cloth.shape[2] == 4:
            cloth_alpha = warped_cloth[:, :, 3]
        else:
            cloth_alpha = np.ones((warped_cloth.shape[0], warped_cloth.shape[1]), dtype=np.uint8) * 255
        
        # 신체 마스크와 옷 마스크의 교집합 (옷이 신체 영역에만 표시)
        refined_alpha = cv2.bitwise_and(cloth_alpha, body_mask)
        
        # 모폴로지 연산으로 부드럽게
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        refined_alpha = cv2.morphologyEx(refined_alpha, cv2.MORPH_CLOSE, kernel)
        refined_alpha = cv2.GaussianBlur(refined_alpha, (5, 5), 0)
        
        # 정제된 알파 채널 적용
        refined_cloth = warped_cloth.copy()
        if refined_cloth.shape[2] == 4:
            refined_cloth[:, :, 3] = refined_alpha
        else:
            # BGR을 RGBA로 변환
            refined_cloth = cv2.cvtColor(refined_cloth, cv2.COLOR_BGR2BGRA)
            refined_cloth[:, :, 3] = refined_alpha
        
        print("[Cloth Processor] ✓ 세그멘테이션 기반 정제 완료")
        return refined_cloth
    
    except Exception as e:
        print(f"[Cloth Processor] 세그멘테이션 정제 실패: {e}")
        return warped_cloth

def warp_cloth_to_pose(cloth_img, cloth_keypoints, body_keypoints, frame_shape, use_segmentation=True, frame=None):
    """
    옷 이미지를 신체 포즈에 맞춰 변형(warp)합니다.
    세그멘테이션 기반 매칭으로 신체 윤곽에 정확하게 피팅
    
    Args:
        cloth_img: 옷 이미지 (RGBA)
        cloth_keypoints: 옷의 키포인트 (left_shoulder, right_shoulder 등)
        body_keypoints: 신체의 키포인트 (left_shoulder, right_shoulder 등)
        frame_shape: 출력 프레임 크기 (height, width)
        use_segmentation: 세그멘테이션 기반 정제 사용 여부 (기본: True)
        frame: 원본 프레임 (세그멘테이션 사용 시 필요)
    
    Returns:
        변형된 옷 이미지 (프레임과 동일한 크기, RGBA)
    """
    frame_h, frame_w = frame_shape[:2]
    
    # === 1. 옷 이미지의 소스 포인트 설정 (3점) ===
    if 'left_shoulder' not in cloth_keypoints or 'right_shoulder' not in cloth_keypoints:
        print("[Cloth Processor] 옷의 어깨 키포인트 없음 - 변형 불가")
        return cloth_img
    
    cloth_left_shoulder = np.array(cloth_keypoints['left_shoulder'], dtype=np.float32)
    cloth_right_shoulder = np.array(cloth_keypoints['right_shoulder'], dtype=np.float32)
    
    # 옷의 중심점 계산
    cloth_mid_x = (cloth_left_shoulder[0] + cloth_right_shoulder[0]) / 2
    cloth_mid_y = (cloth_left_shoulder[1] + cloth_right_shoulder[1]) / 2
    cloth_shoulder_width = np.linalg.norm(cloth_left_shoulder - cloth_right_shoulder)
    
    vertical_offset = np.clip(cloth_shoulder_width * 0.8, 60, 150)
    cloth_center = np.array([cloth_mid_x, cloth_mid_y + vertical_offset], dtype=np.float32)
    
    src_points = np.float32([
        cloth_right_shoulder,  # [0] 오른쪽 어깨
        cloth_left_shoulder,   # [1] 왼쪽 어깨
        cloth_center           # [2] 중심점
    ])
    
    # === 2. 신체의 목적지 포인트 설정 (3점) ===
    if 'left_shoulder' not in body_keypoints or 'right_shoulder' not in body_keypoints:
        print("[Cloth Processor] 신체의 어깨 키포인트 없음 - 변형 불가")
        return cloth_img
    
    body_left_shoulder = np.array(body_keypoints['left_shoulder'], dtype=np.float32)
    body_right_shoulder = np.array(body_keypoints['right_shoulder'], dtype=np.float32)
    
    body_mid_x = (body_left_shoulder[0] + body_right_shoulder[0]) / 2
    body_mid_y = (body_left_shoulder[1] + body_right_shoulder[1]) / 2
    body_shoulder_width = np.linalg.norm(body_left_shoulder - body_right_shoulder)
    
    body_vertical_offset = np.clip(body_shoulder_width * 0.8, 60, 150)
    body_center = np.array([body_mid_x, body_mid_y + body_vertical_offset], dtype=np.float32)
    
    dst_points = np.float32([
        body_right_shoulder,  # [0] 오른쪽 어깨
        body_left_shoulder,   # [1] 왼쪽 어깨
        body_center           # [2] 중심점
    ])
    
    # === 3. 어파인 변환 ===
    try:
        M = cv2.getAffineTransform(src_points, dst_points)
        
        # 옷 이미지 변형
        warped = cv2.warpAffine(
            cloth_img, 
            M, 
            (frame_w, frame_h),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=(0, 0, 0, 0)
        )
        
        # === 4. 세그멘테이션 기반 정제 (옵션) ===
        if use_segmentation and frame is not None:
            warped = refine_cloth_with_segmentation(warped, frame, body_keypoints)
            print(f"[Cloth Processor] ✓ 세그멘테이션 매칭 완료 - 어깨: {body_shoulder_width:.1f}px")
        else:
            print(f"[Cloth Processor] ✓ 어파인 변환 완료 - 어깨: {body_shoulder_width:.1f}px")
        
        return warped
        return warped
        
    except Exception as e:
        print(f"[Cloth Processor] 어파인 변환 실패: {e}")
        return cloth_img
