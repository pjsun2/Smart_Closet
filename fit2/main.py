import cv2
import matplotlib.pyplot as plt
from cloth_mask import create_upper_body_mask

def main():
    """
    메인 실행 함수
    """
    # 1. 이미지 로드
    image_path = 'input/model.jpg'
    try:
        img = cv2.imread(image_path)
        if img is None:
            raise FileNotFoundError(f"이미지 파일을 찾을 수 없습니다: {image_path}")

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    except Exception as e:
        print(e)
        return

    # 2. 마스크 생성 함수 호출
    visual_image, final_mask = create_upper_body_mask(img_rgb)

    # 3. 결과 시각화
    plt.figure(figsize=(15, 5))

    plt.subplot(1, 3, 1)
    plt.imshow(img_rgb)
    plt.title('Original Image')
    plt.axis('off')

    plt.subplot(1, 3, 2)
    plt.imshow(visual_image)
    plt.title('Final Result Preview')
    plt.axis('off')

    plt.subplot(1, 3, 3)
    plt.imshow(final_mask, cmap='gray')
    plt.title('Final Upper Body Mask')
    plt.axis('off')

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()