"use client";

import { useState, useEffect } from "react";
import axios from "axios";
import { BarChart3, Clock, Eye, ExternalLink, Loader2, Download, Image as ImageIcon, FileCode } from "lucide-react";
import { publishPostManual, buildHeaders } from "@/lib/api";

// 환경변수를 못 읽더라도 무조건 형님의 서버 IP를 바라보게 합니다.
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://34.64.50.56";

export default function StatusPage() {
  const [statusData, setStatusData] = useState<any[]>([]);
  const [publishLoading, setPublishLoading] = useState<number | null>(null);

  const fetchStatus = async () => {
    try {
      const res = await axios.get(`${API_BASE_URL}/api/v1/posts/status`, {
        headers: buildHeaders()
      });
      setStatusData(res.data);
    } catch (err) {
      console.error("현황 로드 실패", err);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const handlePublishManual = async (postId: number) => {
    if (!confirm("이 포스팅을 발행 처리하시겠습니까? 발행 후 자동으로 순위 트래킹이 시작됩니다.")) return;
    setPublishLoading(postId);
    try {
      const res = await publishPostManual(postId);
      if (res.status === "success") {
        alert("발행 및 트래킹 시작이 완료되었습니다.");
        fetchStatus();
      } else {
        alert(`발행 실패: ${res.message}`);
      }
    } catch (err) {
      alert("발행 중 오류가 발생했습니다.");
    } finally {
      setPublishLoading(null);
    }
  };

  const handleDownloadHtml = (post: any) => {
    window.open(`${API_BASE_URL}/api/v1/posts/${post.id}/download/html`, "_blank");
  };

  const handleDownloadImages = (post: any) => {
    window.open(`${API_BASE_URL}/api/v1/posts/${post.id}/download/images`, "_blank");
  };

  const getImgGenStatusText = (status: string) => {
    switch (status) {
      case "PENDING": return "이미지 생성 대기 중...";
      case "PROCESSING": return "이미지 생성 중...";
      case "COMPLETED": return "생성 완료";
      case "TIMEOUT": return "타임아웃 (다운로드 권장)";
      case "FAILED": return "생성 실패";
      default: return "대기 중";
    }
  };

  const timeAgo = (date: string) => {
    const now = new Date();
    const past = new Date(date);
    const diff = now.getTime() - past.getTime();
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) return `${days}일 전`;
    if (hours > 0) return `${hours}시간 전`;
    if (minutes > 0) return `${minutes}분 전`;
    return "방금 전";
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
                    <th className="px-6 py-3 font-medium">이미지 상태</th>
                    <th className="px-6 py-3 font-medium">다운로드</th>
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
                        <div className={`text-xs font-semibold ${
                          post.img_gen_status === "COMPLETED" ? "text-green-600" :
                          post.img_gen_status === "TIMEOUT" ? "text-amber-600" :
                          "text-blue-600 animate-pulse"
                        }`}>
                          {getImgGenStatusText(post.img_gen_status)}
                        </div>
                        {post.img_gen_status === "TIMEOUT" && (
                          <p className="text-[10px] text-gray-400 mt-1">서버 부하로 지연됨</p>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleDownloadHtml(post)}
                            className="p-1.5 bg-slate-100 hover:bg-slate-200 rounded-lg transition text-slate-600"
                            title="HTML 다운로드"
                          >
                            <FileCode className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleDownloadImages(post)}
                            disabled={!post.image_paths || post.image_paths.length === 0}
                            className="p-1.5 bg-slate-100 hover:bg-slate-200 rounded-lg transition text-slate-600 disabled:opacity-30"
                            title="이미지 다운로드"
                          >
                            <ImageIcon className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <span className={`px-2 py-1 rounded text-xs font-bold ${
                            post.status === "PUBLISHED" ? "bg-green-100 text-green-700" : 
                            post.status === "PUBLISH_FAILED" ? "bg-red-100 text-red-700" :
                            "bg-gray-100 text-gray-600"
                          }`}>
                            {post.status === "PUBLISH_FAILED" ? "발행 실패" : post.status}
                          </span>
                          {post.status !== "PUBLISHED" && (
                            <button
                              onClick={() => handlePublishManual(post.id)}
                              disabled={publishLoading === post.id}
                              className="px-2 py-1 bg-blue-600 text-white rounded text-[10px] font-bold hover:bg-blue-500 disabled:opacity-50 flex items-center gap-1"
                            >
                              {publishLoading === post.id && <Loader2 className="w-3 h-3 animate-spin" />}
                              발행 완료
                            </button>
                          )}
                        </div>
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

