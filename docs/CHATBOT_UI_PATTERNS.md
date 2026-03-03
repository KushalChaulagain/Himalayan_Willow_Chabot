# Chatbot UI Patterns - Reference

This document summarizes the chatbot UI patterns used in the Himalayan Willow chatbot. Use it as a reference when building or extending chat interfaces.

---

## 1. Component Hierarchy

```
ChatProvider
  └── ChatWidget (full-page container)
        └── ChatWindow
              ├── Header (logo, Browse, Cart, Auth)
              ├── Messages area (scrollable)
              │     ├── TextGenerateEffect (empty-state welcome)
              │     ├── SuggestedActions (when no messages)
              │     ├── ChatMessage[] (per message)
              │     ├── Typing/Streaming indicator
              │     └── messagesEndRef (scroll anchor)
              ├── CartSummaryBar (when cart has items)
              └── ChatInput
```

**Key files:**

| Role | Path |
|------|------|
| Root | `frontend/src/components/ChatWidget.tsx` |
| Main layout | `frontend/src/components/ChatWindow.tsx` |
| Input | `frontend/src/components/ChatInput.tsx` |
| Message | `frontend/src/components/ChatMessage.tsx` |
| Quick replies | `frontend/src/components/QuickReplies.tsx` |
| Suggested actions | `frontend/src/components/SuggestedActions.tsx` |
| State | `frontend/src/contexts/ChatContext.tsx` |

---

## 2. Layout & Container Patterns

**Full-page chat layout:**
- Container: `fixed inset-0` for full viewport
- Flex column: `flex flex-col overflow-hidden w-full h-full`
- Dark theme: `bg-[#1A1A1A]`, `bg-[#262626]`
- Borders: `border-white/10`
- Accent: `amber-500`, `text-amber-400` for CTAs and links

**Header (responsive):**
- `grid grid-cols-[1fr_auto_1fr]` for logo | Browse (centered) | Cart + Auth
- Mobile (< 400px): Smaller logo/text, subtitle hidden, tighter padding
- Tablet+ (xs, sm): Progressive sizing, Cart text shown on sm+
- `min-w-0` and `overflow-hidden` on grid children to prevent overflow
- Auth dropdown: `max-w-[calc(100vw-2rem)]` to stay within viewport

**Messages area (responsive):**
- `flex-1 overflow-y-auto p-2 xs:p-3 sm:p-4 space-y-4`
- Scroll anchor via `ref` + `scrollIntoView({ behavior: "smooth" })` on message/typing changes
- Empty state: animated welcome text (`TextGenerateEffect`) + `SuggestedActions`

---

## 3. Message Rendering

**User vs Bot layout:**
- User: `justify-end`, `max-w-[80%]`, plain text (`whitespace-pre-wrap`)
- Bot: `justify-start`, `max-w-[95%]`

**Bot message content:**
- Markdown: `ReactMarkdown` + `remarkGfm` with custom components (p, strong, ul, ol, li, a)
- Links: `text-amber-400 hover:text-amber-300 underline`
- Timestamp below content: `toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })`

**Attachments:**
- Image preview: `rounded-md mb-2 max-h-40 object-cover`
- Product carousel: horizontal scroll, `scroll-snap-type: x mandatory`, prev/next buttons

**Interactive content:**
- Types: `educational`, `confetti`, `tracking_map` — each mapped to a dedicated component
- Use `Suspense` + lazy loading for heavy components

**Error state:**
- `border-red-500/40`, retry button with icon

---

## 4. Input Patterns

**Text input:**
- Form row: `flex items-center gap-2 min-h-[44px]` — image button, text input, send/stop button
- All row elements vertically centered; `min-h-[44px]` for touch targets
- Image/upload button and send button: `size-10 min-h-[44px] min-w-[44px]`
- Input: `min-h-[44px] py-2.5 leading-normal` for vertical text alignment
- Image upload: hidden `file` input, paste handler for images
- Enter to send; Enter during streaming stops generation
- Input draft persisted in `localStorage` (key: `himalayan-willow-chat-input-draft`)
- Accessibility: `sr-only` label, `aria-label`, `aria-describedby` for help text
- Disabled during `isTyping` / `uploading`

