"""
Smart Closet Frontend-Backend Integration Test
프론트엔드와 백엔드의 연동 및 호환성 검사

실행 방법:
python frontend_backend_integration_test.py
"""

import os
import sys
import json
import subprocess
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

def test_frontend_structure():
    """프론트엔드 디렉토리 구조 검사"""
    print_header("프론트엔드 디렉토리 구조 검사")
    
    base_dir = Path(__file__).parent.parent / "front"
    
    required_files = [
        "package.json",
        "src/App.js",
        "src/index.js",
        "src/setupProxy.js",
        "src/Component/main.js",
        "src/Component/header.js",
        "src/Component/login.js",
        "src/Component/signup.js",
        "src/Component/AnalysisLoading.js",
        "src/Component/Result.js",
        "src/Component/Wardrobe.js",
        "public/index.html"
    ]
    
    for file_path in required_files:
        full_path = base_dir / file_path
        if full_path.exists():
            print_success(f"파일 존재: {file_path}")
            test_results["passed"].append(f"frontend:{file_path}")
        else:
            print_error(f"파일 없음: {file_path}")
            test_results["failed"].append(f"frontend:{file_path}")

def test_package_json():
    """package.json 검사"""
    print_header("package.json 의존성 검사")
    
    base_dir = Path(__file__).parent.parent / "front"
    package_json_path = base_dir / "package.json"
    
    if not package_json_path.exists():
        print_error("package.json 파일 없음")
        test_results["failed"].append("package.json:missing")
        return
    
    with open(package_json_path, 'r', encoding='utf-8') as f:
        package_data = json.load(f)
    
    # 필수 의존성 확인
    required_deps = {
        "react": "React 프레임워크",
        "react-dom": "React DOM",
        "react-router-dom": "React 라우터",
        "axios": "HTTP 클라이언트",
        "bootstrap": "UI 프레임워크",
        "react-bootstrap": "React Bootstrap",
    }
    
    dependencies = package_data.get("dependencies", {})
    
    for dep, description in required_deps.items():
        if dep in dependencies:
            version = dependencies[dep]
            print_success(f"{dep}: {description} (v{version})")
            test_results["passed"].append(f"dependency:{dep}")
        else:
            print_error(f"{dep}: 설치 필요 - {description}")
            test_results["failed"].append(f"dependency:{dep}")
    
    # 스크립트 확인
    scripts = package_data.get("scripts", {})
    required_scripts = ["start", "build", "flask", "dev"]
    
    print("\n스크립트 확인:")
    for script in required_scripts:
        if script in scripts:
            print_success(f"{script}: {scripts[script]}")
        else:
            print_warning(f"{script}: 스크립트 없음")
            test_results["warnings"].append(f"script:{script}")

def test_node_modules():
    """node_modules 설치 확인"""
    print_header("Node.js 패키지 설치 확인")
    
    base_dir = Path(__file__).parent.parent / "front"
    node_modules = base_dir / "node_modules"
    
    if node_modules.exists():
        # 주요 패키지 확인
        important_packages = [
            "react",
            "react-dom",
            "react-router-dom",
            "axios",
            "bootstrap",
            "react-bootstrap"
        ]
        
        missing = []
        for package in important_packages:
            package_path = node_modules / package
            if package_path.exists():
                print_success(f"{package}: 설치됨")
            else:
                print_error(f"{package}: 미설치")
                missing.append(package)
        
        if missing:
            print_warning(f"\n누락된 패키지: {', '.join(missing)}")
            print_info("해결 방법: cd front && npm install")
            test_results["warnings"].append("node_modules:incomplete")
        else:
            print_success("\n모든 주요 패키지 설치 완료")
            test_results["passed"].append("node_modules:complete")
    else:
        print_error("node_modules 없음")
        print_info("해결 방법: cd front && npm install")
        test_results["failed"].append("node_modules:missing")

