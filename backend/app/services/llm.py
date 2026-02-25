import asyncio
import re
from typing import Optional, Dict, List
import structlog
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage

from app.config import settings

logger = structlog.get_logger()

# In-process conversation buffer (replaces ConversationSummaryBufferMemory for LangChain 0.3 compatibility)
MAX_HISTORY_MESSAGES = 20  # last N messages per session


class SessionMessageBuffer:
    """Simple per-session message buffer compatible with our LLM flow."""

    def __init__(self, max_messages: int = MAX_HISTORY_MESSAGES):
        self._messages: List[BaseMessage] = []
        self._max = max_messages

    def load_memory_variables(self, _: Dict) -> Dict[str, List[BaseMessage]]:
        return {"history": list(self._messages)}

    def save_context(self, input_dict: Dict, output_dict: Dict) -> None:
        self._messages.append(HumanMessage(content=input_dict.get("input", "")))
        self._messages.append(AIMessage(content=output_dict.get("output", "")))
        while len(self._messages) > self._max:
            self._messages.pop(0)

# System prompt with cricket domain knowledge
SYSTEM_PROMPT = """You are a helpful sales assistant for Himalayan Willow, Nepal's leading cricket equipment store.

## Your Role
- Help customers find the perfect cricket gear based on their needs
- Provide honest recommendations within their budget
- Process orders and track deliveries
- Handle returns and support questions

## Tone & Voice
- Friendly but professional
- Cricket-savvy (understand terminology like "English Willow", "toe guard", "sweet spot")
- Helpful without being pushy
- Honest about product limitations and budget constraints

## Available Tools
You have access to these tools:
1. search_products(category, max_price, min_rating) - Search product catalogue
2. get_product_details(product_id) - Get full product specifications
3. add_to_cart(product_id, quantity) - Add item to cart
4. create_order(cart_items, delivery_address, payment_method) - Create order
5. track_order(order_id) - Get order status
6. escalate_to_human(reason) - Connect customer with human agent

## Guidelines
- Always ask clarifying questions before recommending products (experience level, budget, playing surface)
- If budget is too low, be honest and suggest closest options
- For bulk orders (>10 items), offer to connect with human for quote
- If you can't help after 3 attempts, offer human escalation
- Always provide 2-3 product options, not just one
- Include brief "why this fits you" rationale with each recommendation

## Language Support
- Respond in the same language as the user (English or Nepali)
- If user switches language mid-conversation, switch with them

## Cricket Equipment Knowledge

### Bat Types
- **English Willow**: Premium, used by professionals. More expensive (NPR 8,000+), better performance, lighter weight
- **Kashmir Willow**: Budget-friendly (NPR 2,000-6,000), heavier, suitable for beginners and club cricket
- **Tape Ball Bats**: Lightweight, for tape ball cricket (NPR 1,500-3,000)

### Bat Selection by Level
- Beginner (first bat): Kashmir Willow, weight 1000-1100g, budget NPR 2,000-3,500
- Intermediate (club cricket): Kashmir Willow Grade A or English Willow Grade 3, weight 1100-1200g, budget NPR 4,000-8,000
- Professional: English Willow Grade 1-2, weight 1150-1200g, budget NPR 10,000+

### Common Questions
- "What's the difference between English and Kashmir Willow?" → Explain material, price, performance
- "Which bat for leather ball?" → Recommend English Willow for hard ball, Kashmir for practice
- "Bat for 12-year-old?" → Ask height, then recommend youth size (5-6) or short handle
- "Bat under 3000?" → Kashmir Willow options, be honest about limitations

### Playing Surfaces
- **Turf wicket**: Recommend proper cricket shoes with spikes
- **Cement wicket**: Rubber sole shoes, more durable bats
- **Indoor nets**: Any equipment works

## Current Context
Store: Himalayan Willow
Currency: NPR (Nepali Rupees)
Delivery: 2-4 business days within Kathmandu Valley, 5-7 days outside
Return Policy: 7 days from delivery, unused items only
"""


