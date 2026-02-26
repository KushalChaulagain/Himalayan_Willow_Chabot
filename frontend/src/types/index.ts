export type InteractiveType =
  | 'educational'
  | 'tracking_map'
  | 'payment_select'
  | 'confetti';

export interface TrackingStage {
  id: string;
  label: string;
  icon: string;
  timestamp?: string;
  completed: boolean;
  current: boolean;
}

export interface InteractiveContent {
  type: InteractiveType;
  educationalContent?: {
    title: string;
    body: string;
    animationType: string;
  };
  trackingData?: TrackingStage[];
  confettiMessage?: string;
  orderId?: string;
  destinationCity?: string;
}

export interface Message {
  id: string;
  sender: 'user' | 'bot';
  message: string;
  timestamp: Date;
  productCards?: ProductCard[];
  quickReplies?: string[];
  failed?: boolean;
  retryText?: string;
  interactiveContent?: InteractiveContent;
  imageUrl?: string;
}

export interface ProductCard {
  id: number;
  name: string;
  price: number;
  original_price?: number;
  image_url?: string;
  images?: string[];
  audio_url?: string;
  is_premium?: boolean;
  category?: string;
  description?: string;
  rating?: number;
  review_count?: number;
  reason: string;
  in_stock: boolean;
  specifications?: Record<string, any>;
}

export interface ChatConfig {
  apiUrl: string;
  storeId: number;
  googleClientId?: string;
}

export interface ChatResponse {
  message: string;
  product_cards?: ProductCard[];
  quick_replies?: string[];
  session_id: string;
  action?: string;
  action_data?: any;
  interactive_content?: InteractiveContent;
}

export interface UserProfile {
  session_id?: string;
  name?: string;
  phone?: string;
  city?: string;
  playing_level?: string;
  preferred_surface?: string;
  budget_range?: string;
  last_visit?: string;
  purchase_history?: Array<{ product_id: number; name: string; date: string }>;
  cart_items?: number[];
}

export interface GreetingResponse {
  message: string;
  quick_replies: string[];
  product_cards?: ProductCard[];
  is_returning_user: boolean;
  seasonal_nudge?: string;
}

export interface TrackingResponse {
  order_id: string;
  status: string;
  stages: TrackingStage[];
  destination_city?: string;
  estimated_delivery?: string;
}
