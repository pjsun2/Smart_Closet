from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event

db = SQLAlchemy()

def init_db(app):
    db.init_app(app)
    
    uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")

        # 이벤트 리스너는 반드시 app.app_context() 안에서 등록!
    if uri.startswith("sqlite"):
        def _set_sqlite_pragmas(dbapi_conn, _):
            try:
                cur = dbapi_conn.cursor()
                cur.execute("PRAGMA journal_mode=WAL;")
                cur.execute("PRAGMA synchronous=NORMAL;")
                cur.execute("PRAGMA foreign_keys=ON;")
                cur.close()
            except Exception:
                pass

        # app 컨텍스트 안에서 db.engine 사용
        with app.app_context():
            event.listen(db.engine, "connect", _set_sqlite_pragmas)
