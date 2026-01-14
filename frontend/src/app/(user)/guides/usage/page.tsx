"use client";

import { ArrowLeft, PlayCircle, MousePointer2, Zap, Settings, BarChart3, Rocket } from "lucide-react";
import Link from "next/link";

export default function UsageGuidePage() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 md:p-12">
      <div className="max-w-4xl mx-auto space-y-16">
        <header className="space-y-4">
          <Link href="/dashboard" className="inline-flex items-center gap-2 text-slate-400 hover:text-white transition">
            <ArrowLeft className="w-4 h-4" />
            대시보드로 돌아가기
          </Link>
          <h1 className="text-4xl font-extrabold tracking-tight flex items-center gap-3">
            <PlayCircle className="w-10 h-10 text-cyan-400" />
            PeakContent 이용 방법 가이드
          </h1>
          <p className="text-lg text-slate-400">
            자동 블로그 운영의 첫 걸음부터 수익화까지, 핵심 기능을 마스터하는 튜토리얼입니다.
          </p>
        </header>

        <div className="grid gap-12">
          {/* Step 1: Blog Connection */}
          <section className="relative pl-12 space-y-4">
            <div className="absolute left-0 top-0 w-8 h-8 bg-cyan-500 text-slate-950 rounded-full flex items-center justify-center font-bold">1</div>
            <h2 className="text-2xl font-bold flex items-center gap-2">
              <Settings className="w-6 h-6 text-cyan-400" />
              블로그 플랫폼 연동하기
            </h2>
            <div className="bg-slate-900 rounded-3xl border border-slate-800 p-8 space-y-4 text-slate-300">
              <p>대시보드 상단의 **[+ 블로그 추가]** 버튼을 눌러 본인의 블로그 플랫폼(네이버, 티스토리 등)을 등록하세요.</p>
              <ul className="list-disc list-inside space-y-2 text-sm">
                <li>별칭: 관리용 이름 (예: 맛집 블로그 1호)</li>
                <li>API 키: 각 플랫폼 가이드에 따라 발급받은 키 입력</li>
                <li>페르소나: AI의 말투 설정 (예: 전문 기자, 친근한 이웃)</li>
              </ul>
              <div className="mt-4 p-4 bg-slate-950 rounded-2xl border border-slate-800 text-xs text-slate-500">
                💡 팁: 페르소나에 '전문 마케터'를 입력하면 좀 더 논리적이고 설득력 있는 글이 작성됩니다.
              </div>
            </div>
          </section>

          {/* Step 2: Content Generation */}
          <section className="relative pl-12 space-y-4">
            <div className="absolute left-0 top-0 w-8 h-8 bg-cyan-500 text-slate-950 rounded-full flex items-center justify-center font-bold">2</div>
            <h2 className="text-2xl font-bold flex items-center gap-2">
              <Zap className="w-6 h-6 text-yellow-400" />
              단건 포스팅 생성 (즉시 생성)
            </h2>
            <div className="bg-slate-900 rounded-3xl border border-slate-800 p-8 space-y-4 text-slate-300">
              <p>원하는 주제와 키워드를 입력하고 **[분석하기]**를 누르면 AI가 SEO 최적화 프롬프트를 구성합니다.</p>
              <div className="grid md:grid-cols-2 gap-4 mt-4">
                <div className="p-4 bg-slate-950 rounded-2xl border border-slate-800">
                  <h4 className="font-bold text-white mb-2">프롬프트 확인</h4>
                  <p className="text-xs">생성된 프롬프트가 본인의 의도와 맞는지 확인하고 수정할 수 있습니다.</p>
                </div>
                <div className="p-4 bg-slate-950 rounded-2xl border border-slate-800">
                  <h4 className="font-bold text-white mb-2">포스팅 하기</h4>
                  <p className="text-xs">설정 저장 후 포스팅 하기 버튼을 누르면 글과 이미지가 동시에 생성됩니다.</p>
                </div>
              </div>
            </div>
          </section>

          {/* Step 3: Scheduling */}
          <section className="relative pl-12 space-y-4">
            <div className="absolute left-0 top-0 w-8 h-8 bg-cyan-500 text-slate-950 rounded-full flex items-center justify-center font-bold">3</div>
            <h2 className="text-2xl font-bold flex items-center gap-2">
              <Rocket className="w-6 h-6 text-purple-400" />
              스케줄링 자동화 (벌크 등록)
            </h2>
            <div className="bg-slate-900 rounded-3xl border border-slate-800 p-8 space-y-4 text-slate-300">
              <p>수십 개의 키워드를 한 번에 등록하고 정해진 시간에 자동으로 발행되도록 설정하세요.</p>
              <p className="text-sm">키워드 당 하나의 포스팅이 순차적으로 발행되며, 모든 키워드가 소진되면 처음부터 다시 순환하여 발행됩니다.</p>
              <div className="p-4 bg-emerald-500/10 rounded-2xl border border-emerald-500/20 text-emerald-400 text-sm">
                ✅ 자동화의 핵심: 발행 주기를 '매일' 혹은 '주 n회'로 설정하여 블로그의 지수를 꾸준히 관리하세요.
              </div>
            </div>
          </section>

          {/* Step 4: Tracking */}
          <section className="relative pl-12 space-y-4">
            <div className="absolute left-0 top-0 w-8 h-8 bg-cyan-500 text-slate-950 rounded-full flex items-center justify-center font-bold">4</div>
            <h2 className="text-2xl font-bold flex items-center gap-2">
              <BarChart3 className="w-6 h-6 text-blue-400" />
              성과 분석 및 트래킹
            </h2>
            <div className="bg-slate-900 rounded-3xl border border-slate-800 p-8 space-y-4 text-slate-300">
              <p>발행된 포스팅의 검색 순위와 조회수를 실시간으로 확인하세요.</p>
              <ul className="list-disc list-inside space-y-2 text-sm">
                <li>순위 트래킹: 메인 키워드가 구글/네이버 몇 위에 노출되는지 추적</li>
                <li>원문 링크: 버튼 하나로 발행된 실제 블로그 페이지로 이동</li>
                <li>성능 로그: AI 엔진의 작업 기록을 실시간으로 모니터링</li>
              </ul>
            </div>
          </section>
        </div>

        <footer className="text-center py-12 border-t border-slate-900">
          <p className="text-slate-500 mb-6">준비가 되셨나요? 지금 바로 첫 포스팅을 시작해보세요.</p>
          <Link href="/dashboard" className="inline-flex items-center gap-2 bg-cyan-500 text-slate-950 px-8 py-4 rounded-2xl font-bold hover:bg-cyan-400 transition">
            대시보드로 가기 <MousePointer2 className="w-5 h-5" />
          </Link>
        </footer>
      </div>
    </div>
  );
}

