import {
    ChatResponse,
    GreetingResponse,
    ProductCard,
    TrackingResponse,
    UserProfile,
} from "../types";

interface RetryConfig {
  maxRetries: number;
  baseDelay: number;
  maxDelay: number;
  timeout: number;
}

interface APIClientOptions {
  getAuthHeaders?: () => Record<string, string>;
}

class APIClient {
  private retryConfig: RetryConfig;
  private _getAuthHeaders?: () => Record<string, string>;

  constructor(
    _baseUrl: string,
    retryConfig?: Partial<RetryConfig>,
    options?: APIClientOptions,
  ) {
    this._getAuthHeaders = options?.getAuthHeaders;
    this.retryConfig = {
      maxRetries: 3,
      baseDelay: 1000,
      maxDelay: 10000,
      timeout: 15000,
      ...retryConfig,
    };
  }

  private getHeaders(
    extra: Record<string, string> = {},
  ): Record<string, string> {
    const auth = this._getAuthHeaders?.() ?? {};
    return { ...auth, ...extra };
  }

  private async sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  private calculateBackoff(attempt: number): number {
    const exponentialDelay = this.retryConfig.baseDelay * Math.pow(2, attempt);
    const jitter = Math.random() * 1000;
    return Math.min(exponentialDelay + jitter, this.retryConfig.maxDelay);
  }

  private async fetchWithTimeout(
    url: string,
    options: RequestInit,
    timeout: number,
  ): Promise<Response> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    const mergedHeaders = {
      ...this.getHeaders(),
      ...(options.headers as Record<string, string>),
    };

