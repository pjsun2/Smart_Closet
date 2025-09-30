import React, { memo } from "react";
import { motion } from "framer-motion";
import { MonitorSmartphone, Shirt, Sparkles } from "lucide-react";

// 색상 토큰을 한 곳에서 관리
const colorTokens = {
  primary: {
    from: "from-blue-500",
    to: "to-indigo-600",
    text: "text-blue-600",
    tint: "bg-blue-100",
  },
  success: {
    from: "from-emerald-500",
    to: "to-teal-600",
    text: "text-emerald-600",
    tint: "bg-emerald-100",
  },
  accent: {
    from: "from-violet-500",
    to: "to-purple-600",
    text: "text-violet-600",
    tint: "bg-violet-100",
  },
};

// Feature 타입 정의 (JS에서도 JSDoc으로 가독성↑)
/**
 * @typedef {Object} Feature
 * @property {string} title
 * @property {string} description
 * @property {React.ElementType} Icon
 * @property {{from:string,to:string,text:string,tint:string}} color
 */

/** @type {Feature[]} */
const features = [
  {
    title: "AI 코디 추천",
    description: "오늘의 날씨와 당신의 스타일에 맞춰 완벽한 코디를 제안합니다.",
    Icon: Sparkles,
    color: colorTokens.primary,
  },
  {
    title: "스마트 의류 관리",
    description: "자동 살균, 탈취, 주름 관리 기능으로 매일 새 옷처럼 관리하세요.",
    Icon: Shirt,
    color: colorTokens.success,
  },
  {
    title: "내 옷장 원격 관리",
    description:
      "언제 어디서든 스마트폰 앱으로 내 옷장의 모든 것을 확인하고 제어합니다.",
    Icon: MonitorSmartphone,
    color: colorTokens.accent,
  },
];

// 공통 애니메이션 프리셋
const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { duration: 0.5 } },
};

// 접근성: skip link
const SkipLink = () => (
  <a
    href="#main"
    className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:left-3 focus:z-50 bg-white text-gray-900 px-3 py-2 rounded-md shadow"
  >
    본문 바로가기
  </a>
);

// 헤더
const Header = () => (
  <header className="w-full bg-white text-gray-800 py-6 shadow-md">
    <div className="mx-auto max-w-screen-xl px-4 text-center">
      <h1 className="text-4xl font-bold tracking-tight text-gray-900">
        Dumir 스마트 클로젯
      </h1>
      <p className="mt-2 text-lg text-gray-600">
        당신의 일상을 변화시킬 단 하나의 스마트 옷장
      </p>
    </div>
  </header>
);

// 메인 배너
const MainBanner = () => (
  <section
    aria-label="주요 소개"
    className={`w-full my-10`}
  >
    <div
      className={`mx-auto max-w-screen-xl px-4`}
    >
      <motion.div
        initial="hidden"
        animate="show"
        variants={fadeUp}
        className={`bg-gradient-to-r ${colorTokens.primary.from} ${colorTokens.primary.to} text-white shadow-xl rounded-2xl p-10 text-center`}
      >
        <h2 className="text-3xl font-semibold mb-4">
          세상에 없던 의류 케어, Dumir가 시작합니다.
        </h2>
        <p className="text-indigo-100 mb-8 text-lg">
          혁신적인 AI 기술로 코디 추천부터 의류 관리, 원격 제어까지.
          <br />
          이제껏 경험하지 못한 스마트한 의류 라이프를 만나보세요.
        </p>
        <button
          aria-label="주요 기능 시연하기"
          className="px-8 py-3 bg-white text-blue-600 font-semibold rounded-xl hover:bg-gray-100 transition shadow-lg"
          onClick={() => alert("데모를 준비 중입니다")}
        >
          주요 기능 시연하기
        </button>
      </motion.div>
    </div>
  </section>
);

// 기능 카드
const FeatureCard = memo(function FeatureCard({ Icon, title, description, color }) {
  return (
    <motion.article
      variants={fadeUp}
      className="bg-white shadow-lg rounded-2xl p-8 text-center flex flex-col items-center"
    >
      <div className={`p-4 rounded-full mb-4 ${color.tint}`}>
        <Icon aria-hidden className={`h-10 w-10 ${color.text}`} />
      </div>
      <h3 className="text-xl font-bold text-gray-800">{title}</h3>
      <p className="text-gray-600 mt-2 leading-relaxed">{description}</p>
    </motion.article>
  );
});

// 푸터
const Footer = () => (
  <footer className="w-full bg-gray-900 text-gray-300 py-8 mt-12">
    <div className="mx-auto max-w-screen-xl px-4 text-center">
      <nav aria-label="푸터 링크" className="mb-3">
        <ul className="flex items-center justify-center gap-6 text-sm">
          <li><a className="hover:underline" href="#features">기능</a></li>
          <li><a className="hover:underline" href="#main">소개</a></li>
          <li><a className="hover:underline" href="#top">상단으로</a></li>
        </ul>
      </nav>
      <p>© 2025 Dumir Inc. All rights reserved.</p>
    </div>
  </footer>
);

// 메인 App
export default function App() {
  return (
    <div id="top" className="min-h-screen bg-gray-100 flex flex-col font-sans">
      <SkipLink />
      <Header />

      <main id="main" className="flex-1">
        <MainBanner />

        <section
          id="features"
          aria-label="주요 기능"
          className="mx-auto max-w-screen-xl w-full px-4 md:px-6"
        >
          <motion.div
            initial="hidden"
            whileInView="show"
            viewport={{ once: true, amount: 0.2 }}
            className="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-8 mt-4"
          >
            {features.map((f) => (
              <FeatureCard
                key={f.title}
                Icon={f.Icon}
                title={f.title}
                description={f.description}
                color={f.color}
              />
            ))}
          </motion.div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
