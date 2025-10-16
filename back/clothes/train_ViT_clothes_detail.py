import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
from PIL import Image
from transformers import AutoImageProcessor, AutoModel
import torch.nn as nn
from torch.optim import AdamW
import os
from tqdm import tqdm 
import argparse

# --- 설정 ---
BASE_DATA_DIR = './specialist_data'
MODEL_NAME = "google/vit-base-patch16-224-in21k"
NUM_EPOCHS = 3 # 먼저 3번만 훈련해서 성공하는지 확인
BATCH_SIZE = 8
LEARNING_RATE = 5e-5 # 5 * 10^-5


# 1. 데이터셋 클래스
class SpecialistDataset(Dataset):
    def __init__(self, csv_path, image_dir, processor):
        self.df = pd.read_csv(csv_path)
        self.image_dir = image_dir
        self.processor = processor
        self.label_columns = [col for col in self.df.columns if col != 'image_name']
        self.label_maps = {}
        self.encoded_labels = {}
        for col in self.label_columns:
            self.df[col] = self.df[col].apply(lambda x: str(x).split(',')[0] if pd.notna(x) else '없음')
            cat_type = self.df[col].astype('category')
            self.encoded_labels[col] = cat_type.cat.codes
            self.label_maps[col] = dict(enumerate(cat_type.cat.categories))
    def __len__(self):
        return len(self.df)
    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        image_path = os.path.join(self.image_dir, row['image_name'])
        try:
            image = Image.open(image_path).convert("RGB")
        except (FileNotFoundError, OSError):
            return self.__getitem__((idx + 1) % len(self))
        inputs = self.processor(images=image, return_tensors="pt")
        item = {"pixel_values": inputs.pixel_values.squeeze()}
        for col in self.label_columns:
            item[f"label_{col}"] = torch.tensor(self.encoded_labels[col].iloc[idx], dtype=torch.long)
        return item

# 2. Multi-Task 모델 설계
class SpecialistClassifier(nn.Module):
    def __init__(self, label_maps):
        super().__init__()
        self.body = AutoModel.from_pretrained(MODEL_NAME)
        hidden_size = self.body.config.hidden_size
        self.heads = nn.ModuleDict({
            col: nn.Linear(hidden_size, len(class_map))
            for col, class_map in label_maps.items()
        })
    def forward(self, pixel_values):
        features = self.body(pixel_values=pixel_values).last_hidden_state[:, 0, :]
        logits = {col: head(features) for col, head in self.heads.items()}
        return logits

# --- 메인 실행 ---
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--category", required=True, type=str, choices=['상의', '하의', '아우터', '원피스'])
    args = parser.parse_args()

    CATEGORY = args.category
    CSV_PATH = os.path.join(BASE_DATA_DIR, f"{CATEGORY}_metadata.csv")
    IMAGE_DIR = os.path.join(BASE_DATA_DIR, CATEGORY)
    OUTPUT_DIR = f"{CATEGORY}_specialist_model"

    # --- 3. 데이터 준비 ---
    processor = AutoImageProcessor.from_pretrained(MODEL_NAME)
    dataset = SpecialistDataset(CSV_PATH, IMAGE_DIR, processor)
    dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)

    # --- 4. 모델, 옵티마이저, 손실 함수 준비 ---
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"'{CATEGORY}' 전문가 모델 훈련에 사용할 장치: {device}")

    model = SpecialistClassifier(dataset.label_maps).to(device)
    optimizer = AdamW(model.parameters(), lr=LEARNING_RATE)
    loss_fn = nn.CrossEntropyLoss()

    # --- 5. 수동 훈련 루프 ---
    print("수동 훈련을 시작합니다...")
    for epoch in range(NUM_EPOCHS):
        print(f"--- 에포크 {epoch + 1}/{NUM_EPOCHS} ---")
        model.train() # 훈련 모드
        
        for batch in tqdm(dataloader, desc=f"에포크 {epoch+1} 훈련 중"):
            # 데이터를 GPU로 이동
            pixel_values = batch['pixel_values'].to(device)
            
            # 순전파 (Forward pass)
            logits_dict = model(pixel_values)
            
            # 손실 계산 (모든 머리의 오답 노트를 합침)
            total_loss = 0
            for col, logits in logits_dict.items():
                labels = batch[f'label_{col}'].to(device)
                total_loss += loss_fn(logits, labels)
            
            # 역전파 (Backward pass)
            optimizer.zero_grad()
            total_loss.backward()
            optimizer.step()
    
    # --- 6. 훈련이 끝나면, 무조건 모델을 저장! ---
    print(f"\n훈련이 완료되었습니다. '{CATEGORY}' 전문가 모델을 직접 저장합니다...")
    os.makedirs(OUTPUT_DIR, exist_ok=True) # 저장 폴더 생성
    
    # 모델의 '두뇌(가중치)' 저장
    torch.save(model.state_dict(), os.path.join(OUTPUT_DIR, 'pytorch_model.bin'))
    
    # 라벨 정보 저장
    torch.save(dataset.label_maps, os.path.join(OUTPUT_DIR, 'label_maps.pth'))
    
    # Hugging Face 형식에 맞는 config.json 파일도 저장 (호환성을 위해)
    model.body.config.save_pretrained(OUTPUT_DIR)

    print(f"최종 모델 저장이 완료되었습니다! '{OUTPUT_DIR}' 폴더에 'pytorch_model.bin' 파일이 생성되었습니다.")