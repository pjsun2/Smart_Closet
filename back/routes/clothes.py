from flask import Blueprint, request, jsonify
import base64
import os
from datetime import datetime
import sys
import importlib.util

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