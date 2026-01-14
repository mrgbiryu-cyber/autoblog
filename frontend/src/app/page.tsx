import Link from "next/link";
import { Bot, Rocket, TrendingUp, CheckCircle, ArrowRight, ShieldCheck } from "lucide-react";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white font-sans text-gray-900">
      
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
            <Link href="/login?mode=signup" className="w-full sm:w-auto px-8 py-4 bg-blue-600 text-white rounded-xl font-bold text-lg hover:bg-blue-700 shadow-lg hover:shadow-blue-500/30 transition transform hover:-translate-y-1 flex items-center justify-center">
              <Bot className="w-5 h-5 mr-2" />
              Email 가입
            </Link>
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

      {/* 4 AI Collaboration Section */}
      <section className="py-32 bg-slate-950 text-white overflow-hidden relative">
        {/* Background Gradients */}
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-600/10 blur-[120px] rounded-full"></div>
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-600/10 blur-[120px] rounded-full"></div>

        <div className="max-w-7xl mx-auto px-6 relative z-10">
          <div className="text-center space-y-6 mb-24">
            <div className="inline-flex items-center px-4 py-1.5 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-xs font-bold tracking-widest uppercase">
              Core Engine
            </div>
            <h2 className="text-4xl md:text-5xl font-black tracking-tight leading-tight">
              V6만의 독보적인 <br className="md:hidden" />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500">
                4개 AI 협업 시스템
              </span>
            </h2>
            <p className="text-slate-400 text-lg max-w-2xl mx-auto">
              단순한 글 작성을 넘어, 검색 엔진의 심장을 꿰뚫는 4개의 전용 AI가 <br className="hidden md:block" />
              실시간으로 소통하며 최상의 포스팅을 완성합니다.
            </p>
          </div>

          <div className="grid lg:grid-cols-4 gap-8">
            {[
              { 
                step: "01", 
                title: "SEO 데이터 엔진", 
                desc: "실시간 검색 트렌드와 경쟁 문서를 심층 분석하여 클릭을 부르는 황금 키워드를 발굴합니다.",
                icon: <TrendingUp className="w-8 h-8" />,
                color: "cyan"
              },
              { 
                step: "02", 
                title: "원문 교차 검증 AI", 
                desc: "다양한 웹 리서치 데이터를 실시간으로 대조하여 AI 특유의 할루시네이션(환각) 없는 정확한 정보만 제공합니다.",
                icon: <ShieldCheck className="w-8 h-8" />,
                color: "blue"
              },
              { 
                step: "03", 
                title: "페르소나 전문 작가", 
                desc: "사용자가 설정한 말투와 지식 수준을 완벽히 흡수하여 실제 전문가가 쓴 듯한 자연스러운 문체를 구사합니다.",
                icon: <Bot className="w-8 h-8" />,
                color: "purple"
              },
              { 
                step: "04", 
                title: "상호 검수 에디터", 
                desc: "가독성, 이미지 배치, SEO 점수를 최종적으로 0.1초 만에 스캔하여 발행 전 완벽한 상태를 보장합니다.",
                icon: <CheckCircle className="w-8 h-8" />,
                color: "emerald"
              }
            ].map((item, idx) => (
              <div key={idx} className="group relative bg-slate-900/50 p-8 rounded-[2rem] border border-white/5 hover:border-cyan-500/30 transition-all duration-500 hover:-translate-y-2">
                <div className={`w-16 h-16 rounded-2xl bg-slate-950 border border-white/10 flex items-center justify-center mb-8 group-hover:scale-110 transition-transform duration-500 text-${item.color}-400`}>
                  {item.icon}
                </div>
                <div className="space-y-4">
                  <div className="flex items-center gap-3">
                    <span className="text-[10px] font-black text-cyan-500 tracking-tighter bg-cyan-500/10 px-2 py-0.5 rounded-md">AI {item.step}</span>
                    <h3 className="text-xl font-bold">{item.title}</h3>
                  </div>
                  <p className="text-sm text-slate-400 leading-relaxed min-h-[80px]">
                    {item.desc}
                  </p>
                </div>
                {/* Decoration */}
                <div className="absolute top-4 right-8 text-4xl font-black text-white/5 tracking-tighter">{item.step}</div>
              </div>
            ))}
          </div>

          {/* Visual Connector Line (Decorative) */}
          <div className="hidden lg:block mt-20 text-center">
            <div className="inline-flex items-center gap-4 text-xs font-bold text-slate-600 tracking-[0.3em] uppercase">
              <span className="w-12 h-px bg-slate-800"></span>
              Synchronized Multi-AI Workflow
              <span className="w-12 h-px bg-slate-800"></span>
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