**Stop button:**
- Shown during streaming (`isStreaming`)
- Red square icon; clicking or pressing Enter calls `stopStream()`

---

## 5. Quick Replies & Suggested Actions

**Quick replies** (under bot messages):
- `flex flex-wrap gap-2`, keyboard navigable
- `min-h-[44px] min-w-[44px]` for touch targets
- `active:scale-[0.98]` for press feedback
- Optional emoji mapping per category

**Suggested actions** (when `messages.length === 0`):
- `flex flex-wrap justify-center gap-3` with `px-4` for alignment
- Cards: `min-w-[160px] flex-1 max-w-[280px]`, `min-h-[44px]` touch target
- Same visual language as quick replies (border, hover, active:scale-[0.98])
- Default options: "Show me Bats", "Balls & Accessories", "Protection Gear"
- Calls `sendMessage(option, true)` for streaming

---

## 6. State Management

**ChatContext:**
- `messages`, `isTyping`, `isStreaming`, `sessionId`, `cartItems`
- `sendMessage(text, useStreaming?)` — adds user message, calls API (stream or non-stream)
- `stopStream()` — aborts in-progress streaming
- `addBotMessage(text, extras?)` — immediate bot message
- `retryMessage(id)` — resend failed message
- `addToCart`, `removeFromCartAt` — cart persistence

**Message flow:**
1. Greeting from API on mount
2. User input → `sendMessage(inputText, true)`
3. Streaming: placeholder bot message, updated on completion; `stopStream()` cancels
4. Quick replies / suggested actions call `sendMessage(option, true)`

---

## 7. Typing / Streaming Indicator

Three dots with staggered `animation-delay` (0ms, 150ms, 300ms). Label: "Streaming..." or "Typing...".

---

## 8. Styling Conventions

**Tailwind theme:**
- `rounded-sharp` (4px), `rounded-card` (6px), `rounded-button` (6px)
- `shadow-subtle`, `shadow-card`, `shadow-premium-sm`, `shadow-premium`, `shadow-premium-lg`, `shadow-premium-glow`
- `font-heading` (Montserrat), `font-sans` (Inter)
- `max-w-chat` (44rem) for message/content width

**Responsive & premium patterns:**
- Breakpoints: `xs` (400px), `sm` (640px), `md` (768px), `lg` (1024px) — mobile-first
- Use `xs:`, `sm:`, `md:` for viewport-specific styles
- Add `min-w-0` to flex/grid children that may overflow; use `truncate` where text can overflow
- Safe areas: `env(safe-area-inset-top)`, `env(safe-area-inset-bottom)` for notched devices
- Touch targets: `min-h-[44px]`, `min-w-[44px]` (or `min-h-[40px]` on xs for dense layouts)
- Touch feedback: `active:scale-[0.98]` or `active:scale-95` on buttons
- Transitions: `transition-all duration-200` for polished micro-interactions
- Suggested actions: `flex-col` on mobile, `sm:flex-row sm:flex-wrap` on tablet+

**Utilities:**
- `cn()` (clsx + tailwind-merge) for conditional classes
- Scrollbar: `scrollbar-thin`, `scrollbar-thumb-white/10`, `scrollbar-track-transparent`
- Product carousel: `scroll-snap-type: x mandatory`, `scroll-snap-align: start`

**Auth gate:**
- Blur + `pointer-events-none` when not logged in
- Centered login overlay with `backdrop-blur`
- Transition: `transition-[filter] duration-300`

---

## 9. Accessibility Checklist

- `aria-label` on icon buttons and interactive elements
- `role="group"` and `aria-label` for quick reply groups
- `sr-only` labels for inputs
- `aria-describedby` for help text
- Keyboard: Enter to send, Tab through quick replies
- Minimum touch targets: `min-h-[44px]`, `min-w-[44px]`

---

## 10. Message Type Structure

```ts
interface Message {
  id: string;
  sender: "user" | "bot";
  message: string;
  timestamp: Date;
  productCards?: ProductCard[];
  quickReplies?: string[];
  failed?: boolean;
  interactiveContent?: InteractiveContent;
  imageUrl?: string;
  retryText?: string;
}
```
