from flask import Flask
from flask_cors import CORS
from config import Config
from db_ import db, init_db
from routes.users import users_bp
from routes.member_test import members_bp

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    app.register_blueprint(members_bp)

    # 308에러 발생 방지
    CORS(app,resources={r"/api/*": {"origins": ["https://localhost:3000", "https://127.0.0.1:3000"]}})
    app.url_map.strict_slashes = False

    os.makedirs(app.instance_path, exist_ok=True)

    @app.route("/")
    def index():
        return {"status": "Flask API running"}

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
