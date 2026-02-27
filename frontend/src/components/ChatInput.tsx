import React, { KeyboardEvent, useEffect, useRef, useState } from "react";
import { useChatContext } from "../contexts/ChatContext";

const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5 MB
const ACCEPTED_TYPES = ["image/jpeg", "image/png", "image/webp"];

const GEAR_ADVICE_PLACEHOLDERS = [
  "Ask for gear advice — e.g. 'Bat for power hitting?'",
  "e.g. 'Which bat has a high sweet spot?'",
  "e.g. 'Kashmir Willow for a beginner?'",
  "Describe what you need, or paste an image...",
];

const ChatInput: React.FC = () => {
  const [inputText, setInputText] = useState("");
  const [placeholderIndex, setPlaceholderIndex] = useState(0);
  const { sendMessage, isTyping, addBotMessage, apiClient } = useChatContext();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const id = setInterval(() => {
      setPlaceholderIndex((i) => (i + 1) % GEAR_ADVICE_PLACEHOLDERS.length);
    }, 4000);
    return () => clearInterval(id);
  }, []);

  const handleSend = async () => {
    if (uploading) return;

    if (selectedFile) {
      await handleImageSend();
      return;
    }

    if (inputText.trim() && !isTyping) {
      await sendMessage(inputText, true);
      setInputText("");
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
      handleSend();
    }
  };

  return (
    <div className="border-t border-white/10 p-4 bg-[#1A1A1A]">
      {/* Image preview */}
      {previewUrl && (
        <div className="mb-3 relative inline-block">
          <img
            src={previewUrl}
            alt="Selected"
            className="h-20 w-20 rounded-lg object-cover border border-white/20"
          />
          <button
            onClick={clearSelectedFile}
            className="absolute -top-1.5 -right-1.5 w-5 h-5 bg-red-500 text-white rounded-full flex items-center justify-center text-xs hover:bg-red-600 transition-colors"
            aria-label="Remove image"
          >
            &times;
          </button>
          {uploading && (
            <div className="absolute inset-0 bg-black/50 rounded-lg flex items-center justify-center">
              <span className="text-xs text-white font-bold">
                {uploadProgress}%
              </span>
            </div>
          )}
        </div>
      )}

      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        autoComplete="off"
        className="flex flex-col"
      >
        <div className="flex space-x-2">
          <label htmlFor="chat-input" className="sr-only">
            Type your message
          </label>

          {/* Image upload button */}
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={isTyping || uploading}
            className="bg-[#262626] border border-white/10 rounded-button px-3 py-2.5 min-h-[44px] min-w-[44px] flex items-center justify-center text-white/50 hover:text-white/80 hover:bg-[#333] disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
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
                : GEAR_ADVICE_PLACEHOLDERS[placeholderIndex]
            }
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onPaste={handlePaste}
            onKeyPress={handleKeyPress}
            disabled={isTyping || uploading}
            className="flex-1 bg-[#262626] border border-white/10 rounded-button px-4 py-2.5 text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-white/30 focus:border-white/20 disabled:opacity-50 disabled:cursor-not-allowed leading-relaxed"
            aria-label="Chat message input"
            aria-describedby="chat-help-text"
          />

          <button
            type="submit"
            disabled={
              (!inputText.trim() && !selectedFile) || isTyping || uploading
            }
            className="bg-white hover:bg-white/90 disabled:opacity-50 disabled:cursor-not-allowed text-[#1A1A1A] px-5 py-2.5 min-h-[44px] min-w-[44px] flex items-center justify-center rounded-button transition-colors focus:outline-none focus:ring-2 focus:ring-white/50 focus:ring-offset-2 focus:ring-offset-[#1A1A1A] font-semibold"
            aria-label="Send message"
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
                d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
              />
            </svg>
          </button>
        </div>
        <p id="chat-help-text" className="text-xs text-white/50 mt-2">
          Press Enter to send{" "}
          {selectedFile
            ? "| Image attached"
            : "| Upload or paste an image to find similar products"}
        </p>
      </form>
    </div>
  );
};

export default ChatInput;
