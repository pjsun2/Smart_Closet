import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

const container = document.getElementById('root');

// 이 컨테이너에 아직 React 루트가 생성되지 않았을 때만 새로 생성하도록 확인합니다.
// 이렇게 하면 스크립트가 중복으로 실행되더라도 에러가 발생하지 않습니다.
if (container && !container._reactRootContainer) {
  const root = ReactDOM.createRoot(container);
  root.render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
}

