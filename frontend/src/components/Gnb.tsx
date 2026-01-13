"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { useEffect, useState } from "react";
import { fetchCreditStatus, fetchCreditLogs, CreditStatusPayload } from "@/lib/api";
import { CreditCard, History, X, ArrowUpRight, ArrowDownLeft } from "lucide-react";

const mainMenu = [
  { label: "기능소개", href: "#features" },
  { label: "요금제", href: "/credits" },
];

const subMenu = [
  { label: "요금제", href: "/credits" },
  { label: "대시보드", href: "/dashboard" },
  { label: "포스팅 현황", href: "/status" },
  { label: "HTML 생성", href: "/dashboard" },
];

export default function Gnb() {
  const pathname = usePathname();
  const { isAuthenticated, logout } = useAuth();
  const [creditInfo, setCreditInfo] = useState<CreditStatusPayload | null>(null);
  const [showHistory, setShowHistory] = useState(false);
  const [history, setHistory] = useState<any[]>([]);

  useEffect(() => {
    if (isAuthenticated) {
      fetchCreditStatus().then(setCreditInfo);
    }
  }, [isAuthenticated]);

  const loadHistory = async () => {
    try {
      const data = await fetchCreditLogs();
      setHistory(data);
      setShowHistory(true);
    } catch (e) {
      console.error(e);
    }
  };

  const isDashboardSection = pathname?.startsWith("/dashboard");
  const showSubMenu = isAuthenticated && isDashboardSection;
  const items = showSubMenu ? subMenu : mainMenu;

  return (
    <nav className="fixed inset-x-0 top-0 z-50 border-b border-slate-900/10 bg-white/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link href="/" className="text-base font-semibold tracking-tight text-slate-900">
          AI Blog Auto-Pilot
        </Link>
        <div className="flex items-center gap-6 text-sm font-medium text-slate-700">
          {items.map((item) => (
            <Link key={item.label} href={item.href} className="hover:text-slate-900 transition">
              {item.label}
            </Link>
          ))}
          {isAuthenticated ? (
            <>
              <button
                onClick={loadHistory}
                className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-100 hover:bg-slate-200 transition text-xs font-bold text-slate-900"
              >
                <CreditCard className="w-4 h-4 text-cyan-600" />
                {creditInfo?.current_credit?.toLocaleString() ?? "0"} C
              </button>
              <Link
                href="/dashboard"
                className="rounded-full border border-slate-900 px-4 py-2 text-xs font-semibold uppercase tracking-[0.4em] text-slate-900 hover:bg-slate-900 hover:text-white transition"
              >
                대시보드
              </Link>
              <button
                onClick={logout}
                className="rounded-full border border-slate-900 px-4 py-2 text-xs font-semibold uppercase tracking-[0.4em] text-slate-900 hover:bg-slate-900 hover:text-white transition"
              >
                로그아웃
              </button>
            </>
          ) : (
            <Link
              href="/login"
              className="rounded-full border border-slate-900 px-4 py-2 text-xs font-semibold uppercase tracking-[0.4em] text-slate-900 hover:bg-slate-900 hover:text-white transition"
            >
              로그인
            </Link>
          )}
        </div>
      </div>

      {showHistory && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-md bg-white rounded-3xl shadow-2xl p-6 relative">
            <button
              onClick={() => setShowHistory(false)}
              className="absolute right-6 top-6 text-slate-400 hover:text-slate-600"
            >
              <X className="w-6 h-6" />
            </button>
            <div className="flex items-center gap-3 mb-6">
              <History className="w-6 h-6 text-cyan-600" />
              <h2 className="text-xl font-bold text-slate-900">크레딧 이용 내역</h2>
            </div>
            <div className="max-h-96 overflow-y-auto space-y-3">
              {history.length === 0 ? (
                <p className="text-center py-8 text-slate-400">내역이 없습니다.</p>
              ) : (
                history.map((item) => (
                  <div key={item.id} className="flex items-center justify-between p-3 rounded-2xl bg-slate-50 border border-slate-100">
                    <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-xl ${item.amount > 0 ? "bg-emerald-100 text-emerald-600" : "bg-rose-100 text-rose-600"}`}>
                            {item.amount > 0 ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownLeft className="w-4 h-4" />}
                        </div>
                        <div>
                            <p className="text-xs text-slate-500">{new Date(item.created_at).toLocaleString()}</p>
                            <p className="text-sm font-semibold text-slate-900">
                                {item.action_type === "DEPOSIT_CONFIRMED" ? "충전 완료" : 
                                 item.action_type === "PREVIEW_GEN" ? "콘텐츠 생성" : 
                                 item.action_type === "DEPOSIT_PENDING" ? "입금 확인 중" : item.action_type}
                            </p>
                        </div>
                    </div>
                    <div className="text-right">
                      <p className={`text-sm font-bold ${item.amount > 0 ? "text-emerald-600" : "text-rose-600"}`}>
                        {item.amount > 0 ? "+" : ""}{item.amount} C
                      </p>
                      {item.details?.amount_krw && <p className="text-[10px] text-slate-400">₩{item.details.amount_krw.toLocaleString()}</p>}
                    </div>
                  </div>
                ))
              )}
            </div>
            <div className="mt-6">
              <Link
                href="/credits"
                onClick={() => setShowHistory(false)}
                className="block w-full py-3 bg-slate-900 text-white text-center rounded-2xl font-bold hover:bg-slate-800 transition"
              >
                크레딧 충전하러 가기
              </Link>
            </div>
          </div>
        </div>
      )}
    </nav>
  );
}

