"use client";

import { useEffect, useState } from "react";
import { updateBlogConfig, updateSchedule, getEstimate } from "@/services/settingsApi";

const days = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"];

export default function SettingsPage() {
  const [blogConfig, setBlogConfig] = useState({
    category: "",
    custom_prompt: "블로그 글을 작성해줘.",
    post_length: "MEDIUM",
    image_count: 1,
  });
  const [schedule, setSchedule] = useState({
    is_active: true,
    frequency: "DAILY",
    active_days: [] as string[],
    posts_per_day: 1,
    target_times: ["09:00"],
  });
  const [estimatedCost, setEstimatedCost] = useState(0);

  useEffect(() => {
    const fetchEstimate = async () => {
      try {
        const res = await getEstimate(blogConfig.post_length, blogConfig.image_count);
        if (res.estimated_credit) setEstimatedCost(res.estimated_credit);
      } catch (e) {
        console.error(e);
      }
    };
    fetchEstimate();
  }, [blogConfig.post_length, blogConfig.image_count]);

  const handlePostCountChange = (count: number) => {
    if (count < 1) return;
    const newTimes = [...schedule.target_times];
    if (count > newTimes.length) {
      for (let i = newTimes.length; i < count; i++) {
        newTimes.push("09:00");
      }
    } else {
      newTimes.splice(count);
    }
    setSchedule({ ...schedule, posts_per_day: count, target_times: newTimes });
  };

  const handleTimeChange = (index: number, value: string) => {
    const newTimes = [...schedule.target_times];
    newTimes[index] = value;
    setSchedule({ ...schedule, target_times: newTimes });
  };

  const handleSave = async () => {
    try {
      await updateBlogConfig(blogConfig);
      await updateSchedule(schedule);
      alert("설정이 저장되었습니다!");
    } catch (e) {
      alert("저장 실패");
    }
  };

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-8 text-gray-800">
      <h1 className="text-2xl font-bold mb-6">자동화 설정 (Auto-Posting Setup)</h1>

      <section className="bg-white p-6 rounded-lg shadow border space-y-4">
        <h2 className="text-xl font-semibold">1. 글 작성 옵션</h2>
        <div className="grid gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">기본 카테고리</label>
            <input
              type="text"
              className="w-full border p-2 rounded"
              value={blogConfig.category}
              onChange={(e) => setBlogConfig({ ...blogConfig, category: e.target.value })}
              placeholder="예: IT/테크, 일상"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">기본 프롬프트 (수정 가능)</label>
            <textarea
              className="w-full border p-2 rounded h-24"
              value={blogConfig.custom_prompt}
              onChange={(e) => setBlogConfig({ ...blogConfig, custom_prompt: e.target.value })}
            />
          </div>
          <div className="flex gap-6">
            <div className="flex-1">
              <label className="block text-sm font-medium mb-1">글 길이</label>
              <select
                className="w-full border p-2 rounded"
                value={blogConfig.post_length}
                onChange={(e) => setBlogConfig({ ...blogConfig, post_length: e.target.value })}
              >
                <option value="SHORT">짧게 (Short)</option>
                <option value="MEDIUM">보통 (Medium)</option>
                <option value="LONG">길게 (Long - 크레딧 ↑)</option>
              </select>
            </div>
            <div className="flex-1">
              <label className="block text-sm font-medium mb-1">이미지 개수 (0~5)</label>
              <input
                type="number"
                min={0}
                max={5}
                className="w-full border p-2 rounded"
                value={blogConfig.image_count}
                onChange={(e) =>
                  setBlogConfig({
                    ...blogConfig,
                    image_count: Number(e.target.value),
                  })
                }
              />
            </div>
          </div>
          <div className="mt-2 bg-blue-50 text-blue-800 p-3 rounded text-right font-bold">
            💰 예상 소모 크레딧: {estimatedCost} Credit / 1 포스팅
          </div>
        </div>
      </section>

      <section className="bg-white p-6 rounded-lg shadow border space-y-4">
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-semibold">2. 스케줄링 설정</h2>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={schedule.is_active}
              onChange={(e) => setSchedule({ ...schedule, is_active: e.target.checked })}
              className="w-5 h-5"
            />
            <span className="font-medium">자동 발행 켜기</span>
          </label>
        </div>

        <div className={`${!schedule.is_active ? "opacity-40 pointer-events-none" : ""}`}>
          <div className="flex gap-4 text-sm">
            <label className="flex items-center gap-2">
              <input
                type="radio"
                name="frequency"
                value="DAILY"
                checked={schedule.frequency === "DAILY"}
                onChange={() => setSchedule({ ...schedule, frequency: "DAILY" })}
              />
              매일 (Daily)
            </label>
            <label className="flex items-center gap-2">
              <input
                type="radio"
                name="frequency"
                value="WEEKLY"
                checked={schedule.frequency === "WEEKLY"}
                onChange={() => setSchedule({ ...schedule, frequency: "WEEKLY" })}
              />
              특정 요일 (Weekly)
            </label>
          </div>

          {schedule.frequency === "WEEKLY" && (
            <div className="flex flex-wrap gap-2 mt-2">
              {days.map((day) => (
                <button
                  key={day}
                  type="button"
                  className={`border px-3 py-1 rounded cursor-pointer ${
                    schedule.active_days.includes(day)
                      ? "bg-blue-600 text-white"
                      : "text-gray-600"
                  }`}
                  onClick={() => {
                    const next = schedule.active_days.includes(day)
                      ? schedule.active_days.filter((d) => d !== day)
                      : [...schedule.active_days, day];
                    setSchedule({ ...schedule, active_days: next });
                  }}
                >
                  {day}
                </button>
              ))}
            </div>
          )}

          <div className="mt-4 border-t pt-4 space-y-4">
            <label className="block">
              <span className="text-sm font-medium">하루 발행 횟수</span>
              <input
                type="number"
                min={1}
                max={10}
                className="border p-2 rounded w-24 mt-1"
                value={schedule.posts_per_day}
                onChange={(e) => handlePostCountChange(Number(e.target.value))}
              />
            </label>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
              {schedule.target_times.map((time, idx) => (
                <label key={idx} className="flex items-center gap-2">
                  <span className="text-gray-500 text-sm">{idx + 1}회:</span>
                  <input
                    type="time"
                    className="border p-2 rounded"
                    value={time}
                    onChange={(e) => handleTimeChange(idx, e.target.value)}
                  />
                </label>
              ))}
            </div>
          </div>
        </div>
      </section>

      <div className="text-right">
        <button
          onClick={handleSave}
          className="bg-black text-white px-8 py-3 rounded-lg text-lg font-bold hover:bg-gray-800 transition"
        >
          설정 저장하기
        </button>
      </div>
    </div>
  );
}

