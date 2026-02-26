import React from 'react';
import { motion } from 'framer-motion';
import { TrackingStage } from '../types';

interface TrackingMapProps {
  stages: TrackingStage[];
  orderId?: string;
  destinationCity?: string;
}

const TrackingMap: React.FC<TrackingMapProps> = ({ stages, orderId, destinationCity }) => {
  const currentIndex = stages.findIndex((s) => s.current);

  return (
    <div className="mt-3 bg-white/5 border border-white/10 rounded-lg p-4">
      {orderId && (
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs text-white/50 font-medium">Order {orderId}</span>
          {destinationCity && (
            <span className="text-[10px] text-white/40">
              Kathmandu → {destinationCity}
            </span>
          )}
        </div>
      )}

      {/* Journey line with animated delivery icon */}
      <div className="relative mb-4">
        <div className="h-1 bg-white/10 rounded-full">
          <motion.div
            className="h-full bg-emerald-500 rounded-full"
            initial={{ width: 0 }}
            animate={{ width: `${Math.max(((currentIndex + 1) / stages.length) * 100, 5)}%` }}
            transition={{ duration: 1, ease: 'easeOut' }}
          />
        </div>
        {/* Animated delivery icon riding the progress bar */}
        <motion.div
          className="absolute -top-3 text-lg"
          initial={{ left: '0%' }}
          animate={{ left: `${Math.max(((currentIndex + 0.5) / stages.length) * 100, 2)}%` }}
          transition={{ duration: 1.2, ease: 'easeOut' }}
          style={{ transform: 'translateX(-50%)' }}
        >
          🚚
        </motion.div>
      </div>

      {/* Stage list */}
      <div className="space-y-0">
        {stages.map((stage, idx) => {
          const isCompleted = stage.completed;
          const isCurrent = stage.current;

          return (
            <div key={stage.id} className="flex items-start gap-3">
              {/* Vertical connector + dot */}
              <div className="flex flex-col items-center w-6 flex-shrink-0">
                <div
                  className={`w-5 h-5 rounded-full flex items-center justify-center text-xs ${
                    isCompleted
                      ? 'bg-emerald-500 text-white'
                      : isCurrent
                        ? 'bg-emerald-500/30 border-2 border-emerald-500 text-emerald-400'
                        : 'bg-white/10 text-white/30'
                  }`}
                >
                  {isCompleted ? (
                    <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  ) : isCurrent ? (
                    <motion.div
                      className="w-2 h-2 bg-emerald-400 rounded-full"
                      animate={{ scale: [1, 1.4, 1] }}
                      transition={{ repeat: Infinity, duration: 1.5 }}
                    />
                  ) : (
                    <span className="text-[10px]">{stage.icon}</span>
                  )}
                </div>
                {idx < stages.length - 1 && (
                  <div
                    className={`w-px flex-1 min-h-[20px] ${
                      isCompleted ? 'bg-emerald-500/50' : 'bg-white/10'
                    }`}
                  />
                )}
              </div>

              {/* Label + time */}
              <div className="pb-3 flex-1 min-w-0">
                <p className={`text-xs font-medium ${
                  isCompleted || isCurrent ? 'text-white' : 'text-white/40'
                }`}>
                  {stage.label}
                </p>
                {stage.timestamp && (
                  <p className="text-[10px] text-white/30 mt-0.5">
                    {new Date(stage.timestamp).toLocaleDateString(undefined, {
                      month: 'short',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default TrackingMap;
