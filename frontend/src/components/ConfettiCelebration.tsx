import React, { useEffect, useState } from 'react';
import confetti from 'canvas-confetti';
import { motion } from 'framer-motion';

interface ConfettiCelebrationProps {
  message: string;
}

const ConfettiCelebration: React.FC<ConfettiCelebrationProps> = ({ message }) => {
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    const duration = 3000;
    const end = Date.now() + duration;

    const colors = ['#22c55e', '#facc15', '#ffffff', '#3b82f6'];

    const frame = () => {
      confetti({
        particleCount: 3,
        angle: 60,
        spread: 55,
        origin: { x: 0, y: 0.7 },
        colors,
        zIndex: 9999,
      });
      confetti({
        particleCount: 3,
        angle: 120,
        spread: 55,
        origin: { x: 1, y: 0.7 },
        colors,
        zIndex: 9999,
      });

      if (Date.now() < end) {
        requestAnimationFrame(frame);
      }
    };

    frame();

    // Big burst at the start
    confetti({
      particleCount: 80,
      spread: 100,
      origin: { y: 0.6 },
      colors,
      zIndex: 9999,
    });

    const timer = setTimeout(() => setVisible(false), 4000);
    return () => clearTimeout(timer);
  }, []);

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: visible ? 1 : 0, scale: 1 }}
      transition={{ duration: 0.4 }}
      className="mt-3 bg-emerald-500/10 border border-emerald-500/30 rounded-lg p-4 text-center"
    >
      <div className="text-3xl mb-2">🎉🏏</div>
      <p className="text-sm text-emerald-300 font-semibold">{message}</p>
      <p className="text-[11px] text-white/50 mt-1">Your gear is heading to the pavilion!</p>
    </motion.div>
  );
};

export default ConfettiCelebration;
