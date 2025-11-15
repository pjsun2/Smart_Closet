import sqlite3
import os
from datetime import datetime
from flask import session, jsonify

DB_PATH = os.path.join(os.path.dirname(__file__), 'smart_closet.db')

def get_current_user_id():
    """현재 세션의 사용자 ID 반환 (없으면 None)"""
    user = session.get("user")
    if not user:
        return None
    
    # 이메일(user_id)로 DB의 User_id 조회
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT User_id FROM User WHERE User_email = ?", (user["id"],))
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result else None

def insert_clothing_for_current_user(image_url, main_category, sub_category, attributes_dict):
    """현재 세션 사용자의 옷 저장"""
    user_id = get_current_user_id()
    
    if not user_id:
        return jsonify(ok=False, message="로그인이 필요합니다."), 401
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 1. clothing_information 테이블에 INSERT
        cursor.execute('''
            INSERT INTO clothing_information 
            (User_id, CI_imageURL, CI_mainCategory, CI_subCategory, CI_createDate, CI_check)
            VALUES (?, ?, ?, ?, DATE('now'), ?)
        ''', (user_id, image_url, main_category, sub_category, 1))
        
        ci_id = cursor.lastrowid
        
        # 2. clothing_attributes 테이블에 INSERT
        for attr_name, attr_value in attributes_dict.items():
            cursor.execute('SELECT A_id FROM attributes WHERE A_name = ?', (attr_name,))
            result = cursor.fetchone()
            
            if result:
                a_id = result[0]
                cursor.execute('''
                    INSERT INTO clothing_attributes 
                    (CI_id, A_id, CA_value, CA_updateDate)
                    VALUES (?, ?, ?, DATE('now'))
                ''', (ci_id, a_id, attr_value))
        
        conn.commit()
        print(f"[DB] 사용자 {user_id}의 옷 저장 완료! (CI_id: {ci_id})")
        return jsonify(ok=True, ci_id=ci_id)
        
    except Exception as e:
        conn.rollback()
        print(f"[DB] 옷 저장 실패: {e}")
        return jsonify(ok=False, message="옷 저장에 실패했습니다.", id=user_id), 500
    finally:
        conn.close()

def get_current_user_clothing():
    """현재 세션 사용자의 모든 옷 조회"""
    user_id = get_current_user_id()
    
    if not user_id:
        return jsonify(ok=False, message="로그인이 필요합니다.", authenticated=False), 401
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT CI_id, CI_imageURL, CI_mainCategory, CI_subCategory, CI_createDate
            FROM clothing_information
            WHERE User_id = ?
            ORDER BY CI_createDate DESC
        ''', (user_id,))
        
        clothing_list = cursor.fetchall()
        result = []
        
        for clothing in clothing_list:
            ci_id, image_url, main_category, sub_category, create_date = clothing
            
            # 각 의류의 속성 조회
            # cursor.execute('''
            #     SELECT a.A_name, ca.CA_value
            #     FROM clothing_attributes ca
            #     JOIN attributes a ON ca.A_id = a.A_id
            #     WHERE ca.CI_id = ?
            # ''', (ci_id,))
            cursor.execute('''
                SELECT 
                    a.A_name,
                    CASE 
                        WHEN a.A_name IN ('추천 스타일 1순위', '추천 스타일 2순위', '추천 스타일 3순위')
                        THEN TRIM(
                            CASE 
                                WHEN instr(ca.CA_value, ' (') > 0
                                    THEN substr(ca.CA_value, 1, instr(ca.CA_value, ' (') - 1)
                                ELSE ca.CA_value
                            END
                        )
                        ELSE ca.CA_value
                    END AS CA_value
                FROM clothing_attributes ca
                JOIN attributes a ON ca.A_id = a.A_id
                WHERE ca.CI_id = ?
                AND a.A_name IN (
                        '추천 스타일 1순위',
                        '추천 스타일 2순위',
                        '추천 스타일 3순위',
                        '기장',
                        '색상',
                        '소매기장',
                        '핏'
                )
                order by a.A_id desc
            ''', (ci_id,))
            
            attributes = cursor.fetchall()
            details = {attr_name: attr_value for attr_name, attr_value in attributes}
            
            result.append({
                'id': ci_id,
                'main_category': main_category,
                'sub_category': sub_category,
                'details': details,
                'created_at': create_date,
                'image_url': image_url
            })
        
        print(f"[DB] 사용자 {user_id}의 옷 {len(result)}개 조회 완료")
        return jsonify(ok=True, clothing=result)
        
    except Exception as e:
        print(f"[DB] 조회 실패: {e}")
        return jsonify(ok=False, message="조회에 실패했습니다."), 500
    finally:
        conn.close()

