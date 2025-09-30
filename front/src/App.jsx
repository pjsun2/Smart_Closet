import React from "react";

function App() {
  return (
    <div className="min-h-screen bg-gray-100 flex flex-col items-center font-sans">
      {/* 헤더 */}
      <header className="w-full bg-white text-gray-800 py-6 text-center shadow-md">
        <h1 className="text-4xl font-bold text-gray-900">Dumir 스마트 클로젯</h1>
        <p className="mt-2 text-lg text-gray-600">
          당신의 일상을 변화시킬 단 하나의 스마트 옷장
        </p>
      </header>

      {/* 메인 배너 */}
      <section className="w-full max-w-5xl my-10 bg-gradient-to-r from-blue-500 to-indigo-600 text-white shadow-xl rounded-2xl p-10 text-center">
        <h2 className="text-3xl font-semibold mb-4">
          세상에 없던 의류 케어, Dumir가 시작합니다.
        </h2>
        <p className="text-indigo-100 mb-8 text-lg">
          혁신적인 AI 기술로 코디 추천부터 의류 관리, 원격 제어까지.
          <br />
          이제껏 경험하지 못한 스마트한 의류 라이프를 만나보세요.
        </p>
        <button className="px-8 py-3 bg-white text-blue-600 font-semibold rounded-xl hover:bg-gray-100 transition shadow-lg">
          주요 기능 시연하기
        </button>
      </section>

      {/* 기능 카드 */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-4 max-w-5xl w-full px-4 md:px-0">
        {/* AI 코디 추천 */}
        <div className="bg-white shadow-lg rounded-2xl p-8 text-center flex flex-col items-center">
          <div className="bg-blue-100 p-4 rounded-full mb-4">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-10 w-10 text-blue-600"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
              />
            </svg>
          </div>
          <h3 className="text-xl font-bold text-gray-800">AI 코디 추천</h3>
          <p className="text-gray-600 mt-2">
            오늘의 날씨와 당신의 스타일에 맞춰 완벽한 코디를 제안합니다.
          </p>
        </div>

        {/* 스마트 의류 관리 */}
        <div className="bg-white shadow-lg rounded-2xl p-8 text-center flex flex-col items-center">
          <div className="bg-green-100 p-4 rounded-full mb-4">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-10 w-10 text-green-600"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"
              />
            </svg>
          </div>
          <h3 className="text-xl font-bold text-gray-800">스마트 의류 관리</h3>
          <p className="text-gray-600 mt-2">
            자동 살균, 탈취, 주름 관리 기능으로 매일 새 옷처럼 관리하세요.
          </p>
        </div>

        {/* 내 옷장 원격 관리 */}
        <div className="bg-white shadow-lg rounded-2xl p-8 text-center flex flex-col items-center">
          <div className="bg-purple-100 p-4 rounded-full mb-4">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-10 w-10 text-purple-600"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z"
              />
            </svg>
          </div>
          <h3 className="text-xl font-bold text-gray-800">내 옷장 원격 관리</h3>
          <p className="text-gray-600 mt-2">
            언제 어디서든 스마트폰 앱으로 내 옷장의 모든 것을 확인하고 제어합니다.
          </p>
        </div>
      </section>

      {/* 푸터 */}
      <footer className="w-full bg-gray-800 text-gray-300 py-6 mt-12 text-center">
        <p>© 2025 Dumir Inc. All rights reserved.</p>
      </footer>
    </div>
  );
}

export default App;

