from flask import Blueprint, request, jsonify, Response
import base64
import os
from datetime import datetime
import sys
import subprocess
import importlib.util
import cv2
import numpy as np

clothes_bp = Blueprint('clothes', __name__, url_prefix='/api')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads', 'clothes')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

MODELS = None
final_pipeline = None

def initialize_models():
    """서버 시작 시 모델 로드"""
    global MODELS, final_pipeline
    
    print("\n" + "="*70)
    print("[clothes.py] 모델 초기화 시작")
    print("="*70)
    
    try:
        # 절대 경로로 final_pipeline.py 찾기
        current_file = os.path.abspath(__file__)
        clothes_dir = os.path.dirname(os.path.dirname(current_file))
        final_pipeline_path = os.path.join(clothes_dir, 'clothes', 'final_pipeline.py')
        
        print("[clothes.py] 현재 파일: " + current_file)
        print("[clothes.py] final_pipeline 경로: " + final_pipeline_path)
        
        if not os.path.exists(final_pipeline_path):
            print("[clothes.py] [ERROR] 파일을 찾을 수 없음")
            return False
        
        print("[clothes.py] [OK] 파일 발견")
        
        # importlib를 사용한 동적 임포트
        spec = importlib.util.spec_from_file_location("final_pipeline", final_pipeline_path)
        final_pipeline = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(final_pipeline)
        
        print("[clothes.py] [OK] 모듈 임포트 성공")
        
        print("[clothes.py] 모델 로드 중... (1-2분 소요)")
        MODELS = final_pipeline.load_all_models()
        
        if MODELS is not None:
            print("[clothes.py] [SUCCESS] 모델 로드 성공")
            print("="*70 + "\n")
            return True
        else:
            print("[clothes.py] [ERROR] 모델 로드 실패")
            print("="*70 + "\n")
            return False
            
    except Exception as e:
        print("[clothes.py] [ERROR] 예외: " + str(e))
        import traceback
        traceback.print_exc()
        print("="*70 + "\n")
        return False

# @clothes_bp.route('/clothes', methods=['POST', 'OPTIONS'])
# def save_clothes():
#     """이미지 저장 및 AI 분석"""
    
#     if request.method == 'OPTIONS':
#         return '', 200
    
#     print("\n[clothes.py] POST /api/clothes 요청")
    
#     try:
#         data = request.get_json()
#         image_data = data.get('image') if data else None
        
#         if not image_data:
#             print("[clothes.py] [ERROR] 이미지 데이터 없음")
#             return jsonify({"error": "이미지 없음"}), 400
        
#         print("[clothes.py] 이미지 크기: " + str(len(image_data)) + " bytes")
        
#         # Base64 디코딩
#         if ',' in image_data:
#             header, encoded = image_data.split(',', 1)
#         else:
#             encoded = image_data
        
#         try:
#             image_bytes = base64.b64decode(encoded)
#             print("[clothes.py] 디코딩 완료: " + str(len(image_bytes)) + " bytes")
#         except Exception as e:
#             print("[clothes.py] [ERROR] 디코딩 실패: " + str(e))
#             return jsonify({"error": "Base64 디코딩 실패"}), 400
        
#         # 파일 저장
#         filename = "cloth_" + datetime.now().strftime('%Y%m%d_%H%M%S') + ".jpg"
#         filepath = os.path.join(UPLOAD_FOLDER, filename)
        
#         with open(filepath, 'wb') as f:
#             f.write(image_bytes)
        
#         print("[clothes.py] 파일 저장 완료: " + filename)
        
#         # AI 분석 실행
#         print("[clothes.py] AI 분석 시작...")
#         analysis_result = None
        