def delete_current_user_clothing(ci_id):
    """현재 세션 사용자의 옷 삭제 (소유권 확인)"""
    user_id = get_current_user_id()
    
    if not user_id:
        return jsonify(ok=False, message="로그인이 필요합니다."), 401
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 1. 해당 의류가 현재 사용자의 소유인지 확인
        cursor.execute('SELECT User_id FROM clothing_information WHERE CI_id = ?', (ci_id,))
        result = cursor.fetchone()
        
        if not result:
            return jsonify(ok=False, message="존재하지 않는 의류입니다."), 404
        
        if result[0] != user_id:
            return jsonify(ok=False, message="삭제 권한이 없습니다."), 403
        
        # 2. clothing_attributes에서 삭제
        cursor.execute('DELETE FROM clothing_attributes WHERE CI_id = ?', (ci_id,))
        
        # 3. clothing_information에서 삭제
        cursor.execute('DELETE FROM clothing_information WHERE CI_id = ?', (ci_id,))
        
        conn.commit()
        print(f"[DB] 사용자 {user_id}의 CI_id {ci_id} 삭제 완료")
        return jsonify(ok=True)
        
    except Exception as e:
        conn.rollback()
        print(f"[DB] 삭제 실패: {e}")
        return jsonify(ok=False, message="삭제에 실패했습니다."), 500
    finally:
        conn.close()

def insert_user(email, password, nickname):
    """사용자 정보를 DB에 저장"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO User (User_email, User_password, User_nickname, User_createDate, User_updateDate)
            VALUES (?, ?, ?, DATE('now'), DATE('now'))
        ''', (email, password, nickname))
        
        conn.commit()
        print(f"사용자 '{nickname}' 저장 완료!")
        return True
    except sqlite3.IntegrityError as e:
        print(f"오류: {e}")
        return False
    finally:
        conn.close()

def insert_clothing(user_id, image_url, main_category, sub_category):
    """옷 정보를 DB에 저장"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO clothing_information 
        (User_id, CI_imageURL, CI_mainCategory, CI_subCategory, CI_createDate, CI_check)
        VALUES (?, ?, ?, ?, DATE('now'), ?)
    ''', (user_id, image_url, main_category, sub_category, 1))
    
    conn.commit()
    conn.close()

def get_user_clothing(user_id):
    """사용자의 모든 옷 조회"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM clothing_information WHERE User_id = ?
    ''', (user_id,))
    
    result = cursor.fetchall()
    conn.close()
    return result

def get_all_users():
    """모든 사용자 조회"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT User_id, User_email, User_password, User_nickname, User_createDate, User_updateDate, User_gender FROM User
    ''')
    
    users = cursor.fetchall()
    conn.close()
    
    print("=== 등록된 사용자 ===")
    for user in users:
        print(f"ID: {user[0]}, 이메일: {user[1]}, 닉네임: {user[2]}, 가입일: {user[3]}, 수정일: {user[4]}")
    
    return users

def insert_attributes():
    """옷 속성 데이터를 DB에 미리 저장"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 모든 속성 목록 (카테고리, 메인 분류 제외)
    attributes = [
        '추천 스타일 1순위',
        '추천 스타일 2순위',
        '추천 스타일 3순위',
        '기장',
        '색상',
        '서브색상',
        '옷깃',
        '소매기장',
        '소재',
        '프린트',
        '넥라인',
        '핏',
        '디테일'
    ]
    
    try:
        for attr in attributes:
            cursor.execute('''
                INSERT OR IGNORE INTO attributes (A_name)
                VALUES (?)
            ''', (attr,))
        
        conn.commit()
        print("속성 데이터 저장 완료!")
        return True
    except Exception as e:
        print(f"오류: {e}")
        return False
    finally:
        conn.close()

