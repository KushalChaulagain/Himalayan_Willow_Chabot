import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useChatContext } from '../contexts/ChatContext';
import WeightSlider from './WeightSlider';
import KnockInCard from './KnockInCard';

interface QuizAnswers {
  playing_level: string;
  surface: string;
  budget: string;
  weight_preference?: number;
}

const STEPS = [
  {
    id: 'playing_level',
    question: "What's your playing level?",
    options: [
      {
        id: 'beginner',
        label: 'Beginner',
        icon: '🏏',
        description: 'Just starting my cricket journey',
      },
      {
        id: 'club',
        label: 'Club / Intermediate',
        icon: '🏟️',
        description: 'Playing in local leagues and tournaments',
      },
      {
        id: 'professional',
        label: 'Professional',
        icon: '🏆',
        description: 'Competitive and serious about my game',
      },
    ],
  },
  {
    id: 'surface',
    question: 'What surface do you usually play on?',
    options: [
      {
        id: 'turf',
        label: 'Turf (Grass)',
        icon: '🌿',
        description: 'Natural grass wickets',
      },
      {
        id: 'cement',
        label: 'Cement / Concrete',
        icon: '🧱',
        description: 'Hard surfaces, common in Nepal',
      },
      {
        id: 'matting',
        label: 'Matting',
        icon: '🎯',
        description: 'Artificial mat on concrete or dirt',
      },
      {
        id: 'street',
        label: 'Tape Ball / Street',
        icon: '🎾',
        description: 'Casual tape ball cricket',
      },
    ],
  },
  {
    id: 'budget',
    question: "What's your budget?",
    options: [
      {
        id: 'under_3k',
        label: 'Under NPR 3,000',
        icon: '💰',
        description: 'Value picks for starting out',
      },
      {
        id: '3k_7k',
        label: 'NPR 3,000 - 7,000',
        icon: '💰💰',
        description: 'Mid-range for regular players',
      },
      {
        id: '7k_15k',
        label: 'NPR 7,000 - 15,000',
        icon: '💰💰💰',
        description: 'Premium gear for serious cricketers',
      },
      {
        id: 'no_limit',
        label: 'No Limit',
        icon: '👑',
        description: 'Show me the very best',
      },
    ],
  },
];

const BatFinderQuiz: React.FC = () => {
  const { addBotMessage, apiClient, sessionId } = useChatContext();
  const [currentStep, setCurrentStep] = useState(0);
  const [answers, setAnswers] = useState<Partial<QuizAnswers>>({});
  const [showSlider, setShowSlider] = useState(false);
  const [completed, setCompleted] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleOptionSelect = (stepId: string, optionId: string) => {
    const newAnswers = { ...answers, [stepId]: optionId };
    setAnswers(newAnswers);

    if (currentStep < STEPS.length - 1) {
      setTimeout(() => setCurrentStep((s) => s + 1), 300);
    } else {
      setShowSlider(true);
    }
  };

  const handleSliderComplete = async (weight: number) => {
    setLoading(true);
    const finalAnswers: QuizAnswers = {
      playing_level: answers.playing_level || 'beginner',
      surface: answers.surface || 'cement',
      budget: answers.budget || 'under_3k',
      weight_preference: weight,
    };

    try {
      const result = await apiClient.submitBatFinder({
        ...finalAnswers,
        session_id: sessionId || undefined,
      });

      setCompleted(true);

      addBotMessage(result.message, {
        productCards: result.product_cards,
        quickReplies: result.quick_replies,
        interactiveContent: result.educational_content
          ? { type: 'educational', educationalContent: result.educational_content }
          : undefined,
      });
    } catch {
      addBotMessage("I had trouble finding bats. Let me show you our popular options instead.", {
        quickReplies: ['Show me bats', 'Talk to human'],
      });
      setCompleted(true);
    } finally {
      setLoading(false);
    }
  };

  const handleSkipSlider = () => {
    handleSliderComplete(1150);
  };

  if (completed) {
    return (
      <div className="text-xs text-white/40 italic mt-1">
        Quiz completed -- results shown below
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center gap-2 py-4">
        <div className="flex space-x-1">
          <div className="w-2 h-2 bg-white/50 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
          <div className="w-2 h-2 bg-white/50 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
          <div className="w-2 h-2 bg-white/50 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
        </div>
        <span className="text-sm text-white/60">Finding your perfect bat...</span>
      </div>
    );
  }

  if (showSlider) {
    return (
      <div className="mt-3 space-y-3">
        <WeightSlider
          onSelect={handleSliderComplete}
          playingLevel={answers.playing_level || 'beginner'}
        />
        <button
          onClick={handleSkipSlider}
          className="text-xs text-white/40 hover:text-white/60 underline transition-colors"
        >
          Skip -- use default weight
        </button>
      </div>
    );
  }

  const step = STEPS[currentStep];

  return (
    <div className="mt-3">
      <div className="flex items-center gap-2 mb-3">
        {STEPS.map((_, idx) => (
          <div
            key={idx}
            className={`h-1 flex-1 rounded-full transition-colors ${
              idx <= currentStep ? 'bg-white/60' : 'bg-white/15'
            }`}
          />
        ))}
      </div>

      <AnimatePresence mode="wait">
        <motion.div
          key={step.id}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -20 }}
          transition={{ duration: 0.25 }}
        >
          <p className="text-sm text-white/80 mb-3 font-medium">{step.question}</p>
          <div className="grid grid-cols-2 gap-2">
            {step.options.map((option) => (
              <button
                key={option.id}
                onClick={() => handleOptionSelect(step.id, option.id)}
                className="group bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/30 rounded-lg p-3 text-left transition-all"
              >
                <span className="text-2xl block mb-1">{option.icon}</span>
                <span className="text-sm font-semibold text-white block">{option.label}</span>
                {option.description && (
                  <span className="text-[11px] text-white/50 block mt-0.5">{option.description}</span>
                )}
              </button>
            ))}
          </div>
        </motion.div>
      </AnimatePresence>
    </div>
  );
};

export { KnockInCard };
export default BatFinderQuiz;
