import React, { useRef, useState, useEffect } from "react";
import { Button, Container, Row, Col, Navbar, Offcanvas } from "react-bootstrap";
import LoginModal from "./login";
import { useNavigate } from "react-router-dom";

function Header() {
    const navigate = useNavigate();
    const [wx, setWx] = useState(null);
    const [err, setErr] = useState("");
    const [open, setOpen] = useState(false);

    const [showLogin, setShowLogin] = useState(false);
    const [pendingAction, setPendingAction] = useState(null); // 'login' | null

    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    const API = process.env.REACT_APP_OPENWEATHER_KEY;

    useEffect(() => {
        if (!API) { setErr("날씨 API 키가 설정되지 않았습니다 (.env)."); return; }

        let watchId = null;
        let last = { lat: null, lon: null };
        let refreshTimer = null;

        const fetchWx = async (lat, lon) => {
        try {
            const url = `https://api.openweathermap.org/data/2.5/weather?lat=${lat}&lon=${lon}&units=metric&lang=kr&appid=${API}`;
            // const url = `https://api.openweathermap.org/geo/1.0/reverse?lat=${lat}&lon=${lon}&limit=5&appid=${API}`;
            const res = await fetch(url);
            if (!res.ok) throw new Error("weather fetch failed");
            const data = await res.json();
            setWx(data);
            last = { lat, lon };
        } catch (e) {
            setErr("날씨 조회 실패");
            console.error(e);
        }
        };

        const onPos = (pos) => {
            const { latitude, longitude } = pos.coords;
            fetchWx(latitude, longitude);
        };
        const onErr = (e) => {
            console.warn("geolocation error:", e);
            setErr("위치 권한 필요(HTTPS에서 허용)");
        };

        if ("geolocation" in navigator) {
            watchId = navigator.geolocation.watchPosition(onPos, onErr, {
                enableHighAccuracy: true,
                maximumAge: 60_000,
                timeout: 10_000,
            });
        } else {
            setErr("기기에서 위치를 지원하지 않습니다");
        }

        // 5분마다 새로고침
        refreshTimer = setInterval(() => {
            if (last.lat && last.lon) fetchWx(last.lat, last.lon);
        }, 300_000);

        return () => {
            if (watchId) navigator.geolocation.clearWatch(watchId);
            if (refreshTimer) clearInterval(refreshTimer);
        };
    }, [API]);

    const [now, setNow] = useState(new Date());

    useEffect(() => {
        const t = setInterval(() => setNow(new Date()), 1000);
        return () => clearInterval(t); // ✅ 언마운트 시 정리
    }, []);

    // 한국 시간/표시
    const timeStr = now.toLocaleTimeString("ko-KR", {
        hour12: false, // 24시간제(원하면 true)
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        timeZone: "Asia/Seoul",
    });

    const dateStr = now.toLocaleDateString("ko-KR", {
        year: "numeric",
        month: "long",
        day: "numeric",
        weekday: "short",
        timeZone: "Asia/Seoul",
    });

    useEffect(() => {
        const fetchSession = async () => {
            try {
                const res = await fetch("/api/auth/me", {
                    credentials: "include", // Flask 세션 쿠키 포함
                });
                const data = await res.json();

                if (data.ok && data.authenticated) {
                    setUser(data.user);
                    sessionStorage.setItem("user", JSON.stringify(data.user));
                    console.log("로그인된 사용자:", data.user);
                } else {
                    setUser(null);
                    sessionStorage.removeItem("user");
                }
            } catch (err) {
                console.error("세션 확인 실패:", err);
                setUser(null);
                sessionStorage.removeItem("user");
            } finally {
                setLoading(false);    
            }
        };
        const savedUser = sessionStorage.getItem("user");
        if (savedUser) {
            setUser(JSON.parse(savedUser));
            setLoading(false);
        } else {
            fetchSession();
        }
    }, []);

        // const fetchSession = async () => {
        //     try {
        //         const res = await fetch("/api/auth/me", {
        //             credentials: "include",  // 세션 쿠키 포함
        //         });
        //         const data = await res.json();

        //         if (data.ok && data.authenticated) {
        //             setUser(data.user); // Flask의 session["user"] 값
        //             console.log(user);
        //         } else {
        //             setUser(null);
        //         }
        //     } catch (err) {
        //         console.error("세션 확인 실패:", err);
        //         setUser(null);
        //     } finally {
        //         setLoading(false);
        //     }
        // };
        // fetchSession();

    return (
        <>
            <Navbar fixed="top" bg="light" className="shadow-sm">
                <Container
                    fluid
                    className="position-relative d-flex justify-content-between align-items-center"
                >
                    <div className="d-flex align-items-center">
                        <Button
                            variant="outline-secondary"
                            size="lg"
                            className="px-4 py-3 fw-bold "
                            onClick={() => setOpen(true)}
                            style={{
                                all: "unset",
                                cursor: "pointer",
                                borderRadius: "12px",
                                fontSize: "1.1rem",
                                minWidth: "150px",
                            }}
                        >
                            <svg width="30" height="30" viewBox="0 0 24 24" aria-hidden style={{ marginRight: 6 }}>
                                <path d="M3 6h18M3 12h18M3 18h18" stroke="currentColor" strokeWidth="3" strokeLinecap="round"/>
                            </svg>
                        </Button>
                    </div>
                    <div className="position-absolute top-50 start-50 translate-middle text-center">
                        <div className="d-flex align-items-center gap-2">
                            <img src="/dumirlogo.png" alt="logo" style={{ height: 64 }} />
                            <Button
                                style={{
                                    all: "unset",
                                    cursor: "pointer",
                                }}
                                onClick={() => {navigate("/")}}
                            >
                                <h3 className="mb-0">Dumir Smart Closet</h3>
                            </Button>
                        </div>
                    </div>

                    {/* 우측: 날씨 */}
                    <div style={{ minWidth: 140, textAlign: "right" }}>
                        {wx ? (
                        <div className="d-flex align-items-center justify-content-end gap-2">
                            <div>
                                <div
                                    className="d-flex justify-content-center"
                                    style={{ fontWeight: 700, fontSize: 25 }}
                                >
                                    <img
                                        alt={wx.weather?.[0]?.description || "weather"}
                                        src={`https://openweathermap.org/img/wn/${wx.weather?.[0]?.icon}@2x.png`}
                                        style={{ width: 20, height: 25 }}
                                    />
                                    {Math.round(wx.main.temp)}°C
                                </div>
                                <div style={{ fontSize: 20, textAlign: "center" }}>
                                    {wx.name} · {wx.weather?.[0]?.description}
                                </div>
                                <div style={{ fontWeight: 700 }}>
                                    {dateStr} {timeStr}
                                </div>
                            </div>
                        </div>
                        ) : (
                        <small className="text-muted">{err || "날씨 로딩 중…"}</small>
                        )}
                    </div>
                </Container>
            </Navbar>

            {/* 사이드 오프캔버스 */}
            <Offcanvas
                show={open}
                onHide={() => setOpen(false)}
                onExited={() => {
                    // Offcanvas 애니메이션 완전히 끝난 뒤 모달 오픈
                    if (pendingAction === "login") {
                        setShowLogin(true);
                        setPendingAction(null);
                    }
                }}
                placement="start"
                scroll
                backdrop
                style={{
                    width: "37%"
                }}
            >
                <Offcanvas.Header closeButton style={{ marginRight: 15 }}>
                    <Offcanvas.Title>
                        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                        <img
                            src="/dumirlogo.png"
                            alt="logo"
                            style={{ height: 70, width: 70, marginLeft: 5 }}
                        />
                        {user ? (
                            <div>
                            <strong>{user.name}</strong> 님 안녕하세요
                            </div>
                        ) : (
                            <div></div>
                        )}
                        </div>
                    </Offcanvas.Title>
                </Offcanvas.Header>
                <hr
                    style={{
                        border: "none",
                        borderTop: "2px solid #000",
                        margin: "0 0 1rem 0",
                    }}
                />
                <Offcanvas.Body>
                    <div className="d-grid gap-2">
                        {user ? (
                            <Button
                                size="lg"
                                onClick={async () => {
                                    await fetch("/api/auth/logout", {
                                        method: "POST",
                                        credentials: "include",
                                    });
                                    sessionStorage.removeItem("user");
                                    setUser(null);
                                    setTimeout(() => {
                                        window.location.reload(); // 현재 페이지 새로고침
                                    }, 500);
                                }}
                            >
                                로그아웃
                            </Button>              
                        ) : (
                            <Button
                                size="lg"
                                onClick={() => {
                                    setPendingAction("login"); // 로그인 의도 기록
                                    setOpen(false);            // 먼저 사이드 패널 닫기
                                }}
                            >
                            로그인
                            </Button>
                        )}
                        {/* <Button
                            size="lg"
                            variant="outline-primary"
                            onClick={() => {
                                // TODO: 원하는 동작
                                setOpen(false);
                            }}
                        >
                        코디 추천
                        </Button> */}
                        <Button
                            size="lg"
                            variant="outline-primary"
                            onClick={() =>{ 
                                navigate("/wardrobe");
                                setOpen(false);
                            }}
                        >
                        옷장 관리
                        </Button>
                    </div>
                </Offcanvas.Body>
            </Offcanvas>
            {/* 로그인 모달 */}
            <LoginModal
                show={showLogin}
                onHide={() => setShowLogin(false)}
            />
        </>
        // <Navbar fixed="top" bg="light" className="shadow-sm">
        //     <Container fluid className="d-flex justify-content-between align-items-center">
        //         {/* 좌측 로고 */}
        //         <div className="d-flex align-items-center gap-2">
        //             <img src="/dumirlogo.png" alt="logo" style={{ height: 80 }} />
        //             <h3>Dumir Smart Closet</h3>
        //         </div>

        //         {/* 우측 날씨 */}
        //         <div style={{ minWidth: 140, textAlign: "right" }}>
        //         {wx ? (
        //             <div className="d-flex align-items-center justify-content-end gap-2">
        //                 <div>
        //                     <div className="d-flex justify-content-center" style={{ fontWeight: 700, fontSize: 30 }}>
        //                         <img
        //                             alt={wx.weather?.[0]?.description || "weather"}
        //                             src={`https://openweathermap.org/img/wn/${wx.weather?.[0]?.icon}@2x.png`}
        //                             style={{ width: 50, height: 50, color:'blue' }}
        //                         />
        //                         {Math.round(wx.main.temp)}°C
        //                     </div>
        //                     <div style={{ fontSize: 20 }}>
        //                         {wx.name} · {wx.weather?.[0]?.description}
        //                     </div>
        //                     <div style={{ fontWeight: 700 }}>
        //                         {dateStr} {timeStr}
        //                     </div>
        //                 </div>
        //             </div>
                    
        //         ) : (
        //             <small className="text-muted">{err || "날씨 로딩 중…"}</small>
        //         )}
        //         </div>
        //     </Container>
        // </Navbar>
    );
}

export default Header;