import asyncio
import base64
import re
import json
from typing import Optional, Dict, List, Tuple, AsyncGenerator
import structlog
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage

from app.config import settings
from app.utils.circuit_breaker import llm_circuit_breaker, CircuitBreakerError

logger = structlog.get_logger()

MAX_HISTORY_MESSAGES = 20

GEMINI_TIMEOUT = 10.0
GROQ_TIMEOUT = 15.0


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


def _build_system_prompt() -> str:
    store_section = ""
    if settings.store_maps_url:
        store_section = f"""
STORE LOCATION & PICKUP
- Our store is in Kathmandu, near the Cricket Stadium.
- When customers ask for directions, pickup location, or "where is the store", ALWAYS share this Google Maps link in your response: {settings.store_maps_url}
- Format it as a clickable markdown link: [Get Directions]({settings.store_maps_url}) or include the URL so they can tap to open turn-by-turn navigation.
- For "Start Navigation" or "Get Directions" intents: include the link prominently in message_md.
"""
    if settings.store_phone:
        store_section += f"\n- Store phone for 'Call Us': {settings.store_phone}\n"

    return f"""You are the Sales Assistant at Himalayan Willow, Nepal's premier cricket equipment store.
{store_section}
GOLDEN RULE — SHOW PRODUCTS FIRST, ASK QUESTIONS LATER
Customers open this chat to shop, not to answer questions.
When someone says "Show me bats" — show bats immediately. Do NOT ask questions first.
When someone says "I need gloves" — show gloves immediately. Do NOT ask about size/level first.
Only ask a clarifying question AFTER showing products, and only if it helps narrow down further.
Think of yourself like an online menu — the food shows up before the waiter asks questions.

SELLING APPROACH
1. ALWAYS show products immediately when the customer mentions a category or need.
2. Keep your text SHORT (2-3 sentences max). Let the product cards do the selling.
3. After showing products, you may suggest: "Want me to narrow these down by budget or playing level?"
4. Suggest ONE complementary item naturally: "A bat cover keeps your willow in top shape."
5. Be honest about budget constraints. Recommend Kashmir Willow for tight budgets.
6. Use cross-selling when it feels natural, not forced:
   - Bat → grip, bat cover, knocking oil
   - Pads → gloves, helmet
   - Ball → stumps, ball box

REFERENCE-BASED SELLING
When a customer mentions they saw something (on TikTok, YouTube, Instagram, from a friend, at a match, etc.):
- Ask them to share a screenshot or describe it — "Send me a photo or describe it and I'll find the closest match we have!"
- If they describe a product, match it to your inventory and show the best matches.
- If they mention a player or brand, recommend the closest products you carry.
- Be confident: "I can find that for you" builds trust.

When a customer says "I have a photo" or similar:
- Encourage them to use the camera button to upload it.
- Say something like: "Go ahead and tap the camera icon to share it — I'll match it to our catalog instantly!"

CRICKET EXPERTISE
Use terminology naturally when describing products: 'sweet spot', 'knocked-in', 'grains', 'pickup weight'.
You understand playing surfaces (turf, cement, matting), player levels, and Nepali cricket culture.

HARD RULES
1) Never invent products, prices, stock, discounts, or policies.
2) Keep responses concise: 2-3 sentences, then let product cards speak.
3) Always include quick replies for next actions.
4) NEVER gate product display behind questions. Show first, refine later.

TONE & VOICE
- Friendly but efficient — like a helpful shopkeeper who knows you're busy
- Cricket-savvy, encouraging, honest
- Speaks English and Nepali naturally
- Build trust quickly — be direct, knowledgeable, and confident

OUTPUT FORMAT (strict JSON only)
Return ONLY valid JSON matching this schema:
{
  "message_md": "short, action-oriented text (2-3 sentences max)",
  "quick_replies": ["...","...","..."]
}
"""


