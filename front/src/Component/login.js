import { useState } from "react";
import { Button, Modal, Form, Spinner } from "react-bootstrap";
import axios from "axios";

export default function LoginModal({ show, onHide }) {
  const [form, setForm] = useState({ userId: "", password: "" });
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErr("");
    setLoading(true);
    try {
      const res = await axios.post(
        "http://127.0.0.1:5000/api/login",
        { userId: form.userId.trim(), password: form.password },
        { withCredentials: true }
      );
      if (res.data?.ok) {
        onHide();
        // TODO: 전역 상태 갱신 or 라우팅 (예: window.location.href = "/")
      } else {
        setErr(res.data?.message || "로그인에 실패했어요.");
      }
    } catch (e) {
      setErr("서버 통신 중 오류가 발생했어요.");
    } finally {
      setLoading(false);
    }
  };

  return (
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
          <Button variant="danger" onClick={onHide}>회원가입</Button>
        </Modal.Footer>
      </Form>
    </Modal>
  );
}