#         if MODELS is not None:
#             try:
#                 analysis_result = final_pipeline.run_full_pipeline(MODELS, filepath)
#                 print("[clothes.py] AI 분석 완료")
#             except Exception as e:
#                 print("[clothes.py] [ERROR] AI 분석 실패: " + str(e))
#                 import traceback
#                 traceback.print_exc()
#                 analysis_result = {"error": str(e), "status": "failed"}
#         else:
#             print("[clothes.py] [WARNING] 모델 미로드")
#             analysis_result = {"error": "모델 미로드", "status": "model_not_loaded"}
        
#         # 응답
#         response = {
#             "success": True,
#             "filename": filename,
#             "path": filepath,
#             "size": len(image_bytes),
#             "detected": analysis_result.get('items', []),  # items를 detected로 변환
#             "status": analysis_result.get('status', 'success')
#         }
        
#         print("[clothes.py] 응답 전송\n")
        
#         return jsonify(response), 200
        
#     except Exception as e:
#         print("[clothes.py] [ERROR] 예외: " + str(e))
#         import traceback
#         traceback.print_exc()
#         return jsonify({"error": str(e)}), 500

@clothes_bp.route('/clothes', methods=['POST', 'OPTIONS'])
def save_clothes():
    """이미지 저장 및 AI 분석"""
    
    if request.method == 'OPTIONS':
        return '', 200
    
    print("\n[clothes.py] POST /api/clothes 요청")
    
    try:
        # FormData (파일) 수신
        if 'file' not in request.files:
            print("[clothes.py] [ERROR] 파일 없음")
            return jsonify({"error": "파일 없음"}), 400
        
        file = request.files['file']
        if file.filename == '':
            print("[clothes.py] [ERROR] 파일명 없음")
            return jsonify({"error": "파일명 없음"}), 400
        
        print("[clothes.py] 파일명: " + file.filename)
        file_content = file.read()
        print("[clothes.py] 파일 크기: " + str(len(file_content)) + " bytes")
        file.seek(0)  # ← 파일 포인터 초기화
        
        # 파일 저장
        filename = "cloth_" + datetime.now().strftime('%Y%m%d_%H%M%S') + ".jpg"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        print("[clothes.py] 파일 저장 완료: " + filename)
        
        # AI 분석 실행
        print("[clothes.py] AI 분석 시작...")
        
        if MODELS is None:
            print("[clothes.py] [WARNING] 모델 미로드")
            return jsonify({
                "success": False,
                "error": "모델 미로드",
                "status": "model_not_loaded"
            }), 500
        
        try:
            analysis_result = final_pipeline.run_full_pipeline(MODELS, filepath)
            print("[clothes.py] AI 분석 완료")
            print("[clothes.py] 분석 결과: " + str(analysis_result))
            print("[clothes.py] 분석 결과 타입: " + str(type(analysis_result)))
            
            # 분석 결과 확인
            if analysis_result is None:
                print("[clothes.py] [ERROR] 분석 결과가 None입니다")
                return jsonify({
                    "success": False,
                    "error": "분석 결과 없음",
                    "status": "no_result"
                }), 400
            
            # items 키 확인
            items = analysis_result.get('items', [])
            print("[clothes.py] items 개수: " + str(len(items)))
            
            if not items or len(items) == 0:
                print("[clothes.py] [WARNING] 옷을 감지하지 못했습니다")
                return jsonify({
                    "success": False,
                    "error": "옷을 감지하지 못했습니다",
                    "status": "no_detection",
                    "message": "더 명확한 옷 사진을 찍어주세요"
                }), 400
            
            # 정상 응답
            response = {
                "success": True,
                "filename": filename,
                "path": filepath,
                "detected": items,
                "status": analysis_result.get('status', 'success'),
                "analysis": analysis_result
            }
            
            print("[clothes.py] 응답 전송\n")
            return jsonify(response), 200
                    
        except Exception as e:
            print("[clothes.py] [ERROR] AI 분석 실패: " + str(e))
            import traceback
            traceback.print_exc()
            return jsonify({
                "success": False,
                "error": "AI 분석 실패: " + str(e),
                "status": "analysis_failed"
            }), 500
        
    except Exception as e:
        print("[clothes.py] [ERROR] 예외: " + str(e))
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e),
            "status": "server_error"
        }), 500

