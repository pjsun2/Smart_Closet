import argparse
from PIL import Image
import torch
import numpy as np
import os
from ultralytics import YOLO
import sys

# 현재 파일 기준 절대 경로 설정
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CURRENT_DIR)

# --- 각 전문가 모델의 클래스와 예측 함수 불러오기 ---
# from train_ViT_classifier import RouterDataset, AutoModelForImageClassification
from train_ViT_clothes_detail import SpecialistDataset, SpecialistClassifier
from transformers import AutoImageProcessor, AutoModelForImageClassification
# ---------------------------------------------------


# --- 설정: 훈련된 모든 모델의 경로 ---
YOLO_MODEL_PATH = os.path.join(CURRENT_DIR, 'runs/segment/train2/weights/best.pt')
ROUTER_MODEL_PATH = os.path.join(CURRENT_DIR, 'router_model')
SPECIALIST_MODEL_PATHS = {
    '상의': os.path.join(CURRENT_DIR, '상의_specialist_model'),
    '하의': os.path.join(CURRENT_DIR, '하의_specialist_model'),
    '아우터': os.path.join(CURRENT_DIR, '아우터_specialist_model'),
    '원피스': os.path.join(CURRENT_DIR, '원피스_specialist_model'),
}
BASE_TRANSFORMER = "google/vit-base-patch16-224-in21k"
# -------------------------------------


def load_all_models():
    """모든 AI 모델들을 미리 메모리에 로드하는 함수"""
    print("모든 AI 모델을 로딩합니다...")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    # 1. YOLO 모델 로드
    yolo_model = YOLO(YOLO_MODEL_PATH)
    
    # 2. 1차 분류기(Router) 모델 로드
    router_model = AutoModelForImageClassification.from_pretrained(ROUTER_MODEL_PATH).to(device)
    
    # 3. 2차 분류기(Specialist) 모델들 로드
    specialist_models = {}
    for category, path in SPECIALIST_MODEL_PATHS.items():
        if os.path.isdir(path):
            # label_maps = torch.load(os.path.join(path, 'label_maps.pth'))
            # model = SpecialistClassifier(label_maps).to(device)
            # model.load_state_dict(torch.load(os.path.join(path, 'pytorch_model.bin')))

            label_maps = torch.load(os.path.join(path, 'label_maps.pth'), map_location=device)
            model = SpecialistClassifier(label_maps).to(device)
            model.load_state_dict(torch.load(os.path.join(path, 'pytorch_model.bin'), map_location=device))

            model.eval()
            specialist_models[category] = {'model': model, 'labels': label_maps}
    
    print("모든 모델 로딩 완료!")
    return {
        "device": device,
        "yolo": yolo_model,
        "router": router_model,
        "specialists": specialist_models,
        "processor": AutoImageProcessor.from_pretrained(BASE_TRANSFORMER)
    }

def run_full_pipeline(models, image_path):
    """AI 서비스의 전체 파이프라인을 실행합니다."""
    print(f"\n=========================================")
    print(f"--- 입력 이미지 분석 시작: {image_path} ---")
    
    analysis_results = []  # 결과 저장소 추가
    
    try:
        original_image = Image.open(image_path).convert("RGBA")
    except FileNotFoundError:
        print(f"오류: '{image_path}' 파일을 찾을 수 없습니다.")
        return {"error": "이미지를 찾을 수 없습니다", "status": "failed"}

    # 1. YOLO로 옷의 외곽선 찾기
    yolo_results = models['yolo'](original_image)
    
    if not yolo_results or yolo_results[0].masks is None:
        print("-> YOLO 모델이 이미지에서 옷을 찾지 못했습니다.")
        return {"error": "옷을 찾을 수 없습니다", "status": "failed"}
        
    print(f"-> 총 {len(yolo_results[0].masks)}개의 옷을 찾았습니다. 각 옷을 분석합니다...")

    # 2. 찾은 옷들을 하나씩 분석
    for i, mask in enumerate(yolo_results[0].masks):
        print(f"\n--- 분석 #{i+1} ---")
        
        item_result = {"item_id": i + 1, "details": {}}  # 개별 아이템 결과
        
        # 3. 마스크를 이용해 옷 부분만 잘라내기
        mask_array = mask.data[0].cpu().numpy().astype(np.uint8)
        mask_image = Image.fromarray(mask_array * 255).resize(original_image.size)
        transparent_array = np.zeros_like(np.array(original_image))
        transparent_array[np.array(mask_image) > 0] = np.array(original_image)[np.array(mask_image) > 0]
        cropped_image = Image.fromarray(transparent_array)
        cropped_image_rgb = cropped_image.convert("RGB")

        # 4. 1차 분류기(Router)로 큰 카테고리 판단
        inputs = models['processor'](images=cropped_image_rgb, return_tensors="pt").to(models['device'])
        with torch.no_grad():
            logits = models['router'](**inputs).logits
        main_category_id = logits.argmax(-1).item()
        main_category = models['router'].config.id2label[main_category_id]
        print(f"1차 분류 결과: 이 옷은 '{main_category}' 종류입니다.")
        
        item_result["main_category"] = main_category  # 카테고리 저장

        # 5. 2차 분류기(Specialist)로 상세 속성 분석
        if main_category in models['specialists']:
            specialist = models['specialists'][main_category]
            specialist_model = specialist['model']
            specialist_labels = specialist['labels']
            
            print(f"'{main_category}' 전문가가 상세 분석을 시작합니다...")
            
            with torch.no_grad():
                outputs = specialist_model(**inputs)
            
            print("\n--- 최종 분석 결과 ---")
            for attr, logits in outputs.items():
                if attr == '스타일':
                    probabilities = torch.nn.functional.softmax(logits, dim=-1)
                    top3 = torch.topk(probabilities, 3)
                    top3_styles = []
                    print("- 추천 스타일 Top 3:")
                    for k in range(3):
                        prob = top3.values[0][k].item()
                        style_id = top3.indices[0][k].item()
                        style_name = specialist_labels[attr][style_id]
                        top3_styles.append({"name": style_name, "confidence": prob})
                        print(f"  * {style_name} (확률: {prob:.2%})")
                    item_result["details"][attr] = top3_styles  # 저장
                else:
                    pred_id = logits.argmax(-1).item()
                    pred_name = specialist_labels[attr][pred_id]
                    item_result["details"][attr] = pred_name  # 저장
                    print(f"- {attr}: {pred_name}")
            print("--------------------")
        else:
            print(f"-> '{main_category}'에 대한 전문 분석 모델이 없습니다.")
        
        analysis_results.append(item_result)  # 결과 추가
    
    # 최종 결과 반환
    return {
        "status": "success",
        "total_items": len(analysis_results),
        "items": analysis_results
    }

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="패션 이미지 분석 통합 파이프라인")
    parser.add_argument("--image", required=True, type=str, help="분석할 이미지 파일 경로")
    args = parser.parse_args()
    
    # 스크립트 시작 시 모든 모델을 한 번에 로드
    all_models = load_all_models()
    # 파이프라인 실행
    run_full_pipeline(all_models, args.image)