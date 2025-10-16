from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event

db = SQLAlchemy()

def init_db(app):
    db.init_app(app)

    # SQLite 성능/안정성 설정 (선택)
    uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    if uri.startswith("sqlite"):
        @event.listens_for(db.engine, "connect")
        def set_sqlite_pragma(dbapi_conn, _):
            try:
                cur = dbapi_conn.cursor()
                cur.execute("PRAGMA journal_mode=WAL;")
                cur.execute("PRAGMA synchronous=NORMAL;")
                cur.execute("PRAGMA foreign_keys=ON;")
                cur.close()
            except Exception:
                pass
