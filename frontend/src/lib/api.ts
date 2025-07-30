const API_BASE_URL = "https://groceryghost-api.qubzes.com/api";

export interface ScrapeRequest {
  url: string;
}

export interface ScrapeResponse {
  message: string;
  session_id: string;
}

export interface Product {
  id: string;
  name: string;
  current_price: string | null;
  original_price: string | null;
  unit_size: string | null;
  category: string | null;
  url: string;
  image_url: string | null;
  dietary_tags: string[];
}

export interface Session {
  id: string;
  name: string;
  url: string;
  status: "queued" | "in_progress" | "completed" | "failed" | "canceled";
  total_pages: number;
  scraped_pages: number;
  started_at: string;
  completed_at: string | null;
  product_count: number;
}

export interface SessionDetail extends Session {
  progress: number;
  error: string | null;
  total_products: number;
  products: Product[];
}

export interface SessionsResponse {
  sessions: Session[];
}

class ApiService {
  private async request<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;

    const response = await fetch(url, {
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const errorData = await response
        .json()
        .catch(() => ({ detail: "Unknown error" }));
      throw new Error(errorData.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  async startScraping(request: ScrapeRequest): Promise<ScrapeResponse> {
    return this.request<ScrapeResponse>("/scrape", {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  async getSessions(): Promise<SessionsResponse> {
    return this.request<SessionsResponse>("/sessions");
  }

  async getSession(sessionId: string): Promise<SessionDetail> {
    return this.request<SessionDetail>(`/session/${sessionId}`);
  }

  async deleteSession(sessionId: string): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/session/${sessionId}`, {
      method: "DELETE",
    });
  }

  async exportSession(sessionId: string): Promise<Blob> {
    const url = `${API_BASE_URL}/session/${sessionId}/export`;
    const response = await fetch(url);

    if (!response.ok) {
      throw new Error(`Export failed: ${response.statusText}`);
    }

    return response.blob();
  }

  // Helper method to download exported data
  downloadExport(blob: Blob, filename: string) {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.style.display = "none";
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  }
}

export const apiService = new ApiService();
