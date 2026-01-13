export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://34.64.50.56";

export const buildHeaders = () => {
  if (typeof window === "undefined") {
    return {
      "Content-Type": "application/json",
    };
  }

  const token = localStorage.getItem("token");
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
};

export type CreditStatusPayload = {
  current_credit: number;
  upcoming_deduction: number;
  currency?: string;
};

export type SchedulePayload = {
  frequency: "hourly" | "daily" | "weekly";
  posts_per_day: number;
  days: string[];
  target_times: string[];
};

export type KeywordTrackerRow = {
  keyword: string;
  platform: string;
  rank: number;
  change: number;
  updated_at: string;
};

export type PreviewRequest = {
  topic: string;
  persona: string;
  free_trial?: boolean;
  image_count?: number;
  custom_prompt?: string;
  word_count_range?: [number, number];
};

export type PreviewResponse = {
  html: string;
  summary: string;
  credits_required?: number;
  images?: string[];
  status?: string;
  image_total?: number;
  post_id?: number;
  image_error?: string | null;
};

export async function fetchCreditStatus(): Promise<CreditStatusPayload> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/credits/status`, {
      method: "GET",
      headers: buildHeaders(),
    });
    if (!response.ok) {
      throw new Error("Credit status API error");
    }
    return await response.json();
  } catch (error) {
    console.warn("fetchCreditStatus fallback triggered", error);
    return { current_credit: 42, upcoming_deduction: 6, currency: "KRW" };
  }
}

export async function fetchScheduleConfig(): Promise<SchedulePayload | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/schedule`, {
      method: "GET",
      headers: buildHeaders(),
    });
    if (!response.ok) {
      throw new Error("Schedule API error");
    }
    return await response.json();
  } catch (error) {
    console.warn("fetchScheduleConfig fallback triggered", error);
    return null;
  }
}

export async function saveScheduleConfig(payload: SchedulePayload): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/schedule`, {
    method: "POST",
    headers: buildHeaders(),
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error("Failed to save schedule");
  }
}

export async function fetchKeywordTracking(): Promise<KeywordTrackerRow[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/posts/keywords`, {
      method: "GET",
      headers: buildHeaders(),
    });
    if (!response.ok) {
      throw new Error("Keyword tracker API error");
    }
    return await response.json();
  } catch (error) {
    console.warn("fetchKeywordTracking fallback triggered", error);
    return [
      {
        keyword: "AI 마케팅 자동화",
        platform: "Naver",
        rank: 3,
        change: 1,
        updated_at: "2시간 전",
      },
      {
        keyword: "노코드 블로그",
        platform: "Tistory",
        rank: 7,
        change: -1,
        updated_at: "5시간 전",
      },
      {
        keyword: "자연어 SEO",
        platform: "WordPress",
        rank: 12,
        change: 0,
        updated_at: "1일 전",
      },
    ];
  }
}

export async function generatePreviewHtml(body: PreviewRequest): Promise<PreviewResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/posts/preview`, {
    method: "POST",
    headers: buildHeaders(),
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    let detail = "Preview API error";
    try {
      const err = await response.json();
      detail = err?.detail || detail;
    } catch {
      // ignore
    }
    throw new Error(detail);
  }
  return await response.json();
}

export type BlogAnalysisResponse = {
  category: string;
  prompt: string;
};

export async function fetchBlogAnalysis(params?: { blog_id?: number; blog_url?: string; alias?: string }): Promise<BlogAnalysisResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/blogs/analyze`, {
    method: "POST",
    headers: buildHeaders(),
    body: JSON.stringify(params || {}),
  });
  if (!response.ok) {
    throw new Error("Blog analysis API error");
  }
  return await response.json();
}

export async function publishPostManual(postId: number): Promise<{ status: string; url?: string; message?: string }> {
  const response = await fetch(`${API_BASE_URL}/api/v1/posts/${postId}/publish`, {
    method: "POST",
    headers: buildHeaders(),
  });
  if (!response.ok) {
    let detail = "Publish API error";
    try {
      const err = await response.json();
      detail = err?.detail || detail;
    } catch {
      // ignore
    }
    throw new Error(detail);
  }
  return await response.json();
}

export type RechargeRequestPayload = {
  amount: number;
  requested_credits: number;
  depositor_name: string;
};

export async function createRechargeRequest(payload: RechargeRequestPayload): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/api/v1/credits/recharge/request`, {
    method: "POST",
    headers: buildHeaders(),
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error("Recharge request failed");
  }
  return await response.json();
}

export async function fetchRechargeHistory(): Promise<any[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/credits/recharge/history`, {
    headers: buildHeaders(),
  });
  return await response.json();
}

export async function fetchPendingPayments(): Promise<any[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/admin/credits/pending-payments`, {
    headers: buildHeaders(),
  });
  return await response.json();
}

export async function confirmPayment(requestId: number, approve: boolean): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/api/v1/admin/credits/confirm-payment`, {
    method: "POST",
    headers: buildHeaders(),
    body: JSON.stringify({ request_id: requestId, approve }),
  });
  if (!response.ok) {
    throw new Error("Payment confirmation failed");
  }
  return await response.json();
}

export async function trackPost(postId: number): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/api/v1/posts/${postId}/track`, {
    method: "POST",
    headers: buildHeaders(),
  });
  if (!response.ok) {
    throw new Error("Tracking request failed");
  }
  return await response.json();
}

