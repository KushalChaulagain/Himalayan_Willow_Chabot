import React, {
    createContext,
    ReactNode,
    useCallback,
    useContext,
    useEffect,
    useRef,
    useState,
} from "react";
import APIClient from "../services/api";
import { ChatConfig, InteractiveContent, Message, ProductCard } from "../types";
import { getSavedSessionId, loadProfile, saveProfile } from "../utils/userProfile";
import { useAuth } from "./AuthContext";

const RESPONSE_TIMEOUT_MS = 30_000;

const STREAMING_CHARS_PER_TICK = 1;
const DEFAULT_STREAM_SPEED_MS = 35;

interface ChatContextType {
  messages: Message[];
  isTyping: boolean;
  isStreaming: boolean;
  streamingMessageId: string | null;
  isOnline: boolean;
  sessionId: string | null;
  sendMessage: (text: string, useStreaming?: boolean) => Promise<void>;
  stopStream: () => void;
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
    throw new Error("useChatContext must be used within ChatProvider");
  }
  return context;
};

interface ChatProviderProps {
  children: ReactNode;
  config: ChatConfig;
}

export const ChatProvider: React.FC<ChatProviderProps> = ({
  children,
  config,
}) => {
  const { token } = useAuth();
  const tokenRef = useRef<string | null>(null);
  useEffect(() => {
    tokenRef.current = token;
  }, [token]);

  const [messages, setMessages] = useState<Message[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [sessionId, setSessionId] = useState<string | null>(() =>
    getSavedSessionId(),
  );
  const [cartItems, setCartItems] = useState<number[]>(() => {
    const profile = loadProfile();
    return profile?.cart_items || [];
  });
  const [apiClient] = useState(
    () =>
      new APIClient(config.apiUrl, undefined, {
        getAuthHeaders: (): Record<string, string> =>
          tokenRef.current
            ? { Authorization: `Bearer ${tokenRef.current}` }
            : {},
      }),
  );
  const [streamingMessageId, setStreamingMessageId] = useState<string | null>(null);
  const responseTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const streamAbortControllerRef = useRef<AbortController | null>(null);
  const streamingAccumulatedRef = useRef<string>("");
  const streamingDisplayedLengthRef = useRef<number>(0);
  const streamingTypingIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const streamingPendingCompleteRef = useRef<{
    message: string;
    quick_replies?: string[];
    product_cards?: ProductCard[];
    interactive_content?: InteractiveContent;
    session_id?: string;
  } | null>(null);

  // Network status detection
  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
    };

    const handleOffline = () => {
      setIsOnline(false);
      const offlineMessage: Message = {
        id: `offline-${Date.now()}`,
        sender: "bot",
        message:
          "You're currently offline. Please check your internet connection.",
        timestamp: new Date(),
        quickReplies: [],
      };
      setMessages((prev) => [...prev, offlineMessage]);
    };

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);

  const addBotMessage = useCallback(
    (text: string, extras?: Partial<Message>) => {
      const botMsg: Message = {
        id: `bot-${Date.now()}`,
        sender: "bot",
        message: text,
        timestamp: new Date(),
        ...extras,
      };
      setMessages((prev) => [...prev, botMsg]);
    },
    [],
  );

  const sendMessage = useCallback(
    async (text: string, useStreaming: boolean = false) => {
      if (!text.trim()) return;

      if (!isOnline) {
        const offlineMessage: Message = {
          id: `offline-${Date.now()}`,
          sender: "bot",
          message:
            "You're currently offline. Please check your internet connection and try again.",
          timestamp: new Date(),
          quickReplies: [],
        };
        setMessages((prev) => [...prev, offlineMessage]);
        return;
      }

      const userMessage: Message = {
        id: Date.now().toString(),
        sender: "user",
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
          streamAbortControllerRef.current = new AbortController();

          const streamingMsgId = (Date.now() + 1).toString();
          setStreamingMessageId(streamingMsgId);
          streamingAccumulatedRef.current = "";
          streamingDisplayedLengthRef.current = 0;

          if (streamingTypingIntervalRef.current) {
            clearInterval(streamingTypingIntervalRef.current);
            streamingTypingIntervalRef.current = null;
          }

          const streamingMessage: Message = {
            id: streamingMsgId,
            sender: "bot",
            message: "",
            timestamp: new Date(),
            retryText: text,
          };
          setMessages((prev) => [...prev, streamingMessage]);

          streamingTypingIntervalRef.current = setInterval(() => {
            const accumulated = streamingAccumulatedRef.current;
            const currentDisplayed = streamingDisplayedLengthRef.current;

            if (currentDisplayed < accumulated.length) {
              const nextLen = Math.min(
                currentDisplayed + STREAMING_CHARS_PER_TICK,
                accumulated.length,
              );
              streamingDisplayedLengthRef.current = nextLen;
              const displayedText = accumulated.slice(0, nextLen);
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === streamingMsgId ? { ...m, message: displayedText } : m,
                ),
              );
              return;
            }

            const pending = streamingPendingCompleteRef.current;
            if (pending) {
              if (streamingTypingIntervalRef.current) {
                clearInterval(streamingTypingIntervalRef.current);
                streamingTypingIntervalRef.current = null;
              }
              streamingPendingCompleteRef.current = null;
              streamAbortControllerRef.current = null;
              streamingAccumulatedRef.current = "";
              if (responseTimeoutRef.current)
                clearTimeout(responseTimeoutRef.current);
              setIsStreaming(false);
              setStreamingMessageId(null);

              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === streamingMsgId
                    ? {
                        ...msg,
                        message: pending.message,
                        quickReplies: pending.quick_replies,
                        productCards: pending.product_cards,
                        interactiveContent: pending.interactive_content,
                        failed: false,
                      }
                    : msg,
                ),
              );

              if (
                pending.session_id &&
                pending.session_id !== currentSessionId
              ) {
                setSessionId(pending.session_id);
                saveProfile({ session_id: pending.session_id });
              }
            }
          }, config.streamSpeedMs ?? DEFAULT_STREAM_SPEED_MS);

          responseTimeoutRef.current = setTimeout(() => {
            if (streamingTypingIntervalRef.current) {
              clearInterval(streamingTypingIntervalRef.current);
              streamingTypingIntervalRef.current = null;
            }
            streamingPendingCompleteRef.current = null;
            streamingAccumulatedRef.current = "";
            setIsStreaming(false);
            setIsTyping(false);
            setStreamingMessageId(null);
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === streamingMsgId
                  ? {
                      ...msg,
                      message:
                        msg.message ||
                        "The server didn't respond in time. Please try again.",
                      failed: true,
                    }
                  : msg,
              ),
            );
          }, RESPONSE_TIMEOUT_MS);

          await apiClient.sendMessageStream(
            text,
            currentSessionId,
            (chunk) => {
              streamingAccumulatedRef.current += chunk;
            },
            (response) => {
              const fullMessage = response.message || streamingAccumulatedRef.current;
              streamingAccumulatedRef.current = fullMessage;
              streamingPendingCompleteRef.current = {
                message: fullMessage,
                quick_replies: response.quick_replies,
                product_cards: response.product_cards,
                interactive_content: response.interactive_content as
                  | InteractiveContent
                  | undefined,
                session_id: response.session_id,
              };
              if (responseTimeoutRef.current)
                clearTimeout(responseTimeoutRef.current);
            },
            (error) => {
              if (streamingTypingIntervalRef.current) {
                clearInterval(streamingTypingIntervalRef.current);
                streamingTypingIntervalRef.current = null;
              }
              streamingPendingCompleteRef.current = null;
              streamAbortControllerRef.current = null;
              streamingAccumulatedRef.current = "";
              if (responseTimeoutRef.current)
                clearTimeout(responseTimeoutRef.current);
              setIsStreaming(false);
              setStreamingMessageId(null);

              const isAborted = error?.name === "AbortError";

              setMessages((prev) =>
                prev.map((m) =>
                  m.id === streamingMsgId
                    ? {
                        ...m,
                        message: isAborted
                          ? (m.message || "Response stopped.")
                          : (m.message || "I encountered an error. Please try again."),
                        failed: !isAborted,
                        quickReplies: isAborted ? undefined : ["Retry", "Talk to human"],
                      }
                    : m,
                ),
              );
            },
            { signal: streamAbortControllerRef.current?.signal },
          );

          return;
        }

        const response = await apiClient.sendMessage(text, currentSessionId);

        if (!response || !response.message) {
          throw new Error("Invalid response from server");
        }

        const botMessage: Message = {
          id: (Date.now() + 1).toString(),
          sender: "bot",
          message: response.message,
          timestamp: new Date(),
          productCards: response.product_cards,
          quickReplies: response.quick_replies,
          interactiveContent: response.interactive_content as
            | InteractiveContent
            | undefined,
        };

        setMessages((prev) => {
          const lastMessage = prev[prev.length - 1];
          if (
            lastMessage &&
            lastMessage.sender === "bot" &&
            lastMessage.message === botMessage.message
          ) {
            return prev;
          }
          return [...prev, botMessage];
        });

        if (response.session_id && response.session_id !== currentSessionId) {
          setSessionId(response.session_id);
          saveProfile({ session_id: response.session_id });
        }
      } catch (error) {
        console.error("Unexpected error in sendMessage:", error);

        const errorMessage: Message = {
          id: (Date.now() + 1).toString(),
          sender: "bot",
          message:
            "I encountered an unexpected error. Please try again or contact support if the problem persists.",
          timestamp: new Date(),
          quickReplies: ["Retry", "Talk to human"],
        };

        setMessages((prev) => [...prev, errorMessage]);
      } finally {
        setIsTyping(false);
      }
    },
    [sessionId, apiClient, isOnline],
  );

  const stopStream = useCallback(() => {
    if (streamAbortControllerRef.current) {
      streamAbortControllerRef.current.abort();
      streamAbortControllerRef.current = null;
    }
  }, []);

  const retryMessage = useCallback(
    (messageId: string) => {
      const msg = messages.find((m) => m.id === messageId);
      if (!msg || !msg.retryText) return;
      setMessages((prev) => prev.filter((m) => m.id !== messageId));
      sendMessage(msg.retryText, true);
    },
    [messages, sendMessage],
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
        streamingMessageId,
        isOnline,
        sessionId,
        sendMessage,
        stopStream,
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
