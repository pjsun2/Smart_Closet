import cv2
import numpy as np
import os
import sys
import threading
import queue
import time
import torch

# 현재 디렉토리를 sys.path에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from mmpose.apis import init_model, inference_topdown
from mmpose.structures import merge_data_samples

# cloth_processor import (같은 디렉토리에서)
try:
    from cloth_processor import (
        remove_background, 
        resize_cloth_to_body, 
        overlay_cloth_on_body,
        detect_cloth_keypoints_advanced,
        warp_cloth_to_pose
    )
except ImportError:
    # 상대 경로로 다시 시도
    from .cloth_processor import (
        remove_background, 
        resize_cloth_to_body, 
        overlay_cloth_on_body,
        detect_cloth_keypoints_advanced,
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

class RTMPoseVirtualFitting:
    """RTMPose 기반 실시간 가상 피팅 클래스"""
    
    def __init__(self, cloth_image_path='input/cloth.jpg', device='cuda:0'):
        """
        Args:
            cloth_image_path: 옷 이미지 경로
            device: 'cuda:0' 또는 'cpu'
        """
        # 현재 파일의 절대 경로 기준으로 경로 설정
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 옷 이미지 경로를 절대 경로로 변환
        if not os.path.isabs(cloth_image_path):
            self.cloth_image_path = os.path.join(current_dir, cloth_image_path)
        else:
            self.cloth_image_path = cloth_image_path
            
        self.cloth_img = None
        self.cloth_original = None
        self.cloth_keypoints = None  # 옷의 관절 위치
        self.device = device
        
        # 추론 최적화: 시간 기반 추론 제어 (25 FPS - 벤치마크 최적값)
        self.last_inference_time = 0
        self.inference_interval = 0.04  # 0.04초 = 25 FPS (벤치마크: 5000.96 FPS)
        self.last_pose_result = None
        
        # 출력 최적화 (60 FPS - 최대)
        self.output_fps = 60
        self.output_interval = 1 / self.output_fps  # 0.0167초
        self.last_output_time = 0
        
        # 프레임 기반 추론도 지원 (하위 호환성)
        self.frame_count = 0
        self.use_time_based_inference = True  # True: 시간 기반, False: 프레임 기반
        
        # 추론 해상도 최적화 (GPU 사용량 증가)
        self.inference_scale = 0.65  # 추론 시 해상도 스케일 (65% - GPU 부하 증가)
        self.use_inference_downscale = True  # 추론 다운스케일 활성화
        
        # 비동기 추론 설정
        self.use_async_inference = True  # 비동기 추론 활성화
        # 배치 처리 설정 (테스트 결과 적용)
        self.use_batch_inference = True  # 배치 처리 활성화
        self.batch_size = 10  # 배치 크기 (최적값: 10)
        self.frame_timeout = 0.050  # 프레임 타임아웃 (초) - 50ms (테스트 결과: 최고 성능)
        self.inference_queue = queue.Queue(maxsize=22)  # 큐 크기 최적화 (테스트 결과: 22)
        self.result_queue = queue.Queue(maxsize=11)  # 결과 큐 (추론 큐의 절반)
        self.inference_thread = None
        self.running = False
        
        # 스트리밍 제어 (새로 추가)
        self.streaming_enabled = False  # 스트리밍 on/off
        self.streaming_lock = threading.Lock()  # 스레드 안전성
        
        # 성능 최적화: 캐싱
        self.resized_cloth_cache = {}  # shoulder_width를 키로 사용
        self.warped_cloth_cache = {}   # 변형된 옷 캐시
        self.cache_max_size = 5        # 최대 캐시 크기
        
        # GPU 사용 여부 확인
        self.use_gpu = self._check_gpu()
        
        # PyTorch GPU 최적화 설정
        if torch.cuda.is_available() and 'cuda' in device:
            # GPU 메모리 할당 최적화
            torch.backends.cudnn.benchmark = True  # cuDNN 자동 튜닝 (속도 향상)
            torch.backends.cuda.matmul.allow_tf32 = True  # TF32 연산 허용 (RTX 30xx 이상)
            torch.backends.cudnn.allow_tf32 = True
            # Mixed Precision 활성화 고려 (추후 적용 가능)
            print("[RTMPose] [GPU 최적화] cuDNN benchmark, TF32 활성화")
        
        # RTMPose 모델 초기화 (절대 경로 사용)
        config_file = os.path.join(current_dir, 'models', 'rtmpose-s_8xb256-420e_aic-coco-256x192.py')
        checkpoint_file = os.path.join(current_dir, 'models', 'rtmpose-s_simcc-aic-coco_pt-aic-coco_420e-256x192-fcb2599b_20230126.pth')
        
        # 파일 존재 여부 확인
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"Config file not found: {config_file}")
        if not os.path.exists(checkpoint_file):
            raise FileNotFoundError(f"Checkpoint file not found: {checkpoint_file}")
        
        print(f"[RTMPose] 모델 로딩 중... (device: {device})")
        print(f"[RTMPose] Config: {config_file}")
        print(f"[RTMPose] Checkpoint: {checkpoint_file}")
        
        try:
            self.model = init_model(config_file, checkpoint_file, device=device)
            
            # 모델을 eval 모드로 설정 (Dropout, BatchNorm 비활성화)
            self.model.eval()
            
            # GPU 워밍업 (첫 추론 속도 개선)
            if torch.cuda.is_available() and 'cuda' in device:
                print("[RTMPose] GPU 워밍업 중...")
                # 더미 이미지로 워밍업 (실제 추론 함수 사용)
                dummy_image = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
                with torch.no_grad():
                    _ = inference_topdown(self.model, dummy_image)
                torch.cuda.empty_cache()
                print("[RTMPose] GPU 워밍업 완료")
            
            print("[RTMPose] 모델 로딩 완료")
        except Exception as e:
            print(f"[RTMPose] [ERROR] 모델 로딩 실패: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        # 옷 이미지 로드 및 배경 제거
        try:
            self.load_cloth()
            print("[RTMPose] 옷 이미지 로드 완료")
        except Exception as e:
            print(f"[RTMPose] [WARNING] 옷 이미지 로드 실패: {e}")
            print("[RTMPose] 기본 설정으로 계속 진행...")
        
        # 비동기 추론 스레드 시작
        if self.use_async_inference:
            try:
                self.start_inference_thread()
            except Exception as e:
                print(f"[RTMPose] [ERROR] 추론 스레드 시작 실패: {e}")
                import traceback
                traceback.print_exc()
                raise
        
        if self.use_time_based_inference:
            print(f"[RTMPose] 추론 최적화: {self.inference_interval}초마다 추론 실행 ({1/self.inference_interval:.1f} FPS)")
        else:
            print(f"[RTMPose] 추론 최적화: {self.inference_interval}프레임마다 추론 실행")
        
        print(f"[RTMPose] 출력 최적화: {self.output_fps} FPS (FHD 지원)")
        
        if self.use_inference_downscale:
            print(f"[RTMPose] 해상도 최적화: 추론 {int(self.inference_scale*100)}% 해상도, 출력 100% 해상도")
        
        if self.use_async_inference:
            print(f"[RTMPose] 비동기 추론: 활성화 (백그라운드 처리)")
            if self.use_batch_inference:
                print(f"[RTMPose] 배치 처리: 활성화 (배치 크기 {self.batch_size}, 타임아웃 {int(self.frame_timeout*1000)}ms)")
                if torch.cuda.is_available() and 'cuda' in self.device:
                    print(f"[RTMPose] CUDA Streams: 활성화 (GPU 병렬 처리)")
                    print(f"[RTMPose] 실시간 최적화: 최신 프레임 우선 처리")
                    print(f"[RTMPose] 예상 처리량: ~500 FPS (테스트 결과 기반)")
                else:
                    print(f"[RTMPose] 실시간 최적화: 최신 프레임 우선 처리")
                    print(f"[RTMPose] 예상 처리량: ~{self.batch_size * 10} FPS")
            else:
                print(f"[RTMPose] 배치 처리: 비활성화 (단일 프레임)")
        
        print(f"[RTMPose] 스켈레톤 표시: 비활성화 (최적 성능)")
    
    def _check_gpu(self):
        """GPU 사용 가능 여부 확인"""
        try:
            import torch
            if torch.cuda.is_available() and 'cuda' in self.device:
                print(f"[RTMPose] [OK] GPU 모드 활성화")
                return True
        except:
            pass
        print("[RTMPose] [WARNING] CPU 모드로 실행")
        return False
    
    def start_inference_thread(self):
        """비동기 추론 스레드 시작"""
        self.running = True
        self.inference_thread = threading.Thread(target=self._inference_worker, daemon=True)
        self.inference_thread.start()
        print("[RTMPose] 비동기 추론 스레드 시작")
    
    def _inference_worker(self):
        """백그라운드 추론 워커 (배치 처리 지원)"""
        while self.running:
            try:
                if self.use_batch_inference:
                    # === 배치 처리 모드 ===
                    batch_frames = []
                    batch_metadata = []
                    
                    # 배치 크기만큼 프레임 수집 (동적 타임아웃)
                    # 프레임 타임아웃: self.frame_timeout 사용 (테스트 시 동적 변경 가능)
                    
                    for i in range(self.batch_size):
                        try:
                            # 동적 타임아웃: 첫 프레임은 기본, 나머지는 짧게
                            timeout = self.frame_timeout if i == 0 else self.frame_timeout * 0.5
                            frame_data = self.inference_queue.get(timeout=timeout)
                            
                            if frame_data is None:  # 종료 신호
                                self.running = False
                                return
                            
                            frame, original_w, original_h = frame_data
                            batch_frames.append(frame)
                            batch_metadata.append((original_w, original_h))
                        except queue.Empty:
                            break  # 타임아웃, 수집된 프레임만 처리
                    
                    if not batch_frames:
                        continue
                    
                    # 배치 추론 실행 (CUDA Streams로 GPU 병렬 처리)
                    results_batch = []
                    try:
                        # === CUDA Streams 병렬 처리 시도 ===
                        if torch.cuda.is_available() and 'cuda' in self.device:
                            # 각 프레임마다 독립적인 CUDA 스트림 생성
                            streams = [torch.cuda.Stream() for _ in range(len(batch_frames))]
                            
                            # 각 스트림에서 병렬 추론 (no_grad로 메모리 절약)
                            stream_results = [None] * len(batch_frames)
                            with torch.no_grad():  # 그래디언트 계산 비활성화 (추론 속도 향상)
                                for i, (frame, stream) in enumerate(zip(batch_frames, streams)):
                                    with torch.cuda.stream(stream):
                                        stream_results[i] = inference_topdown(self.model, frame)
                            
                            # 모든 스트림 완료 대기
                            torch.cuda.synchronize()
                            results_batch = stream_results
                            
                        else:
                            # CPU 모드 또는 폴백: 순차 처리
                            with torch.no_grad():  # CPU도 no_grad 적용
                                for frame in batch_frames:
                                    result = inference_topdown(self.model, frame)
                                    results_batch.append(result)
                                
                    except Exception as e:
                        print(f"[RTMPose] CUDA Streams 실패, 순차 처리로 폴백: {e}")
                        # 에러 발생 시 기존 방식으로 폴백
                        results_batch = []
                        try:
                            for frame in batch_frames:
                                result = inference_topdown(self.model, frame)
                                results_batch.append(result)
                        except Exception as fallback_error:
                            print(f"[RTMPose] 폴백 추론도 실패: {fallback_error}")
                            # 빈 결과 반환
                            for _ in range(len(batch_frames)):
                                results_batch.append(None)
                    
                    # 각 결과 처리 및 저장 (모든 배치 결과 활용)
                    for i, (results, metadata) in enumerate(zip(results_batch, batch_metadata)):
                        if results is None or len(results) == 0:
                            continue
                        
                        original_w, original_h = metadata
                        
                        # 키포인트를 원본 해상도로 스케일 업
                        if self.use_inference_downscale and self.inference_scale < 1.0:
                            inference_h, inference_w = batch_frames[i].shape[:2]
                            scale_x = original_w / inference_w
                            scale_y = original_h / inference_h
                            
                            for result in results:
                                pred_instances = result.pred_instances
                                pred_instances.keypoints[:, :, 0] *= scale_x
                                pred_instances.keypoints[:, :, 1] *= scale_y
                        
                        # 모든 배치 결과를 큐에 저장 (큐가 가득 차면 오래된 것 제거)
                        if self.result_queue.full():
                            try:
                                self.result_queue.get_nowait()  # 가장 오래된 결과 제거
                            except queue.Empty:
                                pass
                        
                        self.result_queue.put((results, time.time()))
                    
                    # 배치 처리 후 짧은 대기 (추론 간격 유지)
                    # 25 FPS 유지 = 0.04초 간격
                    time.sleep(0.001)  # 1ms (최소 대기, CPU 양보)
                    
                else:
                    # === 단일 프레임 모드 ===
                    frame_data = self.inference_queue.get(timeout=0.15)
                    
                    if frame_data is None:  # 종료 신호
                        break
                    
                    frame, original_w, original_h = frame_data
                    
                    # RTMPose 추론 (저해상도)
                    results = inference_topdown(self.model, frame)
                    
                    if results and len(results) > 0:
                        # 키포인트를 원본 해상도로 스케일 업
                        if self.use_inference_downscale and self.inference_scale < 1.0:
                            inference_h, inference_w = frame.shape[:2]
                            scale_x = original_w / inference_w
                            scale_y = original_h / inference_h
                            
                            for result in results:
                                pred_instances = result.pred_instances
                                pred_instances.keypoints[:, :, 0] *= scale_x
                                pred_instances.keypoints[:, :, 1] *= scale_y
                        
                        # 결과 큐에 저장 (최신 것만 유지)
                        if not self.result_queue.empty():
                            try:
                                self.result_queue.get_nowait()
                            except queue.Empty:
                                pass
                        
                        self.result_queue.put((results, time.time()))
                    
                    # 0.1초 대기 (10 FPS 유지)
                    time.sleep(self.inference_interval)
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[RTMPose] 추론 워커 에러: {e}")
                import traceback
                traceback.print_exc()
                continue
    
    def stop_inference_thread(self):
        """비동기 추론 스레드 종료"""
        if self.use_async_inference and self.running:
            self.running = False
            try:
                self.inference_queue.put(None, timeout=1)  # 종료 신호
            except:
                pass
            if self.inference_thread and self.inference_thread.is_alive():
                self.inference_thread.join(timeout=2)
            print("[RTMPose] 비동기 추론 스레드 종료")
    
    def start_streaming(self):
        """스트리밍 시작 (출력 활성화)"""
        with self.streaming_lock:
            self.streaming_enabled = True
            print("[RTMPose] 스트리밍 시작 - 출력 활성화")
    
    def stop_streaming(self):
        """스트리밍 중지 (출력 비활성화, 백그라운드는 계속 실행)"""
        with self.streaming_lock:
            self.streaming_enabled = False
            print("[RTMPose] 스트리밍 중지 - 백그라운드는 계속 실행")
    
    def is_streaming(self):
        """스트리밍 상태 확인"""
        with self.streaming_lock:
            return self.streaming_enabled
    
    def load_cloth(self):
        """옷 이미지 로드 및 배경 제거"""
        # 현재 디렉토리 기준 절대 경로
        current_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(current_dir, 'output')
        os.makedirs(output_dir, exist_ok=True)
        
        output_path = os.path.join(output_dir, 'cloth_nobg.png')
        
        # output/cloth_nobg.png가 이미 있으면 그것을 사용
        if os.path.exists(output_path):
            try:
                self.cloth_original = cv2.imread(output_path, cv2.IMREAD_UNCHANGED)
                
                if self.cloth_original is not None:
                    print(f"[RTMPose] 기존 배경 제거 이미지 사용: {output_path}")
                    
                    # 고급 키포인트 감지 사용
                    self.cloth_keypoints = detect_cloth_keypoints_advanced(output_path)
                    
                    if self.cloth_keypoints:
                        print(f"[RTMPose] 옷 어깨 너비: {self.cloth_keypoints.get('shoulder_width', 'N/A')}px")
                    
                    print(f"[RTMPose] 옷 이미지 로드 완료 (캐시 사용)")
                    return True
            except Exception as e:
                print(f"[RTMPose] 기존 이미지 로드 실패: {e}, 새로 생성합니다")
        
        # 원본 이미지가 없으면 에러
        if not os.path.exists(self.cloth_image_path):
            print(f"[RTMPose] 옷 이미지가 없습니다: {self.cloth_image_path}")
            return False
        
        try:
            # 배경 제거
            print(f"[RTMPose] 새로 배경 제거 시작: {self.cloth_image_path}")
            self.cloth_original = remove_background(self.cloth_image_path, output_path)
            
            # 고급 키포인트 감지 사용
            self.cloth_keypoints = detect_cloth_keypoints_advanced(output_path)
            
            if self.cloth_keypoints:
                print(f"[RTMPose] 옷 어깨 너비: {self.cloth_keypoints.get('shoulder_width', 'N/A')}px")
            
            print(f"[RTMPose] 옷 이미지 로드 완료 (새로 생성)")
            return True
        except Exception as e:
            print(f"[RTMPose] 옷 이미지 로드 실패: {e}")
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
            return 1.0
        
        cloth_shoulder_width = self.cloth_keypoints['shoulder_width']
        scale = body_shoulder_width / cloth_shoulder_width
        scale *= 1.25  # 약간 여유있게 (5% 더 크게)
        
        return scale
    
    def resize_cloth_by_shoulder_matching(self, body_shoulder_width):
        """
        어깨 매칭 기반 자동 리사이즈 (캐싱 최적화)
        
        Args:
            body_shoulder_width: 신체 어깨 너비 (픽셀)
        
        Returns:
            리사이즈된 옷 이미지 (RGBA)
        """
        if self.cloth_original is None:
            return None
        
        # 캐시 키 생성 (10픽셀 단위로 반올림하여 캐시 히트율 향상)
        cache_key = int(body_shoulder_width / 10) * 10
        
        # 캐시 확인
        if cache_key in self.resized_cloth_cache:
            return self.resized_cloth_cache[cache_key].copy()
        
        scale = self.calculate_shoulder_matched_scale(body_shoulder_width)
        
        h, w = self.cloth_original.shape[:2]
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        # INTER_LINEAR이 INTER_AREA보다 빠름 (품질은 약간 낮지만 실시간에 적합)
        resized = cv2.resize(self.cloth_original, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        
        # 캐시 저장 (크기 제한)
        if len(self.resized_cloth_cache) >= self.cache_max_size:
            # 가장 오래된 항목 제거 (FIFO)
            first_key = next(iter(self.resized_cloth_cache))
            del self.resized_cloth_cache[first_key]
        
        self.resized_cloth_cache[cache_key] = resized.copy()
        
        return resized
    
    def calculate_body_metrics(self, keypoints, image_shape):
        """
        신체 치수 계산 및 키포인트 추출
        
        Args:
            keypoints: RTMPose 키포인트 (17개, COCO 포맷)
                0: nose, 1: left_eye, 2: right_eye, 3: left_ear, 4: right_ear
                5: left_shoulder, 6: right_shoulder
                7: left_elbow, 8: right_elbow
                9: left_wrist, 10: right_wrist
                11: left_hip, 12: right_hip
                13: left_knee, 14: right_knee
                15: left_ankle, 16: right_ankle
        
        Returns:
            dict: shoulder_center, shoulder_width, body_height, keypoints
        """
        h, w = image_shape[:2]
        
        # 어깨 포인트 (COCO 포맷)
        left_shoulder = keypoints[5]   # [x, y, score]
        right_shoulder = keypoints[6]
        
        # 골반 포인트
        left_hip = keypoints[11]
        right_hip = keypoints[12]
        
        # 팔꿈치 포인트
        left_elbow = keypoints[7]
        right_elbow = keypoints[8]
        
        # 어깨 중심점
        shoulder_center_x = (left_shoulder[0] + right_shoulder[0]) / 2
        shoulder_center_y = (left_shoulder[1] + right_shoulder[1]) / 2
        
        # 어깨 너비
        shoulder_width = np.linalg.norm(right_shoulder[:2] - left_shoulder[:2])
        
        # 상체 높이 (어깨 → 골반)
        hip_center_y = (left_hip[1] + right_hip[1]) / 2
        body_height = abs(hip_center_y - shoulder_center_y)
        
        # 신체 키포인트 (옷과 매칭용)
        body_keypoints = {
            'left_shoulder': tuple(left_shoulder[:2]),
            'right_shoulder': tuple(right_shoulder[:2]),
            'left_elbow': tuple(left_elbow[:2]),
            'right_elbow': tuple(right_elbow[:2]),
            'left_hip': tuple(left_hip[:2]),
            'right_hip': tuple(right_hip[:2]),
        }
        
        return {
            'shoulder_center': (shoulder_center_x, shoulder_center_y),
            'shoulder_width': shoulder_width,
            'body_height': body_height,
            'keypoints': body_keypoints
        }
    
    def create_face_neck_mask(self, keypoints, scores, image_shape, frame):
        """
        얼굴과 목 영역 마스크 생성 (피부색 기반)
        
        Args:
            keypoints: RTMPose 키포인트 (17개, COCO 포맷)
            scores: 키포인트 신뢰도
            image_shape: 이미지 크기 (h, w, c)
            frame: 원본 프레임 (BGR, 피부색 샘플링용)
        
        Returns:
            mask: 얼굴/목 영역 마스크 (255=보호 영역, 0=옷 가능 영역)
        """
        h, w = image_shape[:2]
        mask = np.zeros((h, w), dtype=np.uint8)
        
        # 얼굴 관련 키포인트
        nose = keypoints[0]  # 코
        left_eye = keypoints[1]
        right_eye = keypoints[2]
        left_ear = keypoints[3]
        right_ear = keypoints[4]
        left_shoulder = keypoints[5]
        right_shoulder = keypoints[6]
        
        # 신뢰도 확인
        if scores[0] < 0.3 or scores[5] < 0.3 or scores[6] < 0.3:
            return mask  # 신뢰도 부족 시 빈 마스크 반환
        
        # 얼굴 중심과 크기 계산
        # 눈 위치 (신뢰도 확인)
        if scores[1] > 0.3 and scores[2] > 0.3:
            eye_center_x = (left_eye[0] + right_eye[0]) / 2
            eye_center_y = (left_eye[1] + right_eye[1]) / 2
            eye_distance = np.linalg.norm(right_eye[:2] - left_eye[:2])
        else:
            # 눈 대신 귀 사용
            if scores[3] > 0.3 and scores[4] > 0.3:
                eye_center_x = (left_ear[0] + right_ear[0]) / 2
                eye_center_y = (left_ear[1] + right_ear[1]) / 2
                eye_distance = np.linalg.norm(right_ear[:2] - left_ear[:2]) * 0.7
            else:
                # 어깨 중심 사용
                eye_center_x = (left_shoulder[0] + right_shoulder[0]) / 2
                eye_center_y = nose[1]
                eye_distance = np.linalg.norm(right_shoulder[:2] - left_shoulder[:2]) * 0.4
        
        # 어깨 중심
        shoulder_center_x = (left_shoulder[0] + right_shoulder[0]) / 2
        shoulder_center_y = (left_shoulder[1] + right_shoulder[1]) / 2
        
        # 얼굴 폭 (눈 거리의 1.8배)
        face_width = eye_distance * 1.8
        
        # 얼굴 높이 (눈 거리의 1.5배)
        face_height = eye_distance * 1.5
        
        # === 피부색 샘플링 (얼굴 중심 영역에서) ===
        # 코 주변에서 피부색 샘플 추출 (가장 신뢰도 높은 영역)
        sample_size = int(eye_distance * 0.15)  # 샘플 영역 크기
        nose_x, nose_y = int(nose[0]), int(nose[1])
        
        # 샘플 영역이 프레임 내부인지 확인
        sample_x1 = max(0, nose_x - sample_size)
        sample_y1 = max(0, nose_y - sample_size)
        sample_x2 = min(w, nose_x + sample_size)
        sample_y2 = min(h, nose_y + sample_size)
        
        if sample_x2 > sample_x1 and sample_y2 > sample_y1:
            face_sample = frame[sample_y1:sample_y2, sample_x1:sample_x2]
            
            # YCrCb 색공간으로 변환 (피부색 검출에 효과적)
            ycrcb_sample = cv2.cvtColor(face_sample, cv2.COLOR_BGR2YCrCb)
            
            # 피부색 범위 계산 (평균 ± 표준편차)
            mean_ycrcb = np.mean(ycrcb_sample.reshape(-1, 3), axis=0)
            std_ycrcb = np.std(ycrcb_sample.reshape(-1, 3), axis=0)
            
            # 피부색 범위 설정 (평균 ± 2*표준편차)
            lower_skin = np.array([
                max(0, mean_ycrcb[0] - 2 * std_ycrcb[0]),
                max(0, mean_ycrcb[1] - 2 * std_ycrcb[1]),
                max(0, mean_ycrcb[2] - 2 * std_ycrcb[2])
            ], dtype=np.uint8)
            
            upper_skin = np.array([
                min(255, mean_ycrcb[0] + 2 * std_ycrcb[0]),
                min(255, mean_ycrcb[1] + 2 * std_ycrcb[1]),
                min(255, mean_ycrcb[2] + 2 * std_ycrcb[2])
            ], dtype=np.uint8)
            
            # 전체 프레임에서 피부색 마스크 생성
            ycrcb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
            skin_mask = cv2.inRange(ycrcb_frame, lower_skin, upper_skin)
            
            # === ROI (관심 영역) 설정: 얼굴+목 영역만 ===
            roi_mask = np.zeros((h, w), dtype=np.uint8)
            
            # 얼굴 영역 타원 (ROI)
            face_center = (int(eye_center_x), int(eye_center_y))
            face_axes = (int(face_width / 2), int(face_height / 2))
            cv2.ellipse(roi_mask, face_center, face_axes, 0, 0, 360, 255, -1)
            
            # 목 영역 다각형 (ROI)
            neck_width = face_width * 0.6  # 목 너비
            chin_y = int(eye_center_y + face_height / 2)
            
            neck_pts = np.array([
                [int(eye_center_x - neck_width / 2), chin_y],  # 왼쪽 턱
                [int(eye_center_x + neck_width / 2), chin_y],  # 오른쪽 턱
                [int(shoulder_center_x + neck_width / 2), int(shoulder_center_y)],  # 오른쪽 어깨
                [int(shoulder_center_x - neck_width / 2), int(shoulder_center_y)]   # 왼쪽 어깨
            ], dtype=np.int32)
            
            cv2.fillPoly(roi_mask, [neck_pts], 255)
            
            # 피부색 마스크와 ROI 마스크 결합 (AND 연산)
            mask = cv2.bitwise_and(skin_mask, roi_mask)
            
            # 노이즈 제거 (Morphological operations)
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)  # 구멍 메우기
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)   # 작은 노이즈 제거
            
            # 경계 부드럽게 (Gaussian Blur)
            mask = cv2.GaussianBlur(mask, (21, 21), 11)
        else:
            # 샘플링 실패 시 키포인트 기반 폴백
            face_center = (int(eye_center_x), int(eye_center_y))
            face_axes = (int(face_width / 2), int(face_height / 2))
            cv2.ellipse(mask, face_center, face_axes, 0, 0, 360, 255, -1)
            
            neck_width = face_width * 0.5
            chin_y = int(eye_center_y + face_height / 2)
            
            neck_pts = np.array([
                [int(eye_center_x - neck_width / 2), chin_y],
                [int(eye_center_x + neck_width / 2), chin_y],
                [int(shoulder_center_x + neck_width / 2), int(shoulder_center_y)],
                [int(shoulder_center_x - neck_width / 2), int(shoulder_center_y)]
            ], dtype=np.int32)
            
            cv2.fillPoly(mask, [neck_pts], 255)
            mask = cv2.GaussianBlur(mask, (21, 21), 11)
        
        return mask
    
    def refine_cloth_with_face_mask(self, cloth_rgba, face_mask):
        """
        얼굴/목 마스크를 사용하여 옷 이미지 정제
        
        Args:
            cloth_rgba: 옷 이미지 (RGBA, 알파 채널 포함)
            face_mask: 얼굴/목 마스크 (255=보호 영역)
        
        Returns:
            정제된 옷 이미지 (RGBA)
        """
        if cloth_rgba is None or face_mask is None:
            return cloth_rgba
        
        # 옷 이미지 크기와 마스크 크기가 다르면 리사이즈
        if cloth_rgba.shape[:2] != face_mask.shape[:2]:
            face_mask = cv2.resize(face_mask, (cloth_rgba.shape[1], cloth_rgba.shape[0]))
        
        # 알파 채널 추출
        if cloth_rgba.shape[2] == 4:
            alpha = cloth_rgba[:, :, 3].copy()
        else:
            alpha = np.ones((cloth_rgba.shape[0], cloth_rgba.shape[1]), dtype=np.uint8) * 255
        
        # 얼굴/목 영역에서 옷 알파 값 제거
        # face_mask가 255인 곳은 알파를 0으로 (투명하게)
        alpha = np.where(face_mask > 128, 0, alpha).astype(np.uint8)
        
        # 부드러운 경계 처리 (그라데이션)
        # face_mask가 128 근처인 곳은 부드럽게 블렌딩
        blend_zone = cv2.GaussianBlur(face_mask, (15, 15), 5)
        blend_factor = (255 - blend_zone) / 255.0
        alpha = (alpha * blend_factor).astype(np.uint8)
        
        # 새로운 RGBA 이미지 생성
        if cloth_rgba.shape[2] == 4:
            result = cloth_rgba.copy()
            result[:, :, 3] = alpha
        else:
            result = cv2.cvtColor(cloth_rgba, cv2.COLOR_BGR2BGRA)
            result[:, :, 3] = alpha
        
        return result
    
    def process_frame(self, frame, show_skeleton=False, use_warp=True):
        """
        프레임 처리 및 가상 피팅 적용 (비동기 추론 + 60 FPS 출력)
        
        Args:
            frame: 입력 비디오 프레임 (BGR, 원본 해상도)
            show_skeleton: 스켈레톤 표시 여부 (기본값: False - 최적 성능)
            use_warp: 관절 매칭 변형 사용 여부
        
        Returns:
            처리된 프레임 (원본 해상도, 60 FPS)
        """
        # 스트리밍 비활성화 시 원본 프레임 반환 (백그라운드는 계속 실행)
        if not self.is_streaming():
            return frame
        
        if self.cloth_original is None:
            return frame
        
        current_time = time.time()
        
        # 원본 프레임 크기 저장
        original_h, original_w = frame.shape[:2]
        
        # === 비동기 추론 처리 ===
        if self.use_async_inference:
            # 추론용 저해상도 프레임 생성
            if self.use_inference_downscale and self.inference_scale < 1.0:
                inference_w = int(original_w * self.inference_scale)
                inference_h = int(original_h * self.inference_scale)
                inference_frame = cv2.resize(frame, (inference_w, inference_h), interpolation=cv2.INTER_LINEAR)
            else:
                inference_frame = frame.copy()
            
            # 추론 큐에 프레임 추가 (오래된 프레임 제거 후 최신 것만 추가)
            try:
                # 큐에 있는 오래된 프레임 전부 제거 (실시간성 보장)
                while not self.inference_queue.empty():
                    try:
                        self.inference_queue.get_nowait()
                    except queue.Empty:
                        break
                
                # 최신 프레임만 추가
                self.inference_queue.put_nowait((inference_frame, original_w, original_h))
            except queue.Full:
                pass  # 추론이 바쁘면 프레임 드롭
            
            # 최신 추론 결과 가져오기
            try:
                result_data = self.result_queue.get_nowait()
                if result_data:
                    results, inference_timestamp = result_data
                    self.last_pose_result = results
            except queue.Empty:
                pass  # 아직 결과 없음, 이전 것 사용
        
        # === 동기 추론 처리 (비동기 비활성화 시) ===
        else:
            should_infer = False
            
            if self.use_time_based_inference:
                if current_time - self.last_inference_time >= self.inference_interval:
                    should_infer = True
                    self.last_inference_time = current_time
            else:
                self.frame_count += 1
                if self.frame_count % int(self.inference_interval) == 0:
                    should_infer = True
            
            if should_infer:
                # 추론용 저해상도 프레임 생성
                if self.use_inference_downscale and self.inference_scale < 1.0:
                    inference_w = int(original_w * self.inference_scale)
                    inference_h = int(original_h * self.inference_scale)
                    inference_frame = cv2.resize(frame, (inference_w, inference_h), interpolation=cv2.INTER_LINEAR)
                else:
                    inference_frame = frame
                
                # RTMPose 추론
                results = inference_topdown(self.model, inference_frame)
                
                if results and len(results) > 0:
                    # 키포인트를 원본 해상도로 스케일 업
                    if self.use_inference_downscale and self.inference_scale < 1.0:
                        scale_x = original_w / inference_w
                        scale_y = original_h / inference_h
                        
                        for result in results:
                            pred_instances = result.pred_instances
                            pred_instances.keypoints[:, :, 0] *= scale_x
                            pred_instances.keypoints[:, :, 1] *= scale_y
                    
                    self.last_pose_result = results
                else:
                    if self.last_pose_result is None:
                        return frame
        
        # === 추론 결과 사용 ===
        if self.last_pose_result is None:
            return frame
        
        results = self.last_pose_result
        
        if not results or len(results) == 0:
            print("[DEBUG] 포즈 감지 실패: 결과 없음")
            return frame
        
        # === 렌더링 처리 ===
        # 첫 번째 사람의 키포인트 추출
        pred_instances = results[0].pred_instances
        keypoints = pred_instances.keypoints[0]  # shape: (17, 2)
        scores = pred_instances.keypoint_scores[0]  # shape: (17,)
        
        # 신뢰도가 낮은 키포인트는 건너뛰기
        if scores[5] < 0.3 or scores[6] < 0.3:  # 어깨 신뢰도
            print(f"[DEBUG] 어깨 신뢰도 부족: left={scores[5]:.2f}, right={scores[6]:.2f}")
            return frame
        
        # 옷 이미지 확인
        if self.cloth_original is None:
            print("[DEBUG] 옷 이미지가 로드되지 않음")
            return frame
        
        # 키포인트에 score 추가
        keypoints_with_score = np.concatenate([keypoints, scores[:, np.newaxis]], axis=1)
        
        # 신체 치수 계산
        metrics = self.calculate_body_metrics(keypoints_with_score, frame.shape)
        
        # 얼굴/목 영역 마스크 생성 (피부색 기반)
        face_neck_mask = self.create_face_neck_mask(keypoints, scores, frame.shape, frame)
        
        # 옷 처리
        if use_warp and self.cloth_keypoints is not None:
            # 어깨 매칭 + 관절 변형
            
            # 1단계: 어깨 매칭 기반 자동 리사이즈
            resized_cloth = self.resize_cloth_by_shoulder_matching(metrics['shoulder_width'])
            
            if resized_cloth is None:
                resized_cloth = self.cloth_original.copy()
            
            # 2단계: 옷을 신체 포즈에 맞춰 변형
            h_resized, w_resized = resized_cloth.shape[:2]
            h_original, w_original = self.cloth_original.shape[:2]
            scale_ratio = w_resized / w_original
            
            # 옷 키포인트 스케일 조정
            scaled_cloth_keypoints = {}
            exclude_keys = {'shoulder_width', 'bounding_box', 'cloth_center'}
            
            for key, value in self.cloth_keypoints.items():
                if key in exclude_keys:
                    continue
                if isinstance(value, (tuple, list)) and len(value) == 2:
                    try:
                        x, y = float(value[0]), float(value[1])
                        scaled_cloth_keypoints[key] = (x * scale_ratio, y * scale_ratio)
                    except (TypeError, ValueError) as e:
                        print(f"[RTMPose] 키포인트 '{key}' 스케일 조정 실패: {e}")
                        continue
            
            # 어파인 변형 + 세그멘테이션 기반 정제
            warped_cloth = warp_cloth_to_pose(
                resized_cloth,
                scaled_cloth_keypoints,
                metrics['keypoints'],
                frame.shape,
                use_segmentation=True,  # 세그멘테이션 활성화
                frame=frame  # 원본 프레임 전달
            )
            
            # 3단계: 얼굴/목 영역 정제 (옷이 얼굴을 가리지 않도록)
            warped_cloth = self.refine_cloth_with_face_mask(warped_cloth, face_neck_mask)
            
            # 알파 블렌딩
            result = overlay_cloth_on_body(
                frame,
                warped_cloth,
                position=None,
                alpha=1.0
            )
        else:
            # 어깨 매칭 리사이즈만 사용
            
            resized_cloth = self.resize_cloth_by_shoulder_matching(metrics['shoulder_width'])
            
            if resized_cloth is None:
                resized_cloth = resize_cloth_to_body(
                    self.cloth_original,
                    metrics['shoulder_width'] * 1.2,
                    metrics['body_height'] * 1.5
                )
            
            # 얼굴/목 영역 정제 (옷이 얼굴을 가리지 않도록)
            resized_cloth = self.refine_cloth_with_face_mask(resized_cloth, face_neck_mask)
            
            # 옷 오버레이 위치
            cloth_position = (
                metrics['shoulder_center'][0],
                metrics['shoulder_center'][1] - 20
            )
            
            result = overlay_cloth_on_body(
                frame,
                resized_cloth,
                cloth_position,
                alpha=1.0
            )
        
        # 스켈레톤 그리기 제거 (깔끔한 출력)
        # show_skeleton 매개변수는 하위 호환성을 위해 유지하지만 사용하지 않음
        
        return result
    
    def run_webcam(self, camera_index=0):
        """
        웹캠을 사용한 실시간 가상 피팅
        
        Args:
            camera_index: 카메라 인덱스
        """
        cap = cv2.VideoCapture(camera_index)
        
        if not cap.isOpened():
            print("[RTMPose] 카메라를 열 수 없습니다")
            return
        
        print("[RTMPose] 실시간 가상 피팅 시작")
        print("'w' - 변형 모드 토글, 'q' - 종료")
        
        show_skeleton = False  # 스켈레톤 항상 비활성화
        use_warp = True
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # 좌우 반전 (거울 효과)
            frame = cv2.flip(frame, 1)
            
            # 가상 피팅 처리 (스켈레톤 항상 비활성화)
            result = self.process_frame(frame, show_skeleton=False, use_warp=use_warp)
            
            # 모드 표시 (스켈레톤 정보 제거)
            mode_text = f"Virtual Fitting | Mode: {'Warp' if use_warp else 'Resize'}"
            cv2.putText(result, mode_text, (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # 화면에 표시
            cv2.imshow('RTMPose Virtual Fitting', result)
            
            # 키 입력 처리 (스켈레톤 토글 제거)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('w'):
                use_warp = not use_warp
                print(f"[RTMPose] 변형 모드: {'관절 매칭' if use_warp else '단순 크기 조정'}")
        
        cap.release()
        cv2.destroyAllWindows()
        self.stop_inference_thread()  # 스레드 종료
        print("[RTMPose] 종료")

def main():
    """메인 실행 함수"""
    import torch
    device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
    
    vf = RTMPoseVirtualFitting(
        cloth_image_path='input/cloth.jpg',
        device=device
    )
    vf.run_webcam()

if __name__ == "__main__":
    main()
