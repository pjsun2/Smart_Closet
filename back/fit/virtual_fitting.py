import cv2
import mediapipe as mp
import numpy as np
import os
from cloth_processor import (
    remove_background, 
    resize_cloth_to_body, 
    overlay_cloth_on_body,
    detect_cloth_keypoints,
    warp_cloth_to_pose
)

# GPU 사용 확인
def check_gpu_availability():
    """GPU 사용 가능 여부 확인"""
    print("\n" + "="*70)
    print("[GPU Check] GPU 사용 가능 여부 확인")
    print("="*70)
    
    # CUDA 확인
    try:
        import torch
        if torch.cuda.is_available():
            print(f"[GPU] [OK] CUDA 사용 가능")
            print(f"[GPU] GPU 개수: {torch.cuda.device_count()}")
            print(f"[GPU] GPU 이름: {torch.cuda.get_device_name(0)}")
        else:
            print("[GPU] [FAIL] CUDA 사용 불가 (CPU 모드)")
    except ImportError:
        print("[GPU] [WARNING] PyTorch 미설치 (CUDA 확인 불가)")
    
    # OpenCV CUDA 확인
    print(f"[GPU] OpenCV 버전: {cv2.__version__}")
    print(f"[GPU] OpenCV CUDA 지원: {cv2.cuda.getCudaEnabledDeviceCount() > 0 if hasattr(cv2, 'cuda') else 'N/A'}")
    
    print("="*70 + "\n")

# GPU 확인 실행
check_gpu_availability()

# MediaPipe 초기화
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

