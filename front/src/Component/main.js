import React, { useRef, useState, useEffect } from "react";
import { Button, Container, Row, Col } from "react-bootstrap";
import { useNavigate } from 'react-router-dom';

function Main() {
    const navigate = useNavigate(); // 페이지 이동
    const videoRef = useRef(null); // 비디오 실행 여부
    const canvasRef = useRef(null); // 캔버스
    const streamRef = useRef(null); // 
    const timerRef = useRef(null); // 캡처 예약 타이머
    const intervalRef = useRef(null); // 카운트다운
    const fileInputRef = useRef(null); // (옷인식에 사용) 파일 입력

    const [isRunning, setIsRunning] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [shot, setShot] = useState(null);
    const [serverPath, setServerPath] = useState(null);
    const [boxRatio, setBoxRatio] = useState("9 / 16"); // 기본값

    const [countdown, setCountdown] = useState(0); // 5 → 0 카운트다운
    const [pendingAction, setPendingAction] = useState(null); // 'cloth' | 'fit' | null ai모델 여부

    // 실시간 가상 피팅 관련 상태
    const [isFittingMode, setIsFittingMode] = useState(false); // 가상 피팅 모드
    const [fittingFrame, setFittingFrame] = useState(null); // 처리된 피팅 프레임
    const fittingIntervalRef = useRef(null); // 피팅 프레임 전송 인터벌
    const [showSkeleton, setShowSkeleton] = useState(true); // 스켈레톤 표시
    const [useWarp, setUseWarp] = useState(true); // 관절 매칭 사용

    // 스크롤 차단
    // useEffect(() => {
    //     const prevHtmlOverflow  = document.documentElement.style.overflow;
    //     const prevBodyOverflow  = document.body.style.overflow;
    //     const prevBodyHeight    = document.body.style.height;

    //     document.documentElement.style.overflow = "hidden";
    //     document.body.style.overflow = "hidden";
    //     document.body.style.height   = "100svh"; // 모바일 안전 뷰포트

    //     return () => {
    //         document.documentElement.style.overflow = prevHtmlOverflow;
    //         document.body.style.overflow = prevBodyOverflow;
    //         document.body.style.height   = prevBodyHeight;
    //         cleanupTimers();
    //         stopCamera();
    //     };
    // }, []);

    const cameraFrame = {
        background: "linear-gradient(45deg, #667eea 0%, #764ba2 100%)",
        padding: "4px",
        borderRadius: "20px",
    };

    useEffect(() => {
        startCamera();
    }, []);


    // 실시간 카메라 실행
    const startCamera = async () => {
        try {
            if (videoRef.current) {
                videoRef.current.setAttribute("playsinline", "true");
                videoRef.current.muted = true; // 모바일 자동재생
            }

            // 이미 스트림 있으면 재사용
            if (streamRef.current) {
                setIsRunning(true);
                return;
            }

            const constraints = {
                audio: false,
                video: {
                facingMode: { ideal: "user" },
                width: { ideal: 1280 },
                height: { ideal: 720 },
                },
            };

            const stream = await navigator.mediaDevices.getUserMedia(constraints);
            streamRef.current = stream;

            if (videoRef.current) {
                videoRef.current.srcObject = stream;
                await videoRef.current.play();
            }

            setIsRunning(true);
        } catch (err) {
            console.error("카메라 시작 실패:", err);
            alert("카메라 접근 실패. HTTPS/권한 허용/브라우저 설정을 확인하세요.");
            setIsRunning(false);
        }
    };

    // 카메라 정지버튼
    const stopCamera = () => {
        if (streamRef.current) {
            streamRef.current.getTracks().forEach((t) => t.stop());
            streamRef.current = null;
        }
        if (videoRef.current) videoRef.current.srcObject = null;
        setIsRunning(false);
    };

    // “정지” 버튼: 예약 캡처 취소 + 썸네일 초기화 + 비디오는 계속 실시간
    const stopCapture = () => {
        cleanupTimers();
        setCountdown(0);
        setPendingAction(null);
        setShot(null);           // 썸네일 초기화
        setServerPath(null);
        // 비디오는 계속 켜져 있어야 하므로, 꺼져 있으면 다시 켬
        if (!isRunning) startCamera();
    };

    // 버튼 클릭 시 5초 뒤 자동 캡처 예약
    const scheduleCapture = (action /* 'cloth' | 'fit' */) => {
        if (!isRunning) {
            // 혹시 꺼져 있으면 켜고 예약
            startCamera().then(() => scheduleCapture(action));
            return;
        }
        if (timerRef.current) return; // 이미 예약 중이면 무시(중복 방지)

        setPendingAction(action);
        setCountdown(5);

        intervalRef.current = setInterval(() => {
            setCountdown((sec) => {
                if (sec <= 1) {
                clearInterval(intervalRef.current);
                intervalRef.current = null;
                }
                return sec - 1;
            });
        }, 1000);

        timerRef.current = setTimeout(async () => {
            timerRef.current = null; // 실행 직후 해제
            const dataUrl = captureFrame();
            // 여기서 dataUrl을 서버로 전송하거나 분기 처리
            // if (action === 'cloth') await uploadToServer(dataUrl, '/api/cloth');
            // cloth 옷인식하여 데이터베이스에 저장하는 백엔드 연동 툴, 옷인식 버튼 클릭시 5초후 저장하고 썸네일 저장

            if (action === 'fit') {
                await uploadToFitServer(dataUrl);
            }
            // fit 옷 피팅하는 백엔드 연동 툴, 옷피팅 버튼 클릭시 5초후 저장하고 썸네일 저장
            
            setPendingAction(null);
            setCountdown(0);
        }, 5000);
    }

     const cleanupTimers = () => {
        if (timerRef.current) {
            clearTimeout(timerRef.current);
            timerRef.current = null;
        }
        if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
        }
    };

    const captureFrame = () => {
        if (!videoRef.current || !canvasRef.current) return null;
        const video = videoRef.current;
        const canvas = canvasRef.current;

        const w = video.videoWidth || 1080;
        const h = video.videoHeight || 1920;

        canvas.width = w;
        canvas.height = h;

        const ctx = canvas.getContext("2d");
        ctx.drawImage(video, 0, 0, w, h);

        const dataUrl = canvas.toDataURL("image/jpeg", 0.92);
        setShot(dataUrl); // 썸네일/상태 저장
        return dataUrl;
    };

    const dataURLtoBlob = (dataUrl) => {
        const arr = dataUrl.split(",");
        const mime = arr[0].match(/:(.*?);/)[1];
        const bstr = atob(arr[1]);
        let n = bstr.length;
        const u8 = new Uint8Array(n);
        while (n--) u8[n] = bstr.charCodeAt(n);
        return new Blob([u8], { type: mime });
    };

    useEffect(() => {
        const v = videoRef.current;
        const onMeta = () => {
            const vw = v.videoWidth || 1080;
            const vh = v.videoHeight || 1920;
            setBoxRatio(`${vw} / ${vh}`);
        };
        v?.addEventListener("loadedmetadata", onMeta);
        return () => v?.removeEventListener("loadedmetadata", onMeta);
    }, []);

    // 입어보기 - 캡처한 이미지를 서버로 전송하고 main.py 실행
    const uploadToFitServer = async (dataUrl) => {
        try {
            setUploading(true);
            setServerPath(null);

            console.log("[프론트] 입어보기 이미지 업로드 시작");

            // AbortController로 타임아웃 설정 (5분)
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 300000); // 5분

            try {
                // Base64 데이터를 JSON으로 전송
                const res = await fetch("/api/fit", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        image: dataUrl
                    }),
                    signal: controller.signal
                });

                clearTimeout(timeoutId);

                if (!res.ok) {
                    throw new Error(`Upload failed: ${res.status}`);
                }

                const json = await res.json();
                console.log("[프론트] 입어보기 처리 응답:", json);
                
                if (json.success) {
                    if (json.status === "processing") {
                        alert("입어보기 처리를 시작했습니다!\n처리가 완료될 때까지 잠시만 기다려주세요.");
                    } else {
                        alert("입어보기 처리가 완료되었습니다!");
                    }
                    setServerPath(json.model_path || null);
                } else {
                    alert("입어보기 처리 중 오류가 발생했습니다.");
                }
            } catch (fetchError) {
                clearTimeout(timeoutId);
                
                if (fetchError.name === 'AbortError') {
                    throw new Error('요청 시간이 초과되었습니다 (5분)');
                }
                throw fetchError;
            }

        } catch (e) {
            console.error("[프론트] 입어보기 업로드 실패:", e);
            alert("입어보기 업로드 실패: " + e.message);
        } finally {
            setUploading(false);
        }
    };

  // const uploadToServer = async (dataUrl) => {
  //   try {
  //     setUploading(true);
  //     setServerPath(null);
  //     const blob = dataURLtoBlob(dataUrl);
  //     const form = new FormData();
  //     form.append("file", blob, `capture_${Date.now()}.jpg`);

  //     // CRA의 "proxy": "http://127.0.0.1:5000" 가정
  //     const res = await fetch("/api/upload", { method: "POST", body: form });
  //     if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
  //     const json = await res.json();
  //     setServerPath(json?.path || null);
  //   } catch (e) {
  //     console.error(e);
  //     alert("업로드 실패");
  //   } finally {
  //     setUploading(false);
  //   }
  // };

    // useEffect(() => {
    //     const load = async () => {
    //         try {
    //             const res = await fetch("/members", {
    //                 headers: { "Cache-Control": "no-cache" }, // 캐시 우회(선택)
    //             });
    //             if (!res.ok) throw new Error(`HTTP ${res.status}`);
    //             const json = await res.json();
    //             setMembers(Array.isArray(json.members) ? json.members : []);
    //         } catch (e) {
    //             console.error("load members failed:", e);
    //             setMembers([]); // 실패 시 안전하게 빈 배열
    //         }
    //     };
    //     load();
    // }, []);

    // const [members, setMembers] = useState([]); // 초기값: 빈 배열
    
    // useEffect(() => {
    //     fetch('/api/members')
    //     .then(res => {
    //         if (!res.ok) throw new Error(`HTTP ${res.status}`);
    //         return res.json();
    //     })
    //     .then(data => {
    //         console.log('api/members response:', data);
    //         const members = Array.isArray(data?.members) ? data.members : [];
    //         setMembers(members);
    //     })
    //     .catch(err => console.error('load members failed:', err));
    // }, []);

    // 옷사진 선택
    const handleFileUpload = async (event) => {
        const file = event.target.files?.[0];
        
        if (!file) {
            console.log("[프론트] 파일 선택 취소됨");
            return;
        }

        console.log(`[프론트] 파일 선택: ${file.name}, 크기: ${file.size} bytes`);

        try {
            setUploading(true);

            // 파일을 Base64로 변환
            const reader = new FileReader();
            
            reader.onload = async (e) => {
                const base64Data = e.target.result;
                
                console.log(`[프론트] Base64 변환 완료: ${base64Data.length} bytes`);

                // ✅ AnalysisLoading 페이지로 이동만 함 (분석은 안 함)
                navigate('/analysis', { 
                    state: { 
                        image: base64Data,  // 분석할 이미지 데이터
                        filename: file.name
                    } 
                });
                
                setUploading(false);
            };

            reader.onerror = (error) => {
                console.error(`[프론트] 파일 읽기 에러:`, error);
                alert("파일 읽기 실패");
                setUploading(false);
            };

            reader.readAsDataURL(file);

        } catch (e) {
            console.error(e);
            alert("에러 발생");
            setUploading(false);
        }
    };
    
    // 옷저장 전용 함수
    const uploadClothes = async () => {
        console.log("[프론트] 옷저장 시작");

        if (uploading || timerRef.current) {
            console.log("[프론트] 진행 중 - 무시");
            return;
        }

        if (!isRunning) {
            await startCamera();
        }

        cleanupTimers();
        setShot(null);
        setUploading(true);
        setPendingAction("cloth");
        setCountdown(5);

        intervalRef.current = setInterval(() => {
            setCountdown((sec) => {
                if (sec <= 1) {
                    clearInterval(intervalRef.current);
                    intervalRef.current = null;
                    return 0;
                }
                return sec - 1;
            });
        }, 1000);

        timerRef.current = setTimeout(async () => {
            timerRef.current = null;
            if (intervalRef.current) {
                clearInterval(intervalRef.current);
                intervalRef.current = null;
            }

            try {
                const dataUrl = captureFrame();
                if (!dataUrl) throw new Error("캡처 실패");

                const blob = dataURLtoBlob(dataUrl);
                const filename = `cloth_${Date.now()}.jpg`;

                const form = new FormData();
                form.append("file", blob, filename);

                console.log("[프론트] 서버 전송 시작...");
                const res = await fetch("/api/clothes", { method: "POST", body: form });
                const json = await res.json();
                console.log("[프론트] 서버 응답:", json);

                if (!res.ok || !json.success) {
                    throw new Error(json.error || json.message || "분석 실패");
                }

                navigate("/analysis", {
                    state: { image: dataUrl, filename, result: json },
                });
            } catch (error) {
                console.error("[프론트] 옷저장 실패:", error);
                alert("옷저장 실패: " + error.message);
            } finally {
                setUploading(false);
                setPendingAction(null);
                setCountdown(0);
                cleanupTimers();
            }
        }, 5000);
    };

    // 옷 인식 버튼 클릭
    const handleClothSave = () => {
        console.log("[프론트] 옷저장 버튼 클릭");
        uploadClothes();
    };

    // const handleClothSave = () => scheduleCapture("cloth");
    
    // ========== 실시간 가상 피팅 기능 ==========
    
    // 실시간 피팅 프레임 전송 및 처리
    const sendFittingFrame = async () => {
        if (!videoRef.current || !canvasRef.current) return;
        
        try {
            const video = videoRef.current;
            const canvas = canvasRef.current;
            
            const w = video.videoWidth || 1280;
            const h = video.videoHeight || 720;
            
            canvas.width = w;
            canvas.height = h;
            
            const ctx = canvas.getContext("2d");
            ctx.drawImage(video, 0, 0, w, h);
            
            const frameData = canvas.toDataURL("image/jpeg", 0.8);
            
            // 서버로 프레임 전송
            const response = await fetch("/api/fit/stream", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    frame: frameData,
                    showSkeleton: showSkeleton,
                    useWarp: useWarp
                })
            });
            
            if (!response.ok) {
                console.error("[프론트] 피팅 프레임 처리 실패:", response.status);
                return;
            }
            
            const result = await response.json();
            
            if (result.success && result.frame) {
                setFittingFrame(result.frame);
            }
            
        } catch (error) {
            console.error("[프론트] 피팅 프레임 전송 오류:", error);
        }
    };
    
    // 가상 피팅 시작
    const startVirtualFitting = () => {
        console.log("[프론트] 가상 피팅 시작");
        setIsFittingMode(true);
        
        // 실시간 프레임 전송 시작 (200ms 간격)
        fittingIntervalRef.current = setInterval(() => {
            sendFittingFrame();
        }, 200);
    };
    
    // 가상 피팅 중지
    const stopVirtualFitting = () => {
        console.log("[프론트] 가상 피팅 중지");
        setIsFittingMode(false);
        setFittingFrame(null);
        
        if (fittingIntervalRef.current) {
            clearInterval(fittingIntervalRef.current);
            fittingIntervalRef.current = null;
        }
    };
    
    // 입어보기 버튼 클릭 (실시간 가상 피팅)
    const handleStartFit = () => {
        if (isFittingMode) {
            stopVirtualFitting();
        } else {
            startVirtualFitting();
        }
    };
    
    // 가상 피팅용 옷 이미지 업로드
    // 컴포넌트 언마운트 시 정리
    useEffect(() => {
        return () => {
            if (fittingIntervalRef.current) {
                clearInterval(fittingIntervalRef.current);
            }
        };
    }, []);

    // tts ver2
    const [voicetext, setvoicetext] = useState(""); // 음성 text 변환 저장
    const [isListening, setIsListening] = useState(false);
    const recognitionRef = useRef(null);

    const handleStart = () => {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

        if(!SpeechRecognition) {
            alert("이 브라우저는 음성 인식을 지원하지 않습니다.");
            return;
        }

        const recognition = new SpeechRecognition();
        recognition.lang = "ko-KR"; // 한국어
        recognition.interimResults = false;
        recognition.maxAlternatives = 3;

        recognition.onstart = () => {
            setIsListening(true);
            setvoicetext("")
        }

        recognition.onresult = (event) => {
            const result = event.results[0][0].transcript;
            setvoicetext(result);
            if(result) postText(result)
            console.log("인식 결과:", result);
        };

        recognition.onerror = (event) => {
            console.error("인식 오류:", event.error);
            setIsListening(false);
        };

        recognition.onend = () => {
            setIsListening(false);
        };

        recognitionRef.current = recognition;
        recognition.start();
    }
    
    // 챗봇 결과 가져오는 post
    const postText = async (txt) => {
        try {
            const res = await fetch("/api/voice/stt", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text: txt })
            });
            if(!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            console.log(data);
            if (data.tts_url) {
                // 1) 그냥 URL로 재생 (재생 동안 서버가 파일을 전송하고, 전송 후 삭제)
                // const audio = new Audio(data.tts_url);
                // audio.play();

                // 2) 안전하게 blob으로 받아 캐시(로컬에 보관) 후 재생 (URL이 삭제되어도 재생 가능)
                const aRes = await fetch(data.tts_url, { method: "GET" });
                if (!aRes.ok) throw new Error(`TTS HTTP ${aRes.status}`);
                const blob = await aRes.blob();
                const blobUrl = URL.createObjectURL(blob);
                const audio = new Audio(blobUrl);
                audio.play();
                // 재생 끝나고 URL 해제
                audio.onended = () => URL.revokeObjectURL(blobUrl);
            }
        } catch(e) {
            console.log(e);
        }
    }

    const handleStop = () => {
        recognitionRef.current?.stop();
        setIsListening(false);
    };

    return (
        <>
        {/* 전체 화면 꽉 채우고 스크롤 금지 */}
        <Container
            fluid
            className="d-flex flex-column justify-content-center align-items-center"
            style={{ height: "105svh", overflow: "hidden" }}
        >
            <Row className="w-100 justify-content-center" style={{ maxWidth: 1200 }}>
            <Col xs={12} sm={10} md={8} lg={5} className="d-flex flex-column align-items-stretch">
                {/* 카메라 프레임 */}
                <div style={cameraFrame}>
                {/* 세로 비율(9:16) 강제 + 부모 폭 기준 */}
                <div
                    className="position-relative"
                    style={{
                    //   aspectRatio: boxRatio,
                    aspectRatio: 9/18,
                    width: "100%", 
                    maxHeight: "100svh",
                    background: "black",
                    borderRadius: 16,
                    overflow: "hidden",
                    }}
                >
                    <video
                        ref={videoRef}
                        autoPlay
                        muted
                        // Tailwind 없이도 동작하도록 스타일로 커버
                        style={{
                            width: "100%",
                            height: "100%",
                            objectFit: "cover",
                            objectPosition: "center center",
                            borderRadius: 16,
                            display: isFittingMode ? "none" : "block", // 피팅 모드에서는 숨김
                            transform: "scaleX(-1)",
                        }}
                    />
                    
                    {/* 실시간 가상 피팅 결과 */}
                    {isFittingMode && fittingFrame && (
                        <img
                            src={fittingFrame}
                            alt="Virtual Fitting"
                            style={{
                                width: "100%",
                                height: "100%",
                                objectFit: "cover",
                                objectPosition: "center center",
                                borderRadius: 16,
                                display: "block",
                                transform: "scaleX(-1)",
                            }}
                        />
                    )}
                    
                    {/* 피팅 모드 표시 */}
                    {isFittingMode && (
                        <div
                            style={{
                                position: "absolute",
                                top: 10,
                                left: 10,
                                background: "rgba(0, 255, 0, 0.7)",
                                color: "white",
                                padding: "8px 16px",
                                borderRadius: 8,
                                fontWeight: "bold",
                                fontSize: "14px",
                            }}
                        >
                            🎽 가상 피팅 중...
                        </div>
                    )}
                    
                    {/* 캡처된 썸네일 오버레이 */}
                    {shot && !isFittingMode && (
                    <div
                        style={{
                        position: "absolute",
                        inset: 0,
                        background: "black",
                        borderRadius: 16,
                        overflow: "hidden",
                        }}
                    >
                        <img
                        src={shot}
                        alt="captured"
                        style={{
                            width: "100%",
                            height: "100%",
                            objectFit: "cover",
                            objectPosition: "center center",
                            transform: "scaleX(-1)",
                        }}
                        />
                    </div>
                    )}

                    {/* 오버레이 (스캔 라인/코너 프레임) */}
                    
                    <div
                    style={{
                        position: "absolute",
                        inset: 0,
                        pointerEvents: "none",
                    }}
                    >
                    {/* 스캔 라인 */}
                    <div
                        style={{
                        position: "absolute",
                        left: 0,
                        right: 0,
                        top: "50%",
                        height: 2,
                        background: "rgba(74, 222, 128, 0.7)", // green-400
                        }}
                    />
                    {/* 코너 프레임 4개 */}
                    <div style={{
                        position:"absolute", top:16, left:16, width:32, height:32,
                        borderLeft:"2px solid #22c55e", borderTop:"2px solid #22c55e"
                    }}/>
                    <div style={{
                        position:"absolute", top:16, right:16, width:32, height:32,
                        borderRight:"2px solid #22c55e", borderTop:"2px solid #22c55e"
                    }}/>
                    <div style={{
                        position:"absolute", bottom:16, left:16, width:32, height:32,
                        borderLeft:"2px solid #22c55e", borderBottom:"2px solid #22c55e"
                    }}/>
                    <div style={{
                        position:"absolute", bottom:16, right:16, width:32, height:32,
                        borderRight:"2px solid #22c55e", borderBottom:"2px solid #22c55e"
                    }}/>
                    </div>

                    {/* 상태 바 */}
                    <div style={{ position:"absolute", left:24, right:24, bottom:24 }}>
                    <div
                        style={{
                        background: "rgba(0,0,0,0.7)",
                        color: "white",
                        borderRadius: 12,
                        padding: 12,
                        }}
                    >
                        <div className="d-flex align-items-center justify-content-between">
                        <span>
                            {isFittingMode
                            ? "🎽 실시간 가상 피팅 활성화"
                            : isRunning
                            ? pendingAction
                                ? `⏳ ${countdown}초 뒤 자동 캡처 (${pendingAction === "cloth" ? "옷 인식" : "입어보기"})`
                                    
                                : "🎥 실시간 촬영 중"
                            : "대기 중"}
                            
                            {uploading ? " (업로드 중...)" : ""}
                        </span>
                        <div className="d-flex align-items-center gap-1">
                            <span className="rounded-circle" style={{width:8,height:8,background:"#22c55e",display:"inline-block"}}/>
                            <span className="rounded-circle" style={{width:8,height:8,background:"#22c55e",display:"inline-block",opacity:.8}}/>
                            <span className="rounded-circle" style={{width:8,height:8,background:"#22c55e",display:"inline-block",opacity:.6}}/>
                        </div>
                        </div>
                    </div>
                    </div>
                </div>
                </div>
                {/* {members.map((m, i) => (
                    <li key={i}>{m}</li>
                ))} */}

                {/* 버튼: 가운데 정렬 */}
                <div className="mt-3 d-flex justify-content-center gap-3">
                <Button
                    variant={isListening ? "warning": "danger"}
                    onClick={isListening ? handleStop : handleStart}
                    className="px-4 py-2"
                >
                    {isListening ? "인식중지" : "질문하기"}
                </Button>
                <Button
                    variant="primary"
                    onClick={handleClothSave}
                    disabled={uploading || !!timerRef.current}
                    className="px-4 py-2"
                >
                    옷저장
                </Button>
                {/* <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    onChange={handleFileUpload}
                    style={{ display: "none" }}
                    id="clothFileInput"
                    disabled={isRunning && !timerRef.current && !uploading}
                />
                <label
                    htmlFor="clothFileInput"
                    className="btn btn-primary px-4 py-2"
                    style={{
                        cursor: "pointer",
                        marginBottom: 0,
                    }}
                >
                    옷저장
                </label> */}
                <Button
                    variant={isFittingMode ? "success" : "warning"}
                    onClick={handleStartFit}
                    disabled={!isRunning || uploading}
                    className="px-4 py-2"
                >
                    {isFittingMode ? "피팅 중지" : "입어보기"}
                </Button>
                <Button
                    variant="secondary"
                    onClick={stopCapture}
                    className="px-4 py-2"
                >
                    정지
                </Button>
                </div>
                {/* {voicetext} */}
                {/* 캡처 미리보기 & 서버 경로 */}
                {/* {shot && (
                <div className="mt-3 text-center">
                    <img
                    src={shot}
                    alt="capture"
                    style={{ maxWidth: "100%", borderRadius: 12, boxShadow: "0 8px 24px rgba(0,0,0,.15)" }}
                    />
                    {serverPath && (
                    <div className="mt-2" style={{fontSize:12,color:"#555"}}>
                        서버 저장 경로: <code>{serverPath}</code>
                    </div>
                    )}
                </div>
                )} */}
            </Col>
            </Row>
        </Container>

        {/* 숨김 캔버스 (캡처용) */}
        <canvas ref={canvasRef} style={{ display: "none" }} />
        </>
    );
}

export default Main;
