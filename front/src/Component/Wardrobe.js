import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Container, Row, Col, Card, Button, Form, Spinner, Alert } from 'react-bootstrap';
import './Wardrobe.css';

function Wardrobe() {
    const navigate = useNavigate();
    const [clothes, setClothes] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState('전체');
    const [searchTerm, setSearchTerm] = useState('');
    const [deletingId, setDeletingId] = useState(null);
    
    // 세션 확인 상태 추가
    const [isLoggedIn, setIsLoggedIn] = useState(false);
    const [isSessionChecked, setIsSessionChecked] = useState(false);

    // 페이지 로드 시 세션 확인
    useEffect(() => {
        const checkSession = async () => {
            try {
                const res = await fetch('/api/auth/me', {
                    credentials: 'include'
                });
                const data = await res.json();
                console.log('[프론트] 세션 확인:', data);
                
                if (data.authenticated) {
                    setIsLoggedIn(true);
                    // 세션 확인 후 옷 목록 조회
                    await fetchClothes();
                } else {
                    setIsLoggedIn(false);
                    setIsSessionChecked(true);
                    // ✅ 1초 후 Main 페이지로 이동
                    setTimeout(() => {
                        alert('로그인이 필요합니다.');
                        navigate('/');
                    }, 100);
                }
            } catch (error) {
                console.error('[프론트] 세션 확인 실패:', error);
                setIsLoggedIn(false);
                setIsSessionChecked(true);
                // ✅ 1초 후 Main 페이지로 이동
                setTimeout(() => {
                    alert('로그인이 필요합니다.');
                    navigate('/');
                }, 100);
            }
        };
        
        checkSession();
    }, [navigate]);

    // 세션의 사용자 옷만 조회
    const fetchClothes = async () => {
        try {
            setLoading(true);
            
            const res = await fetch('/api/clothing/wardrobe', {
                method: 'GET',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            console.log('[프론트] 응답 상태:', res.status);
            
            if (!res.ok) {
                if (res.status === 401) {
                    alert('세션이 만료되었습니다. 다시 로그인해주세요.');
                    navigate('/');
                    return;
                }
                throw new Error(`옷 목록 조회 실패: ${res.status}`);
            }
            
            const data = await res.json();
            console.log('[프론트] 옷장 데이터:', data);
            
            if (data.ok && data.clothing) {
                console.log('[프론트] clothing 배열:', data.clothing);
                setClothes(data.clothing);
            } else if (Array.isArray(data)) {
                console.log('[프론트] 배열 직접 반환');
                setClothes(data);
            } else if (data.clothes) {
                console.log('[프론트] clothes 배열:', data.clothes);
                setClothes(data.clothes);
            } else {
                console.warn('[프론트] 예상치 못한 응답 형식:', data);
                setClothes([]);
            }
            
        } catch (e) {
            console.error('[프론트] 에러:', e);
            alert('옷 목록을 불러올 수 없습니다: ' + e.message);
            setClothes([]);
        } finally {
            setLoading(false);
            setIsSessionChecked(true);
        }
    };

    const getClothingIcon = (category) => {
        const icons = {
            '상의': '[상의]',
            '하의': '[하의]',
            '아우터': '[아우터]',
            '원피스': '[원피스]'
        };
        return icons[category] || '[옷]';
    };

    // 필터링된 옷 목록
    const filteredClothes = clothes.filter(item => {
        const matchCategory = filter === '전체' || item.main_category === filter;
        const matchSearch = item.main_category.includes(searchTerm) || 
                          Object.values(item.details || {}).some(val => 
                              String(val).includes(searchTerm)
                          );
        return matchCategory && matchSearch;
    });

    const deleteClothing = async (id) => {
        if (!window.confirm('정말 삭제하시겠습니까?')) return;
        
        try {
            setDeletingId(id);
            
            const res = await fetch(`/api/clothing/${id}`, { 
                method: 'DELETE',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (!res.ok) {
                const errorData = await res.json();
                throw new Error(errorData.message || '삭제 실패');
            }
            
            // 목록에서 제거
            setClothes(clothes.filter(item => item.id !== id));
            alert('삭제되었습니다');
        } catch (e) {
            console.error('삭제 실패:', e);
            alert('삭제에 실패했습니다: ' + e.message);
        } finally {
            setDeletingId(null);
        }
    };

    // ✅ 세션 확인 중이면 로딩 표시
    if (!isSessionChecked) {
        return (
            <Container style={{ paddingTop: '80px', minHeight: '100vh' }}>
                <div className="text-center mt-5">
                    <Spinner animation="border" role="status">
                        <span className="visually-hidden">세션 확인 중...</span>
                    </Spinner>
                    <p className="mt-3">세션을 확인하는 중...</p>
                </div>
            </Container>
        );
    }

    // ✅ 로그인하지 않으면 빈 페이지 표시 (자동으로 Main으로 이동됨)
    if (!isLoggedIn) {
        return null;
    }

    if (loading) {
        return (
            <Container style={{ paddingTop: '80px', minHeight: '100vh' }}>
                <div className="text-center mt-5">
                    <Spinner animation="border" role="status">
                        <span className="visually-hidden">로딩 중...</span>
                    </Spinner>
                    <p className="mt-3">옷장을 불러오는 중...</p>
                </div>
            </Container>
        );
    }

    return (
        <Container style={{ paddingTop: '80px', paddingBottom: '40px', minHeight: '100vh' }}>
            {/* 헤더 */}
            <div className="wardrobe-header mb-4">
                <h1>내 옷장</h1>
                <p className="text-muted">총 {filteredClothes.length}개의 옷</p>
            </div>

            {/* 필터 및 검색 */}
            <Row className="mb-4">
                <Col md={6}>
                    <Form.Group>
                        <Form.Label>종류별 필터</Form.Label>
                        <Form.Select 
                            value={filter} 
                            onChange={(e) => setFilter(e.target.value)}
                        >
                            <option>전체</option>
                            <option>상의</option>
                            <option>하의</option>
                            <option>아우터</option>
                            <option>원피스</option>
                        </Form.Select>
                    </Form.Group>
                </Col>
                <Col md={6}>
                    <Form.Group>
                        <Form.Label>검색</Form.Label>
                        <Form.Control
                            type="text"
                            placeholder="색상, 종류 등으로 검색..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                    </Form.Group>
                </Col>
            </Row>

            {/* 옷 목록 */}
            {filteredClothes.length === 0 ? (
                <Alert variant="info" className="text-center mt-5">
                    <h5>옷이 없습니다</h5>
                    <p>옷 사진을 업로드해서 옷장을 채워보세요!</p>
                    <Button 
                        variant="primary"
                        onClick={() => navigate('/')}
                    >
                        옷 업로드하기
                    </Button>
                </Alert>
            ) : (
                <Row className="g-4 mb-5">
                    {filteredClothes.map((item, index) => (
                        <Col key={index} md={6} lg={4}>
                            <Card className="clothing-card h-100 shadow-sm">
                                {/* 이미지 표시 */}
                                <div className="image-container">
                                    <img 
                                        src={item.image_url} 
                                        alt={item.main_category}
                                        className="clothing-image"
                                        onError={(e) => {
                                            e.target.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="300" height="400"%3E%3Crect fill="%23f0f0f0" width="300" height="400"/%3E%3Ctext x="50%" y="50%" font-size="14" fill="%23999" text-anchor="middle" dy=".3em"%3E이미지 없음%3C/text%3E%3C/svg%3E';
                                        }}
                                    />
                                </div>

                                <Card.Body>
                                    {/* 카테고리 */}
                                    <div className="category-header mb-3">
                                        <span className="clothing-icon">
                                            {getClothingIcon(item.main_category)}
                                        </span>
                                        <h5 className="category-name ms-2">
                                            {item.main_category}
                                        </h5>
                                    </div>

                                    {/* 세부 정보 */}
                                    <div className="details-section">
                                        {item.details && Object.entries(item.details).map(([key, value]) => {
                                            return (
                                                <div key={key} className="detail-item">
                                                    <span className="detail-label">{key}:</span>
                                                    <span className="detail-value">{value}</span>
                                                </div>
                                            );
                                        })}
                                    </div>

                                    {/* 등록 날짜 */}
                                    <div className="date-section mt-3 pt-3 border-top">
                                        <small className="text-muted">
                                            등록: {item.created_at}
                                        </small>
                                    </div>

                                    {/* 액션 버튼 */}
                                    <div className="action-buttons mt-3 pt-3 border-top">
                                        <Button 
                                            variant="danger" 
                                            size="sm"
                                            className="w-100"
                                            onClick={() => deleteClothing(item.id)}
                                            disabled={deletingId === item.id}
                                        >
                                            {deletingId === item.id ? (
                                                <>
                                                    <Spinner animation="border" size="sm" role="status" className="me-2" />
                                                    삭제 중...
                                                </>
                                            ) : '삭제'}
                                        </Button>
                                    </div>
                                </Card.Body>
                            </Card>
                        </Col>
                    ))}
                </Row>
            )}

            {/* 돌아가기 버튼 */}
            <div className="text-center mt-5">
                <Button 
                    variant="secondary" 
                    size="lg"
                    onClick={() => navigate('/')}
                    className="px-4"
                >
                    ← 홈으로 돌아가기
                </Button>
            </div>
        </Container>
    );
}

export default Wardrobe;