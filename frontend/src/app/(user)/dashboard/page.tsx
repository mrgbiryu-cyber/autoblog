"use client";

import { useState } from "react";
import axios from "axios";
import { Bot, PenTool, Search, Send, CheckCircle, AlertTriangle, Loader2 } from "lucide-react";

export default function Dashboard() {
  const [category, setCategory] = useState("AI Trends");
  const [persona, setPersona] = useState("Friendly IT Expert");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [logs, setLogs] = useState<string[]>([]);

  const handleGenerate = async () => {
    setLoading(true);
    setResult(null);
    setLogs(["🚀 Starting AI Engine...", "🔍 Agent 1: Analyzing Trends...", "✍️ Agent 2: Drafting Content..."]);

    try {
      // 백엔드 호출
      const response = await axios.post("http://127.0.0.1:8000/generate-post", {
        category,
        persona,
      });

      setLogs((prev) => [
        ...prev, 
        "✅ Content Drafted.", 
        "🧐 Agent 3: SEO Checking...", 
        "🧼 Agent 4: Cleaning Images & Publishing..."
      ]);
      
      setResult(response.data);
      setLoading(false);
    } catch (error) {
      console.error(error);
      setLogs((prev) => [...prev, "❌ Error occurred during generation."]);
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8 font-sans text-gray-900">
      <div className="max-w-4xl mx-auto space-y-8">
        
        {/* 헤더 */}
        <div className="flex items-center space-x-3 mb-8">
          <div className="p-3 bg-blue-600 rounded-lg shadow-lg">
            <Bot className="w-8 h-8 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">AI Blog Auto-Pilot</h1>
            <p className="text-gray-500">지능형 콘텐츠 자동화 엔진 대시보드</p>
          </div>
        </div>

        {/* 입력 카드 */}
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <label className="text-sm font-semibold text-gray-700">Topic / Category</label>
              <input
                type="text"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full p-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none transition"
                placeholder="Ex) AI, Stock, Health"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-semibold text-gray-700">Writer Persona</label>
              <input
                type="text"
                value={persona}
                onChange={(e) => setPersona(e.target.value)}
                className="w-full p-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none transition"
                placeholder="Ex) Friendly Expert"
              />
            </div>
          </div>
          
          <button
            onClick={handleGenerate}
            disabled={loading}
            className={`mt-6 w-full py-4 rounded-xl font-bold text-lg flex items-center justify-center space-x-2 transition-all ${
              loading 
                ? "bg-gray-100 text-gray-400 cursor-not-allowed" 
                : "bg-blue-600 text-white hover:bg-blue-700 shadow-md hover:shadow-lg transform hover:-translate-y-0.5"
            }`}
          >
            {loading ? <Loader2 className="animate-spin" /> : <Send className="w-5 h-5" />}
            <span>{loading ? "Generating Content (Please Wait...)" : "Start Auto-Generation"}</span>
          </button>
        </div>

        {/* 상태 로그 창 */}
        {logs.length > 0 && (
          <div className="bg-gray-900 text-green-400 p-6 rounded-2xl font-mono text-sm shadow-inner overflow-hidden">
            <h3 className="text-gray-400 mb-4 border-b border-gray-800 pb-2">System Logs</h3>
            <div className="space-y-1">
              {logs.map((log, i) => (
                <div key={i} className="animate-pulse">{log}</div>
              ))}
            </div>
          </div>
        )}

        {/* 결과 카드 */}
        {result && (
          <div className="bg-white p-8 rounded-2xl shadow-lg border border-blue-100 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-800">🎉 Generation Complete!</h2>
              <span className={`px-4 py-1 rounded-full text-sm font-bold ${result.seo_score >= 80 ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
                SEO Score: {result.seo_score}/100
              </span>
            </div>

            <div className="space-y-6">
              <div className="p-4 bg-gray-50 rounded-xl">
                <p className="text-sm text-gray-500 mb-1">Generated Topic</p>
                <p className="font-semibold text-lg">{result.topic?.topic}</p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                 <div className="p-4 bg-gray-50 rounded-xl border border-gray-200">
                    <p className="text-sm text-gray-500 mb-1">Keywords</p>
                    <div className="flex flex-wrap gap-2">
                        {result.topic?.keywords?.map((k:string, i:number) => (
                            <span key={i} className="bg-blue-100 text-blue-700 px-2 py-0.5 rounded text-xs">#{k}</span>
                        ))}
                    </div>
                 </div>
                 <div className="p-4 bg-gray-50 rounded-xl border border-gray-200">
                    <p className="text-sm text-gray-500 mb-1">Status</p>
                    <div className="flex items-center text-green-600 font-bold">
                        <CheckCircle className="w-4 h-4 mr-2" />
                        {result.published_info?.status?.toUpperCase()}
                    </div>
                 </div>
              </div>

              <div className="pt-4 border-t border-gray-100">
                  <p className="text-sm text-gray-500 mb-2">Publish URL (Simulation)</p>
                  <a href={result.published_info?.url} target="_blank" className="text-blue-600 hover:underline break-all">
                      {result.published_info?.url}
                  </a>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}