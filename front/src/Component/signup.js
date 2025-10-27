import { useState, useEffect} from "react";
import { Modal, Button, Form, Spinner, Alert } from "react-bootstrap";

export default function SignupModal({ show, onHide, onSignedUp }) {
    const [form, setForm] = useState({
        userId: "",
        password: "",
        name: "",
        gender: "",
    });
    const [loading, setLoading] = useState(false);
    const [msg, setMsg] = useState({ type: "", message: "" });

    useEffect(() => {
        if (!show) {
            setForm({ userId: "", password: "", name: "", gender: "" });
            setMsg({ type: "", message: "" });
            setLoading(false);
        }
    }, [show]);

    const handleChange = (key) => (e) => {
        setForm((p) => ({ ...p, [key]: e.target.value }));
        setMsg({ type: "", message: "" });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setMsg({ type: "", message: "" });
        if (!form.userId.trim() || !form.password || !form.name.trim() || !form.gender) {
            setMsg({type: "danger", message: "아이디, 비밀번호, 이름, 성별을 모두 입력하세요."});
            return;
        }

        try {
            setLoading(true);
            const res = await fetch("/api/auth/signup", {
                method: "POST",
                headers: {"Content-Type":"application/json"},
                body: JSON.stringify({
                    userId: form.userId.trim(),
                    password: form.password,
                    name: form.name.trim(),
                    gender: form.gender,
                }),
                credentials: "include",
            });
            const data = await res.json();
            console.log(data);
            if (data.ok == true) {
                setMsg({ type: "success", message: "회원가입이 완료되었습니다.\n 로그인 후 이용해주세요." });
                setForm({ userId: "", password: "", name: "", gender: ""});
                setTimeout(() => {
                    onHide();
                }, 1000);
            } else {
                setMsg({
                    type: "danger",
                    message: data.message,
                });
            }
        } catch (error) {
            // 서버에서 409(중복) 등 내려올 수 있음
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
                    <Modal.Title>회원가입</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    {msg.message && (
                        <Alert
                            variant={msg.type}
                            className="mb-3 py-2"
                            style={{ textAlign: "center", fontWeight: "bold" }}
                        >
                            {msg.message}
                        </Alert>
                    )}
                    <Form.Group className="mb-3" controlId="signupUserId">
                        <Form.Label>아이디</Form.Label>
                        <Form.Control
                            type="text"
                            placeholder="아이디를 입력하세요"
                            value={form.userId}
                            onChange={handleChange("userId")}
                            autoFocus
                            required
                        />
                    </Form.Group>

                    <Form.Group className="mb-3" controlId="signupPassword">
                        <Form.Label>비밀번호</Form.Label>
                        <Form.Control
                            type="password"
                            placeholder="비밀번호를 입력하세요"
                            value={form.password}
                            onChange={handleChange("password")}
                            required
                            minLength={6}
                        />
                        <Form.Text muted>비밀번호는 6자 이상을 권장합니다.</Form.Text>
                    </Form.Group>

                    <Form.Group className="mb-1" controlId="signupName">
                        <Form.Label>이름</Form.Label>
                        <Form.Control
                            type="text"
                            placeholder="이름을 입력하세요"
                            value={form.name}
                            onChange={handleChange("name")}
                            required
                        />
                    </Form.Group>
                    <Form.Group className="mb-3" controlId="signupGender">
                        <Form.Label>성별</Form.Label>
                        <div className="d-flex gap-3 mt-1">
                            <Form.Check
                                type="radio"
                                label="남자"
                                name="gender"
                                value="남자"
                                checked={form.gender === "남자"}
                                onChange={handleChange("gender")}
                                required
                            />
                            <Form.Check
                                type="radio"
                                label="여자"
                                name="gender"
                                value="여자"
                                checked={form.gender === "여자"}
                                onChange={handleChange("gender")}
                            />
                        </div>
                    </Form.Group>
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="secondary" onClick={onHide} disabled={loading}>
                        취소
                    </Button>
                    <Button type="submit" disabled={loading}>
                        {loading ? <Spinner size="sm" animation="border" /> : "회원가입"}
                    </Button>
                </Modal.Footer>
            </Form>
        </Modal>
    </>
  );
}
