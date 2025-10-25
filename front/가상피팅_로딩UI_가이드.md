# 가상 피팅 로딩 UI 통합 가이드

## 개요
"입어보기" 버튼 클릭 시 모델 실행 과정을 직관적으로 표현하는 로딩 UI 구현

## 구현된 기능

### 1. VirtualFittingLoader 컴포넌트
**파일**: `front/src/Component/VirtualFittingLoader.js`

**주요 기능**:
- 실시간 로딩 상태 표시
- 단계별 진행 상황 체크리스트
- 진행률 프로그레스 바
- 현재 설정 (스켈레톤, 변형 모드) 표시
- 애니메이션 효과

**Props**:
```javascript
{
    isLoading: boolean,        // 로딩 중 여부
    stage: string,             // 현재 단계
    progress: number,          // 진행률 (0-100)
    message: string,           // 커스텀 메시지
    showSkeleton: boolean,     // 스켈레톤 표시 여부
    useWarp: boolean          // 관절 매칭 모드 여부
}
```

**단계 (stage)**:
- `'initializing'` - 모델 초기화 중
- `'loading_pose'` - RTMPose 모델 로딩 중
- `'loading_cloth'` - 옷 이미지 처리 중
- `'detecting_pose'` - 신체 포즈 감지 중
- `'warping'` - 옷 변형 처리 중
- `'overlaying'` - 가상 피팅 적용 중
- `'ready'` - 준비 완료

### 2. CSS 스타일
**파일**: `front/src/Component/VirtualFittingLoader.css`

**특징**:
- 그라디언트 배경
- 블러 효과 오버레이
- 펄스 애니메이션 스피너
- 부드러운 페이드인/슬라이드업 효과
- 반응형 디자인

## main.js 통합 방법

### 1단계: Import 추가

```javascript
// main.js 상단에 추가
import VirtualFittingLoader from './VirtualFittingLoader';
```

### 2단계: 상태 변수 추가

```javascript
function Main() {
    // 기존 상태들...
    
    // 로딩 상태 추가
    const [fittingLoading, setFittingLoading] = useState(false);
    const [fittingStage, setFittingStage] = useState('initializing');
    const [fittingProgress, setFittingProgress] = useState(0);
    
    // ... 나머지 코드
}
```

### 3단계: startVirtualFitting 함수 수정

```javascript
const startVirtualFitting = async () => {
    console.log("[프론트] 가상 피팅 시작");
    
    // 로딩 시작
    setFittingLoading(true);
    setFittingStage('initializing');
    setFittingProgress(10);
    
    try {
        // 단계별 진행
        setFittingStage('loading_pose');
        setFittingProgress(30);
        await new Promise(resolve => setTimeout(resolve, 500));
        
        setFittingStage('loading_cloth');
        setFittingProgress(50);
        await new Promise(resolve => setTimeout(resolve, 500));
        
        setFittingStage('detecting_pose');
        setFittingProgress(70);
        await new Promise(resolve => setTimeout(resolve, 500));
        
        setFittingStage('ready');
        setFittingProgress(100);
        await new Promise(resolve => setTimeout(resolve, 300));
        
        // 로딩 완료 후 피팅 모드 활성화
        setIsFittingMode(true);
        
        // 실시간 프레임 전송 시작
        fittingIntervalRef.current = setInterval(() => {
            sendFittingFrame();
        }, 200);
        
    } catch (error) {
        console.error("[프론트] 가상 피팅 시작 실패:", error);
        alert("가상 피팅 시작에 실패했습니다: " + error.message);
    } finally {
        // 로딩 종료
        setFittingLoading(false);
    }
};
```

### 4단계: JSX에 로더 추가

```javascript
return (
    <Container fluid className="main-container">
        {/* 기존 코드... */}
        
        {/* 가상 피팅 로더 오버레이 */}
        <VirtualFittingLoader
            isLoading={fittingLoading}
            stage={fittingStage}
            progress={fittingProgress}
            showSkeleton={showSkeleton}
            useWarp={useWarp}
        />
        
        {/* 나머지 UI... */}
    </Container>
);
```

