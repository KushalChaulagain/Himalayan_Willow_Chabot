import React, { createContext, useContext, useState, useCallback, useRef, ReactNode, useEffect } from 'react';
import { Message, ChatConfig, InteractiveContent } from '../types';
import APIClient from '../services/api';
import { loadProfile, saveProfile, isReturningUser, getSavedSessionId } from '../utils/userProfile';
import { useAuth } from './AuthContext';

const RESPONSE_TIMEOUT_MS = 30_000;

interface ChatContextType {
  messages: Message[];
  isTyping: boolean;
  isStreaming: boolean;
  isOnline: boolean;
  sessionId: string | null;
  sendMessage: (text: string, useStreaming?: boolean) => Promise<void>;
  retryMessage: (messageId: string) => void;
  addToCart: (productId: number) => void;
  removeFromCartAt: (index: number) => void;
  cartItems: number[];
  addBotMessage: (text: string, extras?: Partial<Message>) => void;
  apiClient: APIClient;
  apiUrl: string;
  googleClientId?: string;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export const useChatContext = () => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChatContext must be used within ChatProvider');
  }
  return context;
};

interface ChatProviderProps {
  children: ReactNode;
  config: ChatConfig;
}

export const ChatProvider: React.FC<ChatProviderProps> = ({ children, config }) => {
  const { token } = useAuth();
  const tokenRef = useRef<string | null>(null);
  useEffect(() => {
    tokenRef.current = token;
  }, [token]);

  const [messages, setMessages] = useState<Message[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [sessionId, setSessionId] = useState<string | null>(() => getSavedSessionId());
  const [cartItems, setCartItems] = useState<number[]>(() => {
    const profile = loadProfile();
    return profile?.cart_items || [];
  });
  const [apiClient] = useState(
    () =>
      new APIClient(config.apiUrl, undefined, {
        getAuthHeaders: (): Record<string, string> =>
          tokenRef.current ? { Authorization: `Bearer ${tokenRef.current}` } : {},
      })
  );
  const [, setStreamingMessageId] = useState<string | null>(null);
  const responseTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const greetingFetched = useRef(false);

  // Fetch dynamic greeting on mount
  useEffect(() => {
    if (greetingFetched.current) return;
    greetingFetched.current = true;

    const returning = isReturningUser();

    apiClient.fetchGreeting(sessionId || undefined, returning).then((greeting) => {
      const initialMessage: Message = {
        id: 'greeting-1',
        sender: 'bot',
        message: greeting.message,
        timestamp: new Date(),
        quickReplies: greeting.quick_replies,
        productCards: greeting.product_cards,
      };
      setMessages([initialMessage]);
      saveProfile({ last_visit: new Date().toISOString() });
    });
  }, [apiClient, sessionId]);

  // Network status detection
  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
    };

    const handleOffline = () => {
      setIsOnline(false);
      const offlineMessage: Message = {
        id: `offline-${Date.now()}`,
        sender: 'bot',
        message: "You're currently offline. Please check your internet connection.",
        timestamp: new Date(),
        quickReplies: [],
      };
      setMessages((prev) => [...prev, offlineMessage]);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const addBotMessage = useCallback((text: string, extras?: Partial<Message>) => {
    const botMsg: Message = {
      id: `bot-${Date.now()}`,
      sender: 'bot',
      message: text,
      timestamp: new Date(),
      ...extras,
    };
    setMessages((prev) => [...prev, botMsg]);
  }, []);

  const sendMessage = useCallback(
    async (text: string, useStreaming: boolean = false) => {
      if (!text.trim()) return;

      if (!isOnline) {
        const offlineMessage: Message = {
          id: `offline-${Date.now()}`,
          sender: 'bot',
          message: "You're currently offline. Please check your internet connection and try again.",
          timestamp: new Date(),
          quickReplies: [],
        };
        setMessages((prev) => [...prev, offlineMessage]);
        return;
      }

      const userMessage: Message = {
        id: Date.now().toString(),
        sender: 'user',
        message: text,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, userMessage]);

      setIsTyping(true);

      try {
        let currentSessionId = sessionId;
        if (!currentSessionId) {
          try {
            const session = await apiClient.createSession();
            currentSessionId = session.session_id;
            setSessionId(currentSessionId);
            saveProfile({ session_id: currentSessionId });
          } catch {
            currentSessionId = `temp-${Date.now()}`;
            setSessionId(currentSessionId);
          }
        }

        if (useStreaming) {
          setIsStreaming(true);

          const streamingMsgId = (Date.now() + 1).toString();
          setStreamingMessageId(streamingMsgId);

          const streamingMessage: Message = {
            id: streamingMsgId,
            sender: 'bot',
            message: '...',
            timestamp: new Date(),
            retryText: text,
          };
          setMessages((prev) => [...prev, streamingMessage]);

          responseTimeoutRef.current = setTimeout(() => {
            setIsStreaming(false);
            setIsTyping(false);
            setStreamingMessageId(null);
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === streamingMsgId
                  ? {
                      ...msg,
                      message: msg.message || "The server didn't respond in time. Please try again.",
                      failed: true,
                    }
                  : msg
              )
            );
          }, RESPONSE_TIMEOUT_MS);

          await apiClient.sendMessageStream(
            text,
            currentSessionId,
            (_chunk) => {
              // Only the final parsed message from the "complete" event is shown.
            },
            (response) => {
              if (responseTimeoutRef.current) clearTimeout(responseTimeoutRef.current);
              setIsStreaming(false);
              setStreamingMessageId(null);

              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === streamingMsgId
                    ? {
                        ...msg,
                        message: response.message || msg.message,
                        quickReplies: response.quick_replies,
                        productCards: response.product_cards,
                        interactiveContent: response.interactive_content as InteractiveContent | undefined,
                        failed: false,
                      }
                    : msg
                )
              );

              if (response.session_id && response.session_id !== currentSessionId) {
                setSessionId(response.session_id);
                saveProfile({ session_id: response.session_id });
              }
            },
            (_error) => {
              if (responseTimeoutRef.current) clearTimeout(responseTimeoutRef.current);
              setIsStreaming(false);
              setStreamingMessageId(null);

              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === streamingMsgId
                    ? {
                        ...msg,
                        message: msg.message || "I encountered an error. Please try again.",
                        failed: true,
                      }
                    : msg
                )
              );
            }
          );

          return;
        }

        const response = await apiClient.sendMessage(text, currentSessionId);

        if (!response || !response.message) {
          throw new Error('Invalid response from server');
        }

        const botMessage: Message = {
          id: (Date.now() + 1).toString(),
          sender: 'bot',
          message: response.message,
          timestamp: new Date(),
          productCards: response.product_cards,
          quickReplies: response.quick_replies,
          interactiveContent: response.interactive_content as InteractiveContent | undefined,
        };

        setMessages((prev) => {
          const lastMessage = prev[prev.length - 1];
          if (lastMessage && lastMessage.sender === 'bot' && lastMessage.message === botMessage.message) {
            return prev;
          }
          return [...prev, botMessage];
        });

        if (response.session_id && response.session_id !== currentSessionId) {
          setSessionId(response.session_id);
          saveProfile({ session_id: response.session_id });
        }
      } catch (error) {
        console.error('Unexpected error in sendMessage:', error);

        const errorMessage: Message = {
          id: (Date.now() + 1).toString(),
          sender: 'bot',
          message: "I encountered an unexpected error. Please try again or contact support if the problem persists.",
          timestamp: new Date(),
          quickReplies: ['Retry', 'Talk to human'],
        };

        setMessages((prev) => [...prev, errorMessage]);
      } finally {
        setIsTyping(false);
      }
    },
    [sessionId, apiClient, isOnline]
  );

  const retryMessage = useCallback(
    (messageId: string) => {
      const msg = messages.find((m) => m.id === messageId);
      if (!msg || !msg.retryText) return;
      setMessages((prev) => prev.filter((m) => m.id !== messageId));
      sendMessage(msg.retryText, true);
    },
    [messages, sendMessage]
  );

  const addToCart = useCallback((productId: number) => {
    setCartItems((prev) => {
      const updated = [...prev, productId];
      saveProfile({ cart_items: updated });
      return updated;
    });
  }, []);

  const removeFromCartAt = useCallback((index: number) => {
    setCartItems((prev) => {
      if (index < 0 || index >= prev.length) return prev;
      const updated = prev.filter((_, i) => i !== index);
      saveProfile({ cart_items: updated });
      return updated;
    });
  }, []);

  return (
    <ChatContext.Provider
      value={{
        messages,
        isTyping,
        isStreaming,
        isOnline,
        sessionId,
        sendMessage,
        retryMessage,
        addToCart,
        removeFromCartAt,
        cartItems,
        addBotMessage,
        apiClient,
        apiUrl: config.apiUrl,
        googleClientId: config.googleClientId,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
};
