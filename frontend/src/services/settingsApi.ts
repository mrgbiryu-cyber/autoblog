const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

const getHeaders = () => {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  return {
    "Content-Type": "application/json",
    Authorization: token ? `Bearer ${token}` : "",
  };
};

export const updateBlogConfig = async (data: any) => {
  const res = await fetch(`${API_BASE}/config/blog-settings`, {
    method: "PUT",
    headers: getHeaders(),
    body: JSON.stringify(data),
  });
  return res.json();
};

export const updateSchedule = async (data: any) => {
  const res = await fetch(`${API_BASE}/config/schedule`, {
    method: "PUT",
    headers: getHeaders(),
    body: JSON.stringify(data),
  });
  return res.json();
};

export const getEstimate = async (length: string, imageCount: number) => {
  const res = await fetch(
    `${API_BASE}/config/estimate?length=${length}&image_count=${imageCount}`,
    {
      headers: getHeaders(),
    }
  );
  return res.json();
};

