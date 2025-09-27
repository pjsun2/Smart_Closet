# 파일명: main.py

import cv2
from person_analyzer import analyze_person
from clothing_analyzer import analyze_clothing
from warper import warp_clothing
from synthesizer import synthesize_final_image

# --- 설정할 파일명 ---
PERSON_IMAGE_FILE = "input/person.jpg"    # 입력: 사람 이미지 경로
CLOTHING_IMAGE_FILE = "input/cloth.jpg" # 입력: 옷 이미지 경로
OUTPUT_IMAGE_FILE = "output/result.png"   # 출력: 최종 결과물 경로

if __name__ == "__main__":
    try:
        # 1. 사용자 분석
        print("▶️ 1단계 시작: 사용자 분석...")
        person_img, p_keypoints, p_mask, pose_img = analyze_person(PERSON_IMAGE_FILE)
        print("✅ 1단계 완료!")

        # 2. 의류 분석
        print("▶️ 2단계 시작: 의류 분석...")
        cloth_img, c_mask = analyze_clothing(CLOTHING_IMAGE_FILE)
        print("✅ 2단계 완료!")

        # 3. 의류 변형
        print("▶️ 3단계 시작: 의류 변형...")
        warped_cloth = warp_clothing(person_img, p_keypoints, cloth_img)
        print("✅ 3단계 완료!")

        # (선택) 중간 결과 확인
        cv2.imwrite("output/warped_cloth.png", warped_cloth)
        cv2.imwrite("output/pose_image.png", pose_img)

        # 4. 최종 합성 (GPU 필요)
        synthesize_final_image(pose_img, warped_cloth, OUTPUT_IMAGE_FILE)

    except Exception as e:
        print(f"❌ 오류 발생: {e}")