@clothes_bp.route('/analysis-status/<filename>', methods=['GET'])
def get_analysis_status(filename):
    """분석 상태 확인 API"""
    try:
        # 업로드된 파일 경로
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        if not os.path.exists(filepath):
            return jsonify({
                "completed": False,
                "detected": None,
                "error": "파일을 찾을 수 없습니다"
            }), 404
        
        # DB 구현 전 (임시로 파일 분석 상태 확인)
        # 나중에 DB에서 분석 완료 여부 확인하도록 수정
        
        return jsonify({
            "completed": True,
            "detected": None,  # 나중에 DB에서 가져오기
            "message": "분석 진행 중..."
        }), 200
        
    except Exception as e:
        print(f"[clothes.py] [ERROR] {str(e)}")
        return jsonify({"error": str(e)}), 500

@clothes_bp.route('/fit', methods=['POST', 'OPTIONS'])
def try_on_clothes():
    """입어보기 - 이미지를 받아서 main.py 실행 (백그라운드)"""
    
    if request.method == 'OPTIONS':
        return '', 200
    
    print("\n[clothes.py] POST /api/fit 요청")
    
    try:
        data = request.get_json()
        image_data = data.get('image') if data else None
        
        if not image_data:
            print("[clothes.py] [ERROR] 이미지 데이터 없음")
            return jsonify({"error": "이미지 없음"}), 400
        
        print("[clothes.py] 이미지 크기: " + str(len(image_data)) + " bytes")
        
        # Base64 디코딩
        if ',' in image_data:
            header, encoded = image_data.split(',', 1)
        else:
            encoded = image_data
        
        try:
            image_bytes = base64.b64decode(encoded)
            print("[clothes.py] 디코딩 완료: " + str(len(image_bytes)) + " bytes")
        except Exception as e:
            print("[clothes.py] [ERROR] 디코딩 실패: " + str(e))
            return jsonify({"error": "Base64 디코딩 실패"}), 400
        
        # fit/input 폴더에 model.jpg로 저장
        fit_dir = os.path.join(BASE_DIR, 'fit')
        input_dir = os.path.join(fit_dir, 'input')
        os.makedirs(input_dir, exist_ok=True)
        
        # 타임스탬프를 포함한 파일명 생성
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        model_filename = f'model_{timestamp}.jpg'
        model_path = os.path.join(input_dir, model_filename)
        
        with open(model_path, 'wb') as f:
            f.write(image_bytes)
        
        # model.jpg에도 복사 (main.py가 이 이름을 사용하므로)
        default_model_path = os.path.join(input_dir, 'model.jpg')
        with open(default_model_path, 'wb') as f:
            f.write(image_bytes)
        
        print("[clothes.py] 파일 저장 완료: " + model_path)
        
        # main.py 백그라운드 실행 (Popen 사용)
        print("[clothes.py] main.py 백그라운드 실행 시작...")
        main_py_path = os.path.join(fit_dir, 'main.py')
        
        try:
            # 백그라운드로 실행 (기다리지 않음)
            process = subprocess.Popen(
                [sys.executable, main_py_path],
                cwd=fit_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            print(f"[clothes.py] main.py 백그라운드 실행 시작 (PID: {process.pid})")
            
            response = {
                "success": True,
                "message": "입어보기 처리를 시작했습니다. 처리 중입니다...",
                "model_path": model_path,
                "filename": model_filename,
                "status": "processing",
                "pid": process.pid
            }
            
            return jsonify(response), 200
            
        except Exception as e:
            print("[clothes.py] [ERROR] main.py 실행 실패: " + str(e))
            return jsonify({"error": str(e)}), 500
        
    except Exception as e:
        print("[clothes.py] [ERROR] 예외: " + str(e))
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ========== 실시간 가상 피팅 API ==========

# 전역 VirtualFitting 인스턴스
virtual_fitting_instance = None

def initialize_virtual_fitting():
    """
    서버 시작 시 VirtualFitting 백그라운드 초기화
    - 인스턴스 생성 및 백그라운드 워커 시작
    - 스트리밍은 비활성화 상태 (start_streaming() 호출 시 활성화)
    """
    global virtual_fitting_instance
    
    if virtual_fitting_instance is not None:
        print("[clothes.py] VirtualFitting 이미 초기화됨")
        return
    
    fit_dir = os.path.join(BASE_DIR, 'fit')
    
    # fit 디렉토리를 sys.path에 추가 (중복 체크)
    if fit_dir not in sys.path:
        sys.path.insert(0, fit_dir)
    
    try:
        print(f"[clothes.py] VirtualFitting 백그라운드 초기화 시작...")
        print(f"[clothes.py] fit_dir: {fit_dir}")
        
        from virtual_fitting import RTMPoseVirtualFitting
        
        # device 설정
        import torch
        device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
        print(f"[clothes.py] Device: {device}")
        
        # 옷 이미지 경로 (절대 경로)
        cloth_image_path = os.path.join(fit_dir, 'input', 'cloth.jpg')
        
        # 이미지 파일 존재 확인
        if not os.path.exists(cloth_image_path):
            print(f"[clothes.py] 경고: 옷 이미지 없음 - {cloth_image_path}")
            print(f"[clothes.py] 기본 이미지로 계속 진행...")
        
        virtual_fitting_instance = RTMPoseVirtualFitting(
            cloth_image_path=cloth_image_path,
            device=device
        )
        print("[clothes.py] RTMPoseVirtualFitting 인스턴스 생성 완료")
        print("[clothes.py] 백그라운드 워커 실행 중 (스트리밍 대기)")
        
    except Exception as e:
        print(f"[clothes.py] RTMPoseVirtualFitting 생성 실패: {e}")
        import traceback
        traceback.print_exc()

def get_virtual_fitting():
    """VirtualFitting 싱글톤 인스턴스 반환"""
    global virtual_fitting_instance
    
    if virtual_fitting_instance is None:
        fit_dir = os.path.join(BASE_DIR, 'fit')
        
        # fit 디렉토리를 sys.path에 추가 (중복 체크)
        if fit_dir not in sys.path:
            sys.path.insert(0, fit_dir)
        
        try:
            print(f"[clothes.py] VirtualFitting 초기화 시작...")
            print(f"[clothes.py] fit_dir: {fit_dir}")
            
            from virtual_fitting import RTMPoseVirtualFitting
            
            # device 설정
            import torch
            device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
            print(f"[clothes.py] Device: {device}")
            
            # 옷 이미지 경로 (절대 경로)
            cloth_image_path = os.path.join(fit_dir, 'input', 'cloth.jpg')
            
            # 이미지 파일 존재 확인
            if not os.path.exists(cloth_image_path):
                print(f"[clothes.py] 경고: 옷 이미지 없음 - {cloth_image_path}")
                print(f"[clothes.py] 기본 이미지로 계속 진행...")
            
            virtual_fitting_instance = RTMPoseVirtualFitting(
                cloth_image_path=cloth_image_path,
                device=device
            )
            print("[clothes.py] RTMPoseVirtualFitting 인스턴스 생성 완료")
            
        except Exception as e:
            print(f"[clothes.py] RTMPoseVirtualFitting 생성 실패: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    return virtual_fitting_instance

# 로딩 상태를 저장하는 전역 변수
fitting_loading_status = {
    "stage": "idle",  # idle, initializing, loading_pose, loading_cloth, ready
    "progress": 0,
    "message": ""
}

@clothes_bp.route('/fit/status', methods=['GET', 'OPTIONS'])
def get_fitting_status():
    """가상 피팅 로딩 상태 반환"""
    if request.method == 'OPTIONS':
        return '', 200
    
    global fitting_loading_status, virtual_fitting_instance
    
    # 인스턴스가 이미 있으면 ready 상태
    if virtual_fitting_instance is not None:
        return jsonify({
            "stage": "ready",
            "progress": 100,
            "message": "가상 피팅 준비 완료"
        }), 200
    
    return jsonify(fitting_loading_status), 200

@clothes_bp.route('/fit/initialize', methods=['POST', 'OPTIONS'])
def initialize_fitting():
    """가상 피팅 초기화 (로딩 프로세스 시작)"""
    if request.method == 'OPTIONS':
        return '', 200
    
    global fitting_loading_status, virtual_fitting_instance
    
    try:
        # 이미 초기화되어 있으면 바로 성공 반환
        if virtual_fitting_instance is not None:
            return jsonify({
                "success": True,
                "stage": "ready",
                "progress": 100,
                "message": "이미 초기화되어 있습니다"
            }), 200
        
        # 초기화 시작
        fitting_loading_status = {
            "stage": "initializing",
            "progress": 10,
            "message": "GPU 환경 확인 중..."
        }
        
        fit_dir = os.path.join(BASE_DIR, 'fit')
        if fit_dir not in sys.path:
            sys.path.insert(0, fit_dir)
        
        print("[clothes.py] VirtualFitting 초기화 시작...")
        
        # stage: loading_pose
        fitting_loading_status = {
            "stage": "loading_pose",
            "progress": 30,
            "message": "RTMPose 모델 로딩 중..."
        }
        
        from virtual_fitting import RTMPoseVirtualFitting
        import torch
        device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
        
        # stage: loading_cloth
        fitting_loading_status = {
            "stage": "loading_cloth",
            "progress": 60,
            "message": "옷 이미지 처리 중..."
        }
        
        cloth_image_path = os.path.join(fit_dir, 'input', 'cloth.jpg')
        
        if not os.path.exists(cloth_image_path):
            print(f"[clothes.py] 경고: 옷 이미지 없음 - {cloth_image_path}")
        
        virtual_fitting_instance = RTMPoseVirtualFitting(
            cloth_image_path=cloth_image_path,
            device=device
        )
        
        # stage: ready
        fitting_loading_status = {
            "stage": "ready",
            "progress": 100,
            "message": "가상 피팅 준비 완료!"
        }
        
        print("[clothes.py] RTMPoseVirtualFitting 인스턴스 생성 완료")
        
        return jsonify({
            "success": True,
            "stage": "ready",
            "progress": 100,
            "message": "가상 피팅 준비 완료!"
        }), 200
        
    except Exception as e:
        print(f"[clothes.py] 초기화 실패: {e}")
        import traceback
        traceback.print_exc()
        
        fitting_loading_status = {
            "stage": "error",
            "progress": 0,
            "message": f"초기화 실패: {str(e)}"
        }
        
        return jsonify({
            "success": False,
            "error": str(e),
            "stage": "error"
        }), 500

@clothes_bp.route('/fit/stream', methods=['POST', 'OPTIONS'])
def process_fit_frame():
    """
    실시간 가상 피팅 - 프레임 처리
    - 스트림 시작: 첫 프레임 수신 시 start_streaming() 호출
    - 스트림 중지: 프론트에서 stop_streaming API 호출
    """
    
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        frame_data = data.get('frame') if data else None
        show_skeleton = data.get('showSkeleton', True)
        use_warp = data.get('useWarp', True)  # 관절 매칭 변형 사용 여부
        is_first_frame = data.get('isFirstFrame', False)  # 첫 프레임 플래그
        
        if not frame_data:
            return jsonify({"error": "프레임 데이터 없음"}), 400
        
        # Base64 디코딩
        if ',' in frame_data:
            header, encoded = frame_data.split(',', 1)
        else:
            encoded = frame_data
        
        # 이미지 디코딩
        img_bytes = base64.b64decode(encoded)
        nparr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return jsonify({"error": "프레임 디코딩 실패"}), 400
        
        # VirtualFitting 인스턴스 가져오기
        vf = get_virtual_fitting()
        if vf is None:
            return jsonify({
                "error": "VirtualFitting 초기화 실패",
                "message": "모델 로딩에 실패했습니다. 서버 로그를 확인하세요."
            }), 500
        
        # 첫 프레임이면 스트리밍 활성화
        if is_first_frame:
            vf.start_streaming()
            print("[clothes.py] 스트리밍 시작 - 출력 활성화")
        
        # 프레임 처리 (관절 매칭 옵션 포함)
        try:
            processed_frame = vf.process_frame(frame, show_skeleton=show_skeleton, use_warp=use_warp)
        except Exception as process_error:
            print(f"[clothes.py] process_frame 에러: {process_error}")
            import traceback
            traceback.print_exc()
            return jsonify({
                "error": "프레임 처리 실패",
                "message": str(process_error)
            }), 500
        
        # 원본 해상도 그대로 출력 (추론은 저해상도, 렌더링은 원본 해상도)
        # 업스케일 제거: 프론트에서 HD(1280x720) 전송 → 백엔드 HD 처리 → HD 출력
        
        # 결과를 Base64로 인코딩 (고화질 85%)
        _, buffer = cv2.imencode('.jpg', processed_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        frame_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return jsonify({
            "success": True,
            "frame": f"data:image/jpeg;base64,{frame_base64}"
        }), 200
        
    except Exception as e:
        print(f"[clothes.py] 프레임 처리 에러: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@clothes_bp.route('/fit/stop-streaming', methods=['POST', 'OPTIONS'])
def stop_fit_streaming():
    """
    가상 피팅 스트리밍 중지
    - 백그라운드 워커는 계속 실행 (다음 스트림 대기)
    - 출력만 비활성화
    """
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        vf = get_virtual_fitting()
        if vf is None:
            return jsonify({
                "error": "VirtualFitting 초기화 실패"
            }), 500
        
        vf.stop_streaming()
        print("[clothes.py] 스트리밍 중지 - 백그라운드는 계속 실행")
        
        return jsonify({
            "success": True,
            "message": "스트리밍 중지됨"
        }), 200
        
    except Exception as e:
        print(f"[clothes.py] 스트리밍 중지 에러: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@clothes_bp.route('/fit/upload-cloth', methods=['POST', 'OPTIONS'])
def upload_cloth_image():
    """옷 이미지 업로드 및 배경 제거"""
    
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        image_data = data.get('image') if data else None
        
        if not image_data:
            return jsonify({"error": "이미지 없음"}), 400
        
        # Base64 디코딩
        if ',' in image_data:
            header, encoded = image_data.split(',', 1)
        else:
            encoded = image_data
        
        image_bytes = base64.b64decode(encoded)
        
        # fit/input 폴더에 저장
        fit_dir = os.path.join(BASE_DIR, 'fit')
        input_dir = os.path.join(fit_dir, 'input')
        os.makedirs(input_dir, exist_ok=True)
        
        cloth_path = os.path.join(input_dir, 'cloth.jpg')
        
        with open(cloth_path, 'wb') as f:
            f.write(image_bytes)
        
        print(f"[clothes.py] 옷 이미지 저장 완료: {cloth_path}")
        
        # VirtualFitting 인스턴스 리로드
        global virtual_fitting_instance
        virtual_fitting_instance = None
        vf = get_virtual_fitting()
        
        if vf is None:
            return jsonify({"error": "옷 이미지 처리 실패"}), 500
        
        return jsonify({
            "success": True,
            "message": "옷 이미지 업로드 완료",
            "path": cloth_path
        }), 200
        
    except Exception as e:
        print(f"[clothes.py] 옷 업로드 에러: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500