class LLMService:
    """LLM service with Gemini primary and Groq fallback for zero-timeout architecture."""

    def __init__(self):
        self.primary_llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=settings.gemini_api_key,
            temperature=0.7,
            max_tokens=1000,
        )

        self.fallback_llm = None
        if settings.groq_api_key:
            try:
                from langchain_groq import ChatGroq

                self.fallback_llm = ChatGroq(
                    model="llama-3.3-70b-versatile",
                    groq_api_key=settings.groq_api_key,
                    temperature=0.7,
                    max_tokens=1000,
                )
                logger.info("groq_fallback_initialized")
            except ImportError:
                logger.warning("langchain_groq_not_installed_fallback_disabled")

        self.memories: Dict[str, SessionMessageBuffer] = {}
        self._active_provider = "gemini"

    @property
    def active_provider(self) -> str:
        return self._active_provider

    def _get_memory(self, session_id: str) -> SessionMessageBuffer:
        if session_id not in self.memories:
            self.memories[session_id] = SessionMessageBuffer()
        return self.memories[session_id]

    def _sanitize_input(self, user_message: str) -> str:
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
        if len(sanitized) > 500:
            sanitized = sanitized[:500]
        return sanitized.strip()

    def _detect_language(self, text: str) -> str:
        nepali_chars = sum(1 for c in text if "\u0900" <= c <= "\u097F")
        if nepali_chars > len(text) * 0.3:
            return "nepali"
        nepali_keywords = ["ke", "kasto", "kati", "chha", "huncha", "thik"]
        if any(keyword in text.lower() for keyword in nepali_keywords):
            return "nepali"
        return "english"

    def _validate_response(self, response_content: str) -> bool:
        if not response_content or not isinstance(response_content, str):
            return False
        text_to_check = response_content.strip()
        try:
            parsed = json.loads(response_content)
            if isinstance(parsed, dict) and parsed.get("message_md"):
                text_to_check = (parsed.get("message_md") or "").strip()
        except (json.JSONDecodeError, TypeError):
            pass
        if len(text_to_check) < 3:
            return False
        error_patterns = [
            "i cannot",
            "i'm unable to",
            "as an ai",
            "i don't have access",
            "i apologize, but i cannot",
        ]
        content_lower = text_to_check.lower()
        if any(pattern in content_lower for pattern in error_patterns):
            logger.warning("llm_response_contains_refusal_pattern", response_preview=text_to_check[:100])
            return False
        return True

    def _parse_llm_response(self, response_content: str) -> Tuple[str, Optional[List[str]], Optional[List[Dict]]]:
        """Parse LLM response, returning (message, quick_replies, product_cards)."""
        if not response_content or not isinstance(response_content, str):
            return ("", None, None)
        text = response_content.strip()

        json_str = text
        if "```" in text:
            import re as re_mod
            code_block = re_mod.search(r"```(?:json)?\s*([\s\S]*?)```", text)
            if code_block:
                json_str = code_block.group(1).strip()

        def try_parse(s: str) -> Optional[Tuple[str, Optional[List[str]], Optional[List[Dict]]]]:
            try:
                parsed = json.loads(s)
                if isinstance(parsed, dict):
                    msg = parsed.get("message_md") or parsed.get("message") or ""
                    if isinstance(msg, str) and msg.strip():
                        replies = parsed.get("quick_replies")
                        if not (isinstance(replies, list) and all(isinstance(r, str) for r in replies)):
                            replies = None
                        cards = parsed.get("product_cards")
                        if not (isinstance(cards, list) and len(cards) > 0):
                            cards = None
                        return (msg.strip(), replies, cards)
                    return ("I'm here to help with cricket gear. What would you like to see?", None, None)
            except (json.JSONDecodeError, TypeError):
                pass
            return None

        result = try_parse(json_str)
        if result is not None:
            return result

        start = text.find("{")
        if start >= 0:
            depth = 0
            end = -1
            for i in range(start, len(text)):
                if text[i] == "{":
                    depth += 1
                elif text[i] == "}":
                    depth -= 1
                    if depth == 0:
                        end = i
                        break
            if end >= 0:
                result = try_parse(text[start : end + 1])
                if result is not None:
                    intro = text[:start].strip()
                    if intro and not intro.startswith("{"):
                        msg_part, replies, cards = result
                        return (f"{intro} {msg_part}".strip(), replies, cards)
                    return result

        trimmed = text[:80].strip()
        if trimmed.startswith("{") or (trimmed.startswith("```") and "message_md" in text):
            return (
                "I'm here to help with cricket gear. What would you like to see?",
                ["Show me bats", "Show me gloves", "Talk to human"],
                None,
            )
        if "message_md" in text and ("{" in text or "}" in text):
            idx = text.find("{")
            if idx > 0:
                plain = text[:idx].strip()
                if len(plain) > 10:
                    return (self._strip_trailing_json(plain), None, None)
        return (self._strip_trailing_json(text), None, None)

    def _strip_trailing_json(self, message: str) -> str:
        """Remove any trailing raw JSON or 'message_md': ... from the display message."""
        if not message or not isinstance(message, str):
            return message
        text = message.strip()
        # Remove content from "message_md": or "\n\"message_md\"" to end (leaked JSON)
        for pattern in [
            r'\n\s*"message_md"\s*:',
            r'\n\s*"product_cards"\s*:',
            r'\n\s*"quick_replies"\s*:',
        ]:
            match = re.search(pattern, text)
            if match:
                text = text[: match.start()].strip()
        # Also strip trailing incomplete JSON like , "cross_sell_suggestions": [
        if '"cross_sell_suggestions"' in text:
            idx = text.find('"cross_sell_suggestions"')
            text = text[:idx].strip()
        if '"clarifying_questions"' in text:
            idx = text.find('"clarifying_questions"')
            text = text[:idx].strip()
        return text.strip()

    # ------------------------------------------------------------------
    # Core LLM call with Gemini -> Groq fallback
    # ------------------------------------------------------------------

    async def _call_with_fallback(self, messages: List[BaseMessage]) -> str:
        """Try Gemini (10s timeout), fall back to Groq (15s timeout) on failure."""

        # --- Attempt 1: Gemini (primary) ---
        try:
            self._active_provider = "gemini"
            response = await asyncio.wait_for(
                llm_circuit_breaker.call(self.primary_llm.ainvoke, messages),
                timeout=GEMINI_TIMEOUT,
            )
            return response.content
        except CircuitBreakerError as e:
            logger.warning("gemini_circuit_breaker_open", error=str(e))
        except asyncio.TimeoutError:
            logger.warning("gemini_timeout", timeout=GEMINI_TIMEOUT)
        except Exception as e:
            logger.warning("gemini_call_failed", error=str(e), error_type=type(e).__name__)

        # --- Attempt 2: Groq (fallback) ---
        if self.fallback_llm is None:
            logger.error("no_fallback_llm_available")
            raise RuntimeError("Primary LLM failed and no fallback configured")

        try:
            self._active_provider = "groq"
            logger.info("switching_to_groq_fallback")
            response = await asyncio.wait_for(
                self.fallback_llm.ainvoke(messages),
                timeout=GROQ_TIMEOUT,
            )
            return response.content
        except asyncio.TimeoutError:
            logger.error("groq_timeout", timeout=GROQ_TIMEOUT)
            raise
        except Exception as e:
            logger.error("groq_call_failed", error=str(e), error_type=type(e).__name__)
            raise

    # ------------------------------------------------------------------
    # True token-level streaming with fallback
    # ------------------------------------------------------------------

    async def generate_response_stream(
        self,
        user_message: str,
        session_id: str,
        context: Optional[Dict] = None,
    ) -> AsyncGenerator[Dict, None]:
        """Yield SSE-style dicts: {type:'chunk',content:str} and {type:'complete',...}."""

        sanitized_message = self._sanitize_input(user_message)
        language = self._detect_language(sanitized_message)
        memory = self._get_memory(session_id)

        messages = [SystemMessage(content=_build_system_prompt())]
        history = memory.load_memory_variables({})
        if history.get("history"):
            for msg in history["history"]:
                messages.append(msg)
        messages.append(HumanMessage(content=sanitized_message))

        full_text = ""
        provider_used = "gemini"

        async def _stream_from(llm, timeout: float, name: str) -> AsyncGenerator[str, None]:
            """Stream tokens from an LLM with a global timeout."""
            deadline = asyncio.get_event_loop().time() + timeout
            async for chunk in llm.astream(messages):
                if asyncio.get_event_loop().time() > deadline:
                    raise asyncio.TimeoutError(f"{name} streaming exceeded {timeout}s")
                token = chunk.content if hasattr(chunk, "content") else str(chunk)
                if token:
                    yield token

        # Try Gemini stream, fall back to Groq on failure
        try:
            self._active_provider = "gemini"
            async for token in _stream_from(self.primary_llm, GEMINI_TIMEOUT, "gemini"):
                full_text += token
                yield {"type": "chunk", "content": token}
        except Exception as e:
            logger.warning("gemini_stream_failed_switching_to_groq", error=str(e))
            if self.fallback_llm is not None:
                try:
                    self._active_provider = "groq"
                    provider_used = "groq"
                    full_text = ""
                    async for token in _stream_from(self.fallback_llm, GROQ_TIMEOUT, "groq"):
                        full_text += token
                        yield {"type": "chunk", "content": token}
                except Exception as fallback_err:
                    logger.error("groq_stream_failed", error=str(fallback_err))
                    yield {"type": "error", "message": "I'm having trouble right now. Please try again."}
                    return
            else:
                yield {"type": "error", "message": "I'm having trouble right now. Please try again."}
                return

        display_message, quick_replies, product_cards = self._parse_llm_response(full_text)

        memory.save_context({"input": sanitized_message}, {"output": display_message or full_text})

        complete_event: Dict = {
            "type": "complete",
            "session_id": session_id,
            "language": language,
            "provider": provider_used,
            "quick_replies": quick_replies or ["Show me bats", "Show me gloves", "Talk to human"],
            "message": display_message or full_text,
        }
        if product_cards:
            complete_event["product_cards"] = product_cards
        yield complete_event

    # ------------------------------------------------------------------
    # Non-streaming generate (kept for /message endpoint compatibility)
    # ------------------------------------------------------------------

    async def generate_response(
        self,
        user_message: str,
        session_id: str,
        context: Optional[Dict] = None,
    ) -> Dict:
        start_time = asyncio.get_event_loop().time()

        try:
            sanitized_message = self._sanitize_input(user_message)
            language = self._detect_language(sanitized_message)
            memory = self._get_memory(session_id)

            messages = [SystemMessage(content=_build_system_prompt())]
            history = memory.load_memory_variables({})
            if history.get("history"):
                for msg in history["history"]:
                    messages.append(msg)
            messages.append(HumanMessage(content=sanitized_message))

            try:
                response_content = await self._call_with_fallback(messages)
            except asyncio.TimeoutError:
                logger.warning("llm_timeout_after_fallback", session_id=session_id)
                return self._get_fallback_response()
            except CircuitBreakerError:
                logger.error("circuit_breaker_rejected", session_id=session_id)
                return self._get_fallback_response(circuit_breaker_open=True)

            if not self._validate_response(response_content):
                logger.warning(
                    "llm_response_validation_failed",
                    session_id=session_id,
                    response_preview=response_content[:200] if response_content else None,
                )
                return self._get_fallback_response()

            display_message, quick_replies, product_cards = self._parse_llm_response(response_content)

            memory.save_context({"input": sanitized_message}, {"output": display_message})

            elapsed_time = asyncio.get_event_loop().time() - start_time
            logger.info(
                "llm_response_generated",
                session_id=session_id,
                language=language,
                provider=self._active_provider,
                elapsed_seconds=round(elapsed_time, 2),
            )

            result: Dict = {
                "message": display_message,
                "language": language,
                "session_id": session_id,
            }
            if quick_replies:
                result["quick_replies"] = quick_replies
            if product_cards:
                result["product_cards"] = product_cards
            return result

        except Exception as e:
            error_str = str(e).lower()
            logger.error("llm_generate_error", error=str(e), error_type=type(e).__name__, session_id=session_id)
            return self._get_fallback_response()

    def validate_llm_actions(self, llm_response: Dict) -> Dict:
        validated = llm_response.copy()
        if "discount" in validated and validated.get("discount", 0) > 0:
            logger.warning("llm_attempted_unauthorized_discount", discount=validated["discount"])
            validated["discount"] = 0
            validated["message"] = validated.get("message", "") + "\n\n(Note: Discounts require manager approval)"
        if "product_cards" in validated:
            for card in validated["product_cards"]:
                if "modified_price" in card or "special_price" in card:
                    logger.warning("llm_attempted_price_modification", product_id=card.get("id"))
                    card.pop("modified_price", None)
                    card.pop("special_price", None)
        policy_keywords = ["free shipping", "extended warranty", "price match", "special deal"]
        message_lower = validated.get("message", "").lower()
        for keyword in policy_keywords:
            if keyword in message_lower:
                logger.warning("llm_mentioned_policy_override", keyword=keyword)
        return validated

    def _get_fallback_response(self, circuit_breaker_open: bool = False) -> Dict:
        if circuit_breaker_open:
            message = "I'm experiencing high load right now and need a moment to recover. In the meantime, here are some popular options you might like:"
        else:
            message = "I'm having trouble processing your request right now. Here are some quick options to help you find what you need:"
        return {
            "message": message,
            "quick_replies": ["Show me bats", "Show me gloves", "Show me pads", "Talk to human"],
            "fallback": True,
        }

    def clear_memory(self, session_id: str):
        if session_id in self.memories:
            del self.memories[session_id]
            logger.info("memory_cleared", session_id=session_id)

    # ------------------------------------------------------------------
    # Visual search: image + product catalog -> recommended product IDs
    # ------------------------------------------------------------------

    async def generate_product_recommendations_from_image(
        self,
        image_bytes: bytes,
        product_summaries: List[Dict],
        category_hint: Optional[str] = None,
        limit: int = 5,
    ) -> List[int]:
        """
        Use Gemini vision to analyze an image and return matching product IDs
        from our catalog. Returns up to `limit` product IDs in relevance order.
        """
        if not product_summaries:
            return []

        catalog_text = "\n".join(
            f"- ID {p['id']}: {p['name']} (category: {p['category']}, NPR {p['price']})"
            for p in product_summaries
        )

        prompt = f"""You are a cricket equipment expert at Himalayan Willow store. A customer uploaded an image of cricket gear they're interested in.

Our product catalog (id, name, category, price):
{catalog_text}

Analyze the image and identify what cricket equipment is shown (e.g. bat, gloves, pads, ball, helmet, shoes). From our catalog above, recommend the best matching product IDs. Consider category, type, and typical use. If the image is unclear or not cricket-related, pick the closest general matches.

Return ONLY a JSON array of product IDs, e.g. [3, 7, 12]. Return at most {limit} IDs. No other text."""

        mime_type = "image/jpeg"
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        image_data_url = f"data:{mime_type};base64,{b64}"

        messages = [
            HumanMessage(
                content=[
                    {"type": "image_url", "image_url": {"url": image_data_url}},
                    {"type": "text", "text": prompt},
                ]
            )
        ]

        try:
            response = await asyncio.wait_for(
                self.primary_llm.ainvoke(messages),
                timeout=15.0,
            )
            content = response.content.strip() if hasattr(response, "content") else str(response)
            # Extract JSON array from response (may be wrapped in markdown)
            if "```" in content:
                import re as re_mod
                match = re_mod.search(r"\[[\d,\s]*\]", content)
                if match:
                    content = match.group(0)
            else:
                match = re.search(r"\[[\d,\s]*\]", content)
                if match:
                    content = match.group(0)
            ids = json.loads(content)
            if isinstance(ids, list):
                return [int(i) for i in ids if isinstance(i, (int, float))][:limit]
            return []
        except (asyncio.TimeoutError, json.JSONDecodeError, ValueError) as e:
            logger.warning("gemini_visual_search_failed", error=str(e))
            return []


llm_service = LLMService()


async def get_llm_service() -> LLMService:
    return llm_service
