"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/context/AuthContext";

const mainMenu = [
  { label: "기능소개", href: "#features" },
  { label: "요금제", href: "#pricing" },
];

const subMenu = [
  { label: "요금제", href: "/pricing" },
  { label: "대시보드", href: "/dashboard" },
  { label: "포스팅 현황", href: "/status" },
  { label: "HTML 생성", href: "/dashboard" },
];

export default function Gnb() {
  const pathname = usePathname();
  const { isAuthenticated } = useAuth();
  const isDashboardSection = pathname?.startsWith("/dashboard");
  const showSubMenu = isAuthenticated && isDashboardSection;
  const items = showSubMenu ? subMenu : mainMenu;
  const authLabel = isAuthenticated ? "대시보드" : "로그인";
  const authHref = isAuthenticated ? "/dashboard" : "/login";

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
          <Link
            href={authHref}
            className="rounded-full border border-slate-900 px-4 py-2 text-xs font-semibold uppercase tracking-[0.4em] text-slate-900 hover:bg-slate-900 hover:text-white transition"
          >
            {authLabel}
          </Link>
        </div>
      </div>
    </nav>
  );
}

