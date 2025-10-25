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

    // DB에서 옷 목록 조회 (시뮬레이션)
    useEffect(() => {
        fetchClothes();
    }, []);

    const fetchClothes = async () => {
        try {
            setLoading(true);
            
            // 목업 데이터 (DB에서 가져온 것처럼)
            const mockClothes = [
                {
                    id: 1,
                    main_category: "상의",
                    details: {
                        색상: "파란색",
                        소재: "면",
                        스타일: "캐주얼"
                    },
                    created_at: "2025-10-15",
                    image_url: "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400&h=500&fit=crop"
                },
                {
                    id: 2,
                    main_category: "하의",
                    details: {
                        색상: "검은색",
                        소재: "데님",
                        스타일: "캐주얼"
                    },
                    created_at: "2025-10-16",
                    image_url: "https://via.placeholder.com/300x400?text=검은+하의"  // ✅ 추가
                },
                {
                    id: 3,
                    main_category: "아우터",
                    details: {
                        색상: "회색",
                        소재: "울",
                        스타일: "포멀"
                    },
                    created_at: "2025-10-14",
                    image_url: "https://via.placeholder.com/300x400?text=회색+아우터"  // ✅ 추가
                },
                {
                    id: 4,
                    main_category: "상의",
                    details: {
                        색상: "흰색",
                        소재: "면",
                        스타일: "미니멀"
                    },
                    created_at: "2025-10-13",
                    image_url: "https://via.placeholder.com/300x400?text=흰색+상의"  // ✅ 추가
                },
                {
                    id: 5,
                    main_category: "원피스",
                    details: {
                        색상: "빨간색",
                        소재: "실크",
                        스타일: "포멀"
                    },
                    created_at: "2025-10-12",
                    image_url: "https://via.placeholder.com/300x400?text=빨간+원피스"  // ✅ 추가
                },
                {
                    id: 6,
                    main_category: "하의",
                    details: {
                        색상: "카키색",
                        소재: "면",
                        스타일: "캐주얼"
                    },
                    created_at: "2025-10-11",
                    image_url: "https://via.placeholder.com/300x400?text=카키색+하의"  // ✅ 추가
                }
            ];
            
            // 실제 DB 연동 (나중에 이 부분 교체)
            // const res = await fetch('/api/wardrobe');
            // const data = await res.json();
            // setClothes(data.clothes || []);
            
            setClothes(mockClothes);
            console.log('[프론트] 옷장 데이터:', mockClothes);
        } catch (e) {
            console.error('에러:', e);
        } finally {
            setLoading(false);
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
                          (item.details?.색상 || '').includes(searchTerm);
        return matchCategory && matchSearch;
    });

    const deleteClothing = async (id) => {
        if (window.confirm('정말 삭제하시겠습니까?')) {
            try {
                // 실제 DB 삭제 (나중에 활성화)
                // const res = await fetch(`/api/clothes/${id}`, { method: 'DELETE' });
                
                // 목업: 배열에서 제거
                setClothes(clothes.filter(item => item.id !== id));
                alert('삭제되었습니다');
            } catch (e) {
                console.error('삭제 실패:', e);
            }
        }
    };

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
                                {/* ✅ 이미지 표시 */}
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
                                        >
                                            삭제
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