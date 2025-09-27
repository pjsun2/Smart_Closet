# 파일명: clothing_analyzer.py

import cv2
import numpy as np

def analyze_clothing(image_path):
    """의류 이미지에서 배경을 제거하고 옷 부분과 마스크를 반환한다."""
    cloth_image = cv2.imread(image_path)
    if cloth_image is None:
        raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {image_path}")

    # 딥러닝 모델 대신 간단한 OpenCV 기능으로 배경 제거 예시
    gray = cv2.cvtColor(cloth_image, cv2.COLOR_BGR2GRAY)
    _, cloth_mask = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)

    # 마스크 정제를 위한 Morphological 연산
    kernel = np.ones((5,5), np.uint8)
    cloth_mask = cv2.morphologyEx(cloth_mask, cv2.MORPH_CLOSE, kernel)
    cloth_mask = cv2.morphologyEx(cloth_mask, cv2.MORPH_OPEN, kernel)

    cloth_no_bg = cv2.bitwise_and(cloth_image, cloth_image, mask=cloth_mask)

    return cloth_no_bg, cloth_mask