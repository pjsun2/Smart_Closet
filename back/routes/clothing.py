from flask import Blueprint, request, jsonify, session
import sys
import os
import traceback

back_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if back_dir not in sys.path:
    sys.path.insert(0, back_dir)

from db_files.clothes_db import (
    insert_clothing_for_current_user,
    get_current_user_clothing,
    delete_current_user_clothing
)

clothing_bp = Blueprint('clothing', __name__, url_prefix='/api/clothing')

@clothing_bp.route('/save', methods=['POST'])
def save_clothing():
    """모델 결과를 DB에 저장"""
    try:
        # 세션 확인
        user = session.get("user")
        if not user:
            print("[clothing.py] 로그인이 필요합니다")
            return jsonify({'status': 'error', 'message': '로그인이 필요합니다', 'authenticated': False}), 401
        
        print("\n[clothing.py] /save 요청 시작")
        data = request.json
        
        print(f"[clothing.py] user: {user.get('id')}")
        print(f"[clothing.py] main_category: {data.get('main_category')}")
        print(f"[clothing.py] sub_category: {data.get('sub_category')}")
        print(f"[clothing.py] attributes 개수: {len(data.get('attributes', {}))}")
        
        # 세션의 사용자로 저장
        result = insert_clothing_for_current_user(
            image_url=data['image_url'],
            main_category=data['main_category'],
            sub_category=data['sub_category'],
            attributes_dict=data['attributes']
        )
        
        # result는 jsonify 객체 또는 tuple (response, status_code)
        if isinstance(result, tuple):
            return result  # 이미 jsonify된 응답
        
        print(f"[clothing.py] 저장 성공\n")
        return result
            
    except Exception as e:
        print(f"\n[clothing.py] 예외 발생!")
        print(f"[clothing.py] 에러: {str(e)}\n")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@clothing_bp.route('/wardrobe', methods=['GET'])
def get_wardrobe():
    """사용자의 옷장 조회"""
    try:
        # 세션 확인
        user = session.get("user")
        if not user:
            print("[clothing.py] 로그인이 필요합니다")
            return jsonify({'status': 'error', 'message': '로그인이 필요합니다', 'authenticated': False}), 401
        
        print(f"\n[clothing.py] /wardrobe 요청 (user: {user.get('id')})")
        
        # 세션의 사용자 옷장 조회
        result = get_current_user_clothing()
        
        if isinstance(result, tuple):
            return result
        
        return result
        
    except Exception as e:
        print(f"[clothing.py] 조회 실패: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
    
@clothing_bp.route('/<int:ci_id>', methods=['DELETE', 'OPTIONS'])
def delete_clothing_item(ci_id):
    """의류 삭제 API"""
    
    if request.method == 'OPTIONS':
        return '', 200
    
    # 세션 확인
    user = session.get("user")
    if not user:
        print("[clothing.py] 로그인이 필요합니다")
        return jsonify({'status': 'error', 'message': '로그인이 필요합니다', 'authenticated': False}), 401
    
    print(f"\n[clothing.py] DELETE /api/clothing/{ci_id} 요청 (user: {user.get('id')})")
    
    try:
        # 세션의 사용자 소유 여부 확인하며 삭제
        result = delete_current_user_clothing(ci_id)
        
        if isinstance(result, tuple):
            return result
        
        print(f"[clothing.py] 삭제 성공: CI_id={ci_id}\n")
        return result
            
    except Exception as e:
        print(f"[clothing.py] 삭제 중 예외 발생: {str(e)}\n")
        return jsonify({'status': 'error', 'message': str(e)}), 500