from flask import Blueprint, jsonify

members_bp = Blueprint("members", __name__, url_prefix="/api/members")

@members_bp.route("/", methods=["GET"])
def get_members():
    return jsonify({"members": ["test22", "test", "Member3"]})




