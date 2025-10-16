import os
import argparse
from ultralytics import YOLO
from PIL import Image
import numpy as np

# --- 설정 ---
MODEL_PATH = './runs/segment/train2/weights/best.pt' 
OUTPUT_DIR = 'segment_results_rgb'


def predict_and_extract_rgb(image_path):
    """
    YOLO Segmentation 모델로 옷의 외곽선을 찾아내고,
    배경이 검은색인 RGB 이미지 파일로 옷 부분만 추출하여 저장합니다.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    try:
        model = YOLO(MODEL_PATH)
        print(f"'{MODEL_PATH}' 모델을 성공적으로 불러왔습니다.")
    except Exception as e:
        print(f"오류: 모델을 불러오는 데 실패했습니다. 경로를 확인해주세요. 에러: {e}")
        return

    try:
        # 이미지를 처음부터 3채널(RGB)로 불러옴.
        original_image = Image.open(image_path).convert("RGB")
    except FileNotFoundError:
        print(f"오류: '{image_path}' 이미지 파일을 찾을 수 없습니다.")
        return

    print(f"\n--- '{image_path}' 이미지 분할 시작 ---")
    
    results = model(original_image)

    extracted_count = 0
    for i, r in enumerate(results):
        if r.masks is None:
            continue

        for j, mask in enumerate(r.masks):
            class_name = model.names[int(r.boxes[j].cls[0])]
            
            # 배경을 투명(RGBA)이 아닌 검은색(RGB)으로 만드는 로직
            mask_array = mask.data[0].cpu().numpy()
            
            # 마스크를 원본과 같은 크기로 만들고, 채널 차원을 추가 (H, W) -> (H, W, 1)
            mask_resized = np.expand_dims(Image.fromarray(mask_array).resize(original_image.size), axis=-1)
            
            # 원본 이미지를 numpy 배열로 변환
            original_array = np.array(original_image)
            
            # np.where을 사용하여 마스크가 1인 곳은 원본 픽셀을, 0인 곳은 검은색 [0, 0, 0]을 채움
            # 이것이 배경을 검은색으로 만드는 로직.
            rgb_array = np.where(mask_resized > 0, original_array, [0, 0, 0]).astype(np.uint8)
            
            # -----------------------------------------------------------------

            # 최종 이미지 생성 및 저장
            final_image = Image.fromarray(rgb_array)
            
            base_filename = os.path.splitext(os.path.basename(image_path))[0]
            output_filename = f"{base_filename}_extracted_{j}_{class_name}.jpg"
            output_path = os.path.join(OUTPUT_DIR, output_filename)
            
            final_image.save(output_path)
            print(f"-> '{class_name}'(을)를 추출하여 '{output_path}' 경로에 저장했습니다.")
            extracted_count += 1
            
    if extracted_count == 0:
        print("-> 이미지에서 옷을 찾지 못했습니다.")
    else:
        print(f"\n총 {extracted_count}개의 객체를 추출하여 저장했습니다.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="YOLO Segmentation 모델로 옷을 추출합니다 (RGB 버전).")
    parser.add_argument("--image", required=True, type=str, help="분석할 이미지 파일 경로")
    args = parser.parse_args()
    
    predict_and_extract_rgb(args.image)