## 백엔드 연동 (선택사항)

백엔드에서 실시간 진행 상황을 받으려면:

### clothes.py 수정

```python
@clothes_bp.route('/fit/status', methods=['GET'])
def get_fitting_status():
    """가상 피팅 진행 상황 반환"""
    vf = get_virtual_fitting()
    if vf is None:
        return jsonify({
            "stage": "error",
            "progress": 0,
            "message": "모델 로딩 실패"
        }), 500
    
    # 모델 상태 확인
    status = {
        "stage": "ready" if vf.model else "loading_pose",
        "progress": 100 if vf.model else 50,
        "message": "준비 완료" if vf.model else "모델 로딩 중"
    }
    
    return jsonify(status), 200
```

### main.js에서 상태 폴링

```javascript
const checkFittingStatus = async () => {
    try {
        const response = await fetch('/api/fit/status');
        const status = await response.json();
        
        setFittingStage(status.stage);
        setFittingProgress(status.progress);
        
        return status.stage === 'ready';
    } catch (error) {
        console.error("상태 확인 실패:", error);
        return false;
    }
};

const startVirtualFitting = async () => {
    setFittingLoading(true);
    
    // 상태 폴링
    const checkInterval = setInterval(async () => {
        const isReady = await checkFittingStatus();
        if (isReady) {
            clearInterval(checkInterval);
            setFittingLoading(false);
            setIsFittingMode(true);
            
            // 프레임 전송 시작
            fittingIntervalRef.current = setInterval(() => {
                sendFittingFrame();
            }, 200);
        }
    }, 500);
};
```

## 사용자 경험 개선 옵션

### 1. 첫 프레임 수신 시 로딩 종료

```javascript
const sendFittingFrame = async () => {
    // ... 기존 코드 ...
    
    if (result.success && result.frame) {
        setFittingFrame(result.frame);
        
        // 첫 프레임 수신 시 로딩 종료
        if (fittingLoading) {
            setFittingLoading(false);
        }
    }
};
```

### 2. 에러 발생 시 로딩 메시지 표시

```javascript
const [fittingError, setFittingError] = useState(null);

// VirtualFittingLoader에 error prop 추가
<VirtualFittingLoader
    isLoading={fittingLoading}
    stage={fittingStage}
    progress={fittingProgress}
    error={fittingError}  // 추가
    showSkeleton={showSkeleton}
    useWarp={useWarp}
/>
```

### 3. 취소 버튼 추가

VirtualFittingLoader.js에 추가:
```javascript
<Button 
    variant="outline-light" 
    onClick={onCancel}
    className="loader-cancel-btn"
>
    취소
</Button>
```

## 시각적 효과 추가 옵션

### 1. 파티클 효과
```css
.particle {
    position: absolute;
    width: 4px;
    height: 4px;
    background: white;
    border-radius: 50%;
    animation: float 3s ease-in-out infinite;
}
```

### 2. 3D 회전 효과
```css
.loader-spinner {
    transform-style: preserve-3d;
    animation: rotate3d 2s linear infinite;
}

@keyframes rotate3d {
    from { transform: rotateY(0deg); }
    to { transform: rotateY(360deg); }
}
```

### 3. 리플 효과
```css
.spinner-ripple {
    position: absolute;
    border: 2px solid white;
    border-radius: 50%;
    animation: ripple 1.5s ease-out infinite;
}

@keyframes ripple {
    from {
        width: 0;
        height: 0;
        opacity: 1;
    }
    to {
        width: 150px;
        height: 150px;
        opacity: 0;
    }
}
```

## 테스트

1. 프론트엔드 실행: `npm start`
2. "입어보기" 버튼 클릭
3. 로딩 UI 확인
4. 각 단계별 진행 확인
5. 완료 후 실시간 피팅 작동 확인

---

**작성일**: 2025-10-24
**파일**: VirtualFittingLoader.js, VirtualFittingLoader.css
**통합**: main.js
