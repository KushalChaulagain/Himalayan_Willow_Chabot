import React, { lazy, Suspense, useMemo, useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useChatContext } from "../contexts/ChatContext";
import { Message } from "../types";
import KnockInCard from "./KnockInCard";
import LocationCard from "./LocationCard";
import ProductCard from "./ProductCard";
import QuickReplies from "./QuickReplies";

const ConfettiCelebration = lazy(() => import("./ConfettiCelebration"));
const TrackingMap = lazy(() => import("./TrackingMap"));

/** Matches markdown links to Google Maps / Maps domains */
const MAPS_LINK_REGEX =
  /\[([^\]]*)\]\((https?:\/\/(?:www\.)?(?:maps\.google\.com|maps\.app\.goo\.gl|goo\.gl\/maps|www\.google\.com\/maps)[^)]*)\)/gi;

function extractMapsLinks(message: string): { cleanedMessage: string; mapsUrls: string[] } {
  const mapsUrls: string[] = [];
  let cleanedMessage = message.replace(MAPS_LINK_REGEX, (_, _linkText, url) => {
    mapsUrls.push(url);
    return ""; // Remove link from message body
  });
  // Deduplicate URLs (LLM may repeat the same maps link in the response)
  const uniqueMapsUrls = [...new Set(mapsUrls)];
  // Collapse multiple spaces, clean stray punctuation left after link removal
  cleanedMessage = cleanedMessage
    .replace(/\s{2,}/g, " ")
    .replace(/\s*\.\s*\.+/g, ".")
    .replace(/\s+\.\s*$/, ".")
    .trim();
  return { cleanedMessage, mapsUrls: uniqueMapsUrls };
}

interface ChatMessageProps {
  message: Message;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const isUser = message.sender === "user";
  const { retryMessage } = useChatContext();
  const scrollRef = useRef<HTMLDivElement>(null);

  const { cleanedMessage, mapsUrls } = useMemo(
    () => (isUser ? { cleanedMessage: message.message, mapsUrls: [] as string[] } : extractMapsLinks(message.message)),
    [message.message, isUser]
  );

  const hasProducts = message.productCards && message.productCards.length > 0;
  const productCount = message.productCards?.length || 0;

  const scroll = (direction: "left" | "right") => {
    if (!scrollRef.current) return;
    const amount = 240;
    scrollRef.current.scrollBy({
      left: direction === "left" ? -amount : amount,
      behavior: "smooth",
    });
  };

  const ic = message.interactiveContent;

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`${isUser ? "max-w-[80%]" : "max-w-[95%]"} ${isUser ? "order-2" : "order-1"}`}
      >
        <div
          className={`rounded-card p-3 border ${
            isUser
              ? "bg-[#262626] text-white border-white/10"
              : message.failed
                ? "bg-[#262626] text-white border-red-500/40"
                : "bg-[#262626] text-white border-white/10"
          }`}
        >
          {/* User-uploaded image preview */}
          {message.imageUrl && (
            <img
              src={message.imageUrl}
              alt="Uploaded"
              className="rounded-md mb-2 max-h-40 object-cover"
            />
          )}

          <div className="text-sm leading-relaxed text-white chat-message-content">
            {isUser ? (
              <p className="whitespace-pre-wrap">{message.message}</p>
            ) : (
              <>
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    p: ({ children }) => (
                      <p className="mb-2 last:mb-0">{children}</p>
                    ),
                    strong: ({ children }) => (
                      <strong className="font-semibold">{children}</strong>
                    ),
                    ul: ({ children }) => (
                      <ul className="list-disc list-inside mb-2 space-y-1">
                        {children}
                      </ul>
                    ),
                    ol: ({ children }) => (
                      <ol className="list-decimal list-inside mb-2 space-y-1">
                        {children}
                      </ol>
                    ),
                    li: ({ children }) => <li className="ml-2">{children}</li>,
                    a: ({ href, children }) => (
                      <a
                        href={href}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-amber-400 hover:text-amber-300 underline"
                      >
                        {children}
                      </a>
                    ),
                  }}
                >
                  {cleanedMessage}
                </ReactMarkdown>
                {mapsUrls.length > 0 &&
                  mapsUrls.map((url, i) => (
                    <LocationCard key={i} mapsUrl={url} />
                  ))}
              </>
            )}
          </div>
          <p className="text-xs mt-1 text-white/60">
            {message.timestamp.toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </p>
        </div>

        {message.failed && (
          <button
            onClick={() => retryMessage(message.id)}
            className="mt-2 flex items-center gap-1.5 text-sm text-red-400 hover:text-red-300 transition-colors"
            aria-label="Retry sending message"
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
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
            Retry
          </button>
        )}

        {/* Interactive Content */}
        {ic && (
          <Suspense
            fallback={
              <div className="text-xs text-white/40 py-2">Loading...</div>
            }
          >
            {ic.type === "educational" && ic.educationalContent && (
              <KnockInCard
                title={ic.educationalContent.title}
                body={ic.educationalContent.body}
                animationType={ic.educationalContent.animationType}
              />
            )}

            {ic.type === "confetti" && (
              <ConfettiCelebration
                message={ic.confettiMessage || "Great choice, Skipper!"}
              />
            )}

            {ic.type === "tracking_map" && ic.trackingData && (
              <TrackingMap
                stages={ic.trackingData}
                orderId={ic.orderId}
                destinationCity={ic.destinationCity}
              />
            )}
          </Suspense>
        )}

        {/* Product Carousel */}
        {hasProducts && (
          <div className="mt-3">
            <div className="flex items-center justify-between mb-2 px-1">
              <span className="text-xs text-white/50 font-medium">
                {productCount} product{productCount !== 1 ? "s" : ""} found
              </span>
              {productCount > 1 && (
                <div className="flex gap-1">
                  <button
                    onClick={() => scroll("left")}
                    className="p-1 rounded-md bg-white/5 hover:bg-white/15 text-white/60 hover:text-white transition-colors"
                    aria-label="Scroll left"
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
                        d="M15 19l-7-7 7-7"
                      />
                    </svg>
                  </button>
                  <button
                    onClick={() => scroll("right")}
                    className="p-1 rounded-md bg-white/5 hover:bg-white/15 text-white/60 hover:text-white transition-colors"
                    aria-label="Scroll right"
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
                        d="M9 5l7 7-7 7"
                      />
                    </svg>
                  </button>
                </div>
              )}
            </div>

            <div
              ref={scrollRef}
              className="flex gap-3 overflow-x-auto pb-2 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent"
              style={{ scrollSnapType: "x mandatory" }}
            >
              {message.productCards!.map((card) => (
                <div key={card.id} style={{ scrollSnapAlign: "start" }}>
                  <ProductCard product={card} layout="full" />
                </div>
              ))}
            </div>
          </div>
        )}

        {!message.failed &&
          message.quickReplies &&
          message.quickReplies.length > 0 && (
            <QuickReplies options={message.quickReplies} />
          )}
      </div>
    </div>
  );
};

export default ChatMessage;
