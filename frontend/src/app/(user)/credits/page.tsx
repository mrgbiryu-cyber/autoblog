"use client";

import { useState, useEffect } from "react";
import { CreditCard, ArrowLeft, CheckCircle2 } from "lucide-react";
import Link from "next/link";
import { 
  createRechargeRequest, 
  fetchRechargeHistory, 
  buildHeaders, 
  fetchActivePlans,
  fetchSystemConfigPublic 
} from "@/lib/api";

export default function CreditRecharge() {
  const [options, setOptions] = useState<any[]>([]);
  const [selectedOption, setSelectedOption] = useState<any>(null);
  const [systemConfig, setSystemConfig] = useState<any>(null);
  const [depositorName, setDepositorName] = useState("");
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<any[]>([]);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [historyData, plansData, configData] = await Promise.all([
        fetchRechargeHistory(),
        fetchActivePlans(),
        fetchSystemConfigPublic()
      ]);
      setHistory(Array.isArray(historyData) ? historyData : []);
      setOptions(Array.isArray(plansData) ? plansData : []);
      setSystemConfig(configData);
      
      const validPlans = Array.isArray(plansData) ? plansData : [];
      if (validPlans.length > 0) {
        // 인기 플랜이 있으면 우선 선택, 없으면 두 번째 플랜 선택
        const popular = validPlans.find((p: any) => p.is_popular);
        setSelectedOption(popular || validPlans[Math.min(1, validPlans.length - 1)]);
      }
    } catch (e) {
      console.error(e);
      setHistory([]);
      setOptions([]);
    }
  };

  const handleTossPay = () => {
    if (!systemConfig?.toss_link) {
      alert("토스 송금 링크가 설정되지 않았습니다.");
      return;
    }
    // 관리자가 설정한 딥링크로 이동
    window.location.href = systemConfig.toss_link;
  };

  const handleKakaoPay = () => {
    if (!systemConfig?.kakao_link) {
      alert("카카오페이 링크가 설정되지 않았습니다.");
      return;
    }
    window.open(systemConfig.kakao_link, "_blank");
  };

  const handleRequestConfirm = async () => {
    if (!depositorName.trim()) {
      alert("입금자명을 입력해주세요.");
      return;
    }
    setLoading(true);
    try {
      await createRechargeRequest({
        amount: selectedOption.amount,
        requested_credits: selectedOption.credits,
        depositor_name: depositorName
      });
      setSuccess(true);
      setDepositorName("");
      loadData();
    } catch (e) {
      alert("요청 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      <div className="max-w-3xl mx-auto space-y-8">
        <header className="flex items-center gap-4">
          <Link href="/dashboard" className="p-2 hover:bg-slate-900 rounded-full transition">
            <ArrowLeft className="w-6 h-6" />
          </Link>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <CreditCard className="w-8 h-8 text-cyan-400" />
            크레딧 충전
          </h1>
        </header>

        <section className="bg-slate-900 rounded-3xl border border-slate-800 p-8 space-y-8">
          <div className="space-y-2">
            <h2 className="text-xl font-bold">요금제 선택</h2>
            <p className="text-sm text-slate-400">
              * AI 콘텐츠 생성 시 이미지당 2C, 텍스트 1,000자당 1C가 차감됩니다. (미리보기 포함)
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            {Array.isArray(options) && options.map((option) => (
              <button
                key={option.id}
                onClick={() => setSelectedOption(option)}
                className={`relative p-6 rounded-2xl border-2 transition text-left ${
                  selectedOption?.id === option.id
                    ? "border-cyan-500 bg-cyan-500/10"
                    : "border-slate-800 bg-slate-950 hover:border-slate-600"
                }`}
              >
                {option.is_popular && (
                  <span className="absolute -top-3 right-4 bg-cyan-500 text-slate-950 text-[10px] font-bold px-2 py-1 rounded-full uppercase">
                    Popular
                  </span>
                )}
                <div className="flex items-center justify-between">
                  <p className="text-sm text-slate-400">{option.name}</p>
                  {option.badge_text && (
                    <span className="bg-emerald-500/20 text-emerald-400 text-[10px] font-bold px-2 py-0.5 rounded-full">
                      {option.badge_text}
                    </span>
                  )}
                </div>
                <p className="text-2xl font-bold mt-1">
                  ₩{option.amount.toLocaleString()}
                </p>
                <p className="text-xs text-slate-500 mt-1">{option.credits.toLocaleString()} C 지급</p>
              </button>
            ))}
            
            <button
              onClick={() => window.open("mailto:support@antigravity.kr")}
              className="p-6 rounded-2xl border-2 border-dashed border-slate-800 bg-slate-950 hover:border-slate-600 transition text-left"
            >
              <p className="text-sm text-slate-400">기업 / B2B 대량 구매</p>
              <p className="text-xl font-bold mt-1 text-cyan-400">별도 문의</p>
              <p className="text-xs text-slate-500 mt-1">대량 사용자 맞춤 요금제 제공</p>
            </button>
          </div>

          <div className="space-y-6">
            <div className="p-6 rounded-2xl bg-slate-950 border border-slate-800 space-y-4">
              <h3 className="font-semibold text-lg">1단계: 아래 계좌로 송금하기</h3>
              <div className="flex items-center justify-between p-4 bg-slate-900 rounded-xl border border-slate-800">
                <div>
                  <p className="text-xs text-slate-500 uppercase">입금 계좌</p>
                  <p className="font-mono text-lg">{systemConfig?.bank_name || "불러오는 중..."} {systemConfig?.account_number || ""}</p>
                  <p className="text-sm text-slate-300">예금주: {systemConfig?.account_holder || ""}</p>
                </div>
                <div className="flex flex-col gap-2">
                  <button
                    onClick={handleTossPay}
                    disabled={!selectedOption || !systemConfig?.toss_link}
                    className="px-4 py-2 bg-[#0050FF] text-white rounded-lg text-sm font-bold hover:opacity-90 transition disabled:opacity-30"
                  >
                    토스 송금
                  </button>
                  <button
                    onClick={handleKakaoPay}
                    disabled={!selectedOption || !systemConfig?.kakao_link}
                    className="px-4 py-2 bg-[#FEE500] text-black rounded-lg text-sm font-bold hover:opacity-90 transition disabled:opacity-30"
                  >
                    카카오페이
                  </button>
                </div>
              </div>
              <p className="text-xs text-slate-500">
                * 위 버튼을 누르면 해당 뱅킹 앱으로 바로 연결됩니다.
              </p>
            </div>

            <div className="p-6 rounded-2xl bg-slate-950 border border-slate-800 space-y-4">
              <h3 className="font-semibold text-lg">2단계: 입금 확인 요청하기</h3>
              <div className="space-y-4">
                <label className="block space-y-2">
                  <span className="text-sm text-slate-400">실제 입금자 성함</span>
                  <input
                    type="text"
                    className="w-full bg-slate-900 border border-slate-800 rounded-xl px-4 py-3 focus:border-cyan-500 focus:outline-none"
                    placeholder="입금하신 분의 성함을 입력해주세요"
                    value={depositorName}
                    onChange={(e) => setDepositorName(e.target.value)}
                  />
                </label>
                <button
                  onClick={handleRequestConfirm}
                  disabled={loading || !depositorName}
                  className="w-full py-4 bg-emerald-500 text-white rounded-xl font-bold hover:bg-emerald-400 disabled:opacity-50 transition"
                >
                  {loading ? "요청 중..." : "입금 확인 요청 완료"}
                </button>
              </div>
            </div>
          </div>

          {success && (
            <div className="flex items-center gap-3 p-4 bg-emerald-500/20 border border-emerald-500/50 rounded-xl text-emerald-400">
              <CheckCircle2 className="w-5 h-5" />
              <p className="text-sm">입금 확인 요청이 전송되었습니다. 관리자 확인 후 크레딧이 즉시 지급됩니다.</p>
            </div>
          )}
        </section>

        <section className="bg-slate-900 rounded-3xl border border-slate-800 p-8 space-y-6">
          <h2 className="text-xl font-semibold">충전 내역</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="text-slate-500 border-b border-slate-800">
                  <th className="pb-3">일시</th>
                  <th className="pb-3">금액</th>
                  <th className="pb-3">크레딧</th>
                  <th className="pb-3">상태</th>
                </tr>
              </thead>
              <tbody>
                {!Array.isArray(history) || history.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="py-8 text-center text-slate-600">내역이 없습니다.</td>
                  </tr>
                ) : (
                  history.map((item) => (
                    <tr key={item.id} className="border-b border-slate-800">
                      <td className="py-4 text-slate-400">{new Date(item.created_at).toLocaleDateString()}</td>
                      <td className="py-4">₩{item.amount.toLocaleString()}</td>
                      <td className="py-4">{item.requested_credits.toLocaleString()} C</td>
                      <td className="py-4">
                        <span className={`px-2 py-1 rounded-full text-[10px] font-bold ${
                          item.status === "COMPLETED" ? "bg-emerald-500/20 text-emerald-400" :
                          item.status === "PENDING" ? "bg-yellow-500/20 text-yellow-400" :
                          "bg-slate-800 text-slate-500"
                        }`}>
                          {item.status}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </div>
  );
}

