"use client";

import { useState, useEffect } from "react";
import axios from "axios";
import { BarChart3, Clock, Eye, ExternalLink } from "lucide-react";

export default function StatusPage() {
  const [statusData, setStatusData] = useState<any[]>([]);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await axios.get("http://127.0.0.1:8000/api/v1/posts/status");
        setStatusData(res.data);
      } catch (err) {
        console.error("현황 로드 실패", err);
      }
    };
    fetchStatus();
  }, []);

  const timeAgo = (dateStr: string) => {
    const diff = new Date().getTime() - new Date(dateStr).getTime();
    const hours = Math.floor(diff / (1000 * 60 * 60));
    if (hours < 24) return `${hours}시간 전`;
    return `${Math.floor(hours / 24)}일 전`;
  };

  return (
    <div className="p-8 bg-gray-50 min-h-screen">
      <h1 className="text-3xl font-bold text-gray-900 mb-8 flex items-center">
        <BarChart3 className="w-8 h-8 mr-3 text-blue-600" />
        블로그 발행 현황
      </h1>

      <div className="space-y-8">
        {statusData.map((blog, idx) => (
          <div key={idx} className="bg-white rounded-3xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="bg-gray-50 px-6 py-4 border-b border-gray-100 flex justify-between items-center">
              <div>
                <h2 className="text-lg font-bold text-gray-800 flex items-center">
                  {blog.blog_alias}
                  <span className="ml-2 text-xs font-normal text-gray-500 px-2 py-0.5 bg-white border rounded-full">
                    {blog.platform}
                  </span>
                </h2>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="bg-white text-gray-500 border-b">
                  <tr>
                    <th className="px-6 py-3 font-medium">게시글 제목</th>
                    <th className="px-6 py-3 font-medium">발행일</th>
                    <th className="px-6 py-3 font-medium">조회수</th>
                    <th className="px-6 py-3 font-medium">키워드 순위 (Tracking)</th>
                    <th className="px-6 py-3 font-medium">상태</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {blog.posts.map((post: any) => (
                    <tr key={post.id} className="hover:bg-gray-50 transition">
                      <td className="px-6 py-4 font-medium text-gray-900">
                        {post.title}
                        {post.published_url && (
                          <a href={post.published_url} target="_blank" rel="noreferrer" className="ml-2 text-blue-400 hover:text-blue-600 inline-block">
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        )}
                      </td>
                      <td className="px-6 py-4 text-gray-500 flex items-center">
                        <Clock className="w-3 h-3 mr-1.5" /> {timeAgo(post.created_at)}
                      </td>
                      <td className="px-6 py-4">
                        {post.view_count === 0 && blog.platform === "Naver" ? (
                          <span className="text-gray-300">-</span>
                        ) : (
                          <div className="flex items-center text-gray-700">
                            <Eye className="w-3 h-3 mr-1.5" /> {post.view_count}
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        {Object.keys(post.keyword_ranks || {}).length > 0 ? (
                          <div className="flex flex-wrap gap-2">
                            {Object.entries(post.keyword_ranks || {}).map(([k, v]) => (
                              <span key={k} className="px-2 py-1 bg-blue-50 text-blue-700 rounded text-xs border border-blue-100">
                                {k}: <span className="font-bold">{String(v)}위</span>
                              </span>
                            ))}
                          </div>
                        ) : (
                          <span className="text-gray-300 text-xs">집계 중...</span>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        <span className={`px-2 py-1 rounded text-xs font-bold ${
                          post.status === "PUBLISHED" ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-600"
                        }`}>
                          {post.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                  {blog.posts.length === 0 && (
                    <tr>
                      <td colSpan={5} className="px-6 py-8 text-center text-gray-400">
                        아직 발행된 글이 없습니다. AI로 첫 글을 작성해보세요!
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

