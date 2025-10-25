import React from 'react';
import { Badge, Spinner } from 'react-bootstrap';
import './FittingStatusBadge.css';

/**
 * 간단한 인라인 상태 표시 배지
 * 버튼 위나 비디오 위에 표시
 */
const FittingStatusBadge = ({ 
    isActive, 
    isProcessing, 
    fps,
    latency 
}) => {
    
    if (!isActive && !isProcessing) return null;

    return (
        <div className="fitting-status-badge">
            {/* 상태 표시 */}
            <Badge 
                bg={isProcessing ? "warning" : "success"} 
                className="status-badge"
            >
                {isProcessing ? (
                    <>
                        <Spinner 
                            animation="border" 
                            size="sm" 
                            className="badge-spinner"
                        />
                        <span>처리 중...</span>
                    </>
                ) : (
                    <>
                        <span className="status-dot"></span>
                        <span>실시간 피팅</span>
                    </>
                )}
            </Badge>

            {/* 성능 지표 (활성화 시) */}
            {isActive && !isProcessing && (
                <div className="performance-indicators">
                    {fps && (
                        <span className="perf-badge">
                            {fps} FPS
                        </span>
                    )}
                    {latency && (
                        <span className="perf-badge">
                            {latency}ms
                        </span>
                    )}
                </div>
            )}
        </div>
    );
};

export default FittingStatusBadge;
