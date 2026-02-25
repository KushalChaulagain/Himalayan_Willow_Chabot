export interface Message {
  id: string;
  sender: 'user' | 'bot';
  message: string;
  timestamp: Date;
  productCards?: ProductCard[];
  quickReplies?: string[];
}

export interface ProductCard {
  id: number;
  name: string;
  price: number;
  image_url?: string;
  reason: string;
  in_stock: boolean;
  specifications?: Record<string, any>;
}

export interface ChatConfig {
  apiUrl: string;
  storeId: number;
}

export interface ChatResponse {
  message: string;
  product_cards?: ProductCard[];
  quick_replies?: string[];
  session_id: string;
  action?: string;
  action_data?: any;
}
