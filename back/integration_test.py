"""
Smart Closet Backend Integration & Compatibility Test
백엔드 시스템의 모든 모듈 연동 및 호환성 검사

실행 방법:
python integration_test.py
"""

import os
import sys
import importlib.util
import traceback
from pathlib import Path

# Windows 인코딩 문제 해결
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# 색상 출력용
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.RESET}\n")

def print_success(text):
    print(f"{Colors.GREEN}[OK] {text}{Colors.RESET}")

def print_error(text):
    print(f"{Colors.RED}[FAIL] {text}{Colors.RESET}")

def print_warning(text):
    print(f"{Colors.YELLOW}[WARNING] {text}{Colors.RESET}")

def print_info(text):
    print(f"{Colors.BLUE}[INFO] {text}{Colors.RESET}")

# 테스트 결과 저장
test_results = {
    "passed": [],
    "failed": [],
    "warnings": []
}

def test_import(module_name, file_path):
    """모듈 임포트 테스트"""
    try:
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        print_success(f"{module_name}: 임포트 성공")
        test_results["passed"].append(module_name)
        return True, module
    except Exception as e:
        print_error(f"{module_name}: 임포트 실패 - {str(e)}")
        test_results["failed"].append(f"{module_name}: {str(e)}")
        return False, None

def test_environment():
    """환경 변수 및 디렉토리 구조 테스트"""
    print_header("환경 설정 검사")
    
    base_dir = Path(__file__).parent
    
    # 필수 디렉토리 확인
    required_dirs = [
        "uploads/clothes",
        "instance",
        "chat",
        "clothes",
        "db_files",
        "fit",
        "models",
        "routes"
    ]
    
    for dir_path in required_dirs:
        full_path = base_dir / dir_path
        if full_path.exists():
            print_success(f"디렉토리 존재: {dir_path}")
        else:
            print_warning(f"디렉토리 없음: {dir_path} (자동 생성 가능)")
            test_results["warnings"].append(f"Missing directory: {dir_path}")
    
    # Python 버전 확인
    python_version = sys.version_info
    print_info(f"Python 버전: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version.major == 3 and python_version.minor >= 9:
        print_success("Python 버전 호환")
    else:
        print_warning("Python 3.9 이상 권장")

def test_core_dependencies():
    """핵심 라이브러리 의존성 테스트"""
    print_header("핵심 라이브러리 의존성 검사")
    
    dependencies = {
        "flask": "Flask 웹 프레임워크",
        "flask_cors": "CORS 지원",
        "flask_sqlalchemy": "데이터베이스 ORM",
        "torch": "PyTorch (AI 모델)",
        "torchvision": "PyTorch Vision",
        "cv2": "OpenCV (영상 처리)",
        "PIL": "이미지 처리",
        "numpy": "수치 연산",
        "ultralytics": "YOLO 모델",
        "transformers": "Hugging Face Transformers",
        "langchain_openai": "LangChain OpenAI 연동",
        "langchain_chroma": "ChromaDB 벡터 스토어",
        "speech_recognition": "음성 인식",
        "gtts": "텍스트 음성 변환",
        "mmcv": "MMPose 의존성",
        "mmpose": "포즈 추정",
        "rembg": "배경 제거"
    }
    
    for module_name, description in dependencies.items():
        try:
            if module_name == "cv2":
                import cv2
            elif module_name == "PIL":
                from PIL import Image
            else:
                __import__(module_name)
            print_success(f"{module_name}: {description}")
            test_results["passed"].append(f"dependency:{module_name}")
        except ImportError as e:
            print_error(f"{module_name}: 설치 필요 - {description}")
            test_results["failed"].append(f"dependency:{module_name}")

def test_gpu_availability():
    """GPU 가용성 테스트"""
    print_header("GPU 가용성 검사")
    
    try:
        import torch
        cuda_available = torch.cuda.is_available()
        
        if cuda_available:
            print_success(f"CUDA 사용 가능")
            print_info(f"  - CUDA 버전: {torch.version.cuda}")
            print_info(f"  - GPU 개수: {torch.cuda.device_count()}")
            for i in range(torch.cuda.device_count()):
                print_info(f"  - GPU {i}: {torch.cuda.get_device_name(i)}")
            test_results["passed"].append("GPU:CUDA")
        else:
            print_warning("CUDA 사용 불가 (CPU 모드로 실행됨)")
            test_results["warnings"].append("GPU:CUDA not available")
        
        # OpenCV CUDA 확인
        import cv2
        if cv2.cuda.getCudaEnabledDeviceCount() > 0:
            print_success("OpenCV CUDA 지원")
        else:
            print_warning("OpenCV CUDA 미지원")
            
    except Exception as e:
        print_error(f"GPU 검사 실패: {str(e)}")

def test_modules():
    """백엔드 모듈 임포트 테스트"""
    print_header("백엔드 모듈 연동 검사")
    
    base_dir = Path(__file__).parent
    
    # 주요 모듈 테스트
    modules = {
        "config": base_dir / "config.py",
        "db_": base_dir / "db_.py",
        "server": base_dir / "server.py",
    }
    
    for name, path in modules.items():
        if path.exists():
            test_import(name, str(path))
        else:
            print_error(f"{name}: 파일 없음 - {path}")
            test_results["failed"].append(f"{name}: file not found")

def test_routes():
    """라우트 모듈 테스트"""
    print_header("라우트 모듈 검사")
    
    base_dir = Path(__file__).parent / "routes"
    
    routes = [
        "users.py",
        "member_test.py",
        "clothes.py"
    ]
    
    for route_file in routes:
        path = base_dir / route_file
        if path.exists():
            module_name = route_file.replace(".py", "")
            test_import(f"routes.{module_name}", str(path))
        else:
            print_error(f"{route_file}: 파일 없음")

def test_db_files():
    """데이터베이스 파일 모듈 테스트"""
    print_header("데이터베이스 모듈 검사")
    
    base_dir = Path(__file__).parent / "db_files"
    
    db_modules = [
        "auth_db.py",
        "clothes_db.py",
        "init_db.py"
    ]
    
    for db_file in db_modules:
        path = base_dir / db_file
        if path.exists():
            module_name = db_file.replace(".py", "")
            test_import(f"db_files.{module_name}", str(path))
        else:
            print_error(f"{db_file}: 파일 없음")

def test_ai_modules():
    """AI 모듈 테스트"""
    print_header("AI 모듈 검사")
    
    base_dir = Path(__file__).parent
    
    # Clothes AI
    clothes_dir = base_dir / "clothes"
    if (clothes_dir / "final_pipeline.py").exists():
        success, module = test_import("final_pipeline", str(clothes_dir / "final_pipeline.py"))
        if success:
            print_info("  - YOLO 세그멘테이션")
            print_info("  - ViT 분류 모델")
            print_info("  - 전문가 모델 (상의/하의/아우터/원피스)")
    
    # Virtual Fitting
    fit_dir = base_dir / "fit"
    if (fit_dir / "virtual_fitting.py").exists():
        success, module = test_import("virtual_fitting", str(fit_dir / "virtual_fitting.py"))
        if success:
            print_info("  - RTMPose 포즈 추정")
            print_info("  - 실시간 가상 피팅")
    
    if (fit_dir / "cloth_processor.py").exists():
        success, module = test_import("cloth_processor", str(fit_dir / "cloth_processor.py"))
        if success:
            print_info("  - 배경 제거 (rembg)")
            print_info("  - 옷 변형 처리")
    
    # Chat AI
    chat_dir = base_dir / "chat"
    if (chat_dir / "langspeech_openai_chroma.py").exists():
        success, module = test_import("langspeech_openai", str(chat_dir / "langspeech_openai_chroma.py"))
        if success:
            print_info("  - 음성 인식")
            print_info("  - GPT-4 패션 추천")
            print_info("  - ChromaDB 벡터 검색")

def test_model_files():
    """AI 모델 파일 존재 확인"""
    print_header("AI 모델 파일 검사")
    
    base_dir = Path(__file__).parent
    
    model_paths = {
        "YOLO 세그멘테이션": base_dir / "clothes" / "runs" / "segment" / "train2" / "weights" / "best.pt",
        "라우터 모델": base_dir / "clothes" / "router_model",
        "상의 전문가": base_dir / "clothes" / "상의_specialist_model",
        "하의 전문가": base_dir / "clothes" / "하의_specialist_model",
        "아우터 전문가": base_dir / "clothes" / "아우터_specialist_model",
        "원피스 전문가": base_dir / "clothes" / "원피스_specialist_model",
        "RTMPose 설정": base_dir / "fit" / "models" / "rtmpose-s_8xb256-420e_aic-coco-256x192.py",
        "RTMPose 가중치": base_dir / "fit" / "models" / "rtmpose-s_simcc-aic-coco_pt-aic-coco_420e-256x192-fcb2599b_20230126.pth"
    }
    
    for name, path in model_paths.items():
        if path.exists():
            print_success(f"{name}: 존재")
            if path.is_file():
                size_mb = path.stat().st_size / (1024 * 1024)
                print_info(f"  크기: {size_mb:.1f} MB")
        else:
            print_warning(f"{name}: 없음 (모델 다운로드 필요)")
            test_results["warnings"].append(f"Model missing: {name}")

def test_database():
    """데이터베이스 연결 테스트"""
    print_header("데이터베이스 검사")
    
    base_dir = Path(__file__).parent
    db_path = base_dir / "db_files" / "smart_closet.db"
    
    if db_path.exists():
        print_success(f"SQLite DB 존재: {db_path}")
        
        try:
            import sqlite3
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # 테이블 확인
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            print_info(f"테이블 개수: {len(tables)}")
            for table in tables:
                print_info(f"  - {table[0]}")
            
            conn.close()
            print_success("데이터베이스 연결 성공")
            test_results["passed"].append("database:connection")
            
        except Exception as e:
            print_error(f"데이터베이스 연결 실패: {str(e)}")
            test_results["failed"].append(f"database: {str(e)}")
    else:
        print_warning("데이터베이스 파일 없음 (초기화 필요)")
        test_results["warnings"].append("database:not initialized")

def print_summary():
    """테스트 결과 요약"""
    print_header("테스트 결과 요약")
    
    total = len(test_results["passed"]) + len(test_results["failed"]) + len(test_results["warnings"])
    passed = len(test_results["passed"])
    failed = len(test_results["failed"])
    warnings = len(test_results["warnings"])
    
    print(f"\n총 테스트: {total}")
    print_success(f"성공: {passed}")
    print_error(f"실패: {failed}")
    print_warning(f"경고: {warnings}")
    
    if failed > 0:
        print(f"\n{Colors.RED}{Colors.BOLD}실패 항목:{Colors.RESET}")
        for item in test_results["failed"]:
            print(f"  - {item}")
    
    if warnings > 0:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}경고 항목:{Colors.RESET}")
        for item in test_results["warnings"]:
            print(f"  - {item}")
    
    # 최종 판정
    print("\n" + "="*80)
    if failed == 0:
        print(f"{Colors.GREEN}{Colors.BOLD}[SUCCESS] 모든 핵심 기능이 정상적으로 연동되었습니다!{Colors.RESET}")
        if warnings > 0:
            print(f"{Colors.YELLOW}  (경고 항목은 선택적 기능입니다){Colors.RESET}")
    else:
        print(f"{Colors.RED}{Colors.BOLD}[FAIL] {failed}개의 문제를 해결해야 합니다.{Colors.RESET}")
    print("="*80 + "\n")

def main():
    """메인 테스트 실행"""
    print(f"\n{Colors.BOLD}Smart Closet Backend Integration Test{Colors.RESET}")
    print(f"날짜: 2025-10-24")
    print(f"Python: {sys.version}\n")
    
    try:
        test_environment()
        test_core_dependencies()
        test_gpu_availability()
        test_modules()
        test_routes()
        test_db_files()
        test_ai_modules()
        test_model_files()
        test_database()
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}테스트 중단됨{Colors.RESET}\n")
        return
    except Exception as e:
        print_error(f"테스트 실행 중 오류: {str(e)}")
        traceback.print_exc()
    
    finally:
        print_summary()

if __name__ == "__main__":
    main()
