import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface KnockInCardProps {
  title: string;
  body: string;
  animationType: string;
}

const KnockInCard: React.FC<KnockInCardProps> = ({ title, body, animationType }) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="mt-3">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full bg-amber-900/20 border border-amber-500/20 hover:border-amber-500/40 rounded-lg p-3 text-left transition-all group"
      >
        <div className="flex items-center gap-3">
          {/* Animated mallet icon */}
          <div className="relative w-10 h-10 flex-shrink-0">
            {animationType === 'mallet_tap' ? (
              <motion.div
                animate={expanded ? { rotate: [0, -15, 0] } : {}}
                transition={{ repeat: Infinity, duration: 1.2, ease: 'easeInOut' }}
                className="text-2xl origin-bottom-right"
              >
                🔨
              </motion.div>
            ) : (
              <motion.div
                animate={expanded ? { scale: [1, 1.15, 1] } : {}}
                transition={{ repeat: Infinity, duration: 1.5, ease: 'easeInOut' }}
                className="text-2xl"
              >
                ✨
              </motion.div>
            )}
          </div>

          <div className="flex-1 min-w-0">
            <span className="text-sm font-semibold text-amber-300 block">{title}</span>
            {!expanded && (
              <span className="text-[11px] text-white/40 block truncate">
                Tap to learn more...
              </span>
            )}
          </div>

          <svg
            className={`w-4 h-4 text-white/40 transition-transform ${expanded ? 'rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden"
          >
            <div className="bg-amber-900/10 border border-t-0 border-amber-500/20 rounded-b-lg p-3 -mt-1">
              <p className="text-xs text-white/70 leading-relaxed whitespace-pre-line">{body}</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default KnockInCard;
