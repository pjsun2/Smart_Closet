import React, { useRef, useState, useEffect } from "react";
import { Button, Container, Row, Col, Navbar } from "react-bootstrap";

function Header() {
    const [wx, setWx] = useState(null);
    const [err, setErr] = useState("");
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

    return (
        <Navbar fixed="top" bg="light" className="shadow-sm">
            <Container fluid className="d-flex justify-content-between align-items-center">
                {/* 좌측 로고 */}
                <div className="d-flex align-items-center gap-2">
                    <img src="/dumirlogo.png" alt="logo" style={{ height: 80 }} />
                    <h3>Dumir Smart Closet</h3>
                </div>

                {/* 우측 날씨 */}
                <div style={{ minWidth: 140, textAlign: "right" }}>
                {wx ? (
                    <div className="d-flex align-items-center justify-content-end gap-2">
                        <div>
                            <div className="d-flex justify-content-center" style={{ fontWeight: 700, fontSize: 30 }}>
                                <img
                                    alt={wx.weather?.[0]?.description || "weather"}
                                    src={`https://openweathermap.org/img/wn/${wx.weather?.[0]?.icon}@2x.png`}
                                    style={{ width: 50, height: 50, color:'blue' }}
                                />
                                {Math.round(wx.main.temp)}°C
                            </div>
                            <div style={{ fontSize: 20 }}>
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
    );
}

export default Header;