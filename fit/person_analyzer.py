# 파일명: person_analyzer.py

import cv2
import mediapipe as mp
import numpy as np

# MediaPipe 모델 초기화
mp_pose = mp.solutions.pose
mp_segmentation = mp.solutions.selfie_segmentation
mp_drawing = mp.solutions.drawing_utils

def analyze_person(image_path):
    """사용자 이미지를 분석하여 원본, 키포인트, 마스크, 포즈 이미지를 반환한다."""
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {image_path}")
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    pose_landmarks = None
    keypoints = None
    # 1. 포즈 추정
    with mp_pose.Pose(static_image_mode=True, min_detection_confidence=0.5) as pose:
        results = pose.process(image_rgb)
        if results.pose_landmarks:
            pose_landmarks = results.pose_landmarks
            keypoints = np.array([[lmk.x * image.shape[1], lmk.y * image.shape[0]] for lmk in pose_landmarks.landmark])

    # 2. 신체 분할
    with mp_segmentation.SelfieSegmentation(model_selection=0) as segmenter:
        seg_results = segmenter.process(image_rgb)
        person_mask = (seg_results.segmentation_mask > 0.9).astype(np.uint8) * 255
    
    # 3. ControlNet용 포즈 이미지 생성
    pose_image_for_controlnet = np.zeros_like(image)
    if pose_landmarks:
        mp_drawing.draw_landmarks(
            pose_image_for_controlnet,
            pose_landmarks,
            mp_pose.POSE_CONNECTIONS,
            mp_drawing.DrawingSpec(color=(255,255,0), thickness=2, circle_radius=2),
            mp_drawing.DrawingSpec(color=(255,0,255), thickness=2)
        )

    return image, keypoints, person_mask, pose_image_for_controlnet