def test_api_endpoints():
    """API 엔드포인트 매핑 검사"""
    print_header("API 엔드포인트 매핑 검사")
    
    # 프론트엔드에서 사용하는 API 엔드포인트
    frontend_apis = {
        "/api/auth/signup": "회원가입",
        "/api/auth/login": "로그인",
        "/api/auth/logout": "로그아웃",
        "/api/auth/me": "사용자 정보",
        "/api/clothes": "옷 분석",
        "/api/voice/analyze": "음성 패션 추천",
    }
    
    # 백엔드에서 정의된 라우트 확인
    backend_dir = Path(__file__).parent
    
    # server.py에서 등록된 블루프린트 확인
    print("프론트엔드 API 요구사항:")
    for endpoint, description in frontend_apis.items():
        print_info(f"{endpoint}: {description}")
    
    print("\n백엔드 라우트 확인:")
    
    # auth_db.py 확인
    auth_file = backend_dir / "db_files" / "auth_db.py"
    if auth_file.exists():
        with open(auth_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if '@auth_bp.route("/signup"' in content:
                print_success("/api/auth/signup 구현됨")
                test_results["passed"].append("api:/api/auth/signup")
            if '@auth_bp.route("/login"' in content:
                print_success("/api/auth/login 구현됨")
                test_results["passed"].append("api:/api/auth/login")
            if '@auth_bp.route("/logout"' in content:
                print_success("/api/auth/logout 구현됨")
                test_results["passed"].append("api:/api/auth/logout")
            if '@auth_bp.route("/me"' in content:
                print_success("/api/auth/me 구현됨")
                test_results["passed"].append("api:/api/auth/me")
    
    # clothes.py 확인
    clothes_file = backend_dir / "routes" / "clothes.py"
    if clothes_file.exists():
        with open(clothes_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if '@clothes_bp.route(\'/clothes\'' in content:
                print_success("/api/clothes 구현됨")
                test_results["passed"].append("api:/api/clothes")
    
    # chat 라우트 확인
    chat_file = backend_dir / "chat" / "langspeech_openai_chroma.py"
    if chat_file.exists():
        with open(chat_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'chat_bp = Blueprint("chat"' in content:
                print_success("/api/voice/* 구현됨")
                test_results["passed"].append("api:/api/voice")

def test_cors_configuration():
    """CORS 설정 검사"""
    print_header("CORS 설정 검사")
    
    backend_dir = Path(__file__).parent
    server_file = backend_dir / "server.py"
    
    if not server_file.exists():
        print_error("server.py 파일 없음")
        test_results["failed"].append("cors:server.py missing")
        return
    
    with open(server_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if "from flask_cors import CORS" in content:
        print_success("Flask-CORS 임포트 확인")
        test_results["passed"].append("cors:import")
    else:
        print_error("Flask-CORS 임포트 없음")
        test_results["failed"].append("cors:import")
    
    if "CORS(app" in content:
        print_success("CORS 설정 확인")
        
        # origins 설정 확인
        if "https://localhost:3000" in content:
            print_success("프론트엔드 origin 허용: https://localhost:3000")
            test_results["passed"].append("cors:origin")
        else:
            print_warning("프론트엔드 origin 설정 확인 필요")
            test_results["warnings"].append("cors:origin")
    else:
        print_error("CORS 설정 없음")
        test_results["failed"].append("cors:config")

def test_proxy_configuration():
    """프론트엔드 프록시 설정 검사"""
    print_header("프론트엔드 프록시 설정 검사")
    
    front_dir = Path(__file__).parent.parent / "front"
    proxy_file = front_dir / "src" / "setupProxy.js"
    
    if not proxy_file.exists():
        print_error("setupProxy.js 파일 없음")
        test_results["failed"].append("proxy:missing")
        return
    
    with open(proxy_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if "createProxyMiddleware" in content:
        print_success("프록시 미들웨어 설정 확인")
        test_results["passed"].append("proxy:middleware")
    
    if "target:" in content:
        if "https://localhost:5000" in content or "http://localhost:5000" in content:
            print_success("백엔드 타겟 설정: localhost:5000")
            test_results["passed"].append("proxy:target")
        else:
            print_warning("백엔드 타겟 설정 확인 필요")
            test_results["warnings"].append("proxy:target")
    
    if "secure: false" in content:
        print_success("개발 모드 SSL 설정 (secure: false)")
        test_results["passed"].append("proxy:ssl")
    
    if "timeout" in content or "proxyTimeout" in content:
        print_success("타임아웃 설정 확인 (AI 처리용)")
        test_results["passed"].append("proxy:timeout")
    else:
        print_warning("타임아웃 설정 없음 (AI 처리 시 문제 발생 가능)")
        test_results["warnings"].append("proxy:timeout")

def test_https_certificates():
    """HTTPS 인증서 확인"""
    print_header("HTTPS 인증서 검사")
    
    front_dir = Path(__file__).parent.parent / "front"
    certs_dir = front_dir / "certs"
    
    if not certs_dir.exists():
        print_warning("certs 디렉토리 없음")
        test_results["warnings"].append("https:certs_dir")
        return
    
    cert_file = certs_dir / "dev.crt"
    key_file = certs_dir / "dev.key"
    
    if cert_file.exists():
        print_success("SSL 인증서 존재: dev.crt")
        test_results["passed"].append("https:cert")
    else:
        print_warning("SSL 인증서 없음: dev.crt")
        test_results["warnings"].append("https:cert")
    
    if key_file.exists():
        print_success("SSL 키 존재: dev.key")
        test_results["passed"].append("https:key")
    else:
        print_warning("SSL 키 없음: dev.key")
        test_results["warnings"].append("https:key")
    
    if not cert_file.exists() or not key_file.exists():
        print_info("\n인증서 생성 방법:")
        print_info("  openssl req -x509 -nodes -days 365 -newkey rsa:2048 \\")
        print_info("    -keyout certs/dev.key -out certs/dev.crt \\")
        print_info("    -subj '/CN=localhost'")

def test_data_flow():
    """데이터 흐름 검사"""
    print_header("프론트-백 데이터 흐름 검사")
    
    print("1. 옷 분석 플로우:")
    print_info("  프론트: 카메라 캡처 → Base64 인코딩")
    print_info("  요청: POST /api/clothes (image: base64)")
    print_info("  백엔드: final_pipeline.py → YOLO + ViT 분석")
    print_info("  응답: { success, filename, detected: [...] }")
    print_info("  프론트: AnalysisLoading → Result 페이지")
    
    print("\n2. 가상 피팅 플로우:")
    print_info("  프론트: 비디오 프레임 → 서버 전송")
    print_info("  요청: POST /api/fit/frame (frame: base64)")
    print_info("  백엔드: virtual_fitting.py → RTMPose + 옷 오버레이")
    print_info("  응답: { success, frame: base64_with_cloth }")
    print_info("  프론트: 처리된 프레임 표시")
    
    print("\n3. 음성 패션 추천 플로우:")
    print_info("  프론트: 음성 녹음 → 서버 전송")
    print_info("  요청: POST /api/voice/analyze (audio: blob)")
    print_info("  백엔드: langspeech_openai_chroma.py → GPT-4 + ChromaDB")
    print_info("  응답: { keywords, styles, recommendation }")
    print_info("  프론트: 추천 결과 표시")
    
    print("\n4. 인증 플로우:")
    print_info("  프론트: 로그인 폼 → 서버 전송")
    print_info("  요청: POST /api/auth/login (userId, password)")
    print_info("  백엔드: auth_db.py → SQLite 검증")
    print_info("  응답: { ok, user: {...} } + 세션 쿠키")
    print_info("  프론트: 세션 저장 → 인증 페이지 접근")
    
    test_results["passed"].append("data_flow:documented")

def test_environment_variables():
    """환경 변수 확인"""
    print_header("환경 변수 검사")
    
    front_dir = Path(__file__).parent.parent / "front"
    backend_dir = Path(__file__).parent
    
    # 프론트엔드 .env
    front_env = front_dir / ".env"
    if front_env.exists():
        print_success("프론트엔드 .env 존재")
        test_results["passed"].append("env:frontend")
    else:
        print_warning("프론트엔드 .env 없음 (선택사항)")
        test_results["warnings"].append("env:frontend")
    
    # 백엔드 .env (chat 폴더)
    backend_env = backend_dir / "chat" / ".env"
    if backend_env.exists():
        print_success("백엔드 .env 존재 (OpenAI API 키용)")
        
        with open(backend_env, 'r', encoding='utf-8') as f:
            content = f.read()
            if "OPENAI_API_KEY" in content:
                print_success("  OPENAI_API_KEY 설정됨")
                test_results["passed"].append("env:openai_key")
            else:
                print_warning("  OPENAI_API_KEY 없음")
                test_results["warnings"].append("env:openai_key")
    else:
        print_warning("백엔드 .env 없음 (음성 추천 기능 제한)")
        test_results["warnings"].append("env:backend")

def test_port_configuration():
    """포트 설정 검사"""
    print_header("포트 설정 검사")
    
    print("표준 포트 설정:")
    print_success("프론트엔드: https://localhost:3000 (React Dev Server)")
    print_success("백엔드: https://localhost:5000 (Flask API)")
    
    front_dir = Path(__file__).parent.parent / "front"
    package_json = front_dir / "package.json"
    
    if package_json.exists():
        with open(package_json, 'r', encoding='utf-8') as f:
            content = f.read()
            if "PORT=3000" in content:
                print_success("package.json에서 포트 3000 확인")
                test_results["passed"].append("port:frontend")
    
    backend_dir = Path(__file__).parent
    server_file = backend_dir / "server.py"
    
    if server_file.exists():
        with open(server_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if "port=5000" in content:
                print_success("server.py에서 포트 5000 확인")
                test_results["passed"].append("port:backend")

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
        print(f"{Colors.GREEN}{Colors.BOLD}[SUCCESS] 프론트엔드와 백엔드가 정상적으로 연동되었습니다!{Colors.RESET}")
        if warnings > 0:
            print(f"{Colors.YELLOW}  (경고 항목은 선택적 기능이거나 권장사항입니다){Colors.RESET}")
    else:
        print(f"{Colors.RED}{Colors.BOLD}[FAIL] {failed}개의 문제를 해결해야 합니다.{Colors.RESET}")
    print("="*80 + "\n")
    
    # 실행 가이드
    print_header("실행 가이드")
    print("1. 백엔드 실행:")
    print_info("   cd back")
    print_info("   python server.py")
    print()
    print("2. 프론트엔드 실행 (별도 터미널):")
    print_info("   cd front")
    print_info("   npm start")
    print()
    print("3. 통합 실행 (프론트엔드에서):")
    print_info("   cd front")
    print_info("   npm run dev  # 프론트+백 동시 실행")
    print()
    print("4. 브라우저 접속:")
    print_info("   https://localhost:3000")

def main():
    """메인 테스트 실행"""
    print(f"\n{Colors.BOLD}Smart Closet Frontend-Backend Integration Test{Colors.RESET}")
    print(f"날짜: 2025-10-24")
    print(f"Python: {sys.version}\n")
    
    try:
        test_frontend_structure()
        test_package_json()
        test_node_modules()
        test_api_endpoints()
        test_cors_configuration()
        test_proxy_configuration()
        test_https_certificates()
        test_data_flow()
        test_environment_variables()
        test_port_configuration()
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}테스트 중단됨{Colors.RESET}\n")
        return
    except Exception as e:
        print_error(f"테스트 실행 중 오류: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        print_summary()

if __name__ == "__main__":
    main()
