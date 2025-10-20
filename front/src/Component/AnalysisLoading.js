import { useLocation, useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { Spinner, Container } from 'react-bootstrap';

function AnalysisLoading() {
    const location = useLocation();
    const navigate = useNavigate();
    const [progress, setProgress] = useState(0);
    const [error, setError] = useState(null);

    useEffect(() => {
        const base64Image = location.state?.image;
        const filename = location.state?.filename;
        
        if (!base64Image) {
            navigate('/');
            return;
        }
        
        // ✅ 분석 시작
        performAnalysis(base64Image, filename);
        
    }, [location, navigate]);

    const performAnalysis = async (base64Image, filename) => {
        try {
            setProgress(10);
            console.log("[프론트] 분석 시작: " + filename);
            
            // ✅ 백엔드에 이미지 전송하여 분석 실행
            const res = await fetch("/api/clothes", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    image: base64Image,
                }),
            });

            setProgress(50);
            console.log(`[프론트] 서버 응답 상태: ${res.status}`);

            if (!res.ok) {
                throw new Error(`분석 실패: ${res.status}`);
            }

            const json = await res.json();
            console.log(`[프론트] 분석 완료:`, json);

            // ✅ 감지된 옷이 없는 경우 처리
            if (!json.detected || json.detected.length === 0) {
                alert("❌ 옷을 감지하지 못했습니다.\n옷 사진을 다시 선택해주세요.");
                navigate('/');
                return;
            }

            setProgress(100);

            // ✅ 분석 완료 후 Result 페이지로 이동
            setTimeout(() => {
                navigate('/result', { 
                    state: { 
                        detected: json.detected,
                        filename: json.filename
                    } 
                });
            }, 500);

        } catch (e) {
            console.error(`[프론트] 분석 에러:`, e);
            setError(e.message);
            setProgress(0);
        }
    };

    if (error) {
        return (
            <Container style={{ paddingTop: '80px', minHeight: '100vh' }}>
                <div className="text-center mt-5">
                    <h3>⚠️ 분석 실패</h3>
                    <p>{error}</p>
                    <button 
                        onClick={() => navigate('/')}
                        className="btn btn-primary mt-3"
                    >
                        홈으로 돌아가기
                    </button>
                </div>
            </Container>
        );
    }

    return (
        <Container className="d-flex justify-content-center align-items-center" style={{ height: '100vh', paddingTop: '80px' }}>
            <div className="text-center">
                <Spinner animation="border" role="status" className="mb-3">
                    <span className="visually-hidden">로딩 중...</span>
                </Spinner>
                <h3>🔍 옷 분석 중...</h3>
                <p>AI가 옷을 분석하고 있습니다</p>
                <div className="progress mt-3" style={{ width: '300px' }}>
                    <div
                        className="progress-bar"
                        role="progressbar"
                        style={{ width: `${progress}%` }}
                    />
                </div>
                <p className="mt-2">{Math.round(progress)}%</p>
            </div>
        </Container>
    );
}

export default AnalysisLoading;