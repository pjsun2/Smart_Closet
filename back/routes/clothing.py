from flask import Blueprint, request, jsonify
import sys
import os
import traceback

back_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if back_dir not in sys.path:
    sys.path.insert(0, back_dir)

from db_files.clothes_db import insert_clothing_with_attributes, get_user_clothing_with_attributes, delete_clothing

clothing_bp = Blueprint('clothing', __name__, url_prefix='/api/clothing')

@clothing_bp.route('/save', methods=['POST'])
def save_clothing():
    """모델 결과를 DB에 저장"""
    try:
        print("\n[clothing.py] /save 요청 시작")
        data = request.json
        
        print(f"[clothing.py] user_id: {data.get('user_id')}")
        print(f"[clothing.py] main_category: {data.get('main_category')}")
        print(f"[clothing.py] sub_category: {data.get('sub_category')}")
        print(f"[clothing.py] attributes 개수: {len(data.get('attributes', {}))}")
        
        result = insert_clothing_with_attributes(
            user_id=data['user_id'],
            image_url=data['image_url'],
            main_category=data['main_category'],
            sub_category=data['sub_category'],
            attributes_dict=data['attributes']
        )
        
        if result:
            print(f"[clothing.py] 저장 성공: CI_id={result}\n")
            return jsonify({'status': 'success', 'ci_id': result}), 200
        else:
            print(f"[clothing.py] 저장 실패\n")
            return jsonify({'status': 'error', 'message': '저장 실패'}), 400
            
    except Exception as e:
        print(f"\n[clothing.py] 예외 발생!")
        print(f"[clothing.py] 에러: {str(e)}\n")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@clothing_bp.route('/wardrobe', methods=['GET'])
def get_wardrobe():
    """사용자의 옷장 조회 (현재 사용자는 user_id=1로 고정)"""
    try:
        user_id = 1  # ← 현재는 유저 1로 고정
        print(f"\n[clothing.py] /wardrobe 요청 (user_id={user_id})")
        
        clothes_data = get_user_clothing_with_attributes(user_id)
        
        print(f"[clothing.py] 조회 성공: {len(clothes_data)}개 옷")
        return jsonify({'status': 'success', 'clothes': clothes_data}), 200
        
    except Exception as e:
        print(f"[clothing.py] 조회 실패: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
    
@clothing_bp.route('/<int:ci_id>', methods=['DELETE', 'OPTIONS'])
def delete_clothing_item(ci_id):
    """의류 삭제 API"""
    
    if request.method == 'OPTIONS':
        return '', 200
    
    print(f"\n[clothing.py] DELETE /api/clothing/{ci_id} 요청")
    
    try:
        # DB에서 삭제
        success = delete_clothing(ci_id)
        
        if success:
            print(f"[clothing.py] 삭제 성공: CI_id={ci_id}\n")
            return jsonify({
                "status": "success",
                "message": "의류가 삭제되었습니다"
            }), 200
        else:
            print(f"[clothing.py] 삭제 실패\n")
            return jsonify({
                "status": "error",
                "message": "의류 삭제 실패"
            }), 400
            
    except Exception as e:
        print(f"[clothing.py] 삭제 중 예외 발생: {str(e)}\n")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500