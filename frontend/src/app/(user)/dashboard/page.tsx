"use client";

import { Fragment, useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Bot, CreditCard, Copy, Eye, Loader2, Shield, Search, CircleAlert, FileText } from "lucide-react";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import KeywordSearchModal from "@/components/KeywordSearchModal";
import DimLoadingPopup from "@/components/DimLoadingPopup";
import {
  fetchBlogAnalysis,
  buildHeaders,
  fetchCreditStatus,
  fetchKeywordTracking,
  fetchScheduleConfig,
  generatePreviewHtml,
  saveScheduleConfig,
  CreditStatusPayload,
  KeywordTrackerRow,
  SchedulePayload,
  PreviewRequest,
  PreviewResponse,
  publishPostManual,
  trackPost,
} from "../../../lib/api";
// NOTE: 기존에는 유저 공통 설정(`/config/blog-settings`)에 저장했지만,
// 현재 UX 요구사항은 "블로그별"로 category/prompt/persona/wordRange/imageCount가 저장되어야 합니다.

// 환경변수를 못 읽더라도 무조건 서버를 바라보게 합니다.
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://34.64.50.56";

const WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const TOTAL_BLOG_SLOTS = 5;
const PANEL_DEFAULT_FORM = {
  alias: "",
  platform_type: "Naver",
  blog_url: "",
  blog_id: "",
  api_access_token: "",
};
export default function Dashboard() {
  const [creditInfo, setCreditInfo] = useState<CreditStatusPayload>({
    current_credit: 0,
    upcoming_deduction: 0,
  });
  const [topic, setTopic] = useState("AI Marketing Automation");
  const [personaText, setPersonaText] = useState("전문 SEO 마케터처럼");
  const [previewHtml, setPreviewHtml] = useState("");
  const [modalOpen, setModalOpen] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [keywordTracker, setKeywordTracker] = useState<KeywordTrackerRow[]>([]);
  const [schedule, setSchedule] = useState<SchedulePayload>({
    frequency: "daily",
    posts_per_day: 1,
    days: ["Mon", "Wed", "Fri"],
    target_times: ["09:00"],
  });
  const [scheduleSaving, setScheduleSaving] = useState(false);
  const [statusMessages, setStatusMessages] = useState<string[]>([]);
  const [imageStatus, setImageStatus] = useState<"idle" | "processing" | "completed">("idle");
  const [imageTotal, setImageTotal] = useState(0);
  const [completedImages, setCompletedImages] = useState(0);
  const [imageCards, setImageCards] = useState<{id: number; src: string | null}[]>([]);
  const imageTimersRef = useRef<ReturnType<typeof setTimeout>[]>([]);
  const [previewImageCount, setPreviewImageCount] = useState(3);
  const [analysisCategory, setAnalysisCategory] = useState("");
  const [analysisPrompt, setAnalysisPrompt] = useState("");
  const [analysisButtonText, setAnalysisButtonText] = useState("분석하기");
  const router = useRouter();
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [wordRange, setWordRange] = useState({ min: 800, max: 1200 });
  const [blogs, setBlogs] = useState<any[]>([]);
  const [postsStatus, setPostsStatus] = useState<any[]>([]);
  const [panelMode, setPanelMode] = useState<"create" | "edit">("create");
  const [panelForm, setPanelForm] = useState({
    alias: "",
    platform_type: "Naver",
    blog_url: "",
    blog_id: "",
    api_access_token: "",
  });
  const [selectedBlogId, setSelectedBlogId] = useState<number | null>(null);
  const [selectedCreateSlotIdx, setSelectedCreateSlotIdx] = useState<number | null>(null);
  const [regMode, setRegMode] = useState<"single" | "schedule">("single");
  const [keywordSearchOpen, setKeywordSearchOpen] = useState(false);
  const [dimLoadingOpen, setDimLoadingOpen] = useState(false);
  const [dimLoadingStatus, setDimLoadingStatus] = useState<"loading" | "success" | "error">("loading");
  const [dimLoadingLogs, setDimLoadingLogs] = useState<string[]>([]);
  const selectedBlog = blogs.find((blog) => blog.id === selectedBlogId);
  const [generateResult, setGenerateResult] = useState<PreviewResponse | null>(null);

  useEffect(() => {
    if (!selectedBlog) {
      setTopic("AI Marketing Automation");
      setPersonaText("전문 SEO 마케터처럼");
      setWordRange({ min: 800, max: 1200 });
      setPreviewImageCount(3);
      setAnalysisCategory("");
      setAnalysisPrompt("");
      return;
    }

    // topic은 "관심 주제"이며 카테고리와 분리됩니다.
    setTopic(selectedBlog.interest_topic ?? topic ?? "AI Marketing Automation");
    setPersonaText(selectedBlog.persona ?? "전문 SEO 마케터처럼");
    setWordRange({
      min: selectedBlog.word_range?.min ?? 800,
      max: selectedBlog.word_range?.max ?? 1200,
    });
    setPreviewImageCount(selectedBlog.image_count ?? 3);
    setAnalysisCategory(selectedBlog.default_category ?? "");
    setAnalysisPrompt(selectedBlog.custom_prompt ?? "");
  }, [selectedBlog]);

  const clearImageTimers = () => {
    imageTimersRef.current.forEach((timer) => clearTimeout(timer));
    imageTimersRef.current = [];
  };

  const { displayName } = useAuth();

  useEffect(() => {
    return () => {
      clearImageTimers();
    };
  }, []);

  // NOTE: Dashboard 컴포넌트 내부에서 BlogSettingsPanel을 "컴포넌트"로 정의하고 (<BlogSettingsPanel />)
  // 렌더하면, 렌더링마다 함수 레퍼런스가 바뀌면서 React가 패널을 언마운트/리마운트할 수 있습니다.
  // 그 결과 입력 중 포커스가 한 글자마다 튕기는 현상이 발생할 수 있어
  // 컴포넌트가 아니라 "렌더 함수"로 호출해 DOM을 유지합니다.
  const renderBlogSettingsPanel = () => {
    const blog = selectedBlog;
    const displayAlias = blog?.alias || panelForm.alias || "새 블로그 등록";
    const displayUrl = blog?.blog_url || panelForm.blog_url || "등록 대기";
    const displayPlatform = blog?.platform_type || panelForm.platform_type;
    const hasApiKey = !!(blog?.api_key_data?.access_token || panelForm.api_access_token);
    const statusText = blog ? blog.status || "연결 대기" : "등록 전";

    const hasAnalysis = Boolean(analysisCategory || analysisPrompt);

    return (
      <div className="rounded-3xl border border-slate-800 bg-slate-950/60 p-6 space-y-8 text-slate-100">
        {/* 1. 공통 설정 섹션 */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold flex items-center gap-2">
              <Shield className="w-5 h-5 text-cyan-400" />
              공통 설정
            </h3>
            <div className="text-xs text-slate-400">
              ID: {blog?.id || "신규"} | 상태: {statusText}
            </div>
          </div>
          
          <div className="grid gap-4 md:grid-cols-3">
            <label className="space-y-2 text-sm text-slate-300">
              블로그 별칭
              <input
                className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-slate-100 placeholder:text-slate-500 focus:border-cyan-400 focus:outline-none"
                value={panelForm.alias}
                onChange={(e) => handlePanelFormChange("alias", e.target.value)}
                placeholder="내 티스토리 1호"
              />
            </label>
            <label className="space-y-2 text-sm text-slate-300">
              플랫폼
              <select
                className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-slate-100 focus:border-cyan-400 focus:outline-none"
                value={panelForm.platform_type}
                onChange={(e) => handlePanelFormChange("platform_type", e.target.value)}
              >
                {["Naver", "Blogger", "Tistory", "InBlog", "WordPress"].map((platform) => (
                  <option key={platform} value={platform}>
                    {platform}
                  </option>
                ))}
              </select>
            </label>
            <label className="space-y-2 text-sm text-slate-300">
              블로그 URL
              <input
                className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-slate-100 placeholder:text-slate-500 focus:border-cyan-400 focus:outline-none"
                value={panelForm.blog_url}
                onChange={(e) => handlePanelFormChange("blog_url", e.target.value)}
                placeholder="https://example.tistory.com"
              />
            </label>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <label className="space-y-2 text-sm text-slate-300">
              블로그 ID / 사용자 ID
              <input
                className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-slate-100 placeholder:text-slate-500 focus:border-cyan-400 focus:outline-none"
                value={panelForm.blog_id}
                onChange={(e) => handlePanelFormChange("blog_id", e.target.value)}
                placeholder="tistory-id"
              />
            </label>
            <label className="space-y-2 text-sm text-slate-300">
              API 키 / 액세스 토큰
              <input
                type="password"
                className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-slate-100 placeholder:text-slate-500 focus:border-cyan-400 focus:outline-none"
                value={panelForm.api_access_token}
                onChange={(e) => handlePanelFormChange("api_access_token", e.target.value)}
                placeholder="••••••••••••••••"
              />
            </label>
          </div>

          <label className="block space-y-2 text-sm text-slate-300">
            페르소나 설정
            <div className="flex gap-2">
              <input
                type="text"
                className="flex-1 rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-slate-100 placeholder:text-slate-500 focus:border-cyan-400 focus:outline-none"
                placeholder="예: 전문 작가처럼 신뢰감 있게, 친근한 이웃처럼 부드럽게"
                value={personaText}
                onChange={(e) => setPersonaText(e.target.value)}
              />
            </div>
            <div className="flex flex-wrap gap-2 mt-1">
              {['전문 작가', '친근한 이웃', 'IT 전문가', '뷰티 인플루언서'].map(p => (
                <button 
                  key={p} 
                  onClick={() => setPersonaText(p)}
                  className="px-2 py-1 rounded-lg border border-slate-800 bg-slate-900 text-[10px] text-slate-400 hover:border-cyan-500 hover:text-cyan-400 transition"
                >
                  #{p}
                </button>
              ))}
            </div>
          </label>
        </div>

        <hr className="border-slate-800" />

        {/* 2. 등록 모드 토글 */}
        <div className="flex items-center justify-center">
          <div className="bg-slate-900 p-1 rounded-2xl flex border border-slate-800">
            <button
              onClick={() => setRegMode("single")}
              className={`px-6 py-2 rounded-xl text-sm font-bold transition ${
                regMode === "single" ? "bg-cyan-500 text-slate-950 shadow-lg" : "text-slate-400 hover:text-slate-200"
              }`}
            >
              단건 등록
            </button>
            <button
              onClick={() => setRegMode("schedule")}
              className={`px-6 py-2 rounded-xl text-sm font-bold transition ${
                regMode === "schedule" ? "bg-cyan-500 text-slate-950 shadow-lg" : "text-slate-400 hover:text-slate-200"
              }`}
            >
              스케줄링 자동등록
            </button>
          </div>
        </div>

        {/* 3-1. 단건 등록 섹션 */}
        {regMode === "single" && (
          <div className="space-y-6 animate-in fade-in slide-in-from-top-2">
            <div className="grid gap-4 md:grid-cols-2">
              <label className="space-y-2 text-sm text-slate-300">
                포스팅 주제 / 키워드
                <div className="flex gap-2">
                  <input
                    className="flex-1 rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-slate-100 placeholder:text-slate-500 focus:border-cyan-400 focus:outline-none"
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    placeholder="예: 강남역 맛집 베스트 5"
                  />
                  <button
                    onClick={() => setKeywordSearchOpen(true)}
                    className="p-3 rounded-2xl border border-slate-700 bg-slate-900 hover:border-cyan-400 text-slate-300 transition"
                  >
                    <Search className="w-5 h-5" />
                  </button>
                </div>
              </label>
              <label className="space-y-2 text-sm text-slate-300">
                이미지 생성 개수
                <input
                  type="number"
                  min={1}
                  max={8}
                  className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-slate-100 focus:border-cyan-400 focus:outline-none"
                  value={previewImageCount}
                  onChange={(e) => setPreviewImageCount(Math.max(1, Number(e.target.value)))}
                />
              </label>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <label className="space-y-2 text-sm text-slate-300">
                글자수 범위 (min / max)
                <div className="flex gap-3">
                  <input
                    type="number"
                    className="w-1/2 rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-slate-100 focus:border-cyan-400 focus:outline-none"
                    value={wordRange.min}
                    onChange={(e) => updateWordRange("min", Number(e.target.value))}
                  />
                  <input
                    type="number"
                    className="w-1/2 rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-slate-100 focus:border-cyan-400 focus:outline-none"
                    value={wordRange.max}
                    onChange={(e) => updateWordRange("max", Number(e.target.value))}
                  />
                </div>
              </label>
              <div className="rounded-2xl border border-slate-800 bg-slate-900 px-5 py-4 text-sm flex items-center justify-between">
                <div>
                  <p className="text-xs text-slate-400">예상 소모 크레딧</p>
                  <p className="text-xl font-bold text-white">{creditEstimate} C</p>
                </div>
                <div className="text-right text-[10px] text-slate-500">
                  이미지 {previewImageCount}장 <br /> 최대 {wordRange.max}자 기준
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 3-2. 스케줄링 섹션 */}
        {regMode === "schedule" && (
          <div className="space-y-6 animate-in fade-in slide-in-from-top-2">
            <label className="block space-y-2 text-sm text-slate-300">
              벌크 키워드 입력 (엔터로 구분)
              <textarea
                className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-slate-100 placeholder:text-slate-500 focus:border-cyan-400 focus:outline-none"
                rows={4}
                placeholder="강남역 카페&#10;홍대 맛집&#10;제주도 여행 코스"
              />
              <p className="text-[10px] text-amber-400 flex items-center gap-1">
                <CircleAlert className="w-3 h-3" />
                입력된 키워드 순서대로 설정된 주기에 맞춰 자동 발행됩니다.
              </p>
            </label>

            <div className="grid gap-4 md:grid-cols-3">
              <label className="space-y-2 text-sm text-slate-300">
                발행 빈도
                <select
                  className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-slate-100 focus:border-cyan-400 focus:outline-none"
                  value={schedule.frequency}
                  onChange={(e) => setSchedule((p: any) => ({...p, frequency: e.target.value}))}
                >
                  <option value="hourly">매시간</option>
                  <option value="daily">매일</option>
                  <option value="weekly">매주</option>
                </select>
              </label>
              <label className="space-y-2 text-sm text-slate-300">
                하루 발행 수
                <input
                  type="number"
                  className="w-full rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-slate-100 focus:border-cyan-400 focus:outline-none"
                  value={schedule.posts_per_day}
                  onChange={(e) => setSchedule((p: any) => ({...p, posts_per_day: Number(e.target.value)}))}
                />
              </label>
              <div className="space-y-2">
                <span className="text-sm text-slate-300">스케줄 상태</span>
                <div className="flex items-center gap-3 py-3">
                   <button 
                    onClick={() => setSchedule((p: any) => ({...p, is_active: !p.is_active}))}
                    className={`flex-1 py-1 rounded-xl text-xs font-bold transition ${
                      schedule.is_active ? "bg-emerald-500 text-white" : "bg-slate-800 text-slate-400"
                    }`}
                   >
                     {schedule.is_active ? "스케줄링 활성" : "스케줄링 중단"}
                   </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* 4. 분석 및 저장 버튼 */}
        <div className="pt-4 border-t border-slate-800">
          <div className="flex flex-wrap gap-3">
            <button
              onClick={handleAnalyze}
              disabled={analysisLoading}
              className="px-6 py-3 rounded-2xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold transition disabled:opacity-50"
            >
              {analysisLoading ? "분석 중..." : "블로그 스타일 분석하기"}
            </button>
            
            {hasAnalysis && (
              <button
                onClick={handleSaveAll}
                disabled={saveLoading}
                className="px-6 py-3 rounded-2xl bg-slate-800 hover:bg-slate-700 text-white font-bold border border-slate-700 transition"
              >
                {saveLoading ? "저장 중..." : "설정 저장"}
              </button>
            )}

            {regMode === "single" && (
              <button
                onClick={() => handlePreview(false)}
                disabled={previewLoading}
                className="px-8 py-3 rounded-2xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold shadow-lg shadow-cyan-500/20 transition disabled:opacity-50 ml-auto"
              >
                {previewLoading ? "생성 중..." : "포스팅 하기"}
              </button>
            )}
          </div>

          {hasAnalysis && (
            <div className="mt-4 p-4 rounded-2xl bg-slate-900 border border-slate-800 space-y-2">
              <p className="text-xs text-slate-400 uppercase tracking-widest">분석된 프롬프트 (수정 가능)</p>
              <textarea
                className="w-full bg-transparent text-sm text-slate-300 border-none focus:ring-0 resize-none"
                rows={3}
                value={analysisPrompt}
                onChange={(e) => setAnalysisPrompt(e.target.value)}
              />
            </div>
          )}
        </div>

        {/* 5. 생성 결과 및 이미지 상태 */}
        <div className="space-y-6 pt-6 border-t border-slate-800">
          <div className="flex flex-wrap gap-3 text-sm">
            {previewHtml && (
              <button
                onClick={() => setModalOpen(true)}
                className="rounded-2xl border border-slate-200 bg-white px-5 py-3 text-sm font-semibold text-slate-900 hover:border-slate-400"
              >
                <span className="flex items-center gap-2">
                  <Eye className="w-4 h-4" />
                  미리보기 열기
                </span>
              </button>
            )}
            {generateResult && (
              <button
                onClick={handleDownloadAll}
                className="rounded-2xl px-5 py-3 text-sm font-semibold bg-emerald-500 text-white"
              >
                다운로드
              </button>
            )}
          </div>
          
          <p className="text-xs text-slate-500">
            HTML 복사는 모달에서 복사 버튼을 이용하세요.{" "}
            {imageStatus === "processing"
              ? `이미지 생성 중 (${completedImages}/${imageTotal})...`
              : imageStatus === "completed"
              ? "이미지 생성이 완료되었습니다."
              : ""}
          </p>

          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {imageCards.length === 0 && (
              <div className="rounded-2xl border border-dashed border-slate-700 p-4 text-center text-xs text-slate-500">
                이미지 생성 요청 시 스켈레톤이 표시됩니다.
              </div>
            )}
            {imageCards.map((card) => (
              <div key={card.id} className="rounded-2xl border border-slate-800 bg-slate-950 p-3 shadow-inner">
                <div className="h-40 w-full overflow-hidden rounded-2xl bg-slate-900">
                  {card.src ? (
                    <img src={card.src} alt={`이미지 ${card.id}`} className="h-full w-full object-cover" />
                  ) : (
                    <div className="h-full w-full animate-pulse bg-gradient-to-br from-slate-900 to-slate-800" />
                  )}
                </div>
                <p className="mt-2 text-xs text-slate-400">
                  이미지 #{card.id} {card.src ? "완료" : "생성 중..."}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };


  const creditBadgeColor = useMemo(
    () => (creditInfo.current_credit > 30 ? "bg-green-100 text-green-700" : "bg-yellow-100 text-yellow-700"),
    [creditInfo]
  );
  const creditEstimate = useMemo(() => {
    // 백엔드 credit_service와 동일한 계산식:
    // image: 2 credits / image, text: floor(maxWords / 1000)
    const imageCredits = previewImageCount * 2;
    const wordCredits = Math.floor(wordRange.max / 1000);
    return imageCredits + wordCredits;
  }, [previewImageCount, wordRange]);

  const fetchBlogList = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/blogs/`, {
        headers: buildHeaders(),
      });
      if (res.ok) {
        setBlogs(await res.json());
      }
    } catch (error) {
      console.warn("블로그 목록 로딩 실패", error);
    }
  };

  const preparePanelForCreate = (slotIdx: number) => {
    setPanelMode("create");
    setPanelForm(PANEL_DEFAULT_FORM);
    setSelectedBlogId(null);
    setSelectedCreateSlotIdx((prev) => (prev === slotIdx ? null : slotIdx));
  };

  const preparePanelForEdit = (blog: any) => {
    setPanelMode("edit");
    setSelectedCreateSlotIdx(null);
    setPanelForm({
      alias: blog.alias || "",
      platform_type: blog.platform_type || "Naver",
      blog_url: blog.blog_url || "",
      blog_id: blog.blog_id || "",
      api_access_token: blog.api_key_data?.access_token || "",
    });
    setSelectedBlogId((prev) => (prev === blog.id ? null : blog.id));
  };

  const handleDeleteBlog = async (id: number) => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/blogs/${id}`, {
        method: "DELETE",
        headers: buildHeaders(),
      });
      if (res.ok) {
        await fetchBlogList();
        setStatusMessages((prev) => [...prev, "블로그가 삭제되었습니다."]);
        if (selectedBlogId === id) {
          setSelectedBlogId(null);
          setSelectedCreateSlotIdx(null);
        }
      }
    } catch (error) {
      console.warn("삭제 실패", error);
    }
  };

  useEffect(() => {
    const fetchPosts = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/api/v1/posts/status`, {
          headers: buildHeaders(),
        });
        if (res.ok) {
          setPostsStatus(await res.json());
        }
      } catch (error) {
        console.warn("포스팅 현황 로딩 실패", error);
      }
    };
    const fetchBoard = async () => {
      try {
        const [credit, keywords, savedSchedule] = await Promise.all([
          fetchCreditStatus(),
          fetchKeywordTracking(),
          fetchScheduleConfig(),
        ]);
        setCreditInfo(credit);
        setKeywordTracker(keywords);
        if (savedSchedule) {
          setSchedule((prev: SchedulePayload) => ({ ...prev, ...savedSchedule }));
        }
      } catch (error) {
        console.warn("Dashboard initial load failed, populating defaults.", error);
      }
      fetchPosts();
    };
    fetchBoard();
    fetchBlogList();
  }, []);

  const resolvePostLength = (maxWords: number) => {
    if (maxWords <= 900) return "SHORT";
    if (maxWords <= 1400) return "MEDIUM";
    return "LONG";
  };

  const handlePreview = async (freeTrial = false) => {
    setPreviewLoading(true);
    setDimLoadingOpen(true);
    setDimLoadingStatus("loading");
    setDimLoadingLogs([freeTrial ? "무료 체험 HTML을 요청합니다..." : "미리보기 AI 엔진을 실행합니다..."]);
    
    try {
    const previewPayload: PreviewRequest = {
      topic,
      persona: personaText,
      image_count: previewImageCount,
      custom_prompt: analysisPrompt || undefined,
      word_count_range: [wordRange.min, wordRange.max],
      free_trial: freeTrial,
    };
      const preview = await generatePreviewHtml(previewPayload);
      setPreviewHtml(preview.html);
      setGenerateResult(preview);
      setModalOpen(true);
      setDimLoadingLogs((prev) => [...prev, "AI 엔진이 HTML 초안 생성을 완료했습니다."]);

      if (preview.status === "processing" && preview.images && preview.images.length) {
        setDimLoadingLogs((prev) => [...prev, "백그라운드에서 이미지 생성을 시작합니다..."]);
        // 백엔드가 HTML 먼저 반환하고, 이미지는 백그라운드로 생성됨
        setImageTotal(preview.images.length);
        setCompletedImages(0);
        setImageStatus("processing");
        setImageCards(preview.images.map((src, idx) => ({ id: idx + 1, src: null })));

        // 이미지 URL을 폴링해서 생성 완료되면 스켈레톤을 실제 이미지로 교체
        const poll = async () => {
          const urls = preview.images || [];
          const checks = await Promise.all(
            urls.map(async (u) => {
              try {
                const res = await fetch(`${u}?t=${Date.now()}`, { method: "HEAD" });
                return res.ok;
              } catch {
                return false;
              }
            })
          );
          const done = checks.filter(Boolean).length;
          setCompletedImages(done);
          setImageCards(urls.map((u, idx) => ({ id: idx + 1, src: checks[idx] ? u : null })));
          
          if (done > 0) {
            setDimLoadingLogs((prev) => {
                const last = prev[prev.length - 1];
                if (last.startsWith("이미지 생성 중")) {
                    return [...prev.slice(0, -1), `이미지 생성 중 (${done}/${urls.length})...` ];
                }
                return [...prev, `이미지 생성 중 (${done}/${urls.length})...` ];
            });
          }

          if (done >= urls.length) {
            setImageStatus("completed");
            setDimLoadingLogs((prev) => [...prev, "모든 이미지가 성공적으로 생성되었습니다!"]);
            setDimLoadingStatus("success");
            return;
          }
          setTimeout(poll, 1500);
        };
        setTimeout(poll, 1000);
      } else {
        setDimLoadingStatus("success");
      }
    } catch (error) {
      console.error("Preview generation failed", error);
      setDimLoadingStatus("error");
      setDimLoadingLogs((prev) => [...prev, `오류 발생: ${(error as Error).message}`]);
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleCopyPreview = async () => {
    if (!previewHtml) return;
    try {
      await navigator.clipboard.writeText(previewHtml);
      setStatusMessages((prev: string[]) => [...prev, "HTML이 클립보드에 복사되었습니다."]);
    } catch (error) {
      // HTTP 환경 등에서 navigator.clipboard가 막히는 경우 fallback
      try {
        const textarea = document.createElement("textarea");
        textarea.value = previewHtml;
        textarea.style.position = "fixed";
        textarea.style.left = "-9999px";
        textarea.style.top = "0";
        document.body.appendChild(textarea);
        textarea.focus();
        textarea.select();
        const ok = document.execCommand("copy");
        document.body.removeChild(textarea);
        setStatusMessages((prev: string[]) => [...prev, ok ? "HTML이 클립보드에 복사되었습니다." : "클립보드 복사에 실패했습니다."]);
      } catch {
        setStatusMessages((prev: string[]) => [...prev, "클립보드 복사가 지원되지 않는 환경입니다."]);
      }
    }
  };

  const normalizeAnalysisPrompt = (maybeJson: string) => {
    const text = (maybeJson || "").trim();
    if (!text) return "";
    // prompt에 JSON 전체가 박히는 케이스를 복구
    try {
      const stripped = text.replace(/^```json/i, "```").replace(/^```/i, "```");
      const start = stripped.indexOf("{");
      const end = stripped.lastIndexOf("}");
      if (start !== -1 && end !== -1 && end > start) {
        const obj = JSON.parse(stripped.slice(start, end + 1));
        if (obj && typeof obj === "object") {
          const p = (obj.prompt || obj.custom_prompt || "").toString();
          if (p.trim()) return p.trim();
        }
      }
    } catch {
      // ignore
    }
    return text;
  };

  const handleAnalyze = async () => {
    if (analysisLoading) return;
    setAnalysisLoading(true);
    try {
      const result = await fetchBlogAnalysis(
        selectedBlogId
          ? { blog_id: selectedBlogId }
          : panelForm.blog_url
          ? { blog_url: panelForm.blog_url, alias: panelForm.alias || undefined }
          : {}
      );
      setAnalysisCategory(result.category);
      setAnalysisPrompt(normalizeAnalysisPrompt(result.prompt));
      setAnalysisButtonText("다시 분석하기");
      setStatusMessages((prev: string[]) => [...prev, "블로그 분석 결과를 적용했습니다."]);
    } catch (error) {
      console.error("Blog analysis failed", error);
      setStatusMessages((prev: string[]) => [...prev, "블로그 분석에 실패했습니다."]);
    } finally {
      setAnalysisLoading(false);
    }
  };

  const [saveLoading, setSaveLoading] = useState(false);

  const handleSaveAll = async () => {
    setSaveLoading(true);
    try {
      // 1) 블로그 기본정보 저장 (등록/수정)
      let blogId = selectedBlogId;
      if (panelMode === "create") {
        const createRes = await fetch(`${API_BASE_URL}/api/v1/blogs/`, {
          method: "POST",
          headers: buildHeaders(),
          body: JSON.stringify({
            alias: panelForm.alias,
            platform_type: panelForm.platform_type,
            blog_url: panelForm.blog_url,
            blog_id: panelForm.blog_id,
            api_access_token: panelForm.api_access_token || undefined,
          }),
        });
        if (!createRes.ok) {
          const body = await createRes.json();
          throw new Error(body.detail || "블로그 등록 실패");
        }
        const created = await createRes.json();
        blogId = created.id;

        // 생성 직후 블로그별 설정 저장(POST 스키마를 깨지 않기 위해 PUT로 한번 더 저장)
        const settingsRes = await fetch(`${API_BASE_URL}/api/v1/blogs/${created.id}`, {
          method: "PUT",
          headers: buildHeaders(),
          body: JSON.stringify({
            interest_topic: topic,
            persona: personaText,
            default_category: analysisCategory || undefined,
            custom_prompt: analysisPrompt || undefined,
            word_range: { min: wordRange.min, max: wordRange.max },
            image_count: previewImageCount,
          }),
        });
        if (!settingsRes.ok) {
          const body = await settingsRes.json().catch(() => ({}));
          throw new Error(body.detail || "블로그 설정 저장 실패");
        }

        setPanelMode("edit");
        setSelectedBlogId(created.id);
        setSelectedCreateSlotIdx(null);
        setPanelForm({
          alias: created.alias || panelForm.alias,
          platform_type: created.platform_type || panelForm.platform_type,
          blog_url: created.blog_url || panelForm.blog_url,
          blog_id: created.blog_id || panelForm.blog_id,
          api_access_token: created.api_key_data?.access_token || panelForm.api_access_token,
        });
        await fetchBlogList();
      } else if (panelMode === "edit" && blogId) {
        const updateRes = await fetch(`${API_BASE_URL}/api/v1/blogs/${blogId}`, {
          method: "PUT",
          headers: buildHeaders(),
          body: JSON.stringify({
            alias: panelForm.alias,
            platform_type: panelForm.platform_type,
            blog_url: panelForm.blog_url,
            blog_id: panelForm.blog_id,
            api_access_token: panelForm.api_access_token || undefined,
            // 블로그별 설정 저장
            interest_topic: topic,
            persona: personaText,
            default_category: analysisCategory || undefined,
            custom_prompt: analysisPrompt || undefined,
            word_range: { min: wordRange.min, max: wordRange.max },
            image_count: previewImageCount,
          }),
        });
        if (!updateRes.ok) {
          const body = await updateRes.json();
          throw new Error(body.detail || "블로그 수정 실패");
        }
        await updateRes.json();
        await fetchBlogList();
      }

      // 2) 스케줄링 저장 (유저 공통 설정 DB)
      await saveScheduleConfig(schedule);

      setStatusMessages((prev: string[]) => [...prev, "설정이 저장되었습니다."]);
    } catch (error: any) {
      console.error("Save all failed", error);
      setStatusMessages((prev: string[]) => [...prev, `설정 저장 실패: ${error.message}`]);
    } finally {
      setSaveLoading(false);
    }
  };

  const handlePanelFormChange = (key: keyof typeof PANEL_DEFAULT_FORM, value: string) => {
    setPanelForm((prev) => ({ ...prev, [key]: value }));
  };

  // blog create/update is included in handleSaveAll()

  const updateWordRange = (key: "min" | "max", value: number) => {
    setWordRange((prev) => {
      const normalized = key === "min" ? Math.min(value, prev.max) : Math.max(value, prev.min);
      return { ...prev, [key]: normalized };
    });
  };

  // NOTE: 카드 열 때마다 자동 분석이 돌면 저장된 값을 덮어쓰고 UX가 나빠집니다.
  // 분석은 사용자가 "분석하기" 버튼을 눌렀을 때만 실행합니다.

  const handleDownloadAssets = () => {
    if (!previewHtml) return;
    const blob = new Blob([previewHtml], { type: "text/html" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `ai_preview_${Date.now()}.html`;
    anchor.click();
    URL.revokeObjectURL(url);
    setStatusMessages((prev: string[]) => [...prev, "HTML 다운로드 링크가 생성되었습니다."]);
  };

  const handleDownloadAll = () => {
    if (!generateResult) return;
    const htmlBlob = new Blob([generateResult.html], { type: "text/html" });
    const htmlUrl = URL.createObjectURL(htmlBlob);
    const htmlAnchor = document.createElement("a");
    htmlAnchor.href = htmlUrl;
    htmlAnchor.download = `ai_preview_${Date.now()}.html`;
    htmlAnchor.click();
    URL.revokeObjectURL(htmlUrl);
    generateResult.images?.forEach((path, idx) => {
      const anchor = document.createElement("a");
      anchor.href = path;
      anchor.download = `preview_image_${idx + 1}.png`;
      anchor.click();
    });
    setStatusMessages((prev: string[]) => [...prev, "HTML 및 이미지 다운로드가 완료되었습니다."]);
  };

  const [publishLoading, setPublishLoading] = useState<number | null>(null);

  const handlePublishManual = async (postId: number) => {
    if (publishLoading) return;
    setPublishLoading(postId);
    setStatusMessages((prev) => [...prev, `포스트 #${postId} 발행을 시도합니다...`]);
    try {
      const result = await publishPostManual(postId);
      if (result.status === "success") {
        setStatusMessages((prev) => [...prev, `성공적으로 발행되었습니다! URL: ${result.url}`]);
        // 포스팅 현황 새로고침
        const res = await fetch(`${API_BASE_URL}/api/v1/posts/status`, {
          headers: buildHeaders(),
        });
        if (res.ok) {
          setPostsStatus(await res.json());
        }
      } else {
        setStatusMessages((prev) => [...prev, `발행 실패: ${result.message}`]);
      }
    } catch (error: any) {
      console.error("Publish failed", error);
      setStatusMessages((prev) => [...prev, `발행 중 오류 발생: ${error.message}`]);
    } finally {
      setPublishLoading(null);
    }
  };

  const [trackLoading, setTrackLoading] = useState<number | null>(null);

  const handleTrackPost = async (postId: number) => {
    if (trackLoading) return;
    setTrackLoading(postId);
    setStatusMessages((prev) => [...prev, `포스트 #${postId} 순위 추적을 시작합니다...`]);
    try {
      const result = await trackPost(postId);
      setStatusMessages((prev) => [...prev, `순위 추적 완료: ${JSON.stringify(result.keyword_ranks)}`]);
      // 데이터 갱신
      const res = await fetch(`${API_BASE_URL}/api/v1/posts/status`, {
        headers: buildHeaders(),
      });
      if (res.ok) {
        setPostsStatus(await res.json());
      }
    } catch (error: any) {
      console.error("Tracking failed", error);
      setStatusMessages((prev) => [...prev, `순위 추적 중 오류 발생: ${error.message}`]);
    } finally {
      setTrackLoading(null);
    }
  };

  const simulateImageGeneration = (total: number) => {
    if (total <= 0) return;
    clearImageTimers();
    setImageTotal(total);
    setCompletedImages(0);
    setImageCards(Array.from({ length: total }, (_, idx) => ({ id: idx + 1, src: null })));
    setImageStatus("processing");

    Array.from({ length: total }).forEach((_, index) => {
      const timer = setTimeout(() => {
        setImageCards((prev) =>
          prev.map((card) =>
            card.id === index + 1
              ? {
                  ...card,
                  src: `https://via.placeholder.com/320x180.png?text=Image+${index + 1}`,
                }
              : card
          )
        );
        setCompletedImages((prev) => prev + 1);
        if (index === total - 1) {
          setImageStatus("completed");
          setStatusMessages((prev: string[]) => [...prev, "모든 이미지가 준비되었습니다."]);
        }
      }, (index + 1) * 900);
      imageTimersRef.current.push(timer);
    });
  };

  const toggleDay = (day: string) => {
    setSchedule((prev: SchedulePayload) => {
      const already = prev.days.includes(day);
      const updatedDays = already ? prev.days.filter((d) => d !== day) : [...prev.days, day];
      return { ...prev, days: updatedDays };
    });
  };

  const updateTime = (value: string, index: number) => {
    setSchedule((prev: SchedulePayload) => {
      const targetTimes = [...prev.target_times];
      targetTimes[index] = value;
      return { ...prev, target_times: targetTimes };
    });
  };

  const addTimeSlot = () => {
    setSchedule((prev: SchedulePayload) => ({ ...prev, target_times: [...prev.target_times, "09:00"] }));
  };

  const removeTimeSlot = (index: number) => {
    setSchedule((prev: SchedulePayload) => ({
      ...prev,
      target_times: prev.target_times.filter((_, i) => i !== index),
    }));
  };

  const handleScheduleSave = async () => {
    setScheduleSaving(true);
    try {
      await saveScheduleConfig(schedule);
      setStatusMessages((prev: string[]) => [...prev, "일정이 저장되었습니다."]);
    } catch (error) {
      console.error("Schedule save failed", error);
      setStatusMessages((prev: string[]) => [...prev, "일정 저장 중 문제가 발생했습니다."]);
    } finally {
      setScheduleSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 px-6 py-10">
      <div className="max-w-6xl mx-auto space-y-8">
        <header className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.25em] text-slate-400">AI Marketing Automation Engine</p>
        <h1 className="text-4xl font-bold flex items-center gap-3">
              <Bot className="w-10 h-10 text-cyan-400" />
          {displayName ? `${displayName}님의 AI 대시보드` : "고객님의 AI 대시보드"}
            </h1>
            <p className="text-slate-400 mt-1">통합 블로그/플랫폼 일정, 크레딧, SEO 트래킹을 한 눈에.</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <div className={`rounded-2xl px-5 py-3 text-sm font-semibold flex items-center gap-2 ${creditBadgeColor}`}>
              <CreditCard className="w-4 h-4" />
              크레딧 {creditInfo.current_credit} + 차감 예정 {creditInfo.upcoming_deduction}
            </div>
            <button className="bg-cyan-500 hover:bg-cyan-400 text-slate-950 px-5 py-3 rounded-2xl font-bold">
              크레딧 충전하기
            </button>
          </div>
        </header>

        <section className="bg-slate-900 rounded-3xl border border-slate-800 p-6 shadow-sm space-y-5">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-slate-100">블로그 관리</h2>
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
            {blogs.map((blog) => (
              <Fragment key={blog.id}>
                <button
                  onClick={() => preparePanelForEdit(blog)}
                  className="w-full relative rounded-2xl border border-slate-800 bg-slate-950 p-4 space-y-2 text-left hover:border-slate-600 transition"
                >
                  <div className="absolute right-3 top-3 flex gap-1">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        preparePanelForEdit(blog);
                      }}
                      className="rounded-full border border-slate-700 bg-slate-950 px-2 py-1 text-xs text-slate-200 hover:border-slate-500"
                    >
                      <span className="sr-only">수정</span>⚙️
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteBlog(blog.id);
                      }}
                      className="rounded-full border border-rose-700 bg-slate-950 px-2 py-1 text-xs text-rose-300 hover:border-rose-400"
                    >
                      ✕
                    </button>
            </div>
                  <p className="text-xs text-slate-400 uppercase tracking-[0.2em]">{blog.platform_type}</p>
                  <h3 className="text-lg font-semibold text-white">{blog.alias || "블로그 이름 없음"}</h3>
                  <p className="text-xs text-slate-400 truncate">{blog.blog_url}</p>
                  <p className="text-xs text-slate-500">등록 ID: {blog.blog_id}</p>
                </button>

                {selectedBlogId === blog.id && (
                  <div className="col-span-full rounded-3xl border border-slate-800 bg-slate-950/30 p-3">
                    {renderBlogSettingsPanel()}
                  </div>
                )}
              </Fragment>
            ))}
              </div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
            {Array.from({ length: Math.max(0, TOTAL_BLOG_SLOTS - blogs.length) }).map((_, idx) => (
              <Fragment key={`slot-${idx}`}>
                <button
                  onClick={() => preparePanelForCreate(idx)}
                  className="w-full h-full min-h-[140px] rounded-2xl border-2 border-dashed border-slate-700 p-4 text-center text-sm text-slate-300 hover:border-cyan-500 hover:text-cyan-400 transition flex flex-col items-center justify-center gap-2"
                >
                  <div className="h-10 w-10 rounded-full border border-slate-700 flex items-center justify-center text-xl font-bold bg-slate-950">
                    +
                  </div>
                  블로그 추가
                </button>

                {panelMode === "create" && selectedBlogId === null && selectedCreateSlotIdx === idx && (
                  <div className="col-span-full rounded-3xl border border-slate-800 bg-slate-950/30 p-3">
                    {renderBlogSettingsPanel()}
                  </div>
                )}
              </Fragment>
                        ))}
                    </div>
        </section>

        <section className="bg-slate-900 rounded-3xl p-6 border border-slate-800">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-semibold flex items-center gap-2">
                키워드 노출 트래킹
                {keywordTracker.some(r => r.updated_at.includes("전")) && (
                    <span className="bg-blue-500/10 text-blue-400 text-[10px] px-2 py-0.5 rounded-full border border-blue-500/20">
                        예제 데이터입니다
                    </span>
                )}
            </h2>
            <small className="text-xs text-slate-500">최신 24시간 내 데이터</small>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-xs">
              <thead>
                <tr className="text-slate-400">
                  <th className="pb-3 pr-6">키워드</th>
                  <th className="pb-3 pr-6">플랫폼</th>
                  <th className="pb-3 pr-6">순위</th>
                  <th className="pb-3 pr-6">변동</th>
                  <th className="pb-3">업데이트</th>
                </tr>
              </thead>
              <tbody className="text-slate-200">
                {keywordTracker.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-6 text-center text-slate-500">
                      데이터가 없습니다. AI 포스팅을 생성하면 자동으로 수집됩니다.
                    </td>
                  </tr>
                ) : (
                  keywordTracker.map((row) => (
                    <tr key={row.keyword + row.platform} className="border-t border-slate-800">
                      <td className="py-3 pr-6 font-semibold">{row.keyword}</td>
                      <td className="py-3 pr-6 text-slate-400">{row.platform}</td>
                      <td className="py-3 pr-6 text-cyan-300">{row.rank}위</td>
                      <td className="py-3 pr-6 text-sm">
                        {row.change >= 0 ? (
                          <span className="flex items-center gap-1 text-lime-300">
                            <ArrowIcon />
                            {row.change >= 0 ? `+${row.change}` : row.change}
                          </span>
                        ) : (
                          <span className="flex items-center gap-1 text-rose-300">
                            <ArrowIcon down />
                            {row.change}
                          </span>
                        )}
                      </td>
                      <td className="py-3 text-slate-500">{row.updated_at}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </section>

        <section className="bg-slate-900 rounded-3xl p-6 border border-slate-800">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-semibold">포스팅 현황</h2>
            <Link href="/status" className="text-xs uppercase tracking-[0.3em] text-slate-400 hover:text-white transition">
              전체 보기
            </Link>
                 </div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm text-slate-200">
              <thead className="text-xs text-slate-400">
                <tr>
                  <th className="pb-3 pr-6">발행 글 제목</th>
                  <th className="pb-3 pr-6">날짜</th>
                  <th className="pb-3 pr-6">키워드</th>
                  <th className="pb-3 pr-6">플랫폼</th>
                  <th className="pb-3 pr-6">순위</th>
                  <th className="pb-3 pr-6">조회수</th>
                  <th className="pb-3 pr-6">상태/트래킹</th>
                  <th className="pb-3">원문링크</th>
                </tr>
              </thead>
              <tbody>
                {postsStatus.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="py-20 text-center text-slate-500">
                      <div className="flex flex-col items-center gap-3">
                        <FileText className="w-12 h-12 opacity-20" />
                        <p className="text-sm">아직 발행된 포스팅이 없습니다. <br /> 상단 블로그 관리에서 첫 글을 만들어보세요!</p>
                      </div>
                    </td>
                  </tr>
                ) : (
                  postsStatus.flatMap((blogGroup) =>
                    blogGroup.posts.map((post: any) => (
                      <tr key={`${post.id}-${blogGroup.blog_alias}`} className="border-t border-slate-800">
                        <td className="py-3 pr-6 font-semibold text-slate-100">{post.title}</td>
                        <td className="py-3 pr-6 text-slate-400">{new Date(post.created_at).toLocaleString()}</td>
                        <td className="py-3 pr-6 text-slate-200">
                          {post.keyword_ranks && Object.keys(post.keyword_ranks).length
                            ? Object.keys(post.keyword_ranks).join(", ")
                            : "집계 중"}
                        </td>
                        <td className="py-3 pr-6 text-slate-200">{blogGroup.platform}</td>
                        <td className="py-3 pr-6 text-cyan-300">
                          {post.keyword_ranks && Object.values(post.keyword_ranks).length ? (
                            (() => {
                              const values = Object.values(post.keyword_ranks);
                              const ranks = values.map((v: any) => (typeof v === "number" ? v : v.rank)).filter(r => r > 0);
                              return ranks.length ? `${Math.min(...ranks)}위` : "-";
                            })()
                          ) : (
                            "-"
                          )}
                        </td>
                        <td className="py-3 pr-6 text-slate-200">
                          {post.view_count.toLocaleString()}회
                        </td>
                        <td className="py-3 pr-6 text-xs text-slate-500">
                            <div className="flex flex-col gap-1">
                                <div className="flex items-center gap-2">
                                    <span>{post.status}</span>
                                    {post.published_url && (
                                        <button
                                            onClick={() => handleTrackPost(post.id)}
                                            disabled={trackLoading === post.id}
                                            className="px-2 py-0.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-md text-[10px]"
                                            title="순위 추적 업데이트"
                                        >
                                            {trackLoading === post.id ? "..." : "트래킹 시작"}
                                        </button>
                                    )}
                                </div>
                                <span className={`px-2 py-0.5 rounded-full text-[10px] w-fit ${
                                    post.tracking_status === "COMPLETED" ? "bg-emerald-500/20 text-emerald-400" :
                                    post.tracking_status === "TRACKING" ? "bg-cyan-500/20 text-cyan-400 animate-pulse" :
                                    "bg-slate-800 text-slate-400"
                                }`}>
                                    {post.tracking_status || "PENDING"}
                                </span>
                            </div>
                        </td>
                        <td className="py-3 text-slate-200">
                          <div className="flex items-center gap-2">
                            {post.status !== "PUBLISHED" && (
                                <button
                                    onClick={() => handlePublishManual(post.id)}
                                    disabled={publishLoading === post.id}
                                    className="px-3 py-1 bg-cyan-500 text-slate-950 rounded-lg text-xs font-bold hover:bg-cyan-400 disabled:opacity-50"
                                >
                                    {publishLoading === post.id ? "발행 중..." : "즉시 발행"}
                                </button>
                            )}
                            {post.published_url ? (
                                <a
                                    href={post.published_url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-blue-300 hover:text-blue-500 text-xs"
                                >
                                    원문 보기
                                </a>
                            ) : (
                                <Link
                                    href="/status"
                                    className="text-slate-400 hover:text-slate-200 text-xs"
                                >
                                    상세 보기
                                </Link>
                            )}
                 </div>
                        </td>
                      </tr>
                    ))
                  )
                )}
              </tbody>
            </table>
                    </div>
        </section>

        <section className="bg-slate-900 rounded-3xl p-6 border border-slate-800 space-y-3">
          <h2 className="text-2xl font-semibold">실행 로그</h2>
          <div className="space-y-2 text-xs text-slate-400">
            {statusMessages.length === 0 ? (
              <p>최근 액션 기록이 없습니다.</p>
            ) : (
              statusMessages.slice(-5).map((message, index) => (
                <p key={index} className="flex items-center gap-2">
                  <Shield className="h-3 w-3 text-cyan-400" />
                  {message}
                </p>
              ))
            )}
                 </div>
        </section>
              </div>

      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4 py-6">
          <div className="w-full max-w-3xl rounded-3xl bg-slate-950 p-6 border border-cyan-500 shadow-2xl">
            <div className="flex items-center justify-between">
              <h3 className="text-xl font-semibold">HTML 미리보기</h3>
              <button className="text-sm text-slate-400" onClick={() => setModalOpen(false)}>
                닫기
              </button>
            </div>
            <div className="my-4 max-h-96 overflow-y-auto rounded-2xl border border-slate-800 bg-slate-900/70 p-4 text-xs text-slate-300">
              <pre className="whitespace-pre-wrap">{previewHtml || "아직 생성된 HTML이 없습니다."}</pre>
            </div>
            <div className="flex justify-end gap-3">
              <button
                onClick={handleCopyPreview}
                className="inline-flex items-center gap-2 rounded-2xl border border-slate-700 px-4 py-2 text-sm text-slate-300"
              >
                <Copy className="h-4 w-4" />
                HTML 복사
              </button>
              </div>
            </div>
          </div>
        )}

      <KeywordSearchModal
        isOpen={keywordSearchOpen}
        onClose={() => setKeywordSearchOpen(false)}
        onSelect={(selected) => setTopic(selected.join(", "))}
      />

      <DimLoadingPopup
        isOpen={dimLoadingOpen}
        logs={dimLoadingLogs}
        status={dimLoadingStatus}
        onClose={() => setDimLoadingOpen(false)}
      />
    </div>
  );
}

function ArrowIcon({ down }: { down?: boolean }) {
  return (
    <span
      className={`h-3 w-3 inline-block border-b-2 transform ${down ? "border-rose-300 rotate-45" : "border-lime-300 -rotate-45"}`}
    />
  );
}