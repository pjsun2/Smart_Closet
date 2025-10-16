# import os

# BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# class Config:
#     # SQLite 파일: ./instance/app.db (Flask 관례 폴더)
#     SQLALCHEMY_DATABASE_URI = os.getenv(
#         "DATABASE_URL",
#         f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'app.db')}"
#     )
#     SQLALCHEMY_TRACK_MODIFICATIONS = False

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_DIR = BASE_DIR / "instance" # Flask 관례 폴더
DB_DIR.mkdir(parents=True, exist_ok=True)  # 폴더 없으면 생성

DB_PATH = (DB_DIR / "app.db").as_posix()   # 윈도우에서도 안전한 경로 문자열

class Config:
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DB_PATH}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False