def get_all_attributes():
    """모든 속성 조회"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT A_id, A_name FROM attributes')
    attrs = cursor.fetchall()
    conn.close()
    
    print("=== 등록된 속성 ===")
    for attr in attrs:
        print(f"ID: {attr[0]}, 속성명: {attr[1]}")
    
    return attrs

def insert_clothing_with_attributes(user_id, image_url, main_category, sub_category, attributes_dict):
    """
    옷 정보와 속성을 함께 저장
    
    attributes_dict 예시:
    {
        '추천 스타일 1순위': '모던 (확률: 70.17%)',
        '추천 스타일 2순위': '로맨틱 (확률: 29.29%)',
        '추천 스타일 3순위': '클래식 (확률: 0.48%)',
        '기장': '없음',
        '색상': '베이지',
        '소재': '시폰',
        '프린트': '무지',
        '넥라인': '없음',
        '소매기장': '긴팔',
        '핏': '노멀',
        '디테일': '없음',
        '옷깃': '없음',
        '서브색상': '없음'
    }
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 1. clothing_information 테이블에 INSERT
        cursor.execute('''
            INSERT INTO clothing_information 
            (User_id, CI_imageURL, CI_mainCategory, CI_subCategory, CI_createDate, CI_check)
            VALUES (?, ?, ?, ?, DATE('now'), ?)
        ''', (user_id, image_url, main_category, sub_category, 1))
        
        # 방금 INSERT된 의류의 ID 가져오기
        ci_id = cursor.lastrowid
        
        # 2. clothing_attributes 테이블에 INSERT (반복)
        for attr_name, attr_value in attributes_dict.items():
            # 속성 이름으로 A_id 조회
            cursor.execute('SELECT A_id FROM attributes WHERE A_name = ?', (attr_name,))
            result = cursor.fetchone()
            
            if result:
                a_id = result[0]
                cursor.execute('''
                    INSERT INTO clothing_attributes 
                    (CI_id, A_id, CA_value, CA_updateDate)
                    VALUES (?, ?, ?, DATE('now'))
                ''', (ci_id, a_id, attr_value))
        
        conn.commit()
        print(f"옷 정보 저장 완료! (CI_id: {ci_id})")
        return ci_id
        
    except Exception as e:
        conn.rollback()
        print(f"오류 발생: {e}")
        return None
    finally:
        conn.close()

