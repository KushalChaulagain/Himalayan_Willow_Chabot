import React from "react";
import { motion } from "framer-motion";
import { useChatContext } from "../contexts/ChatContext";

export type SuggestionItem =
  | string
  | { title: string; label?: string; prompt: string };

const DEFAULT_SUGGESTED_ACTIONS: SuggestionItem[] = [
  {
    title: "Show me Bats",
    label: "Kashmir & English Willow",
    prompt: "Show me Bats",
  },
  {
    title: "Balls & Accessories",
    label: "Cricket balls, grips & more",
    prompt: "Balls & Accessories",
  },
  {
    title: "Protection Gear",
    label: "Pads, gloves, helmets",
    prompt: "Protection Gear",
  },
];

const CATEGORY_ICONS: Record<string, string> = {
  "Show me Bats": "\u{1F3CF}",
  "Balls & Accessories": "\u26BE",
  "Protection Gear": "\u{1F6E1}\uFE0F",
};

interface SuggestedActionsProps {
  options?: SuggestionItem[];
}

function getPrompt(item: SuggestionItem): string {
  return typeof item === "string" ? item : item.prompt;
}

function getTitle(item: SuggestionItem): string {
  return typeof item === "string" ? item : item.title;
}

function getLabel(item: SuggestionItem): string | undefined {
  return typeof item === "string" ? undefined : item.label;
}

const SuggestionCard: React.FC<{
  item: SuggestionItem;
  index: number;
  onSelect: (prompt: string) => void;
}> = ({ item, index, onSelect }) => {
  const prompt = getPrompt(item);
  const title = getTitle(item);
  const label = getLabel(item);
  const icon = CATEGORY_ICONS[title] || CATEGORY_ICONS[prompt];

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2, delay: index * 0.08 }}
      className="w-full sm:w-auto sm:min-w-[160px] sm:flex-1 sm:max-w-[280px]"
    >
      <button
        onClick={() => onSelect(prompt)}
        className="w-full flex flex-col gap-1 rounded-2xl border border-white/15 px-3 xs:px-4 py-3 text-left transition-all duration-200 active:scale-[0.98] focus:outline-none focus:ring-2 focus:ring-amber-500/30 focus:ring-offset-2 focus:ring-offset-[#1A1A1A] bg-transparent hover:bg-white/10 hover:border-white/25 hover:shadow-premium-sm text-white min-h-[44px]"
        tabIndex={0}
      >
        <span className="font-medium text-xs xs:text-sm flex items-center gap-2">
          {icon && <span className="text-base xs:text-lg shrink-0">{icon}</span>}
          {title}
        </span>
        {label && (
          <span className="text-[11px] xs:text-xs text-white/60 line-clamp-2">{label}</span>
        )}
      </button>
    </motion.div>
  );
};

const SuggestedActions: React.FC<SuggestedActionsProps> = ({
  options = DEFAULT_SUGGESTED_ACTIONS,
}) => {
  const { sendMessage } = useChatContext();

  const handleClick = (prompt: string) => {
    sendMessage(prompt, true);
  };

  return (
    <div
      className="flex flex-col sm:flex-row sm:flex-wrap justify-center gap-2 xs:gap-3 mt-4 xs:mt-6 w-full max-w-chat mx-auto px-2 xs:px-4"
      role="group"
      aria-label="Suggested actions to get started"
    >
      {options.map((item, index) => (
        <SuggestionCard
          key={index}
          item={item}
          index={index}
          onSelect={handleClick}
        />
      ))}
    </div>
  );
};

export default SuggestedActions;
