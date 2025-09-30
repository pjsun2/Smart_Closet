import React from "react";

// 1. 데이터 정의: 기능 카드에 들어갈 내용들을 배열로 관리합니다.
// 이렇게 하면 나중에 기능을 추가하거나 수정할 때 이 배열만 바꾸면 됩니다.
const featuresData = [
  {
    title: "AI 코디 추천",
    description: "오늘의 날씨와 당신의 스타일에 맞춰 완벽한 코디를 제안합니다.",
    icon: (
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
    ),
    bgColor: "bg-blue-100",
  },
  {
    title: "스마트 의류 관리",
    description: "자동 살균, 탈취, 주름 관리 기능으로 매일 새 옷처럼 관리하세요.",
    icon: (
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
    ),
    bgColor: "bg-green-100",
  },
  {
    title: "내 옷장 원격 관리",
    description:
      "언제 어디서든 스마트폰 앱으로 내 옷장의 모든 것을 확인하고 제어합니다.",
    icon: (
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
    ),
    bgColor: "bg-purple-100",
  },
];

// 2. 컴포넌트 분리: 각 UI 섹션을 별도의 컴포넌트로 만듭니다.

// 헤더 컴포넌트
const Header = () => (
  <header className="w-full bg-white text-gray-800 py-6 text-center shadow-md">
    <h1 className="text-4xl font-bold text-gray-900">Dumir 스마트 클로젯</h1>
    <p className="mt-2 text-lg text-gray-600">
      당신의 일상을 변화시킬 단 하나의 스마트 옷장
    </p>
  </header>
);

// 메인 배너 컴포넌트
const MainBanner = () => (
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
);

// 기능 카드 컴포넌트 (재사용 가능)
const FeatureCard = ({ icon, title, description, bgColor }) => (
  <div className="bg-white shadow-lg rounded-2xl p-8 text-center flex flex-col items-center">
    <div className={`p-4 rounded-full mb-4 ${bgColor}`}>{icon}</div>
    <h3 className="text-xl font-bold text-gray-800">{title}</h3>
    <p className="text-gray-600 mt-2">{description}</p>
  </div>
);

// 푸터 컴포넌트
const Footer = () => (
  <footer className="w-full bg-gray-800 text-gray-300 py-6 mt-12 text-center">
    <p>© 2025 Dumir Inc. All rights reserved.</p>
  </footer>
);

// 3. 메인 App 컴포넌트: 분리된 컴포넌트들을 조립하고, 데이터를 전달합니다.
function App() {
  return (
    <div className="min-h-screen bg-gray-100 flex flex-col items-center font-sans">
      <Header />
      <MainBanner />

      <section className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-4 max-w-5xl w-full px-4 md:px-0">
        {/* 데이터를 기반으로 기능 카드를 동적으로 생성합니다. */}
        {featuresData.map((feature) => (
          <FeatureCard
            key={feature.title}
            icon={feature.icon}
            title={feature.title}
            description={feature.description}
            bgColor={feature.bgColor}
          />
        ))}
      </section>

      <Footer />
    </div>
  );
}

export default App;

