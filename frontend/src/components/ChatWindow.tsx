import React, { lazy, Suspense, useEffect, useRef, useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import { useChatContext } from "../contexts/ChatContext";
import ChatInput from "./ChatInput";
import ChatMessage from "./ChatMessage";
import GoogleSignInButton from "./GoogleSignInButton";

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
  const [kitBagOpen, setKitBagOpen] = useState(false);
  const [authDropdownOpen, setAuthDropdownOpen] = useState(false);
  const [avatarLoadError, setAvatarLoadError] = useState(false);
  const [filterMenuOpen, setFilterMenuOpen] = useState(false);
  const filterButtonRef = useRef<HTMLButtonElement>(null);

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
      {/* Header */}
      <div className="bg-[#1A1A1A] text-white p-4 flex items-center justify-between shrink-0 border-b border-white/10 relative">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-sharp overflow-hidden bg-[#262626] flex items-center justify-center shrink-0 border border-white/10">
            <img
              src={HimalyanWillowLogo}
              alt="Himalayan Willow"
              className="w-full h-full object-contain p-0.5"
            />
          </div>
          <div>
            <h3 className="font-heading font-bold text-base text-white uppercase tracking-wide">
              Himalayan Willow
            </h3>
            <p className="text-xs text-white/70">
              {user ? "Cricket Equipment Store" : "Sign in to continue"}
            </p>
          </div>
        </div>

        <div className="relative">
          {user && (
            <>
              <button
                ref={filterButtonRef}
                onClick={() => setFilterMenuOpen((v) => !v)}
                className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-sm font-medium text-white/90 transition-colors min-h-[44px]"
                aria-expanded={filterMenuOpen}
                aria-haspopup="dialog"
                aria-label="Open filters"
              >
                <svg
                  className="w-4 h-4"
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
                Browse
              </button>
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

        <div className="flex items-center gap-1">
          {/* Cart button - only when logged in */}
          {user && (
            <button
              onClick={() => setKitBagOpen(true)}
              className="relative flex items-center gap-1.5 px-2.5 py-1.5 text-white hover:text-white hover:bg-white/10 rounded-lg transition-colors"
              aria-label="Open cart"
              title="My Kit Bag"
            >
              <svg
                className="w-5 h-5 shrink-0"
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
              <span className="text-sm font-medium hidden sm:inline">
                Cart{cartItems.length > 0 ? ` (${cartItems.length})` : ""}
              </span>
              {cartItems.length > 0 && (
                <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-amber-500 text-[#1A1A1A] text-[9px] font-bold rounded-full flex items-center justify-center sm:hidden">
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
                className="p-1 flex items-center rounded-sharp hover:bg-white/10 transition-colors"
                aria-label="Account menu"
                aria-expanded={authDropdownOpen}
              >
                {user.avatar_url && !avatarLoadError ? (
                  <img
                    src={user.avatar_url}
                    alt={user.name || "User"}
                    className="w-7 h-7 rounded-full border border-white/20"
                    referrerPolicy="no-referrer"
                    onError={() => setAvatarLoadError(true)}
                  />
                ) : (
                  <div className="w-7 h-7 rounded-full bg-amber-600 flex items-center justify-center text-[#1A1A1A] text-xs font-bold">
                    {(user.name || user.email || "U").charAt(0).toUpperCase()}
                  </div>
                )}
              </button>
              {authDropdownOpen && (
                <>
                  <div
                    className="fixed inset-0 z-10"
                    onClick={() => setAuthDropdownOpen(false)}
                    aria-hidden="true"
                  />
                  <div className="absolute right-0 top-full mt-1 py-1 w-40 bg-[#262626] rounded-md border border-white/10 shadow-lg z-20">
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
      </div>

      {/* Messages + Input: blur when not logged in */}
      <div className="relative flex-1 flex flex-col min-h-0">
        <div
          className={`flex-1 flex flex-col min-h-0 transition-[filter] duration-300 ${
            !user ? "blur-sm pointer-events-none select-none" : ""
          }`}
        >
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-[#1A1A1A]">
            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}
            {(isTyping || isStreaming) && (
              <div className="flex items-center space-x-2 text-white/60">
                <div className="flex space-x-1">
                  <div
                    className="w-2 h-2 bg-white/50 rounded-full animate-bounce"
                    style={{ animationDelay: "0ms" }}
                  ></div>
                  <div
                    className="w-2 h-2 bg-white/50 rounded-full animate-bounce"
                    style={{ animationDelay: "150ms" }}
                  ></div>
                  <div
                    className="w-2 h-2 bg-white/50 rounded-full animate-bounce"
                    style={{ animationDelay: "300ms" }}
                  ></div>
                </div>
                <span className="text-sm text-white/70">
                  {isStreaming ? "Streaming..." : "Typing..."}
                </span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
          {cartItems.length > 0 && (
            <Suspense fallback={null}>
              <CartSummaryBar onOpenCart={() => setKitBagOpen(true)} />
            </Suspense>
          )}
          <ChatInput />
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
              <div className="flex flex-col items-center gap-6 p-8 rounded-xl bg-[#2a2a2a]/95 border border-white/15 shadow-2xl max-w-sm text-center mx-4 backdrop-blur-sm">
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
              <div className="flex flex-col items-center gap-4 p-8 rounded-xl bg-[#2a2a2a]/95 border border-white/15 max-w-sm text-center mx-4 backdrop-blur-sm">
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
