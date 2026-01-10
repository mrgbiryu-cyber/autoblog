import Link from "next/link";
import { Bot, Rocket, TrendingUp, CheckCircle, ArrowRight } from "lucide-react";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white font-sans text-gray-900">
      
      {/* 1. 네비게이션 바 (GNB) */}
      <nav className="fixed w-full bg-white/80 backdrop-blur-md border-b border-gray-100 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="p-2 bg-blue-600 rounded-lg">
              <Bot className="w-6 h-6 text-white" />
            </div>
            <span className="text-xl font-bold tracking-tight">AI Blog Auto-Pilot</span>
          </div>
          <div className="hidden md:flex items-center space-x-8 text-sm font-medium text-gray-600">
            <a href="#features" className="hover:text-blue-600 transition">기능 소개</a>
            <a href="#pricing" className="hover:text-blue-600 transition">요금제</a>
            <Link href="/login" className="px-5 py-2.5 bg-gray-900 text-white rounded-full hover:bg-gray-800 transition">
              로그인
            </Link>
          </div>
        </div>
      </nav>

      {/* 2. 히어로 섹션 (가장 중요한 첫인상) */}
      <section className="pt-32 pb-20 px-6">
        <div className="max-w-4xl mx-auto text-center space-y-8">
          <div className="inline-flex items-center px-4 py-2 rounded-full bg-blue-50 text-blue-700 text-sm font-semibold mb-4 border border-blue-100">
            <span className="flex h-2 w-2 bg-blue-600 rounded-full mr-2"></span>
            GPT-4o & Gemini 2.5 탑재
          </div>
          <h1 className="text-5xl md:text-6xl font-extrabold tracking-tight leading-tight text-gray-900">
            블로그 포스팅, <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600">
              AI에게 맡기고 수익만 챙기세요.
            </span>
          </h1>
          <p className="text-xl text-gray-500 max-w-2xl mx-auto leading-relaxed">
            주제 선정부터 글쓰기, SEO 최적화, 이미지 생성, 그리고 업로드까지.
            <br className="hidden md:block" />
            단 한 번의 클릭으로 귀찮은 블로그 운영을 자동화하세요.
          </p>
          
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
            <Link href="/dashboard" className="w-full sm:w-auto px-8 py-4 bg-blue-600 text-white rounded-xl font-bold text-lg hover:bg-blue-700 shadow-lg hover:shadow-blue-500/30 transition transform hover:-translate-y-1 flex items-center justify-center">
              <Rocket className="w-5 h-5 mr-2" />
              무료로 시작하기
            </Link>
            <a href="#demo" className="w-full sm:w-auto px-8 py-4 bg-gray-100 text-gray-700 rounded-xl font-bold text-lg hover:bg-gray-200 transition flex items-center justify-center">
              데모 영상 보기
            </a>
          </div>
          
          <p className="text-sm text-gray-400 mt-4">
            * 신용카드 등록 없이 즉시 체험 가능
          </p>
        </div>
      </section>

      {/* 3. 핵심 기능 3가지 */}
      <section id="features" className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid md:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-100 hover:shadow-md transition">
              <div className="w-12 h-12 bg-blue-100 text-blue-600 rounded-xl flex items-center justify-center mb-6">
                <TrendingUp className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-bold mb-3">실시간 트렌드 분석</h3>
              <p className="text-gray-500 leading-relaxed">
                구글 트렌드와 뉴스 데이터를 분석하여, 지금 당장 조회수가 터질 수 있는 '황금 키워드'를 AI가 찾아냅니다.
              </p>
            </div>
            
            {/* Feature 2 */}
            <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-100 hover:shadow-md transition">
              <div className="w-12 h-12 bg-purple-100 text-purple-600 rounded-xl flex items-center justify-center mb-6">
                <Bot className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-bold mb-3">사람 같은 글쓰기</h3>
              <p className="text-gray-500 leading-relaxed">
                단순 번역투가 아닙니다. 사용자가 설정한 페르소나(전문가, 친근한 이웃 등)에 맞춰 자연스러운 글을 작성합니다.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-100 hover:shadow-md transition">
              <div className="w-12 h-12 bg-green-100 text-green-600 rounded-xl flex items-center justify-center mb-6">
                <CheckCircle className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-bold mb-3">SEO 점수 자동 검수</h3>
              <p className="text-gray-500 leading-relaxed">
                네이버와 구글의 상위 노출 알고리즘을 분석하여, 발행 전 SEO 점수를 채점하고 부족한 부분을 스스로 수정합니다.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* 4. 하단 CTA */}
      <section className="py-24 px-6 text-center">
        <div className="max-w-3xl mx-auto bg-gray-900 rounded-3xl p-12 text-white shadow-2xl">
          <h2 className="text-3xl font-bold mb-6">지금 바로 자동화를 경험하세요.</h2>
          <p className="text-gray-400 mb-8 text-lg">
            초기 베타 기간 동안 모든 기능을 무료로 제공하고 있습니다. <br/>
            선착순 100명에게는 평생 할인 혜택을 드립니다.
          </p>
          <Link href="/dashboard" className="inline-flex items-center px-8 py-4 bg-white text-gray-900 rounded-xl font-bold text-lg hover:bg-gray-100 transition">
            지금 시작하기 <ArrowRight className="w-5 h-5 ml-2" />
          </Link>
        </div>
      </section>

      {/* 푸터 */}
      <footer className="py-8 text-center text-gray-400 text-sm border-t border-gray-100">
        © 2026 AI Blog Auto-Pilot. All rights reserved.
      </footer>
    </div>
  );
}
