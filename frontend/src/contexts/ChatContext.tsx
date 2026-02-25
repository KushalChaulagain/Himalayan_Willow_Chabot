import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { Message, ChatConfig } from '../types';
import APIClient from '../services/api';

interface ChatContextType {
  messages: Message[];
  isTyping: boolean;
  sessionId: string | null;
  sendMessage: (text: string) => Promise<void>;
  addToCart: (productId: number) => void;
  cartItems: number[];
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
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      sender: 'bot',
      message: "Namaste! 🏏 Welcome to Himalayan Willow. I'm here to help you find the perfect cricket gear. What are you looking for today?",
      timestamp: new Date(),
      quickReplies: ['Show me bats', 'Show me gloves', 'Show me pads', 'I need help choosing'],
    },
  ]);
  const [isTyping, setIsTyping] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [cartItems, setCartItems] = useState<number[]>([]);
  const [apiClient] = useState(() => new APIClient(config.apiUrl));

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim()) return;

      // Add user message
      const userMessage: Message = {
        id: Date.now().toString(),
        sender: 'user',
        message: text,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, userMessage]);

      // Show typing indicator
      setIsTyping(true);

      try {
        // Create session if needed
        let currentSessionId = sessionId;
        if (!currentSessionId) {
          const session = await apiClient.createSession();
          currentSessionId = session.session_id;
          setSessionId(currentSessionId);
        }

        // Send message to API
        const response = await apiClient.sendMessage(text, currentSessionId);

        // Add bot response
        const botMessage: Message = {
          id: (Date.now() + 1).toString(),
          sender: 'bot',
          message: response.message,
          timestamp: new Date(),
          productCards: response.product_cards,
          quickReplies: response.quick_replies,
        };
        setMessages((prev) => [...prev, botMessage]);

        // Update session ID if returned
        if (response.session_id) {
          setSessionId(response.session_id);
        }
      } catch (error) {
        console.error('Error sending message:', error);
        const errorMessage: Message = {
          id: (Date.now() + 1).toString(),
          sender: 'bot',
          message: "Sorry, I'm having trouble right now. Please try again.",
          timestamp: new Date(),
          quickReplies: ['Retry', 'Talk to human'],
        };
        setMessages((prev) => [...prev, errorMessage]);
      } finally {
        setIsTyping(false);
      }
    },
    [sessionId, apiClient]
  );

  const addToCart = useCallback((productId: number) => {
    setCartItems((prev) => [...prev, productId]);
    console.log('Added to cart:', productId);
  }, []);

  return (
    <ChatContext.Provider
      value={{
        messages,
        isTyping,
        sessionId,
        sendMessage,
        addToCart,
        cartItems,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
};
