from flask import Flask
from flask_cors import CORS
from config import Config
from db_ import db, init_db
from routes.users import users_bp
from routes.member_test import members_bp
from routes.clothes import clothes_bp, initialize_models
import os

# CUDA 비활성화 (CPU만 사용)
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    
    # 308에러 발생 방지
    CORS(app,resources={r"/api/*": {"origins": ["https://localhost:3000", "https://127.0.0.1:3000"]}})
    app.url_map.strict_slashes = False
    
    # 사용
    app.register_blueprint(members_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(clothes_bp)

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

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        use_reloader=False,
        ssl_context='adhoc'  # ← HTTPS 지원
    )