class LLMService:
    """LLM service for chatbot interactions"""
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=settings.gemini_api_key,
            temperature=0.7,
            max_tokens=1000
        )
        self.memories: Dict[str, SessionMessageBuffer] = {}

    def _get_memory(self, session_id: str) -> SessionMessageBuffer:
        """Get or create conversation memory for session"""
        if session_id not in self.memories:
            self.memories[session_id] = SessionMessageBuffer()
        return self.memories[session_id]
    
    def _sanitize_input(self, user_message: str) -> str:
        """Prevent prompt injection attacks"""
        dangerous_patterns = [
            r"ignore previous instructions",
            r"system:",
            r"<\|im_start\|>",
            r"<\|im_end\|>",
            r"### Instruction:",
            r"SYSTEM PROMPT:",
        ]
        
        sanitized = user_message
        for pattern in dangerous_patterns:
            sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)
        
        # Limit length
        if len(sanitized) > 500:
            sanitized = sanitized[:500]
        
        return sanitized.strip()
    
    def _detect_language(self, text: str) -> str:
        """Detect if message is in Nepali or English"""
        # Check for Devanagari script
        nepali_chars = sum(1 for c in text if '\u0900' <= c <= '\u097F')
        
        if nepali_chars > len(text) * 0.3:
            return "nepali"
        
        # Check for romanized Nepali keywords
        nepali_keywords = ["ke", "kasto", "kati", "chha", "huncha", "thik"]
        if any(keyword in text.lower() for keyword in nepali_keywords):
            return "nepali"
        
        return "english"
    
    async def generate_response(
        self,
        user_message: str,
        session_id: str,
        context: Optional[Dict] = None
    ) -> Dict:
        """Generate chatbot response"""
        try:
            # Sanitize input
            sanitized_message = self._sanitize_input(user_message)
            
            # Detect language
            language = self._detect_language(sanitized_message)
            
            # Get conversation memory
            memory = self._get_memory(session_id)
            
            # Build messages
            messages = [
                SystemMessage(content=SYSTEM_PROMPT),
            ]
            
            # Add conversation history
            history = memory.load_memory_variables({})
            if history.get("history"):
                for msg in history["history"]:
                    messages.append(msg)
            
            # Add current user message
            messages.append(HumanMessage(content=sanitized_message))
            
            # Generate response with timeout
            response = await asyncio.wait_for(
                self.llm.ainvoke(messages),
                timeout=8.0
            )
            
            # Save to memory
            memory.save_context(
                {"input": sanitized_message},
                {"output": response.content}
            )
            
            logger.info(
                "llm_response_generated",
                session_id=session_id,
                language=language,
                message_length=len(sanitized_message)
            )
            
            return {
                "message": response.content,
                "language": language,
                "session_id": session_id
            }
            
        except asyncio.TimeoutError:
            logger.warning("llm_timeout", session_id=session_id)
            return self._get_fallback_response()
        
        except Exception as e:
            error_str = str(e).lower()
            error_type = type(e).__name__
            
            # Categorize error for better logging
            if "api key" in error_str or "authentication" in error_str or "unauthorized" in error_str:
                logger.error("gemini_api_auth_error", error=str(e), error_type=error_type, session_id=session_id)
            elif "quota" in error_str or "rate limit" in error_str or "resource_exhausted" in error_str:
                logger.error("gemini_api_quota_error", error=str(e), error_type=error_type, session_id=session_id)
            elif "not_found" in error_str or "404" in error_str:
                logger.error("gemini_api_model_not_found", error=str(e), error_type=error_type, session_id=session_id)
            else:
                logger.error("gemini_api_unknown_error", error=str(e), error_type=error_type, session_id=session_id)
            
            return self._get_fallback_response()
    
    def _get_fallback_response(self) -> Dict:
        """Get fallback response when LLM fails"""
        return {
            "message": "I'm having trouble thinking right now. Here are some quick options:",
            "quick_replies": [
                "Show me bats",
                "Show me gloves",
                "Show me pads",
                "Talk to human"
            ],
            "fallback": True
        }
    
    def clear_memory(self, session_id: str):
        """Clear conversation memory for session"""
        if session_id in self.memories:
            del self.memories[session_id]
            logger.info("memory_cleared", session_id=session_id)


# Global LLM service instance
llm_service = LLMService()


async def get_llm_service() -> LLMService:
    """Dependency to get LLM service"""
    return llm_service
