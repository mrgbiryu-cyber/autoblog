"use client";

import { ArrowLeft, BookOpen, Key, Globe, ShieldCheck } from "lucide-react";
import Link from "next/link";

export default function ApiGuidePage() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 md:p-12">
      <div className="max-w-4xl mx-auto space-y-12">
        <header className="space-y-4">
          <Link href="/dashboard" className="inline-flex items-center gap-2 text-slate-400 hover:text-white transition">
            <ArrowLeft className="w-4 h-4" />
            대시보드로 돌아가기
          </Link>
          <h1 className="text-4xl font-extrabold tracking-tight flex items-center gap-3">
            <BookOpen className="w-10 h-10 text-cyan-400" />
            플랫폼 API 연동 가이드
          </h1>
          <p className="text-lg text-slate-400">
            자동 발행을 위해 각 블로그 플랫폼의 API 키를 발급받는 과정을 상세히 안내해 드립니다.
          </p>
        </header>

        <div className="grid gap-8">
          {/* Tistory Guide */}
          <section className="bg-slate-900 rounded-3xl border border-slate-800 p-8 space-y-6">
            <div className="flex items-center gap-3 border-b border-slate-800 pb-4">
              <div className="w-10 h-10 bg-orange-500 rounded-xl flex items-center justify-center font-bold text-white">T</div>
              <h2 className="text-2xl font-bold">티스토리 (Tistory)</h2>
            </div>
            <div className="space-y-4 text-slate-300">
              <p>1. <a href="https://www.tistory.com/guide/api/manage/register" target="_blank" className="text-cyan-400 underline">티스토리 API 등록 페이지</a>에 접속합니다.</p>
              <p>2. 앱 이름과 설명, 서비스 URL(http://localhost:3000 등)을 입력합니다.</p>
              <p>3. 발급된 **App ID**와 **Secret Key**를 복사합니다.</p>
              <p>4. 피크컨텐츠 대시보드의 블로그 수정 메뉴에서 해당 키를 입력하여 연동을 완료합니다.</p>
            </div>
          </section>

          {/* Google Blogger Guide */}
          <section className="bg-slate-900 rounded-3xl border border-slate-800 p-8 space-y-6">
            <div className="flex items-center gap-3 border-b border-slate-800 pb-4">
              <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center font-bold text-white">B</div>
              <h2 className="text-2xl font-bold">구글 블로거 (Blogger)</h2>
            </div>
            <div className="space-y-4 text-slate-300">
              <p>1. <a href="https://console.cloud.google.com/" target="_blank" className="text-cyan-400 underline">Google Cloud Console</a>에서 프로젝트를 생성합니다.</p>
              <p>2. **Blogger API v3**를 활성화합니다.</p>
              <p>3. 사용자 인증 정보에서 **OAuth 2.0 클라이언트 ID**를 생성합니다.</p>
              <p>4. 발급된 JSON 파일의 내용 또는 Access Token을 대시보드에 입력합니다.</p>
            </div>
          </section>

          {/* InBlog Guide */}
          <section className="bg-slate-900 rounded-3xl border border-slate-800 p-8 space-y-6">
            <div className="flex items-center gap-3 border-b border-slate-800 pb-4">
              <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center font-bold text-white">I</div>
              <h2 className="text-2xl font-bold">인블로그 (InBlog)</h2>
            </div>
            <div className="space-y-4 text-slate-300">
              <p>1. 인블로그 대시보드 설정의 **API** 메뉴로 이동합니다.</p>
              <p>2. 새 API Key를 생성하고 발급된 토큰을 복사합니다.</p>
              <p>3. 함께 제공되는 **Writer ID**를 대시보드에 입력하여 연동을 마무리합니다.</p>
            </div>
          </section>
        </div>

        <footer className="p-8 bg-cyan-500/10 rounded-3xl border border-cyan-500/20 flex items-center gap-4">
          <ShieldCheck className="w-8 h-8 text-cyan-400 shrink-0" />
          <p className="text-sm text-slate-400">
            입력하신 모든 API 키는 강력한 암호화 알고리즘으로 보호되며, 오직 포스팅 발행 목적으로만 사용됩니다.
          </p>
        </footer>
      </div>
    </div>
  );
}