class VirtualFitting:
    """실시간 가상 피팅 클래스"""
    
    def __init__(self, cloth_image_path='input/cloth.jpg'):
        """
        Args:
            cloth_image_path: 옷 이미지 경로
        """
        self.cloth_image_path = cloth_image_path
        self.cloth_img = None
        self.cloth_original = None
        self.cloth_keypoints = None  # 옷의 관절 위치
        
        # 추론 최적화: 4프레임마다 추론 진행
        self.frame_count = 0  # 프레임 카운터
        self.inference_interval = 4  # 4프레임마다 추론
        self.last_pose_result = None  # 마지막 추론 결과 캐싱
        
        # GPU 사용 여부 확인
        self.use_gpu = self._check_gpu()
        
        # MediaPipe Pose 초기화 (GPU 활성화)
        self.pose = mp_pose.Pose(
            static_image_mode=False,
            model_complexity=2,  # GPU 사용 시 최고 품질 모델 (0=빠름, 1=보통, 2=정확)
            enable_segmentation=False,
            min_detection_confidence=0.5,  # 감지 신뢰도 (낮추면 빠르지만 부정확)
            min_tracking_confidence=0.5,   # 추적 신뢰도 (낮추면 빠르지만 떨림 증가)
            smooth_landmarks=True,         # 랜드마크 스무딩 (GPU 사용, 더 부드러움)
            smooth_segmentation=False      # 세그멘테이션 미사용
        )
        
        # 옷 이미지 로드 및 배경 제거
        self.load_cloth()
        
        print(f"[Virtual Fitting] 추론 최적화: {self.inference_interval}프레임마다 추론 실행")
    
    def _check_gpu(self):
        """GPU 사용 가능 여부 확인"""
        try:
            import torch
            if torch.cuda.is_available():
                print(f"[Virtual Fitting] [OK] GPU 모드 활성화 ({torch.cuda.get_device_name(0)})")
                return True
        except:
            pass
        print("[Virtual Fitting] [WARNING] CPU 모드로 실행")
        return False
    
    def load_cloth(self):
        """옷 이미지 로드 및 배경 제거"""
        # 출력 폴더 생성
        output_dir = 'output'
        os.makedirs(output_dir, exist_ok=True)
        
        # 배경 제거된 이미지 경로
        output_path = os.path.join(output_dir, 'cloth_nobg.png')
        
        # output/cloth_nobg.png가 이미 있으면 그것을 사용
        if os.path.exists(output_path):
            try:
                import cv2
                # 기존 배경 제거된 이미지 로드
                self.cloth_original = cv2.imread(output_path, cv2.IMREAD_UNCHANGED)
                
                if self.cloth_original is not None:
                    print(f"[Virtual Fitting] 기존 배경 제거 이미지 사용: {output_path}")
                    
                    # 고급 키포인트 감지 사용 (cloth_nobg.png 기반)
                    from cloth_processor import detect_cloth_keypoints_advanced
                    self.cloth_keypoints = detect_cloth_keypoints_advanced(output_path)
                    
                    if self.cloth_keypoints:
                        print(f"[Virtual Fitting] 옷 어깨 너비: {self.cloth_keypoints.get('shoulder_width', 'N/A')}px")
                    
                    print(f"[Virtual Fitting] 옷 이미지 로드 완료 (캐시 사용)")
                    return True
            except Exception as e:
                print(f"[Virtual Fitting] 기존 이미지 로드 실패: {e}, 새로 생성합니다")
        
        # 원본 이미지가 없으면 에러
        if not os.path.exists(self.cloth_image_path):
            print(f"[Virtual Fitting] 옷 이미지가 없습니다: {self.cloth_image_path}")
            return False
        
        try:
            # 배경 제거
            print(f"[Virtual Fitting] 새로 배경 제거 시작: {self.cloth_image_path}")
            self.cloth_original = remove_background(self.cloth_image_path, output_path)
            
            # 고급 키포인트 감지 사용 (cloth_nobg.png 기반)
            from cloth_processor import detect_cloth_keypoints_advanced
            self.cloth_keypoints = detect_cloth_keypoints_advanced(output_path)
            
            if self.cloth_keypoints:
                print(f"[Virtual Fitting] 옷 어깨 너비: {self.cloth_keypoints.get('shoulder_width', 'N/A')}px")
            self.cloth_keypoints = detect_cloth_keypoints(self.cloth_image_path)
            
            print(f"[Virtual Fitting] 옷 이미지 로드 완료 (새로 생성)")
            return True
        except Exception as e:
            print(f"[Virtual Fitting] 옷 이미지 로드 실패: {e}")
            return False
    
    def calculate_shoulder_matched_scale(self, body_shoulder_width):
        """
        옷의 어깨와 신체 어깨를 매칭하여 최적 스케일 계산
        
        Args:
            body_shoulder_width: 신체 어깨 너비 (픽셀)
        
        Returns:
            float: 리사이즈 스케일
        """
        if not self.cloth_keypoints or 'shoulder_width' not in self.cloth_keypoints:
            # 키포인트 정보 없으면 기본 비율 사용
            return 1.0
        
        cloth_shoulder_width = self.cloth_keypoints['shoulder_width']
        
        # 신체 어깨에 맞춰 스케일 계산
        scale = body_shoulder_width / cloth_shoulder_width
        
        # 약간 여유있게 (10% 더 크게)
        scale *= 1.1
        
        return scale
    
    def resize_cloth_by_shoulder_matching(self, body_shoulder_width):
        """
        어깨 매칭 기반 자동 리사이즈
        
        Args:
            body_shoulder_width: 신체 어깨 너비 (픽셀)
        
        Returns:
            리사이즈된 옷 이미지 (RGBA)
        """
        if self.cloth_original is None:
            return None
        
        # 스케일 계산
        scale = self.calculate_shoulder_matched_scale(body_shoulder_width)
        
        h, w = self.cloth_original.shape[:2]
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        # 리사이즈
        resized = cv2.resize(self.cloth_original, (new_w, new_h), interpolation=cv2.INTER_AREA)
        
        print(f"[Virtual Fitting] 어깨 매칭 리사이즈: {w}x{h} → {new_w}x{new_h} (스케일: {scale:.2f})")
        
        return resized
    
    def calculate_body_metrics(self, landmarks, image_shape):
        """
        신체 치수 계산 및 키포인트 추출
        
        Returns:
            dict: shoulder_center, shoulder_width, body_height, keypoints
        """
        h, w = image_shape[:2]
        
        # 어깨 랜드마크
        left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
        right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
        
        # 골반 랜드마크
        left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
        right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]
        
        # 팔꿈치 랜드마크
        left_elbow = landmarks[mp_pose.PoseLandmark.LEFT_ELBOW]
        right_elbow = landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW]
        
        # 어깨 중심점
        shoulder_center_x = (left_shoulder.x + right_shoulder.x) / 2 * w
        shoulder_center_y = (left_shoulder.y + right_shoulder.y) / 2 * h
        
        # 어깨 너비
        shoulder_width = abs(right_shoulder.x - left_shoulder.x) * w
        
        # 상체 높이 (어깨 → 골반)
        hip_center_y = (left_hip.y + right_hip.y) / 2 * h
        body_height = abs(hip_center_y - shoulder_center_y)
        
        # 신체 키포인트 (옷과 매칭용)
        body_keypoints = {
            'left_shoulder': (left_shoulder.x * w, left_shoulder.y * h),
            'right_shoulder': (right_shoulder.x * w, right_shoulder.y * h),
            'left_elbow': (left_elbow.x * w, left_elbow.y * h),
            'right_elbow': (right_elbow.x * w, right_elbow.y * h),
            'left_hip': (left_hip.x * w, left_hip.y * h),
            'right_hip': (right_hip.x * w, right_hip.y * h),
        }
        
        return {
            'shoulder_center': (shoulder_center_x, shoulder_center_y),
            'shoulder_width': shoulder_width,
            'body_height': body_height,
            'keypoints': body_keypoints
        }
    
    def process_frame(self, frame, show_skeleton=True, use_warp=True):
        """
        프레임 처리 및 가상 피팅 적용
        
        Args:
            frame: 입력 비디오 프레임 (BGR)
            show_skeleton: 스켈레톤 표시 여부
            use_warp: 관절 매칭 변형 사용 여부
        
        Returns:
            처리된 프레임
        """
        if self.cloth_original is None:
            return frame
        
        # 프레임 카운터 증가
        self.frame_count += 1
        
        # BGR → RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 4프레임마다 추론 실행 (나머지는 캐시된 결과 사용)
        if self.frame_count % self.inference_interval == 0:
            # 포즈 감지 (GPU 추론)
            results = self.pose.process(rgb_frame)
            
            if results.pose_landmarks:
                # 추론 결과 캐싱
                self.last_pose_result = results
            else:
                # 포즈 감지 실패 시 이전 결과 유지
                if self.last_pose_result is None:
                    return frame
        else:
            # 캐시된 결과 사용 (GPU 추론 생략)
            if self.last_pose_result is None:
                return frame
            results = self.last_pose_result
        
        if not results.pose_landmarks:
            return frame
        
        # 신체 치수 계산 및 키포인트 추출
        metrics = self.calculate_body_metrics(
            results.pose_landmarks.landmark, 
            frame.shape
        )
        
        # 옷 처리 - 어깨 매칭 기반 자동 리사이즈 사용
        if use_warp and self.cloth_keypoints is not None:
            # 방법 1: 어깨 매칭 + 관절 변형 (최고급)
            print("[Virtual Fitting] 어깨 매칭 + 관절 변형 모드 (RTMPose 스타일)")
            
            # 1단계: 어깨 매칭 기반 자동 리사이즈
            resized_cloth = self.resize_cloth_by_shoulder_matching(metrics['shoulder_width'])
            
            if resized_cloth is None:
                resized_cloth = self.cloth_original.copy()
            
            # 2단계: 옷을 신체 포즈에 맞춰 변형 (3점 어파인 변환)
            # 리사이즈된 옷의 키포인트 재계산
            h_resized, w_resized = resized_cloth.shape[:2]
            h_original, w_original = self.cloth_original.shape[:2]
            scale_ratio = w_resized / w_original
            
            # 옷 키포인트를 스케일에 맞춰 조정 (좌표 튜플만 처리)
            # shoulder_width, bounding_box 같은 비좌표 데이터는 제외
            scaled_cloth_keypoints = {}
            exclude_keys = {'shoulder_width', 'bounding_box', 'cloth_center'}  # 스케일 조정 불필요한 키
            
            for key, value in self.cloth_keypoints.items():
                if key in exclude_keys:
                    continue
                # 튜플이고 2개 요소인 경우만 처리 (x, y 좌표)
                if isinstance(value, (tuple, list)) and len(value) == 2:
                    try:
                        x, y = float(value[0]), float(value[1])
                        scaled_cloth_keypoints[key] = (x * scale_ratio, y * scale_ratio)
                    except (TypeError, ValueError) as e:
                        print(f"[Virtual Fitting] 키포인트 '{key}' 스케일 조정 실패: {e}")
                        continue
            
            # RTMPose 스타일 어파인 변형 (프레임 크기로 변환)
            warped_cloth = warp_cloth_to_pose(
                resized_cloth,
                scaled_cloth_keypoints,
                metrics['keypoints'],
                frame.shape  # 프레임 크기 전달
            )
            
            # RTMPose 스타일 알파 블렌딩 (위치 지정 불필요, 완전 불투명)
            result = overlay_cloth_on_body(
                frame,
                warped_cloth,
                position=None,  # 이미 변형된 이미지 사용
                alpha=1.0  # 완전 불투명
            )
        else:
            # 방법 2: 어깨 매칭 리사이즈만 사용 (기본)
            print("[Virtual Fitting] 어깨 매칭 리사이즈 모드")
            
            # 어깨 매칭 기반 자동 리사이즈
            resized_cloth = self.resize_cloth_by_shoulder_matching(metrics['shoulder_width'])
            
            if resized_cloth is None:
                # 폴백: 기존 방식
                resized_cloth = resize_cloth_to_body(
                    self.cloth_original,
                    metrics['shoulder_width'] * 1.2,
                    metrics['body_height'] * 1.5
                )
            
            # 옷 오버레이 위치
            cloth_position = (
                metrics['shoulder_center'][0],
                metrics['shoulder_center'][1] - 20
            )
            
            # 옷 오버레이 (완전 불투명)
            result = overlay_cloth_on_body(
                frame,
                resized_cloth,
                cloth_position,
                alpha=1.0  # 완전 불투명
            )
        
        # 스켈레톤 그리기 (선택적)
        if show_skeleton:
            mp_drawing.draw_landmarks(
                result,
                results.pose_landmarks,
                mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=mp_drawing.DrawingSpec(
                    color=(0, 255, 0), thickness=2, circle_radius=2
                ),
                connection_drawing_spec=mp_drawing.DrawingSpec(
                    color=(0, 255, 0), thickness=2
                )
            )
        
        return result
    
    def run_webcam(self, camera_index=0):
        """
        웹캠을 사용한 실시간 가상 피팅
        
        Args:
            camera_index: 카메라 인덱스
        """
        cap = cv2.VideoCapture(camera_index)
        
        if not cap.isOpened():
            print("[Virtual Fitting] 카메라를 열 수 없습니다")
            return
        
        print("[Virtual Fitting] 실시간 가상 피팅 시작")
        print("'s' - 스켈레톤 토글, 'w' - 변형 모드 토글, 'q' - 종료")
        
        show_skeleton = True
        use_warp = True  # 관절 매칭 변형 사용
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # 좌우 반전 (거울 효과)
            frame = cv2.flip(frame, 1)
            
            # 가상 피팅 처리
            result = self.process_frame(frame, show_skeleton=show_skeleton, use_warp=use_warp)
            
            # 모드 표시
            mode_text = f"Mode: {'Warp' if use_warp else 'Resize'} | Skeleton: {'ON' if show_skeleton else 'OFF'}"
            cv2.putText(result, mode_text, (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # 화면에 표시
            cv2.imshow('Virtual Fitting', result)
            
            # 키 입력 처리
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                show_skeleton = not show_skeleton
                print(f"[Virtual Fitting] 스켈레톤: {'ON' if show_skeleton else 'OFF'}")
            elif key == ord('w'):
                use_warp = not use_warp
                print(f"[Virtual Fitting] 변형 모드: {'관절 매칭' if use_warp else '단순 크기 조정'}")
        
        cap.release()
        cv2.destroyAllWindows()
        print("[Virtual Fitting] 종료")
    
    def __del__(self):
        """소멸자 - 리소스 정리"""
        if hasattr(self, 'pose'):
            self.pose.close()

def main():
    """메인 실행 함수"""
    vf = VirtualFitting(cloth_image_path='input/cloth.jpg')
    vf.run_webcam()

if __name__ == "__main__":
    main()
