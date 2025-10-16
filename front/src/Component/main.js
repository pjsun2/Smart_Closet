import React, { useRef, useState, useEffect } from "react";
import { Button, Container, Row, Col } from "react-bootstrap";

function Main() {
    const videoRef = useRef(null);
    const canvasRef = useRef(null);
    const streamRef = useRef(null);
    const timerRef = useRef(null);

    const [isRunning, setIsRunning] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [shot, setShot] = useState(null);
    const [serverPath, setServerPath] = useState(null);
    const [boxRatio, setBoxRatio] = useState("9 / 16"); // 기본값

    // 스크롤 차단
    useEffect(() => {
        const prevHtmlOverflow  = document.documentElement.style.overflow;
        const prevBodyOverflow  = document.body.style.overflow;
        const prevBodyHeight    = document.body.style.height;

        document.documentElement.style.overflow = "hidden";
        document.body.style.overflow = "hidden";
        document.body.style.height   = "100svh"; // 모바일 안전 뷰포트

        return () => {
            document.documentElement.style.overflow = prevHtmlOverflow;
            document.body.style.overflow = prevBodyOverflow;
            document.body.style.height   = prevBodyHeight;
            stopCamera();
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const cameraFrame = {
        background: "linear-gradient(45deg, #667eea 0%, #764ba2 100%)",
        padding: "4px",
        borderRadius: "20px",
    };

    const startCamera = async () => {
        try {
        if (videoRef.current) {
            videoRef.current.setAttribute("playsinline", "true");
            videoRef.current.muted = true; // 모바일 자동재생
        }

        const constraints = {
            audio: false,
            video: {
            // 카메라
            facingMode: { ideal: "user" },
            width:  { ideal: 1280 }, // 4/3 기준으로 
            height: { ideal: 720  },
            },
        };

        const stream = await navigator.mediaDevices.getUserMedia(constraints);
        streamRef.current = stream;

        if (videoRef.current) {
            videoRef.current.srcObject = stream;
            await videoRef.current.play();
        }

        setIsRunning(true);

        // 3초 뒤 자동 1회 캡처 + 업로드
        timerRef.current = setTimeout(async () => {
            const dataUrl = captureFrame();
            // if (dataUrl) await uploadToServer(dataUrl); // -> 캡처후 서버로 이동
            stopCamera(); // 요구사항대로 캡처 후 종료
        }, 10000);
        } catch (err) {
            console.error("카메라 시작 실패:", err);
            alert("카메라 접근 실패. HTTPS/권한 허용/브라우저 설정을 확인하세요.");
            setIsRunning(false);
        }
    };

    const stopCamera = () => {
        if (timerRef.current) {
            clearTimeout(timerRef.current);
            timerRef.current = null;
        }
        if (streamRef.current) {
            streamRef.current.getTracks().forEach(t => t.stop());
            streamRef.current = null;
        }
        if (videoRef.current) videoRef.current.srcObject = null;
        setIsRunning(false);
    };

    const captureFrame = () => {
        if (!videoRef.current || !canvasRef.current) return null;
        const video  = videoRef.current;
        const canvas = canvasRef.current;

        const w = video.videoWidth  || 1080;
        const h = video.videoHeight || 1920;

        canvas.width  = w;
        canvas.height = h;

        const ctx = canvas.getContext("2d");
        ctx.drawImage(video, 0, 0, w, h);

        const dataUrl = canvas.toDataURL("image/jpeg", 0.92);
        setShot(dataUrl);
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
            const vw = v.videoWidth  || 1080;
            const vh = v.videoHeight || 1920;
            setBoxRatio(`${vw} / ${vh}`); // ✅ 비디오 원본 비율로 박스 설정
        };
        v?.addEventListener("loadedmetadata", onMeta);
        return () => v?.removeEventListener("loadedmetadata", onMeta);
    }, []);

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

    const [members, setMembers] = useState([]); // 초기값: 빈 배열
    
    useEffect(() => {
        fetch('/api/members')
        .then(res => {
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            return res.json();
        })
        .then(data => {
            console.log('api/members response:', data);
            const members = Array.isArray(data?.members) ? data.members : [];
            setMembers(members);
        })
        .catch(err => console.error('load members failed:', err));
    }, []);


    return (
        <>
        {/* 전체 화면 꽉 채우고 스크롤 금지 */}
        <Container
            fluid
            className="d-flex flex-column justify-content-center align-items-center"
            style={{ height: "108svh", overflow: "hidden" }}
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
                            display: "block",
                            transform: "scaleX(-1)",
                        }}
                    />
                    {/* 캡처된 썸네일 오버레이 */}
                    {shot && (
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
                            {isRunning ? "📸 10초 후 자동 캡처 중..." : "대기 중"}
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
                    variant="danger"
                    onClick={startCamera}
                    disabled={isRunning || uploading}
                    className="px-4 py-2"
                >
                    질문하기
                </Button>
                <Button
                    variant="primary"
                    onClick={startCamera}
                    disabled={isRunning || uploading}
                    className="px-4 py-2"
                >
                    시작(10초 뒤 자동 캡처)
                </Button>
                <Button
                    variant="secondary"
                    onClick={stopCamera}
                    disabled={!isRunning}
                    className="px-4 py-2"
                >
                    정지
                </Button>
                </div>
                
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
