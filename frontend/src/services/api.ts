import { ChatResponse } from '../types';

class APIClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  async sendMessage(message: string, sessionId?: string): Promise<ChatResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/api/chat/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message,
          session_id: sessionId,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Chat API error:', error);
      return {
        message: "I'm having trouble connecting. Please try again in a moment.",
        quick_replies: ['Retry', 'Talk to human'],
        session_id: sessionId || '',
      };
    }
  }

  async createSession(): Promise<{ session_id: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/api/chat/session`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({}),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      return { session_id: data.session_id };
    } catch (error) {
      console.error('Session creation error:', error);
      // Generate a temporary session ID
      return { session_id: `temp-${Date.now()}` };
    }
  }
}

export default APIClient;
