import { useState } from "react";
import LoginModal from "./LoginModal";
import SignupModal from "./SignupModal";

export default function AuthContainer() {
    const [showLogin, setShowLogin] = useState(false);
    const [showSignup, setShowSignup] = useState(false);

    return (
        <>
        {/* 트리거 버튼은 원하는 위치에 */}
        {/* <button onClick={() => setShowLogin(true)}>로그인</button>
        <button onClick={() => setShowSignup(true)}>회원가입</button> */}

        <LoginModal
            show={showLogin}
            onHide={() => setShowLogin(false)}
            onOpenSignup={() => {
            setShowLogin(false);
            setShowSignup(true);
            }}
        />

        <SignupModal
            show={showSignup}
            onHide={() => setShowSignup(false)}
            onSignedUp={() => {
            setShowSignup(false);
            setShowLogin(true); // 가입 성공 → 로그인 모달 열기
            }}
        />
        </>
    );
}
