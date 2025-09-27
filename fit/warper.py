# 파일명: warper.py

import numpy as np
from skimage.transform import PiecewiseAffineTransform, warp

def warp_clothing(person_image, person_keypoints, cloth_image):
    """사람의 포즈에 맞게 옷 이미지를 변형(Warp)한다."""
    if person_keypoints is None:
        raise ValueError("포즈 키포인트를 찾을 수 없어 의류 변형을 진행할 수 없습니다.")

    person_h, person_w, _ = person_image.shape
    cloth_h, cloth_w, _ = cloth_image.shape

    # 소스 좌표: 의류 이미지의 주요 지점 (직접 정의 필요)
    src_points = np.array([
        [cloth_w * 0.25, cloth_h * 0.2],  # 왼쪽 어깨
        [cloth_w * 0.75, cloth_h * 0.2],  # 오른쪽 어깨
        [cloth_w * 0.1,  cloth_h * 0.5],  # 왼쪽 허리
        [cloth_w * 0.9,  cloth_h * 0.5],  # 오른쪽 허리
        [cloth_w * 0.2,  cloth_h * 0.9],  # 왼쪽 하단
        [cloth_w * 0.8,  cloth_h * 0.9]   # 오른쪽 하단
    ])

    # 타겟 좌표: 사람 이미지의 해당 포즈 키포인트 (MediaPipe 인덱스 기준)
    dst_points = person_keypoints[[11, 12, 23, 24, 25, 26]]

    # TPS 변환 실행
    tform = PiecewiseAffineTransform()
    tform.estimate(dst_points, src_points)
    
    warped_cloth = warp(cloth_image, tform.inverse, output_shape=(person_h, person_w))
    warped_cloth = (warped_cloth * 255).astype(np.uint8)

    return warped_cloth