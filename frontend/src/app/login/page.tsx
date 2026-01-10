"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import axios from "axios";
import { Bot, Mail, Lock, User, ArrowRight, Loader2, CheckSquare, Square } from "lucide-react";

export default function AuthPage() {
  const router = useRouter();
  const [isLogin, setIsLogin] = useState(true);
  const [loading, setLoading] = useState(false);
  const [agreed, setAgreed] = useState(false);
  const [formData, setFormData] = useState({ email: "", password: "", name: "" });
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    if (!isLogin && !agreed) {
      setError("서비스 이용약관에 동의해야 합니다.");
      setLoading(false);
      return;
    }
    if (!isLogin && !formData.name) {
      setError("이름을 입력해주세요.");
      setLoading(false);
      return;
    }

    try {
      const endpoint = isLogin ? "/login" : "/signup";
      const url = `http://127.0.0.1:8000/api/v1/auth${endpoint}`;
      const payload = isLogin ? { email: formData.email, password: formData.password } : formData;
      console.log("Sending Request:", url, payload);

      const response = await axios.post(url, payload);

      if (isLogin) {
        const token = response.data.access_token;
        localStorage.setItem("token", token);
        axios.defaults.headers.common["Authorization"] = `Bearer ${token}`;
        router.push("/dashboard");
      } else {
        alert("🎉 회원가입 성공! 로그인해주세요.");
        setIsLogin(true);
        setAgreed(false);
      }
    } catch (err: any) {
      console.error("Auth Error:", err);
      const serverMsg = err.response?.data?.detail;
      setError(serverMsg || "서버와 연결할 수 없습니다. (백엔드가 켜져 있나요?)");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex bg-white">
      <div className="hidden lg:flex w-1/2 bg-gray-900 items-center justify-center relative overflow-hidden">
        <div className="absolute inset-0 opacity-20 bg-[url('https://images.unsplash.com/photo-1620712943543-bcc4688e7485?q=80&w=2000&auto=format&fit=crop')] bg-cover bg-center"></div>
        <div className="relative z-10 text-white p-12 max-w-lg">
          <div className="p-3 bg-blue-600 rounded-xl w-fit mb-6 shadow-lg shadow-blue-500/50">
            <Bot className="w-10 h-10 text-white" />
          </div>
          <h1 className="text-5xl font-bold mb-6 leading-tight">Automation <br/> for Bloggers.</h1>
          <p className="text-lg text-gray-300 leading-relaxed">
            더 이상 글쓰기에 스트레스 받지 마세요.<br/>
            AI가 트렌드 분석부터 포스팅까지 완벽하게 처리합니다.
          </p>
        </div>
      </div>

      <div className="w-full lg:w-1/2 flex items-center justify-center p-8 lg:p-24 bg-gray-50">
        <div className="w-full max-w-md bg-white p-8 rounded-3xl shadow-xl border border-gray-100">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-gray-900">
              {isLogin ? "Welcome Back" : "계정 만들기"}
            </h2>
            <p className="text-gray-500 mt-2 text-sm">
              {isLogin ? "서비스 이용을 위해 로그인해주세요." : "30초 만에 가입하고 자동화를 시작하세요."}
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            {!isLogin && (
              <div className="animate-in slide-in-from-top-2 duration-300">
                <label className="block text-sm font-semibold text-gray-700 mb-1">Name</label>
                <div className="relative">
                  <User className="absolute left-3 top-3.5 w-5 h-5 text-gray-400" />
                  <input
                    type="text"
                    className="w-full pl-10 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none transition"
                    placeholder="홍길동"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  />
                </div>
              </div>
            )}

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-3.5 w-5 h-5 text-gray-400" />
                <input
                  type="email"
                  required
                  className="w-full pl-10 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none transition"
                  placeholder="name@company.com"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1">Password</label>
              <div className="relative">
                <Lock className="absolute left-3 top-3.5 w-5 h-5 text-gray-400" />
                <input
                  type="password"
                  required
                  className="w-full pl-10 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none transition"
                  placeholder="••••••••"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                />
              </div>
            </div>

            {!isLogin && (
              <div 
                className="flex items-start space-x-3 p-3 bg-blue-50 rounded-xl cursor-pointer hover:bg-blue-100 transition animate-in slide-in-from-top-2 duration-300"
                onClick={() => setAgreed(!agreed)}
              >
                <div className="mt-0.5 text-blue-600">
                  {agreed ? <CheckSquare className="w-5 h-5" /> : <Square className="w-5 h-5" />}
                </div>
                <div className="text-xs text-gray-600 leading-relaxed select-none">
                  <span className="font-bold text-blue-700">이용약관</span> 및 <span className="font-bold text-blue-700">개인정보 처리방침</span>에 동의하며, 서비스 이용을 시작합니다.
                </div>
              </div>
            )}

            {error && (
              <div className="p-3 bg-red-50 text-red-600 text-sm rounded-lg text-center font-medium border border-red-100">
                ⚠️ {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-4 bg-gray-900 hover:bg-black text-white font-bold rounded-xl shadow-lg hover:shadow-xl transition transform hover:-translate-y-0.5 flex items-center justify-center text-lg"
            >
              {loading ? <Loader2 className="animate-spin w-5 h-5" /> : (
                <>
                  {isLogin ? "로그인하기" : "회원가입 완료"}
                  <ArrowRight className="w-5 h-5 ml-2" />
                </>
              )}
            </button>
          </form>

          <div className="mt-8 text-center">
            <p className="text-sm text-gray-500">
              {isLogin ? "아직 회원이 아니신가요?" : "이미 계정이 있으신가요?"}
              <button
                onClick={() => { setIsLogin(!isLogin); setError(""); }}
                className="ml-2 font-bold text-blue-600 hover:text-blue-700 hover:underline transition"
              >
                {isLogin ? "회원가입 하기" : "로그인 하러가기"}
              </button>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

