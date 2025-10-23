import { useState, useEffect } from "react";
import { Button, Modal, Form, Spinner } from "react-bootstrap";
import SignupModal from "./signup";

export default function LoginModal({ show, onHide }) {
  const [form, setForm] = useState({ userId: "", password: "" });
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const [msg, setMsg] = useState({type: "", message: ""});
  const [user, setUser] = useState(null); 

  const [showSignup, setShowSignup] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErr("");
    setLoading(true);
    try {
      const res = await fetch("/api/auth/login", { 
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
          userId: form.userId.trim(), 
          password: form.password
        }),
        credentials: "include",
      });
      const data = await res.json();
      console.log(data);
      if (data.ok == true) {
        setMsg({ type: "success", message: `환영합니다. ${data.user.name}님` });
        setTimeout(() => {
          window.location.reload(); // 현재 페이지 새로고침
        }, 500);
      } else {
        setMsg({
          type: "danger",
          message: data.message,
        });
      }
    } catch (e) {
      setMsg({
        type: "danger",
        message: "서버 통신 중 오류가 발생했습니다.",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Modal show={show} onHide={onHide} centered>
        <Form onSubmit={handleSubmit}>
          <Modal.Header closeButton>
            <Modal.Title>로그인</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <Form.Group className="mb-3">
              <Form.Label>아이디</Form.Label>
              <Form.Control
                type="text"
                value={form.userId}
                onChange={(e) => setForm((p) => ({ ...p, userId: e.target.value }))}
                placeholder="아이디를 입력하세요"
                autoFocus
                required
              />
            </Form.Group>
            <Form.Group className="mb-1">
              <Form.Label>비밀번호</Form.Label>
              <Form.Control
                type="password"
                value={form.password}
                onChange={(e) => setForm((p) => ({ ...p, password: e.target.value }))}
                placeholder="비밀번호를 입력하세요"
                required
              />
            </Form.Group>
            {err && <div className="text-danger mt-2">{err}</div>}
          </Modal.Body>
          <Modal.Footer>
            <Button type="submit" disabled={loading}>
              {loading ? <Spinner size="sm" animation="border" /> : "로그인"}
            </Button>
            <Button 
              variant="danger"
              onClick={() => {
                  onHide();           // 로그인 모달 닫기
                  setTimeout(() => {  // 약간의 딜레이 후 회원가입 모달 열기
                    setShowSignup(true);
                  }, 200);
              }}
              >
              회원가입
            </Button>
          </Modal.Footer>
        </Form>
      </Modal>
      <SignupModal
          show={showSignup}
          onHide={() => setShowSignup(false)}
          onSignedUp={() => {
            // 회원가입 완료 후 로그인 모달 다시 열기
            setShowSignup(false);
            setTimeout(() => {
              onHide(false);
            }, 300);
          }}
      />
    </>
  );
}