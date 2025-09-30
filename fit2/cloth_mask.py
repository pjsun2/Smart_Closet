import cv2
import mediapipe as mp
import numpy as np

# MediaPipe 유틸리티 초기화
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

def create_upper_body_mask(image):
    """
    몸 전체 세그멘테이션 마스크에서 골반 라인 기준 하반신을 제외하여
    머리를 포함한 상반신 마스크를 생성합니다.
    """
    print("머리 포함 상반신 마스크 생성을 시작합니다...")

    with mp_pose.Pose(
        static_image_mode=True,
        model_complexity=2,
        enable_segmentation=True
    ) as pose:

        results = pose.process(image)

        if not results.pose_landmarks or results.segmentation_mask is None:
            print("포즈 또는 세그멘테이션 마스크를 찾지 못했습니다.")
            return image, np.zeros(image.shape[:2], dtype=np.uint8)

        h, w, _ = image.shape

        # 1. 정교한 몸 전체 실루엣 마스크 생성
        condition = results.segmentation_mask > 0.5
        final_mask = condition.astype(np.uint8) * 255

        # 2. 제외할 하반신 영역 정의 (골반 라인 기준)
        landmarks = results.pose_landmarks.landmark

        # --- 얼굴(머리) 마스크 제거 로직 전체 삭제 ---

        right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]
        left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]

        lower_body_points = np.array([
            [right_hip.x * w, right_hip.y * h],
            [left_hip.x * w, left_hip.y * h],
            [0, h],
            [w, h],
        ], dtype=np.int32)

        # 3. 전체 실루엣 마스크에서 하반신 영역 제외
        cv2.fillPoly(final_mask, [lower_body_points], 0)

        # 4. 시각화용 이미지 생성 및 포즈 그리기
        visual_image = cv2.bitwise_and(image, image, mask=final_mask)

        green_spec = mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2)

        mp_drawing.draw_landmarks(
            image=visual_image,
            landmark_list=results.pose_landmarks,
            connections=mp_pose.POSE_CONNECTIONS,
            landmark_drawing_spec=green_spec,
            connection_drawing_spec=green_spec
        )

        return visual_image, final_mask