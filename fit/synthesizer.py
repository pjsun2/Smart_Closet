# 파일명: synthesizer.py

from diffusers import StableDiffusionControlNetPipeline, ControlNetModel, UniPCMultistepScheduler
import torch
from PIL import Image

def synthesize_final_image(pose_image, warped_cloth_image, output_filename):
    """디퓨전 모델을 사용하여 최종 이미지를 합성하고 파일로 저장한다."""
    print("🚀 4단계 시작: 최종 이미지 합성 (GPU 사용)")

    # 경량화된 모델 또는 표준 모델 로드
    base_model_path = "runwayml/stable-diffusion-v1-5"
    controlnet_path = "lllyasviel/sd-controlnet-openpose"

    controlnet = ControlNetModel.from_pretrained(controlnet_path, torch_dtype=torch.float16)
    pipe = StableDiffusionControlNetPipeline.from_pretrained(
        base_model_path,
        controlnet=controlnet,
        torch_dtype=torch.float16,
        safety_checker=None # 안전 검사기 비활성화 (선택 사항)
    ).to("cuda")

    # 속도 향상을 위한 Scheduler 설정
    pipe.scheduler = UniPCMultistepScheduler.from_config(pipe.scheduler.config)

    # (선택) xformers를 통한 메모리 최적화
    # pipe.enable_xformers_memory_efficient_attention()

    # PIL Image로 변환
    pose_pil = Image.fromarray(pose_image)
    
    prompt = "a person is wearing a new stylish t-shirt, photorealistic, high quality, full body shot"
    negative_prompt = "bad anatomy, ugly, deformed, malformed, worst quality, low quality"

    # 이미지 생성
    generator = torch.Generator(device="cuda").manual_seed(42) # 결과 재현을 위한 시드 설정
    result_image = pipe(
        prompt,
        negative_prompt=negative_prompt,
        image=pose_pil,
        num_inference_steps=20,
        generator=generator
    ).images[0]
    
    result_image.save(output_filename)
    print(f"✅ 4단계 완료: 최종 이미지가 '{output_filename}'으로 저장되었습니다.")