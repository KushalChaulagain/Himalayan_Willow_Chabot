import React, { useState, useMemo } from 'react';

interface WeightSliderProps {
  onSelect: (weight: number) => void;
  playingLevel: string;
}

const MIN = 1000;
const MAX = 1300;
const STEP = 10;

function getWeightLabel(weight: number): string {
  if (weight < 1080) return 'Ultra Light';
  if (weight < 1120) return 'Light';
  if (weight < 1180) return 'Balanced';
  if (weight < 1230) return 'Heavy';
  return 'Extra Heavy';
}

function getSweetSpotOffset(weight: number): number {
  const range = MAX - MIN;
  const normalized = (weight - MIN) / range;
  return 15 + normalized * 50;
}

const WeightSlider: React.FC<WeightSliderProps> = ({ onSelect, playingLevel }) => {
  const defaultWeight = playingLevel === 'beginner' ? 1080 : playingLevel === 'professional' ? 1180 : 1140;
  const [weight, setWeight] = useState(defaultWeight);

  const label = useMemo(() => getWeightLabel(weight), [weight]);
  const sweetSpotTop = useMemo(() => getSweetSpotOffset(weight), [weight]);
  const percent = ((weight - MIN) / (MAX - MIN)) * 100;

  return (
    <div className="bg-white/5 border border-white/10 rounded-lg p-4">
      <p className="text-sm text-white/80 font-medium mb-4">
        Preferred bat weight? Slide to set your ideal pickup.
      </p>

      <div className="flex gap-4 items-center">
        {/* Bat SVG with moving sweet spot */}
        <div className="relative w-10 h-48 flex-shrink-0">
          <svg viewBox="0 0 40 180" className="w-full h-full">
            {/* Bat handle */}
            <rect x="16" y="0" width="8" height="60" rx="3" fill="rgba(255,255,255,0.15)" />
            {/* Bat blade */}
            <rect x="8" y="58" width="24" height="110" rx="4" fill="rgba(255,255,255,0.2)" />
            {/* Sweet spot highlight */}
            <rect
              x="10"
              y={sweetSpotTop + 50}
              width="20"
              height="30"
              rx="4"
              fill="rgba(251,191,36,0.35)"
              className="transition-all duration-200"
            />
            {/* Toe */}
            <rect x="10" y="165" width="20" height="8" rx="3" fill="rgba(255,255,255,0.12)" />
          </svg>
          <span className="absolute -right-1 text-[9px] text-amber-400/80 font-medium whitespace-nowrap"
            style={{ top: `${sweetSpotTop + 55}px` }}
          >
            sweet spot
          </span>
        </div>

        {/* Slider controls */}
        <div className="flex-1 space-y-3">
          <div className="text-center">
            <span className="text-2xl font-bold text-white">{weight}g</span>
            <span className="block text-xs text-amber-400 font-medium mt-0.5">{label}</span>
          </div>

          <input
            type="range"
            min={MIN}
            max={MAX}
            step={STEP}
            value={weight}
            onChange={(e) => setWeight(Number(e.target.value))}
            className="w-full accent-white cursor-pointer"
            aria-label="Bat weight preference"
          />

          <div className="flex justify-between text-[10px] text-white/40">
            <span>More Control</span>
            <span>More Power</span>
          </div>

          {/* Visual bar */}
          <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-blue-400 via-amber-400 to-red-400 rounded-full transition-all duration-150"
              style={{ width: `${percent}%` }}
            />
          </div>

          <button
            onClick={() => onSelect(weight)}
            className="w-full bg-white hover:bg-white/90 text-[#1A1A1A] text-sm py-2 rounded-lg font-semibold transition-colors mt-2"
          >
            Find Bats at {weight}g
          </button>
        </div>
      </div>
    </div>
  );
};

export default WeightSlider;
