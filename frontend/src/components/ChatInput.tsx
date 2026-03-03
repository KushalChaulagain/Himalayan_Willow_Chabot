import React, { KeyboardEvent, useEffect, useRef, useState } from "react";
import { useChatContext } from "../contexts/ChatContext";

const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5 MB
const ACCEPTED_TYPES = ["image/jpeg", "image/png", "image/webp"];
const INPUT_DRAFT_KEY = "himalayan-willow-chat-input-draft";

const PLACEHOLDER = "Describe what you need, or paste an image...";

const ChatInput: React.FC = () => {
  const [inputText, setInputText] = useState(() => {
    try {
      return localStorage.getItem(INPUT_DRAFT_KEY) || "";
    } catch {
      return "";
    }
  });
  const {
    sendMessage,
    stopStream,
    isTyping,
    isStreaming,
    addBotMessage,
    apiClient,
  } = useChatContext();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    try {
      localStorage.setItem(INPUT_DRAFT_KEY, inputText);
    } catch {
      /* ignore */
    }
  }, [inputText]);

  const handleSend = async () => {
    if (uploading) return;

    if (selectedFile) {
      await handleImageSend();
      return;
    }

    if (inputText.trim() && !isTyping) {
      const text = inputText.trim();
      setInputText("");
      try {
        localStorage.removeItem(INPUT_DRAFT_KEY);
      } catch {
        /* ignore */
      }
      await sendMessage(text, true);
    }
  };

  const handleImageSend = async () => {
    if (!selectedFile) return;

    setUploading(true);
    setUploadProgress(0);

    addBotMessage("Analyzing your image...", {
      id: `upload-preview-${Date.now()}`,
      imageUrl: previewUrl || undefined,
    });

    try {
      const result = await apiClient.uploadImageForSearch(
        selectedFile,
        undefined,
        (percent) => setUploadProgress(percent),
      );

      if (result.products.length > 0) {
        addBotMessage(
          `I found ${result.count} similar product${result.count !== 1 ? "s" : ""} in our catalog:`,
          {
            productCards: result.products,
            quickReplies: [
              "Show me more",
              "Different category",
              "Talk to human",
            ],
          },
        );
      } else {
        addBotMessage(
          "I couldn't find matching products for this image. Try a different angle or describe what you're looking for.",
          { quickReplies: ["Show me bats", "Show me gloves", "Talk to human"] },
        );
      }
    } catch {
      addBotMessage(
        "Image search is temporarily unavailable. Please describe what you are looking for instead.",
        { quickReplies: ["Show me bats", "Show me gloves", "Talk to human"] },
      );
    } finally {
      setUploading(false);
      setUploadProgress(0);
      clearSelectedFile();
    }
  };

  const processImageFile = (file: File) => {
    if (!ACCEPTED_TYPES.includes(file.type)) {
      addBotMessage("Please use a JPEG, PNG, or WebP image.", {
        quickReplies: ["Try again"],
      });
      return;
    }

    if (file.size > MAX_FILE_SIZE) {
      addBotMessage("Image is too large. Please use an image under 5 MB.", {
        quickReplies: ["Try again"],
      });
      return;
    }

    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    processImageFile(file);
  };

  const handlePaste = (e: React.ClipboardEvent<HTMLInputElement>) => {
    const items = e.clipboardData?.items;
    if (!items) return;

    for (const item of Array.from(items)) {
      if (item.kind === "file" && item.type.startsWith("image/")) {
        e.preventDefault();
        const file = item.getAsFile();
        if (file) processImageFile(file);
        return;
      }
    }
  };

  const clearSelectedFile = () => {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setSelectedFile(null);
    setPreviewUrl(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (isStreaming) {
        stopStream();
      } else {
        handleSend();
      }
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.dataTransfer.types.includes("Files")) setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file && file.type.startsWith("image/")) processImageFile(file);
  };

  return (
    <div className="border-t border-white/10 p-2 xs:p-3 sm:p-4 bg-[#1A1A1A]">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        autoComplete="off"
        className="flex flex-col min-w-0"
      >
        <div
          className={`flex w-full flex-col rounded-2xl border bg-[#1A1A1A] px-2 xs:px-3 sm:px-4 py-2.5 sm:py-3 outline-none transition-all duration-200 focus-within:border-amber-500/40 focus-within:ring-2 focus-within:ring-amber-500/30 focus-within:shadow-premium-glow ${
            isDragging
              ? "border-amber-500/50 border-dashed bg-amber-500/5"
              : "border-white/15"
          }`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          {/* Image preview - attachment tile style */}
          {previewUrl && (
            <div className="mb-2 flex items-center gap-2">
              <div className="relative size-14 shrink-0 overflow-hidden rounded-[14px] border border-white/20">
                <img
                  src={previewUrl}
                  alt="Selected"
                  className="size-full object-cover"
                />
                <button
                  type="button"
                  onClick={clearSelectedFile}
                  className="absolute top-1 right-1 size-4 bg-white/90 text-[#1A1A1A] rounded-full flex items-center justify-center text-[10px] hover:bg-white transition-colors"
                  aria-label="Remove image"
                >
                  &times;
                </button>
                {uploading && (
                  <div className="absolute inset-0 bg-black/60 flex items-center justify-center">
                    <span className="text-[10px] text-white font-bold">
                      {uploadProgress}%
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}

          <div className="flex items-center gap-1 xs:gap-2 min-h-[44px] min-w-0">
            <label htmlFor="chat-input" className="sr-only">
              Type your message
            </label>

            {/* Image upload button */}
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={isTyping || uploading}
              className="shrink-0 rounded-full size-10 min-h-[44px] min-w-[44px] flex items-center justify-center text-white/50 hover:text-white/80 hover:bg-white/10 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              aria-label="Upload image for visual search"
              title="Upload image to find similar products"
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
                  d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"
                />
              </svg>
            </button>

            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/png,image/webp"
              onChange={handleFileSelect}
              className="hidden"
              aria-hidden="true"
            />

            <input
              id="chat-input"
              type="text"
              autoComplete="off"
              placeholder={
                selectedFile
                  ? "Send to find matching products..."
                  : PLACEHOLDER
              }
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onPaste={handlePaste}
              onKeyPress={handleKeyPress}
              disabled={isTyping || uploading}
              className="min-h-[44px] min-w-0 flex-1 resize-none bg-transparent py-2.5 px-1 text-xs xs:text-sm text-white placeholder-white/40 outline-none disabled:opacity-50 disabled:cursor-not-allowed leading-normal focus-visible:ring-0"
              aria-label="Chat message input"
              aria-describedby="chat-help-text"
            />

            {isStreaming ? (
              <button
                type="button"
                onClick={(e) => {
                  e.preventDefault();
                  stopStream();
                }}
                className="shrink-0 size-10 min-h-[44px] min-w-[44px] rounded-full bg-red-500/90 hover:bg-red-500 text-white flex items-center justify-center font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-red-400 focus:ring-offset-2 focus:ring-offset-[#1A1A1A]"
                aria-label="Stop generating"
              >
                <svg
                  className="w-4 h-4"
                  fill="currentColor"
                  viewBox="0 0 24 24"
                >
                  <rect x="6" y="6" width="12" height="12" rx="1" />
                </svg>
              </button>
            ) : (
              <button
                type="submit"
                disabled={
                  (!inputText.trim() && !selectedFile) || isTyping || uploading
                }
                className="shrink-0 size-10 min-h-[44px] min-w-[44px] rounded-full bg-white hover:bg-white/90 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed text-[#1A1A1A] flex items-center justify-center font-semibold transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-amber-500/30 focus:ring-offset-2 focus:ring-offset-[#1A1A1A]"
                aria-label="Send message"
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
                    d="M5 10l7-7m0 0l7 7m-7-7v18"
                  />
                </svg>
              </button>
            )}
          </div>
        </div>
        <p id="chat-help-text" className="text-[10px] xs:text-[11px] sm:text-xs text-white/50 mt-1.5 xs:mt-2 px-1">
          {selectedFile ? (
            "Image attached — Enter to send"
          ) : (
            <>
              Enter to send
              <span className="hidden xs:inline"> | Upload or paste an image to find similar products</span>
            </>
          )}
        </p>
      </form>
    </div>
  );
};

export default ChatInput;
