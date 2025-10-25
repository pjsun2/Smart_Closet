# Smart Closet 실행 가이드

## 🚀 빠른 시작

### 방법 1: GUI 런처 사용 (권장) ⭐

더블클릭으로 실행:
```
Smart_Closet_Launcher.pyw
```

GUI에서 버튼을 클릭하여 서버를 시작/중지할 수 있습니다.

### 방법 2: 배치 파일 사용

#### 통합 실행 (백엔드 + 프론트엔드)
```
start_all.bat 더블클릭
```

#### 개별 실행
- **백엔드만 실행**: `start_backend.bat` 더블클릭
- **프론트엔드만 실행**: `start_frontend.bat` 더블클릭

#### 서버 중지
```
stop_servers.bat 더블클릭
```

## 📁 실행 파일 설명

| 파일명 | 용도 |
|--------|------|
| `Smart_Closet_Launcher.pyw` | GUI 런처 (Python) |
| `start_all.bat` | 백엔드+프론트엔드 동시 시작 |
| `start_backend.bat` | 백엔드 서버만 시작 |
| `start_frontend.bat` | 프론트엔드 서버만 시작 |
| `stop_servers.bat` | 모든 서버 중지 |

## 🌐 접속 주소

- **프론트엔드 (사용자 인터페이스)**: https://localhost:3000
- **백엔드 (API 서버)**: https://localhost:5000

## ⚙️ 시스템 요구사항

### 백엔드
- Python 3.9.13
- 가상환경: `.venv309`
- CUDA 12.1 (GPU 사용 시)

### 프론트엔드
- Node.js (LTS 버전)
- npm
- `node_modules` 설치 완료

## 🔧 초기 설정 (최초 1회)

### 1. 프론트엔드 패키지 설치
```powershell
cd front
npm install
```

### 2. Python 가상환경 확인
```powershell
.venv309\Scripts\activate
python --version  # 3.9.13 확인
```

### 3. 환경 변수 설정
- `back/chat/.env`: OpenAI API 키
- `front/.env`: 프론트엔드 환경변수 (선택)

## 🐛 문제 해결

### 백엔드가 시작되지 않는 경우
1. 가상환경 경로 확인: `.venv309` 폴더 존재 확인
2. Python 버전 확인: `python --version`
3. 필요한 패키지 설치: `pip install -r requirements.txt`

### 프론트엔드가 시작되지 않는 경우
1. Node.js 설치 확인: `node --version`
2. npm 패키지 설치: `cd front && npm install`
3. 포트 3000 사용 중 확인: `netstat -ano | findstr :3000`

### 포트가 이미 사용 중인 경우
```powershell
# 포트 사용 프로세스 확인
netstat -ano | findstr :5000  # 백엔드
netstat -ano | findstr :3000  # 프론트엔드

# 프로세스 종료
taskkill /F /PID <프로세스ID>
```

### HTTPS 인증서 경고
브라우저에서 "안전하지 않음" 경고가 나타나면:
1. "고급" 클릭
2. "localhost로 이동" 클릭
(개발용 자체 서명 인증서이므로 안전함)

## 📊 기능 확인

### 백엔드 상태 확인
브라우저에서 접속: https://localhost:5000
- 서버가 정상 작동하면 응답이 표시됩니다.

### 프론트엔드 확인
브라우저에서 접속: https://localhost:3000
- React 앱이 로드되어야 합니다.

## 💡 사용 팁

1. **첫 실행**: `start_all.bat`으로 한 번에 시작
2. **개발 중**: 백엔드와 프론트엔드를 각각 실행하여 개별 로그 확인
3. **종료**: `stop_servers.bat` 또는 각 콘솔창에서 `Ctrl+C`

## 🎯 주요 기능

- 📸 웹캠을 통한 옷 촬영 및 AI 분석
- 🔍 YOLO 세그멘테이션 + ViT 분류
- 👔 실시간 가상 피팅 (RTMPose)
- 🎤 음성 패션 추천 (GPT-4 + ChromaDB)
- 👤 회원가입 및 로그인
- 💾 옷장 관리 (저장/조회)

## 📞 추가 도움말

- 통합 테스트 실행: `python back/frontend_backend_integration_test.py`
- 백엔드 테스트: `python back/integration_test.py`
- 로그 확인: 각 서버 콘솔 창 참조

---

**제작**: Smart Closet Team  
**업데이트**: 2025-10-24
