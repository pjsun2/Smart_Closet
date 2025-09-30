import React from 'react';

// 각 기능 카드를 위한 아이콘 컴포넌트 (SVG)
const StyleIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 14l-3 3m0 0l-3-3m3 3V3" />
  </svg>
);

const CareIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M5 3v4M3 5h4M6 17v4m-2-2h4M14 3v4m-2-2h4M16 17v4m-2-2h4M9 9l2 2 4-4" />
    <path strokeLinecap="round" strokeLinejoin="round" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const RemoteIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
  </svg>
);


function App() {
  return (
    <div className="min-h-screen bg-gray-100 font-sans text-gray-800">
      {/* 헤더 */}
      <header className="w-full bg-white shadow-sm sticky top-0 z-10">
        <div className="container mx-auto max-w-6xl px-4 py-4 flex justify-between items-center">
          <h1 className="text-3xl font-bold text-gray-900">
            Dumir <span className="text-blue-600">Smart Closet</span>
          </h1>
          <nav>
            <a href="#features" className="text-gray-600 hover:text-blue-600 transition">주요 기능</a>
          </nav>
        </div>
      </header>

      {/* 메인 섹션 */}
      <main className="container mx-auto max-w-6xl px-4 py-16 text-center">
        <h2 className="text-5xl font-extrabold mb-4">내일을 바꾸는 옷장, Dumir</h2>
        <p className="text-xl text-gray-600 mb-10 max-w-3xl mx-auto">
          두미르 스마트 클로젯은 단순한 옷장을 넘어, 당신의 일상을 더욱 스마트하고 편리하게 만드는 라이프스타일 솔루션입니다.
        </p>
        <img
          src="https://placehold.co/1000x500/EBF4FF/3B82F6?text=Dumir+Smart+Closet"
          alt="Dumir 스마트 클로젯 제품 이미지"
          className="mx-auto rounded-2xl shadow-xl w-full"
        />
      </main>

      {/* 기능 시연 섹션 */}
      <section id="features" className="bg-white py-20">
        <div className="container mx-auto max-w-6xl px-4">
          <h3 className="text-4xl font-bold text-center mb-12">주요 기능 시연</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-10">

            {/* 기능 1: AI 코디 추천 */}
            <div className="bg-gray-50 rounded-2xl p-8 text-center shadow-lg hover:shadow-2xl transition-shadow duration-300">
              <div className="flex justify-center mb-4"><StyleIcon /></div>
              <h4 className="text-2xl font-semibold mb-3">AI 코디 추천</h4>
              <p className="text-gray-600 mb-6">
                오늘의 날씨와 일정에 맞춰 옷장 속 옷들로 최적의 스타일을 제안합니다. 더 이상 아침마다 고민하지 마세요.
              </p>
              <button className="w-full px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition">
                데모 체험하기
              </button>
            </div>

            {/* 기능 2: 스마트 의류 관리 */}
            <div className="bg-gray-50 rounded-2xl p-8 text-center shadow-lg hover:shadow-2xl transition-shadow duration-300">
              <div className="flex justify-center mb-4"><CareIcon /></div>
              <h4 className="text-2xl font-semibold mb-3">스마트 의류 관리</h4>
              <p className="text-gray-600 mb-6">
                자동 스팀, 살균, 탈취 기능으로 언제나 새 옷처럼 쾌적하게 관리합니다. 드라이클리닝 비용과 시간을 절약하세요.
              </p>
              <button className="w-full px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition">
                기능 살펴보기
              </button>
            </div>

            {/* 기능 3: 내 옷장 원격 관리 */}
            <div className="bg-gray-50 rounded-2xl p-8 text-center shadow-lg hover:shadow-2xl transition-shadow duration-300">
              <div className="flex justify-center mb-4"><RemoteIcon /></div>
              <h4 className="text-2xl font-semibold mb-3">내 옷장 원격 관리</h4>
              <p className="text-gray-600 mb-6">
                스마트폰 앱으로 언제 어디서든 내 옷장의 모든 옷을 확인하고 관리할 수 있습니다. 쇼핑할 때도 유용하게 활용하세요.
              </p>
              <button className="w-full px-6 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition">
                앱 미리보기
              </button>
            </div>

          </div>
        </div>
      </section>

      {/* 푸터 */}
      <footer className="w-full bg-gray-800 text-gray-300 py-8 text-center">
        <p>© 2025 Dumir Inc. All rights reserved.</p>
        <p className="text-sm mt-2">당신의 삶을 바꾸는 스마트한 선택, 두미르</p>
      </footer>
    </div>
  );
}

export default App;


