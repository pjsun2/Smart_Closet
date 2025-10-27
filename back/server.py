from flask import Flask
from flask_cors import CORS
from config import Config
from db_ import db, init_db
from routes.users import users_bp
#from routes.member_test import members_bp
from routes.clothing import clothing_bp
from chat.langspeech_openai_chroma import chat_bp
from db_files.auth_db import auth_bp
from routes.clothes import clothes_bp, initialize_models
import os

# GPU 활성화 - CUDA 사용
# os.environ['CUDA_VISIBLE_DEVICES'] = '-1'  # CPU 모드 (비활성화)
os.environ['CUDA_VISIBLE_DEVICES'] = '0'  # GPU 0번 사용
os.environ['TF_FORCE_GPU_ALLOW_GROWTH'] = 'true'  # GPU 메모리 동적 할당

# OpenCV CUDA 활성화 (pip 버전은 CUDA 미지원이지만 설정)
os.environ['OPENCV_ENABLE_CUDA'] = '1'

# MediaPipe GPU 설정
os.environ['MEDIAPIPE_DISABLE_GPU'] = '0'  # GPU 활성화

# ONNX Runtime GPU 설정 (rembg 배경 제거에 사용)
os.environ['ORT_CUDA_UNAVAILABLE'] = '0'  # CUDA 사용 가능 표시

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev_secret_key_123")
    
    # 308에러 발생 방지
    CORS(app,resources={r"/api/*": {"origins": ["https://localhost:3000", "https://127.0.0.1:3000"]}})
    app.url_map.strict_slashes = False
    
    # Blueprint 등록
    app.register_blueprint(users_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(clothes_bp)
    app.register_blueprint(clothing_bp)

    app.register_blueprint(auth_bp)
    
    app.config.from_object(Config)
    os.makedirs(app.instance_path, exist_ok=True)
    
    # DB 초기화 & 테이블 생성(마이그레이션 없이)
    init_db(app)
    with app.app_context():
        db.create_all()

    @app.route("/")
    def index():
        return {"status": "Flask API running"}

    return app

if __name__ == "__main__":
    app = create_app()

    # 모델 초기화
    print("\n[server.py] AI 모델 초기화 중...")
    try:
        initialize_models()
        print("[server.py] AI 모델 초기화 완료\n")
    except Exception as e:
        print("[server.py] 모델 초기화 오류: " + str(e) + "\n")

    # 가상 피팅 초기화는 건너뛰기 (mmengine 이슈)
    print("[server.py] 가상 피팅 초기화 건너뛰기 (별도 초기화 필요)\n")

    # HTTPS 시도, 실패 시 HTTP로 폴백
    try:
        print("[server.py] HTTPS 모드로 서버 시작 시도...")
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,
            use_reloader=False,
            ssl_context='adhoc'  # ← HTTPS 지원
        )
    except Exception as e:
        print(f"[server.py] HTTPS 시작 실패: {e}")
        print("[server.py] HTTP 모드로 서버 재시작...")
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,
            use_reloader=False
        )