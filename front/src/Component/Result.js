import { useLocation, useNavigate } from 'react-router-dom';
import { Container, Button, Card, Row, Col } from 'react-bootstrap';
import './Result.css';

function Result() {
    const location = useLocation();
    const navigate = useNavigate();
    const detected = location.state?.detected;
    const image = location.state?.image;

    const getClothingIcon = (category) => {
        const icons = {
            '상의': '👕',
            '하의': '👖',
            '아우터': '🧥',
            '원피스': '👗'
        };
        return icons[category] || '👔';
    };

    const formatDetails = (details) => {
        return Object.entries(details).map(([key, value]) => {
            let displayValue = value;
            
            if (Array.isArray(value)) {
                displayValue = value[0]?.name ? `${value[0].name} (${(value[0].confidence * 100).toFixed(1)}%)` : value.join(', ');
            }
            
            return (
                <div key={key} className="detail-item">
                    <span className="detail-label">{key}:</span>
                    <span className="detail-value">{displayValue}</span>
                </div>
            );
        });
    };

    // 모델 결과를 DB 형식으로 변환
const convertToDbFormat = (clothingItem) => {
    const attributes = {};
    
    Object.entries(clothingItem.details).forEach(([key, value]) => {
        if (Array.isArray(value)) {
            // 스타일(확률이 있는 배열)인 경우 - Top 3로 변환
            if (key === '스타일' && value.length > 0) {
                value.slice(0, 3).forEach((item, index) => {
                    const rank = index + 1;
                    attributes[`추천 스타일 ${rank}순위`] = 
                        `${item.name} (확률: ${(item.confidence * 100).toFixed(2)}%)`;
                });
            } else {
                // 다른 배열 타입은 첫번째 값 사용
                attributes[key] = value[0]?.name || value.join(', ');
            }
        } else {
            // 일반 문자열/숫자 값
            attributes[key] = value;
        }
    });
    
    return attributes;
};

    // 옷장에 저장하는 함수
    const saveToWardrobe = async () => {
        try {
            console.log("[프론트] 옷장에 저장 시작");
            
            const userConfirm = window.confirm('옷장에 저장하시겠습니까?');
            
            if (!userConfirm) {
                console.log("[프론트] 저장 취소됨");
                return;
            }

            const saveButton = document.querySelector('button[variant="success"]');
            if (saveButton) saveButton.disabled = true;

            let successCount = 0;
            let failedCount = 0;

            for (let i = 0; i < detected.length; i++) {
                const clothingItem = detected[i];
                const attributes = convertToDbFormat(clothingItem);
                
                console.log(`[프론트] ${i + 1}번 옷 속성:`, attributes);

                try {
                    const res = await fetch('/api/clothing/save', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            user_id: 1,
                            image_url: image,
                            main_category: clothingItem.main_category,
                            sub_category: clothingItem.details.카테고리 || '기타',  // ← 수정
                            attributes: attributes
                        })
                    });

                    if (res.ok) {
                        const result = await res.json();
                        console.log(`[프론트] ${i + 1}번 옷 저장 성공:`, result);
                        successCount++;
                    } else {
                        const errorData = await res.json();
                        console.error(`[프론트] ${i + 1}번 옷 저장 실패:`, errorData);
                        failedCount++;
                    }
                } catch (err) {
                    console.error(`[프론트] ${i + 1}번 옷 저장 중 오류:`, err);
                    failedCount++;
                }
            }

            if (failedCount === 0) {
                alert(`모든 옷이 저장되었습니다! (${successCount}개)`);
                navigate('/wardrobe');
            } else if (successCount > 0) {
                const retry = window.confirm(
                    `${successCount}개 저장 성공, ${failedCount}개 저장 실패\n\n` +
                    `다시 시도하시겠습니까?`
                );
                if (retry) {
                    saveToWardrobe();
                } else {
                    navigate('/wardrobe');
                }
            } else {
                const retry = window.confirm(
                    `모든 옷 저장에 실패했습니다.\n\n` +
                    `다시 시도하시겠습니까?`
                );
                if (retry) {
                    saveToWardrobe();
                }
            }

            if (saveButton) saveButton.disabled = false;
            
        } catch (e) {
            console.error('저장 실패:', e);
            alert('저장 중 오류가 발생했습니다.');
            
            const retry = window.confirm('다시 시도하시겠습니까?');
            if (retry) {
                saveToWardrobe();
            }
        }
    };

    if (!detected || detected.length === 0) {
        return (
            <Container style={{ paddingTop: '80px', minHeight: '100vh' }}>
                <div className="text-center mt-5">
                    <h2>감지된 옷이 없습니다</h2>
                    <Button 
                        variant="primary" 
                        onClick={() => navigate('/')}
                        className="mt-3"
                    >
                        홈으로 돌아가기
                    </Button>
                </div>
            </Container>
        );
    }

    return (
        <Container style={{ paddingTop: '80px', paddingBottom: '40px', minHeight: '100vh' }}>
            <div className="result-header mb-5">
                <h1>옷 분석 완료!</h1>
                <p className="text-muted">총 {detected.length}개의 옷을 감지했습니다</p>
            </div>

            {/* 업로드된 이미지 표시 */}
            {image && (
                <Row className="mb-5">
                    <Col md={8} className="mx-auto">
                        <Card className="image-preview-card shadow-sm">
                            <Card.Body className="p-0">
                                <img 
                                    src={image}
                                    alt="업로드된 사진"
                                    style={{
                                        width: '100%',
                                        height: 'auto',
                                        maxHeight: '500px',
                                        objectFit: 'cover',
                                        borderRadius: '8px'
                                    }}
                                    onError={(e) => {
                                        console.error('이미지 로드 실패:', image);
                                        e.target.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="400" height="300"%3E%3Crect fill="%23f0f0f0" width="400" height="300"/%3E%3Ctext x="50%" y="50%" font-size="16" fill="%23999" text-anchor="middle" dy=".3em"%3E이미지를 불러올 수 없습니다%3C/text%3E%3C/svg%3E';
                                    }}
                                />
                            </Card.Body>
                        </Card>
                        <p className="text-center text-muted mt-3">📸 분석된 이미지</p>
                    </Col>
                </Row>
            )}

            {/* 옷 카드 목록 */}
            <h5 className="mb-4">감지된 옷 목록</h5>
            <Row className="g-4 mb-5">
                {detected.map((item, index) => (
                    <Col key={index} md={6} lg={4}>
                        <Card className="clothing-card h-100 shadow-sm">
                            <Card.Body>
                                <div className="category-header mb-3">
                                    <span className="clothing-icon">
                                        {getClothingIcon(item.main_category)}
                                    </span>
                                    <h5 className="category-name ms-2">
                                        {item.main_category}
                                    </h5>
                                </div>

                                <div className="details-section">
                                    {formatDetails(item.details)}
                                </div>
                            </Card.Body>
                        </Card>
                    </Col>
                ))}
            </Row>

            <div className="action-buttons d-flex justify-content-center gap-3 mt-5 flex-wrap">
                <Button 
                    variant="secondary" 
                    size="lg"
                    onClick={() => navigate('/')}
                    className="px-4"
                >
                    ← 홈으로 돌아가기
                </Button>
                <Button 
                    variant="success" 
                    size="lg"
                    onClick={saveToWardrobe}
                    className="px-4"
                >
                    옷장에 저장
                </Button>
                <Button 
                    variant="primary" 
                    size="lg"
                    onClick={() => navigate('/wardrobe')}
                    className="px-4"
                >
                    내 옷장 보기 →
                </Button>
            </div>
        </Container>
    );
}

export default Result;