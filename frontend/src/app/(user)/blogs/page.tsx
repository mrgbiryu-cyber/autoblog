"use client";

import { useState, useEffect } from "react";
import axios from "axios";
import { Plus, Globe } from "lucide-react";

export default function BlogManagePage() {
  const [blogs, setBlogs] = useState<any[]>([]);
  const [isAdding, setIsAdding] = useState(false);
  const [newBlog, setNewBlog] = useState({
    alias: "",
    platform_type: "Naver",
    blog_url: "",
    blog_id: "",
    api_access_token: ""
  });

  const fetchBlogs = async () => {
    try {
      const res = await axios.get("http://127.0.0.1:8000/api/v1/blogs/");
      setBlogs(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchBlogs();
  }, []);

  const handleAddBlog = async () => {
    try {
      await axios.post("http://127.0.0.1:8000/api/v1/blogs/", newBlog);
      alert("블로그가 추가되었습니다.");
      setIsAdding(false);
      setNewBlog({ alias: "", platform_type: "Naver", blog_url: "", blog_id: "", api_access_token: "" });
      fetchBlogs();
    } catch (err) {
      alert("등록 실패: 입력 정보를 확인해주세요.");
    }
  };

  return (
    <div className="p-8 bg-gray-50 min-h-screen space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">블로그 관리</h1>
          <p className="text-gray-500">여러 개의 블로그를 등록하고 관리하세요. (다다익선!)</p>
        </div>
        <button 
          onClick={() => setIsAdding(!isAdding)}
          className="bg-blue-600 text-white px-5 py-3 rounded-xl font-bold hover:bg-blue-700 flex items-center transition"
        >
          <Plus className="w-5 h-5 mr-2" /> 새 블로그 추가
        </button>
      </div>

      {isAdding && (
        <div className="bg-white p-6 rounded-2xl shadow-lg border border-blue-100">
          <h3 className="font-bold text-lg mb-4">새 블로그 등록</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <label className="text-sm font-bold text-gray-700">관리용 별칭</label>
              <input 
                type="text" 
                placeholder="예: 내 맛집 블로그"
                className="w-full p-3 border rounded-lg"
                value={newBlog.alias}
                onChange={(e) => setNewBlog({...newBlog, alias: e.target.value})}
              />
            </div>
            <div>
              <label className="text-sm font-bold text-gray-700">플랫폼</label>
              <select 
                className="w-full p-3 border rounded-lg"
                value={newBlog.platform_type}
                onChange={(e) => setNewBlog({...newBlog, platform_type: e.target.value})}
              >
                <option value="Naver">네이버 블로그</option>
                <option value="WordPress">워드프레스</option>
                <option value="Tistory">티스토리</option>
              </select>
            </div>
            <div>
              <label className="text-sm font-bold text-gray-700">블로그 ID</label>
              <input 
                type="text" 
                placeholder="ID 또는 Username"
                className="w-full p-3 border rounded-lg"
                value={newBlog.blog_id}
                onChange={(e) => setNewBlog({...newBlog, blog_id: e.target.value})}
              />
            </div>
            <div>
              <label className="text-sm font-bold text-gray-700">블로그 URL</label>
              <input 
                type="text" 
                placeholder="https://..."
                className="w-full p-3 border rounded-lg"
                value={newBlog.blog_url}
                onChange={(e) => setNewBlog({...newBlog, blog_url: e.target.value})}
              />
            </div>
          </div>
          <div className="flex justify-end">
            <button onClick={handleAddBlog} className="bg-gray-900 text-white px-6 py-2 rounded-lg font-bold">저장하기</button>
          </div>
        </div>
      )}

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        {blogs.map((blog) => (
          <div key={blog.id} className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
            <div className="flex justify-between items-start mb-4">
              <div className={`p-2 rounded-lg ${blog.platform_type === 'Naver' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'}`}>
                <Globe className="w-6 h-6" />
              </div>
              <span className="text-xs font-mono bg-gray-100 px-2 py-1 rounded text-gray-500">{blog.platform_type}</span>
            </div>
            <h3 className="text-xl font-bold text-gray-900 mb-1">{blog.alias || "이름 없음"}</h3>
            <p className="text-sm text-gray-500 mb-4 truncate">{blog.blog_url}</p>
            <div className="flex items-center text-xs text-gray-400 space-x-2">
              <span>ID: {blog.blog_id}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

