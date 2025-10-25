import React from 'react';
import { Spinner, Alert, ProgressBar } from 'react-bootstrap';
import './VirtualFittingLoader.css';

/**
 * 가상 피팅 로딩 인디케이터 컴포넌트
 * 모델 실행 진행 상황을 시각적으로 표현
 */
const VirtualFittingLoader = ({ 
    isLoading, 
    stage, 
    progress, 
    message,
    showSkeleton,
    useWarp,
    onCancel
}) => {
    
    // 로딩 단계별 메시지
    const stageMessages = {
        'initializing': '모델 초기화 중...',
        'loading_pose': 'RTMPose 모델 로딩 중...',
        'loading_cloth': '옷 이미지 처리 중...',
        'detecting_pose': '신체 포즈 감지 중...',
        'warping': '옷 변형 처리 중...',
        'overlaying': '가상 피팅 적용 중...',
        'ready': '준비 완료!'
    };

    const currentMessage = message || stageMessages[stage] || '처리 중...';

    if (!isLoading) return null;

    return (
        <div className="virtual-fitting-loader-overlay">
            <div className="virtual-fitting-loader-container">
                
                {/* 메인 스피너 */}
                <div className="loader-spinner-wrapper">
                    <Spinner 
                        animation="border" 
                        variant="primary" 
                        className="loader-spinner"
                    />
                    <div className="spinner-glow"></div>
                </div>

                {/* 로딩 메시지 */}
                <h4 className="loader-title">가상 피팅 시작 중</h4>
                <p className="loader-message">{currentMessage}</p>

                {/* 진행률 바 */}
                {progress !== undefined && (
                    <div className="loader-progress">
                        <ProgressBar 
                            now={progress} 
                            label={`${progress}%`}
                            animated
                            variant="info"
                        />
                    </div>
                )}

                {/* 단계별 체크리스트 */}
                <div className="loader-checklist">
                    <ChecklistItem 
                        label="GPU 확인" 
                        isComplete={progress > 10} 
                        isCurrent={stage === 'initializing'} 
                    />
                    <ChecklistItem 
                        label="RTMPose 모델 로딩" 
                        isComplete={progress > 30} 
                        isCurrent={stage === 'loading_pose'} 
                    />
                    <ChecklistItem 
                        label="옷 이미지 준비" 
                        isComplete={progress > 50} 
                        isCurrent={stage === 'loading_cloth'} 
                    />
                    <ChecklistItem 
                        label="포즈 감지 시스템" 
                        isComplete={progress > 70} 
                        isCurrent={stage === 'detecting_pose'} 
                    />
                    <ChecklistItem 
                        label="실시간 처리 준비" 
                        isComplete={progress > 90} 
                        isCurrent={stage === 'ready'} 
                    />
                </div>

                {/* 설정 정보 */}
                <div className="loader-settings">
                    <span className={`setting-badge ${showSkeleton ? 'active' : ''}`}>
                        스켈레톤: {showSkeleton ? 'ON' : 'OFF'}
                    </span>
                    <span className={`setting-badge ${useWarp ? 'active' : ''}`}>
                        모드: {useWarp ? '관절 매칭' : '단순 크기'}
                    </span>
                </div>

                {/* 팁 */}
                <Alert variant="info" className="loader-tip">
                    <small>
                        최초 실행 시 1-2분 소요될 수 있습니다.<br/>
                        모델이 로딩되면 실시간으로 처리됩니다.
                    </small>
                </Alert>

                {/* 취소 버튼 */}
                {onCancel && (
                    <div className="loader-cancel-wrapper">
                        <button 
                            className="loader-cancel-btn"
                            onClick={onCancel}
                        >
                            취소
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};

/**
 * 체크리스트 아이템 컴포넌트
 */
const ChecklistItem = ({ label, isComplete, isCurrent }) => {
    return (
        <div className={`checklist-item ${isComplete ? 'complete' : ''} ${isCurrent ? 'current' : ''}`}>
            <div className="checklist-icon">
                {isComplete ? (
                    <span className="icon-check">✓</span>
                ) : isCurrent ? (
                    <Spinner animation="border" size="sm" />
                ) : (
                    <span className="icon-pending">○</span>
                )}
            </div>
            <span className="checklist-label">{label}</span>
        </div>
    );
};

export default VirtualFittingLoader;
