import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    # SQLite 파일: ./instance/app.db (Flask 관례 폴더)
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'app.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False