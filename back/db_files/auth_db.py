import sqlite3
import os
from datetime import datetime
from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), 'smart_closet.db')

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")    

@auth_bp.route("/signup", methods=["POST"])
def signup():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    data = request.get_json(silent=True) or {}
    user_id = (data.get("userId") or "").strip()
    password = data.get("password") or ""
    name = (data.get("name") or "").strip()
    gender = data.get("gender") or ""
    
    print(data)
    
    try:
        cursor.execute("SELECT 1 FROM User WHERE User_email = ? ", (user_id,))
        if cursor.fetchone():
            return jsonify(ok=False, message="이미 존재하는 아이디입니다."), 409
        
        pw_hash = generate_password_hash(password)
        conn.execute(
            "INSERT INTO User (User_email, User_password, User_nickname, User_createDate, User_updateDate, User_gender) VALUES (?, ?, ?, DATE('now'), DATE('now'), ?)",
            (user_id, pw_hash, name, gender,)
        )
        
        conn.commit()
        return jsonify(ok=True)
    
    except sqlite3.IntegrityError:
        # UNIQUE 위반 등
        return jsonify(ok=False, message="이미 존재하는 아이디입니다."), 409
    except Exception as e:
        # 개발 중에는 원인 확인을 위해 로그 남기기
        print("[signup][ERROR]", repr(e))
        return jsonify(ok=False, message="서버 오류가 발생했습니다."), 500
    finally:
        try:
            conn.close()
        except:
            pass
        
@auth_bp.route("/login", methods=["POST"])
def login():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    conn.row_factory = sqlite3.Row
    
    data = request.get_json(silent=True) or {}
    user_id = (data.get("userId") or "").strip()
    password = data.get("password") or ""
    
    cursor.execute("SELECT User_password, User_nickname, User_gender FROM User WHERE User_email = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return jsonify(ok=False, message="아이디 또는 비밀번호가 올바르지 않습니다."), 401

    # row_factory 설정했다면 키로 접근 가능
    stored_hash = row[0]
    nickname = row[1]
    gender = row[2]

    if check_password_hash(stored_hash, password):
        # 세션 저장 (쿠키로 클라이언트에 서명되어 전달됨)
        session["user"] = {"id": user_id, "name": nickname, "gender": gender}
        return jsonify(ok=True, user=session["user"])
    else:
        return jsonify(ok=False, message="아이디 또는 비밀번호가 올바르지 않습니다."), 401

@auth_bp.route("/me", methods=["GET"])
def me():
    user = session.get("user")
    if not user:
        return jsonify(ok=False, authenticated=False)
    return jsonify(ok=True, authenticated=True, user=user)

@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.pop("user", None)
    return jsonify(ok=True)