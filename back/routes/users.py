from flask import Blueprint, jsonify, request
from db_ import db
from models.user import User

users_bp = Blueprint("users", __name__, url_prefix="/api/users")

@users_bp.get("/")
def list_users():
    rows = User.query.order_by(User.id).all()
    return jsonify([u.to_dict() for u in rows])

@users_bp.post("/")
def create_user():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return {"error": "name is required"}, 400

    u = User(name=name)
    db.session.add(u)
    db.session.commit()
    return {"ok": True, "id": u.id}, 201