def get_all_clothing():
    """모든 의류 정보 조회"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM clothing_information')
    clothing_list = cursor.fetchall()
    conn.close()
    
    print("=== 저장된 의류 정보 ===")
    for clothing in clothing_list:
        print(f"ID: {clothing[0]}, User: {clothing[1]}, 메인카테고리: {clothing[2]}, 서브카테고리: {clothing[3]}, 생성일: {clothing[5]}")
    
    return clothing_list

def get_clothing_attributes(ci_id):
    """특정 의류의 속성 조회"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT ca.CA_id, a.A_name, ca.CA_value, ca.CA_updateDate
        FROM clothing_attributes ca
        JOIN attributes a ON ca.A_id = a.A_id
        WHERE ca.CI_id = ?
    ''', (ci_id,))
    
    attributes = cursor.fetchall()
    conn.close()
    
    print(f"\n=== CI_id {ci_id}의 속성 ===")
    for attr in attributes:
        print(f"  속성명: {attr[1]}, 값: {attr[2]}")
    
    return attributes

def get_all_clothing_with_attributes():
    """모든 의류와 해당 속성 조회 (종합)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT CI_id FROM clothing_information')
    clothing_ids = cursor.fetchall()
    conn.close()
    
    print("=== 의류 및 속성 종합 ===")
    for (ci_id,) in clothing_ids:
        get_clothing_attributes(ci_id)

def check_database_contents():
    """DB의 모든 테이블 내용을 상세하게 확인"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("\n" + "="*80)
    print(" 데이터베이스 전체 내용 확인")
    print("="*80)
    
    # 1. User 테이블
    print("\n [User 테이블]")
    cursor.execute('SELECT * FROM User')
    users = cursor.fetchall()
    if users:
        for user in users:
            print(f"  User_id: {user[0]}, Email: {user[1]}, Nickname: {user[3]}, Created: {user[4]}")
    else:
        print("  (데이터 없음)")
    
    # 2. clothing_information 테이블 (CI_imageURL 제외)
    print("\n [clothing_information 테이블]")
    cursor.execute('SELECT CI_id, User_id, CI_mainCategory, CI_subCategory, CI_createDate, CI_check FROM clothing_information')
    clothing_info = cursor.fetchall()
    if clothing_info:
        for cloth in clothing_info:
            print(f"  CI_id: {cloth[0]}, User_id: {cloth[1]}, MainCategory: {cloth[2]}, SubCategory: {cloth[3]}, Created: {cloth[4]}, Check: {cloth[5]}")
    else:
        print("  (데이터 없음)")
    
    # 3. attributes 테이블
    print("\n [attributes 테이블]")
    cursor.execute('SELECT * FROM attributes')
    attributes = cursor.fetchall()
    if attributes:
        for attr in attributes:
            print(f"  A_id: {attr[0]}, A_name: {attr[1]}")
    else:
        print("  (데이터 없음)")
    
    # 4. clothing_attributes 테이블 (상세)
    print("\n [clothing_attributes 테이블 (상세)]")
    cursor.execute('''
        SELECT ca.CA_id, ca.CI_id, a.A_name, ca.CA_value, ca.CA_updateDate
        FROM clothing_attributes ca
        JOIN attributes a ON ca.A_id = a.A_id
        ORDER BY ca.CI_id, a.A_name
    ''')
    clothing_attrs = cursor.fetchall()
    
    if clothing_attrs:
        current_ci_id = None
        for attr in clothing_attrs:
            ca_id, ci_id, a_name, ca_value, update_date = attr
            
            # CI_id가 바뀔 때마다 새 섹션 시작
            if ci_id != current_ci_id:
                current_ci_id = ci_id
                print(f"\n  ┌─ CI_id: {ci_id}")
            
            print(f"  │  CA_id: {ca_id}, 속성: {a_name}, 값: {ca_value}")
        print(f"  └─────")
    else:
        print("  (데이터 없음)")
    
    # 5. 통계
    print("\n [통계]")
    cursor.execute('SELECT COUNT(*) FROM User')
    user_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM clothing_information')
    clothing_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM clothing_attributes')
    attr_count = cursor.fetchone()[0]
    
    print(f"  총 사용자: {user_count}명")
    print(f"  총 의류: {clothing_count}개")
    print(f"  총 속성 항목: {attr_count}개")
    
    print("\n" + "="*80)
    
    conn.close()

# llm에 넣어서 처리
def get_user_clothing_with_attributes(user_id):
    """사용자의 모든 옷과 속성을 조회"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 사용자의 모든 의류 조회
        cursor.execute('''
            SELECT CI_id, CI_imageURL, CI_mainCategory, CI_subCategory, CI_createDate
            FROM clothing_information
            WHERE User_id = ?
            ORDER BY CI_createDate DESC
        ''', (user_id,))
        
        clothing_list = cursor.fetchall()
        result = []
        
        for clothing in clothing_list:
            ci_id, image_url, main_category, sub_category, create_date = clothing
            
            # 각 의류의 속성 조회
            cursor.execute('''
                SELECT a.A_name, ca.CA_value
                FROM clothing_attributes ca
                JOIN attributes a ON ca.A_id = a.A_id
                WHERE ca.CI_id = ?
            ''', (ci_id,))
            
            attributes = cursor.fetchall()
            
            # 속성을 딕셔너리로 변환
            details = {}
            for attr_name, attr_value in attributes:
                details[attr_name] = attr_value
            
            # 결과에 추가
            result.append({
                'id': ci_id,
                'main_category': main_category,
                'sub_category': sub_category,
                'details': details,
                'created_at': create_date,
                'image_url': image_url
            })
        
        print(f"[DB] 사용자 {user_id}의 옷 {len(result)}개 조회 완료")
        print(result)
        return result
        
    except Exception as e:
        print(f"[DB] 조회 실패: {str(e)}")
        return []
    finally:
        conn.close()

def delete_clothing(ci_id):
    """의류 삭제 (속성도 함께 삭제)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 1. clothing_attributes 테이블에서 먼저 삭제 (외래키 제약)
        cursor.execute('DELETE FROM clothing_attributes WHERE CI_id = ?', (ci_id,))
        
        # 2. clothing_information 테이블에서 삭제
        cursor.execute('DELETE FROM clothing_information WHERE CI_id = ?', (ci_id,))
        
        conn.commit()
        print(f"[DB] CI_id {ci_id} 삭제 완료")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"[DB] 삭제 실패: {str(e)}")
        return False
    finally:
        conn.close()

def insert_test_data():
    """테스트용 의류 데이터 3개 삽입"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 1. 사용자가 없으면 먼저 사용자 생성
        cursor.execute('SELECT COUNT(*) FROM User')
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO User (User_email, User_password, User_nickname, User_createDate, User_updateDate)
                VALUES (?, ?, ?, DATE('now'), DATE('now'))
            ''', ('test@example.com', 'password123', '테스트사용자'))
            conn.commit()
            print("테스트 사용자 생성 완료")
        
        user_id = 16
        
        # 2. 속성 데이터가 없으면 먼저 생성
        cursor.execute('SELECT COUNT(*) FROM attributes')
        if cursor.fetchone()[0] == 0:
            insert_attributes()
            print("속성 데이터 생성 완료")
        
        # 3. 테스트 의류 데이터 3개 삽입
        test_clothes = [
            {
                'image_url': 'http://example.com/shirt1.jpg',
                'main_category': '상의',
                'sub_category': '티셔츠',
                'attributes': {
                    '추천 스타일 1순위': '모던 (확률: 85.50%)',
                    '추천 스타일 2순위': '캐주얼 (확률: 10.20%)',
                    '추천 스타일 3순위': '포멀 (확률: 4.30%)',
                    '색상': '화이트',
                    '소재': '코튼',
                    '핏': '노멀',
                    '기장': '노멀',
                    '소매기장': '반팔',
                    '프린트': '솔리드',
                    '넥라인': '라운드넥',
                    '디테일': '없음',
                    '옷깃': '없음',
                    '서브색상': '없음'
                }
            },
            {
                'image_url': 'http://example.com/pants1.jpg',
                'main_category': '하의',
                'sub_category': '팬츠',
                'attributes': {
                    '추천 스타일 1순위': '모던 (확률: 88.50%)',
                    '추천 스타일 2순위': '클래식 (확률: 9.10%)',
                    '추천 스타일 3순위': '캐주얼 (확률: 2.40%)',
                    '색상': '베이지',
                    '소재': '코튼',
                    '핏': '와이드',
                    '기장': '발목',
                    '소매기장': '없음',
                    '프린트': '솔리드',
                    '넥라인': '없음',
                    '디테일': '없음',
                    '옷깃': '없음',
                    '서브색상': '없음'
                }
            },
            {
                'image_url': 'http://example.com/blouse1.jpg',
                'main_category': '상의',
                'sub_category': '블라우스',
                'attributes': {
                    '추천 스타일 1순위': '모던 (확률: 72.30%)',
                    '추천 스타일 2순위': '로맨틱 (확률: 20.10%)',
                    '추천 스타일 3순위': '클래식 (확률: 7.60%)',
                    '색상': '검은색',
                    '소재': '코튼',
                    '핏': '타이트',
                    '기장': '노멀',
                    '소매기장': '긴팔',
                    '프린트': '솔리드',
                    '넥라인': '브이넥',
                    '디테일': '단추',
                    '옷깃': '없음',
                    '서브색상': '없음'
                }
            }
        ]
        
        # 각 의류 데이터 삽입
        for idx, cloth_data in enumerate(test_clothes, 1):
            ci_id = insert_clothing_with_attributes(
                user_id=user_id,
                image_url=cloth_data['image_url'],
                main_category=cloth_data['main_category'],
                sub_category=cloth_data['sub_category'],
                attributes_dict=cloth_data['attributes']
            )
            print(f"테스트 의류 {idx}/3 삽입 완료 (CI_id: {ci_id})")
        
        print("\n모든 테스트 데이터 삽입 완료!")
        return True
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()

if __name__ == '__main__':

    # 동미랑 사용자 생성
    # insert_user('dongmirang@example.com', 'password123', '동미랑')

    # 모든 사용자 조회
    # get_all_users()

    # 속성 데이터 저장
    # insert_attributes()

    # 저장된 속성 조회
    # get_all_attributes()

    # 모든 의류 정보 조회
    # get_all_clothing()
    
    # 모든 의류와 속성 종합 조회
    # get_all_clothing_with_attributes()

    # DB 전체 내용 확인
    # check_database_contents()

    # 테스트 데이터 삽입
    # insert_test_data()

    # 특정 사용자의 옷과 속성 조회, session 정보에 저장된 user_id를 검색함.
    user = session.get['user']
    get_user_clothing_with_attributes(user['useridseq']) 
