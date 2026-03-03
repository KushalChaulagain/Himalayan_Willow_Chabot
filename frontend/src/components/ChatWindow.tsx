import React, { lazy, Suspense, useEffect, useRef, useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import { useChatContext } from "../contexts/ChatContext";
import ChatInput from "./ChatInput";
import ChatMessage from "./ChatMessage";
import GoogleSignInButton from "./GoogleSignInButton";
import SuggestedActions from "./SuggestedActions";
import { TextGenerateEffect } from "./ui/text-generate-effect";

import HimalyanWillowLogo from "../Himalyan_Willow_image.png";

const KitBagView = lazy(() => import("./KitBagView"));
const CricketFilterMegaMenu = lazy(() => import("./CricketFilterMegaMenu"));
const CartSummaryBar = lazy(() => import("./CartSummaryBar"));

const ChatWindow: React.FC = () => {
  const {
    messages,
    isTyping,
    isStreaming,
    cartItems,
    sessionId,
    apiUrl,
    googleClientId,
  } = useChatContext();
  const { user, isLoading, setAuthFromCredential, linkSession, logout } =
    useAuth();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const viewportRef = useRef<HTMLDivElement>(null);
  const [showScrollToBottom, setShowScrollToBottom] = useState(false);
  const [kitBagOpen, setKitBagOpen] = useState(false);
  const [authDropdownOpen, setAuthDropdownOpen] = useState(false);
  const [avatarLoadError, setAvatarLoadError] = useState(false);
  const [filterMenuOpen, setFilterMenuOpen] = useState(false);
  const filterButtonRef = useRef<HTMLButtonElement>(null);

  const checkScrollPosition = () => {
    const el = viewportRef.current;
    if (!el) return;
    const threshold = 80;
    const isNearBottom =
      el.scrollHeight - el.scrollTop - el.clientHeight < threshold;
    setShowScrollToBottom(!isNearBottom);
  };

  useEffect(() => {
    const el = viewportRef.current;
    if (!el) return;
    checkScrollPosition();
    el.addEventListener("scroll", checkScrollPosition);
    return () => el.removeEventListener("scroll", checkScrollPosition);
  }, [messages, isTyping]);

  const handleGoogleSuccess = async (credential: string) => {
    const success = await setAuthFromCredential(credential, apiUrl);
    if (success && sessionId) {
      await linkSession(sessionId, apiUrl);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  useEffect(() => {
    setAvatarLoadError(false);
  }, [user?.id, user?.avatar_url]);

  return (
    <div className="chat-window bg-[#1A1A1A] flex flex-col overflow-hidden w-full h-full rounded-none">
      {/* Header - fully responsive: mobile-first, adapts to all viewports */}
      <header className="bg-[#1A1A1A] text-white px-3 xs:px-4 py-2.5 sm:py-3 md:p-4 pt-[max(0.5rem,env(safe-area-inset-top))] grid grid-cols-[1fr_auto_1fr] items-center shrink-0 border-b border-white/10 relative gap-1 xs:gap-2 sm:gap-4 min-h-[56px] overflow-visible z-50">
        {/* Logo + brand - truncates on narrow, full on wider */}
        <div className="flex items-center space-x-1.5 xs:space-x-2 sm:space-x-3 justify-self-start min-w-0 overflow-hidden">
          <div className="w-8 h-8 xs:w-9 xs:h-9 sm:w-10 sm:h-10 rounded-sharp overflow-hidden bg-[#262626] flex items-center justify-center shrink-0 border border-white/10 shadow-premium-sm">
            <img
              src={HimalyanWillowLogo}
              alt="Himalayan Willow"
              className="w-full h-full object-contain p-0.5"
            />
          </div>
          <div className="min-w-0 overflow-hidden">
            <h3 className="font-heading font-bold text-xs xs:text-sm sm:text-base text-white uppercase tracking-wide truncate">
              Himalayan Willow
            </h3>
            <p className="text-[10px] xs:text-[11px] sm:text-xs text-white/70 truncate hidden xs:block">
              {user ? "Cricket Equipment Store" : "Sign in to continue"}
            </p>
          </div>
        </div>

        {/* Browse - centered, responsive padding */}
        <div className="relative justify-self-center min-w-0">
          {user && (
            <>
              <button
                ref={filterButtonRef}
                onClick={() => setFilterMenuOpen((v) => !v)}
                className="flex items-center gap-1 xs:gap-2 px-2 xs:px-3 py-1.5 xs:py-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-xs xs:text-sm font-medium text-white/90 transition-colors min-h-[40px] xs:min-h-[44px]"
                aria-expanded={filterMenuOpen}
                aria-haspopup="dialog"
                aria-label="Open filters"
              >
                <svg
                  className="w-3.5 h-3.5 xs:w-4 xs:h-4 shrink-0"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"
                  />
                </svg>
                <span className="whitespace-nowrap">Browse</span>
              </button>
              {filterMenuOpen && (
                <div
                  className="fixed inset-0 z-[45]"
                  onClick={() => setFilterMenuOpen(false)}
                  aria-hidden="true"
                />
              )}
              <Suspense fallback={null}>
                <CricketFilterMegaMenu
                  open={filterMenuOpen}
                  onClose={() => setFilterMenuOpen(false)}
                  anchorRef={filterButtonRef}
                />
              </Suspense>
            </>
          )}
        </div>

        <div className="flex items-center gap-0.5 xs:gap-1 justify-self-end min-w-0">
          {/* Cart button - only when logged in; icon-only on xs, text on sm+ */}
          {user && (
            <button
              onClick={() => setKitBagOpen(true)}
              className="relative flex items-center gap-1 xs:gap-1.5 px-2 xs:px-2.5 py-1.5 text-white hover:text-white hover:bg-white/10 rounded-lg transition-colors min-h-[40px] xs:min-h-[44px]"
              aria-label={`Open cart${cartItems.length > 0 ? ` (${cartItems.length} items)` : ""}`}
              title="My Kit Bag"
            >
              <svg
                className="w-4 h-4 xs:w-5 xs:h-5 shrink-0"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M3 3h2l.4 2M7 13h10l4-8H7.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"
                />
              </svg>
              <span className="text-xs xs:text-sm font-medium hidden sm:inline truncate">
                Cart{cartItems.length > 0 ? ` (${cartItems.length})` : ""}
              </span>
              {cartItems.length > 0 && (
                <span className="absolute -top-0.5 -right-0.5 w-3.5 h-3.5 xs:w-4 xs:h-4 bg-amber-500 text-[#1A1A1A] text-[8px] xs:text-[9px] font-bold rounded-full flex items-center justify-center sm:hidden shrink-0">
                  {cartItems.length}
                </span>
              )}
            </button>
          )}

          {/* Auth: user avatar (when logged in); when !user, login is in centered overlay */}
          {user ? (
            <div className="relative">
              <button
                onClick={() => setAuthDropdownOpen((v) => !v)}
                className="p-1 flex items-center rounded-sharp hover:bg-white/10 transition-colors min-h-[40px] xs:min-h-[44px] min-w-[40px] xs:min-w-[44px] justify-center"
                aria-label="Account menu"
                aria-expanded={authDropdownOpen}
              >
                {user.avatar_url && !avatarLoadError ? (
                  <img
                    src={user.avatar_url}
                    alt={user.name || "User"}
                    className="w-6 h-6 xs:w-7 xs:h-7 rounded-full border border-white/20"
                    referrerPolicy="no-referrer"
                    onError={() => setAvatarLoadError(true)}
                  />
                ) : (
                  <div className="w-6 h-6 xs:w-7 xs:h-7 rounded-full bg-amber-600 flex items-center justify-center text-[#1A1A1A] text-[10px] xs:text-xs font-bold">
                    {(user.name || user.email || "U").charAt(0).toUpperCase()}
                  </div>
                )}
              </button>
              {authDropdownOpen && (
                <>
                  <div
                    className="fixed inset-0 z-[45]"
                    onClick={() => setAuthDropdownOpen(false)}
                    aria-hidden="true"
                  />
                  <div className="absolute right-0 top-full mt-1 py-1 w-36 xs:w-40 min-w-[8rem] max-w-[calc(100vw-2rem)] bg-[#262626] rounded-md border border-white/10 shadow-lg z-[50]">
                    <div className="px-3 py-2 border-b border-white/10 text-sm text-white/80 truncate">
                      {user.name || user.email || "Signed in"}
                    </div>
                    <button
                      onClick={() => {
                        logout();
                        setAuthDropdownOpen(false);
                      }}
                      className="w-full px-3 py-2 text-left text-sm text-white hover:bg-white/10"
                    >
                      Sign out
                    </button>
                  </div>
                </>
              )}
            </div>
          ) : null}
        </div>
      </header>

      {/* Messages + Input: blur when not logged in */}
      <div className="relative flex-1 flex flex-col min-h-0">
        <div
          className={`flex-1 flex flex-col min-h-0 transition-[filter] duration-300 ${
            !user ? "blur-sm pointer-events-none select-none" : ""
          }`}
        >
          <div
            ref={viewportRef}
            className="relative flex-1 overflow-y-auto overflow-x-hidden p-2 xs:p-3 sm:p-4 space-y-4 bg-[#1A1A1A] scroll-smooth scrollbar-hide"
          >
            {messages.length === 0 && user && !isTyping && !isStreaming && (
              <div className="mx-auto flex min-h-full w-full max-w-chat flex-col px-2 xs:px-3 sm:px-4">
                <div className="flex flex-1 flex-col items-center justify-center text-center">
                  <h1 className="font-heading font-semibold text-lg xs:text-xl sm:text-2xl text-white mb-1 tracking-tight">
                    Hello there!
                  </h1>
                  <p className="text-sm xs:text-base sm:text-xl text-white/70 mb-3 xs:mb-4">
                    How can I help you with cricket gear today?
                  </p>
                  <TextGenerateEffect
                    words="Browse bats, balls, protection gear, or ask about recommendations."
                    className="[&_span]:text-white/80 [&_span]:font-normal [&_span]:text-xs xs:[&_span]:text-sm sm:[&_span]:text-base"
                    duration={1.2}
                    filter={true}
                  />
                </div>
                <SuggestedActions />
              </div>
            )}
            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}
            {isTyping && !isStreaming && (
              <div className="flex justify-start mx-auto max-w-chat w-full">
                <div className="max-w-[95%]">
                  <div className="rounded-2xl px-4 py-2.5 border border-white/10 bg-[#262626] shadow-subtle">
                    <div className="flex items-center space-x-2 text-white/70">
                      <div className="flex space-x-1">
                        <div
                          className="w-2 h-2 bg-white/50 rounded-full animate-bounce"
                          style={{ animationDelay: "0ms" }}
                        />
                        <div
                          className="w-2 h-2 bg-white/50 rounded-full animate-bounce"
                          style={{ animationDelay: "150ms" }}
                        />
                        <div
                          className="w-2 h-2 bg-white/50 rounded-full animate-bounce"
                          style={{ animationDelay: "300ms" }}
                        />
                      </div>
                      <span className="text-sm">Typing...</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Footer: scroll-to-bottom + cart + composer - responsive padding, safe area */}
          <div className="shrink-0 z-10 mx-auto flex w-full max-w-chat flex-col gap-3 xs:gap-4 overflow-visible rounded-t-3xl bg-[#1A1A1A] pb-[max(0.75rem,env(safe-area-inset-bottom))] sm:pb-[max(1rem,env(safe-area-inset-bottom))] md:pb-6 pt-2 px-2 xs:px-3 sm:px-0">
            {showScrollToBottom && (
              <div className="flex justify-center -mb-2">
                <button
                  onClick={scrollToBottom}
                  className="rounded-full size-10 flex items-center justify-center border border-white/15 bg-[#262626] text-white/80 hover:bg-white/10 hover:text-white transition-all duration-200 active:scale-95 focus:outline-none focus:ring-2 focus:ring-amber-500/30 focus:ring-offset-2 focus:ring-offset-[#1A1A1A] shadow-premium"
                  aria-label="Scroll to bottom"
                >
                  <svg
                    className="w-5 h-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M19 14l-7 7m0 0l-7-7m7 7V3"
                    />
                  </svg>
                </button>
              </div>
            )}
            {cartItems.length > 0 && (
              <Suspense fallback={null}>
                <CartSummaryBar onOpenCart={() => setKitBagOpen(true)} />
              </Suspense>
            )}
            <ChatInput />
          </div>
        </div>

        {/* Login overlay: textured gradient (brushed metal feel), centered when !user */}
        {!user && (
          <div
            className="absolute inset-0 flex items-center justify-center z-20 bg-gradient-to-br from-black/70 via-slate-900/60 to-black/70 backdrop-blur-[2px]"
            style={{
              backgroundImage:
                "radial-gradient(ellipse at 50% 50%, rgba(71,85,105,0.15) 0%, transparent 70%)",
            }}
          >
            {isLoading ? (
              <div className="flex flex-col items-center gap-3">
                <div
                  className="w-10 h-10 border-2 border-white/30 border-t-white rounded-full animate-spin"
                  aria-hidden="true"
                />
                <span className="text-sm text-white/70">Loading...</span>
              </div>
            ) : googleClientId ? (
              <div className="flex flex-col items-center gap-6 p-6 sm:p-8 rounded-2xl bg-[#2a2a2a]/95 border border-white/15 shadow-premium-lg max-w-sm text-center mx-4 backdrop-blur-md">
                <img
                  src={HimalyanWillowLogo}
                  alt="Himalayan Willow"
                  className="w-16 h-16 object-contain"
                />
                <p className="text-white/95 text-sm leading-relaxed">
                  Sign in to chat and get personalized cricket gear
                  recommendations
                </p>
                <GoogleSignInButton
                  onSuccess={handleGoogleSuccess}
                  className="w-full min-h-[48px] [&_iframe]:!h-12 [&_iframe]:!min-h-12 [&_iframe]:!w-full"
                />
              </div>
            ) : (
              <div className="flex flex-col items-center gap-4 p-4 xs:p-6 sm:p-8 rounded-2xl bg-[#2a2a2a]/95 border border-white/15 shadow-premium w-[calc(100%-2rem)] max-w-sm text-center mx-4 backdrop-blur-md">
                <img
                  src={HimalyanWillowLogo}
                  alt="Himalayan Willow"
                  className="w-16 h-16 object-contain"
                />
                <p className="text-white/90 text-sm">
                  Sign-in is required. Contact support if you need access.
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Kit Bag side panel */}
      <Suspense fallback={null}>
        <KitBagView open={kitBagOpen} onClose={() => setKitBagOpen(false)} />
      </Suspense>
    </div>
  );
};

export default ChatWindow;
