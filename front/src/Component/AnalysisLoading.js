import { useLocation, useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { Spinner, Container } from 'react-bootstrap';

function AnalysisLoading() {
    const location = useLocation();
    const navigate = useNavigate();
    const [progress, setProgress] = useState(0);
    const [error, setError] = useState(null);

    useEffect(() => {
        // ✅ 이미 분석된 결과를 받아옴 (다시 분석 안 함!)
        const { image, filename, result } = location.state ?? {};

        console.log("[AnalysisLoading] 데이터 수신:", { image: !!image, filename, result });

        if (!image || !result) {
            console.log("[AnalysisLoading] 데이터 없음 - 홈으로 이동");
            navigate('/');
            return;
        }

        // ✅ 진행률 애니메이션
        setProgress(30);

        // ✅ 분석 결과 확인
        if (!result.success || !result.detected?.length) {
            console.error("[AnalysisLoading] 분석 실패:", result.error);
            setError(result.error || "옷을 감지하지 못했습니다.");
            setProgress(0);
            return;
        }

        console.log("[AnalysisLoading] 분석 성공! 감지된 옷:", result.detected.length);

        // ✅ 500ms 후 Result 페이지로 이동
        const timer = setTimeout(() => {
            setProgress(100);
            console.log("[AnalysisLoading] Result 페이지로 이동");
            
            navigate('/result', {
                state: {
                    detected: result.detected,
                    filename,
                    image,
                    analysis: result.analysis,
                    backendPath: result.path
                }
            });
        }, 500);

        return () => clearTimeout(timer);
    }, [location, navigate]);

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