    try {
      const response = await fetch(url, {
        ...options,
        headers: mergedHeaders,
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      return response;
    } catch (error) {
      clearTimeout(timeoutId);
      if (error instanceof Error && error.name === "AbortError") {
        throw new Error("Request timeout - server took too long to respond");
      }
      throw error;
    }
  }

  async sendMessage(
    message: string,
    sessionId?: string,
  ): Promise<ChatResponse> {
    let lastError: Error | null = null;

    for (let attempt = 0; attempt <= this.retryConfig.maxRetries; attempt++) {
      try {
        const response = await this.fetchWithTimeout(
          `/api/chat/message`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              message,
              session_id: sessionId,
            }),
          },
          this.retryConfig.timeout,
        );

        if (!response.ok) {
          if (response.status === 429) {
            throw new Error("RATE_LIMIT");
          } else if (response.status >= 500) {
            throw new Error(`SERVER_ERROR_${response.status}`);
          } else if (response.status === 404) {
            throw new Error("ENDPOINT_NOT_FOUND");
          } else {
            throw new Error(`HTTP_${response.status}`);
          }
        }

        const data = await response.json();

        if (!data || typeof data.message !== "string") {
          throw new Error("INVALID_RESPONSE_FORMAT");
        }

        return data;
      } catch (error) {
        lastError = error instanceof Error ? error : new Error(String(error));
        console.error(
          `Chat API error (attempt ${attempt + 1}/${this.retryConfig.maxRetries + 1}):`,
          lastError,
        );

        const shouldNotRetry =
          lastError.message.includes("404") ||
          lastError.message.includes("INVALID_RESPONSE_FORMAT") ||
          lastError.message.includes("ENDPOINT_NOT_FOUND");

        if (shouldNotRetry || attempt === this.retryConfig.maxRetries) {
          break;
        }

        const backoffDelay = this.calculateBackoff(attempt);
        await this.sleep(backoffDelay);
      }
    }

    return this.createErrorResponse(lastError!, sessionId);
  }

  private createErrorResponse(error: Error, sessionId?: string): ChatResponse {
    const isNetworkError =
      error instanceof TypeError &&
      (error.message === "Failed to fetch" || error.message?.includes("fetch"));
    const isTimeout = error.message.includes("timeout");
    const isRateLimit = error.message.includes("RATE_LIMIT");
    const isServerError = error.message.includes("SERVER_ERROR");

    let message: string;
    let quickReplies: string[];

    if (isNetworkError) {
      message =
        "I can't reach the server right now. Please check your internet connection and try again.";
      quickReplies = ["Retry", "Talk to human"];
    } else if (isTimeout) {
      message =
        "The server is taking longer than usual to respond. This might be due to high traffic. Would you like to try again?";
      quickReplies = ["Retry", "Show me popular products", "Talk to human"];
    } else if (isRateLimit) {
      message =
        "You're sending messages too quickly. Please wait a moment before trying again.";
      quickReplies = ["Wait and retry", "Talk to human"];
    } else if (isServerError) {
      message =
        "I'm experiencing technical difficulties on my end. Our team has been notified. Would you like to try again or speak with a human?";
      quickReplies = ["Retry", "Talk to human"];
    } else {
      message =
        "I'm having trouble processing your request. Could you try rephrasing? For example: 'Show me bats under 5000 rupees'";
      quickReplies = ["Show me bats", "Show me gloves", "Talk to human"];
    }

    return {
      message,
      quick_replies: quickReplies,
      session_id: sessionId || "",
    };
  }

  async createSession(): Promise<{ session_id: string }> {
    try {
      const response = await this.fetchWithTimeout(
        `/api/chat/session`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({}),
        },
        5000,
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      return { session_id: data.session_id };
    } catch (error) {
      console.error("Session creation error:", error);
      return { session_id: `temp-${Date.now()}` };
    }
  }

  async sendMessageStream(
    message: string,
    sessionId: string,
    onChunk: (chunk: string) => void,
    onComplete: (response: ChatResponse) => void,
    onError: (error: Error) => void,
  ): Promise<void> {
    try {
      const response = await this.fetchWithTimeout(
        `/api/chat/stream`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            message,
            session_id: sessionId,
          }),
        },
        30000,
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error("No response body");
      }

      let buffer = "";
      let fullMessage = "";

      while (true) {
        const { done, value } = await reader.read();

        if (done) {
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = JSON.parse(line.slice(6));

            if (data.type === "chunk") {
              fullMessage += data.content;
              onChunk(data.content);
            } else if (data.type === "complete") {
              onComplete({
                message: data.message || fullMessage,
                session_id: data.session_id,
                quick_replies: data.quick_replies || [],
                product_cards: data.product_cards,
                interactive_content: data.interactive_content,
              });
            } else if (data.type === "error") {
              throw new Error(data.message);
            }
          }
        }
      }
    } catch (error) {
      console.error("Streaming error:", error);
      onError(error instanceof Error ? error : new Error(String(error)));
    }
  }

  // ── Dynamic Greeting ─────────────────────────────────────────────

  async fetchGreeting(
    sessionId?: string,
    isReturning?: boolean,
    userId?: number,
    cartItemIds?: number[],
  ): Promise<GreetingResponse> {
    try {
      const params = new URLSearchParams();
      if (sessionId) params.set("session_id", sessionId);
      if (isReturning) params.set("returning", "true");
      if (userId) params.set("user_id", String(userId));
      if (cartItemIds?.length)
        params.set("cart_item_ids", cartItemIds.join(","));

      const response = await this.fetchWithTimeout(
        `/api/chat/greeting?${params.toString()}`,
        { method: "GET" },
        5000,
      );

      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch {
      return {
        message:
          "Namaste! Welcome to Himalayan Willow. Browse our gear or describe what you need:",
        quick_replies: [
          "Show me Bats",
          "Balls & Accessories",
          "Protection Gear",
        ],
        product_cards: [],
        is_returning_user: false,
      };
    }
  }

  // ── Image Upload (Visual Search) ─────────────────────────────────

  async uploadImageForSearch(
    file: File,
    category?: string,
    onProgress?: (percent: number) => void,
  ): Promise<{ products: ProductCard[]; count: number }> {
    const formData = new FormData();
    formData.append("file", file);
    if (category) formData.append("category", category);

    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open("POST", "/api/chat/visual-search");
      const authHeaders = this.getHeaders();
      if (authHeaders.Authorization) {
        xhr.setRequestHeader("Authorization", authHeaders.Authorization);
      }

      if (onProgress) {
        xhr.upload.addEventListener("progress", (e) => {
          if (e.lengthComputable)
            onProgress(Math.round((e.loaded / e.total) * 100));
        });
      }

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          const data = JSON.parse(xhr.responseText);
          const products: ProductCard[] = (data.products || []).map(
            (p: any) => ({
              id: p.product_id ?? p.id,
              name: p.name,
              price: p.price,
              image_url: p.image_url,
              category: p.category,
              rating: p.rating,
              reason: p.reason || "Visually similar product",
              in_stock: true,
            }),
          );
          resolve({ products, count: data.count || products.length });
        } else {
          reject(new Error(`Upload failed: HTTP ${xhr.status}`));
        }
      };

      xhr.onerror = () => reject(new Error("Upload failed: network error"));
      xhr.ontimeout = () => reject(new Error("Upload timed out"));
      xhr.timeout = 30000;
      xhr.send(formData);
    });
  }

  // ── Bat Finder Quiz ─────────────────────────────────────────────

  async submitBatFinder(params: {
    playing_level: string;
    surface: string;
    budget: string;
    weight_preference?: number;
    session_id?: string;
  }): Promise<{
    message: string;
    product_cards?: ProductCard[];
    educational_content?: {
      title: string;
      body: string;
      animationType: string;
    };
    quick_replies?: string[];
  }> {
    try {
      const response = await this.fetchWithTimeout(
        `/api/chat/bat-finder`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(params),
        },
        10000,
      );
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      console.error("Bat finder error:", error);
      return {
        message:
          "I couldn't process your bat finder quiz. Please try again or ask me to show you bats.",
        quick_replies: ["Show me bats", "Talk to human"],
      };
    }
  }

  // ── Order Tracking ───────────────────────────────────────────────

  async getOrderTracking(orderId: string): Promise<TrackingResponse | null> {
    try {
      const response = await this.fetchWithTimeout(
        `/api/orders/${orderId}/tracking`,
        { method: "GET" },
        this.retryConfig.timeout,
      );

      if (!response.ok) return null;
      return await response.json();
    } catch {
      return null;
    }
  }

  // ── User Profile (Personalization) ───────────────────────────────

  async getUserProfile(sessionId: string): Promise<UserProfile | null> {
    try {
      const response = await this.fetchWithTimeout(
        `/api/user/profile/${sessionId}`,
        { method: "GET" },
        5000,
      );

      if (!response.ok) return null;
      return await response.json();
    } catch {
      return null;
    }
  }

  async updateUserProfile(
    sessionId: string,
    profile: Partial<UserProfile>,
  ): Promise<boolean> {
    try {
      const response = await this.fetchWithTimeout(
        `/api/user/profile/${sessionId}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(profile),
        },
        5000,
      );

      return response.ok;
    } catch {
      return false;
    }
  }

  // ── Instant Buy (Order Creation) ─────────────────────────────────

  async getCartProducts(ids: number[]): Promise<ProductCard[]> {
    if (!ids.length) return [];
    try {
      const response = await this.fetchWithTimeout(
        `/api/products?ids=${ids.join(",")}`,
        { method: "GET" },
        5000,
      );
      if (!response.ok) return [];
      const data = await response.json();
      const products = (data.products || []) as Array<{
        id: number;
        name: string;
        price: number;
        image_url?: string;
        category?: string;
        in_stock?: boolean;
      }>;
      return products.map((p) => ({
        id: p.id,
        name: p.name,
        price: p.price,
        image_url: p.image_url,
        category: p.category,
        reason: "",
        in_stock: p.in_stock ?? true,
      }));
    } catch {
      return [];
    }
  }

  async createOrder(orderData: {
    session_id: string;
    payment_method: string;
    customer_phone: string;
    customer_email?: string;
    delivery_address: Record<string, string>;
    items: Array<{
      product_id: number;
      product_name: string;
      product_sku: string;
      unit_price: number;
      quantity: number;
      subtotal: number;
    }>;
  }): Promise<{ order_id: string; total_amount: number } | null> {
    try {
      const response = await this.fetchWithTimeout(
        `/api/orders/create`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(orderData),
        },
        this.retryConfig.timeout,
      );

      if (!response.ok) return null;
      const data = await response.json();
      return { order_id: data.order_id, total_amount: data.total_amount };
    } catch {
      return null;
    }
  }
}

export default APIClient;
