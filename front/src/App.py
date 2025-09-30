// App.jsx
import React from "react";

function App() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center">
      {/* 헤더 */}
      <header className="w-full bg-blue-600 text-white py-6 text-center shadow-md">
        <h1 className="text-3xl font-bold">SmartLife Electronics</h1>
        <p className="mt-2 text-lg">당신의 삶을 스마트하게 바꿔드립니다</p>
      </header>

      {/* 메인 배너 */}
      <section className="w-full max-w-5xl mt-10 bg-white shadow-lg rounded-2xl p-8 text-center">
        <h2 className="text-2xl font-semibold mb-4">신제품 출시!</h2>
        <p className="text-gray-600 mb-6">
          혁신적인 AI 냉장고, 스마트 청소기, 최신형 TV로 당신의 생활을 업그레이드하세요.
        </p>
        <button className="px-6 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition">
          지금 만나보기
        </button>
      </section>

      {/* 제품 카드 */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-12 max-w-5xl">
        <div className="bg-white shadow-lg rounded-2xl p-6 text-center">
          <img
            src="https://via.placeholder.com/200"
            alt="냉장고"
            className="mx-auto mb-4 rounded-xl"
          />
          <h3 className="text-xl font-bold">AI 냉장고</h3>
          <p className="text-gray-600 mt-2">식재료 자동 관리 및 신선도 유지</p>
        </div>

        <div className="bg-white shadow-lg rounded-2xl p-6 text-center">
          <img
            src="https://via.placeholder.com/200"
            alt="청소기"
            className="mx-auto mb-4 rounded-xl"
          />
          <h3 className="text-xl font-bold">스마트 청소기</h3>
          <p className="text-gray-600 mt-2">AI 자율 주행, 집 안隅々까지 청소</p>
        </div>

        <div className="bg-white shadow-lg rounded-2xl p-6 text-center">
          <img
            src="https://via.placeholder.com/200"
            alt="TV"
            className="mx-auto mb-4 rounded-xl"
          />
          <h3 className="text-xl font-bold">4K 스마트 TV</h3>
          <p className="text-gray-600 mt-2">생생한 화질, 몰입형 엔터테인먼트</p>
        </div>
      </section>

      {/* 푸터 */}
      <footer className="w-full bg-gray-800 text-gray-200 py-6 mt-12 text-center">
        <p>© 2025 SmartLife Electronics. All rights reserved.</p>
      </footer>
    </div>
  );
}

export default App;
