import React from 'react';
import { useChatContext } from '../contexts/ChatContext';

interface QuickRepliesProps {
  options: string[];
}

const CATEGORY_ICONS: Record<string, string> = {
  'Show me Bats': '\u{1F3CF}',
  'Balls & Accessories': '\u26BE',
  'Protection Gear': '\u{1F6E1}\uFE0F',
  'Show me gloves': '\u{1F9E4}',
  'Show me pads': '\u{1F9B5}',
  'Show me helmets': '\u26D1\uFE0F',
  'Kashmir Willow bats': '\u{1F3CF}',
  'English Willow bats': '\u{1F3CF}',
  'Bats for beginners': '\u{1F3CF}',
  'I have a photo': '\u{1F4F7}',
  'Talk to human': '\u{1F64B}',
};

const QuickReplies: React.FC<QuickRepliesProps> = ({ options }) => {
  const { sendMessage } = useChatContext();

  const handleClick = (option: string) => {
    sendMessage(option);
  };

  return (
    <div className="flex flex-wrap gap-1.5 xs:gap-2 mt-3" role="group" aria-label="Quick reply options">
      {options.map((option, index) => {
        const icon = CATEGORY_ICONS[option];

        return (
          <button
            key={index}
            onClick={() => handleClick(option)}
            className="border border-white/15 text-[11px] xs:text-xs sm:text-sm py-1.5 xs:py-2 px-2.5 xs:px-3 sm:px-4 rounded-2xl transition-all duration-200 active:scale-[0.98] focus:outline-none focus:ring-2 focus:ring-amber-500/30 focus:ring-offset-2 focus:ring-offset-[#1A1A1A] bg-transparent hover:bg-white/10 hover:border-white/25 text-white min-h-[40px] xs:min-h-[44px] min-w-[44px]"
            tabIndex={0}
          >
            {icon && `${icon} `}
            {option}
          </button>
        );
      })}
    </div>
  );
};

export default QuickReplies;
