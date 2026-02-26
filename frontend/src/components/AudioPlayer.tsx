import React, { useState, useRef, useEffect } from 'react';

interface AudioPlayerProps {
  src: string;
  label?: string;
}

const AudioPlayer: React.FC<AudioPlayerProps> = ({ src, label = 'Bat Ping' }) => {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [playing, setPlaying] = useState(false);
  const [barHeights, setBarHeights] = useState([3, 5, 7, 4]);

  useEffect(() => {
    if (!playing) return;

    const interval = setInterval(() => {
      setBarHeights([
        2 + Math.random() * 10,
        2 + Math.random() * 10,
        2 + Math.random() * 10,
        2 + Math.random() * 10,
      ]);
    }, 150);

    return () => clearInterval(interval);
  }, [playing]);

  const toggle = () => {
    if (!audioRef.current) {
      audioRef.current = new Audio(src);
      audioRef.current.addEventListener('ended', () => setPlaying(false));
    }

    if (playing) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      setPlaying(false);
    } else {
      audioRef.current.play().then(() => setPlaying(true)).catch(() => {});
    }
  };

  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, []);

  return (
    <button
      onClick={toggle}
      className="flex items-center gap-1.5 bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/20 rounded-md px-2 py-1 transition-colors group"
      aria-label={playing ? 'Stop audio' : `Play ${label}`}
    >
      {/* Play / stop icon */}
      {playing ? (
        <svg className="w-3 h-3 text-amber-400" fill="currentColor" viewBox="0 0 24 24">
          <rect x="6" y="4" width="4" height="16" rx="1" />
          <rect x="14" y="4" width="4" height="16" rx="1" />
        </svg>
      ) : (
        <svg className="w-3 h-3 text-amber-400" fill="currentColor" viewBox="0 0 24 24">
          <path d="M8 5v14l11-7z" />
        </svg>
      )}

      {/* Waveform bars */}
      <div className="flex items-end gap-[2px] h-3">
        {barHeights.map((h, i) => (
          <div
            key={i}
            className="w-[3px] rounded-full bg-amber-400 transition-all duration-150"
            style={{ height: playing ? `${h}px` : '3px' }}
          />
        ))}
      </div>

      <span className="text-[10px] text-amber-400/80 font-medium">{label}</span>
    </button>
  );
};

export default AudioPlayer;
