import React, { useEffect, useRef, useState } from "react";
import { useChatContext } from "../contexts/ChatContext";

export interface CricketFilters {
  category?: string;
  willow_type?: string;
  weight_range?: string;
  player_level?: string;
}

const CATEGORIES = [
  { id: "bat", label: "Bats", icon: "🏏" },
  { id: "ball", label: "Balls & Accessories", icon: "⚾" },
  { id: "gloves", label: "Gloves", icon: "🧤" },
  { id: "pads", label: "Pads", icon: "🦵" },
  { id: "helmet", label: "Helmets", icon: "⛑️" },
  { id: "shoes", label: "Shoes", icon: "👟" },
  { id: "kit_bag", label: "Kit Bags", icon: "🎒" },
];

const WILLOW_TYPES = [
  { id: "Kashmir Willow", label: "Kashmir Willow" },
  { id: "English Willow", label: "English Willow" },
];

const WEIGHT_RANGES = [
  { id: "1000-1100", label: "1000–1100g (Light)" },
  { id: "1100-1200", label: "1100–1200g (Medium)" },
  { id: "1200-1300", label: "1200–1300g (Heavy)" },
];

const PLAYER_LEVELS = [
  { id: "Beginner", label: "Beginner" },
  { id: "Intermediate", label: "Intermediate" },
  { id: "Professional", label: "Professional" },
];

interface CricketFilterMegaMenuProps {
  open: boolean;
  onClose: () => void;
  anchorRef: React.RefObject<HTMLElement | null>;
}

const CricketFilterMegaMenu: React.FC<CricketFilterMegaMenuProps> = ({
  open,
  onClose,
  anchorRef,
}) => {
  const { sendMessage } = useChatContext();
  const [filters, setFilters] = useState<CricketFilters>({});
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        open &&
        menuRef.current &&
        !menuRef.current.contains(e.target as Node) &&
        anchorRef.current &&
        !anchorRef.current.contains(e.target as Node)
      ) {
        onClose();
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [open, onClose, anchorRef]);

  const buildSearchMessage = (): string => {
    const parts: string[] = [];
    if (filters.category) {
      const cat = CATEGORIES.find((c) => c.id === filters.category);
      parts.push(cat?.label.toLowerCase() || filters.category);
    }
    if (filters.willow_type) {
      parts.push(filters.willow_type.toLowerCase());
    }
    if (filters.weight_range) {
      parts.push(`bats ${filters.weight_range}g`);
    }
    if (filters.player_level) {
      parts.push(`for ${filters.player_level.toLowerCase()}s`);
    }
    if (parts.length === 0) return "Show me products";
    return `Show me ${parts.join(" ")}`;
  };

  const handleApply = () => {
    const msg = buildSearchMessage();
    sendMessage(msg, true);
    onClose();
  };

  const handleClear = () => {
    setFilters({});
  };

  if (!open) return null;

  return (
    <div
      ref={menuRef}
      className="absolute left-1/2 -translate-x-1/2 top-full mt-1 z-50 min-w-[340px] w-[380px] max-w-[min(90vw,420px)] bg-[#262626] border border-white/15 rounded-xl shadow-xl overflow-hidden"
      role="dialog"
      aria-label="Cricket filters"
    >
      <div className="p-4 max-h-[70vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h4 className="text-sm font-bold text-white uppercase tracking-wide">
            Filter by
          </h4>
          <button
            onClick={handleClear}
            className="text-xs text-white/60 hover:text-white transition-colors"
          >
            Clear all
          </button>
        </div>

        {/* Category */}
        <section className="mb-4">
          <h5 className="text-xs text-white/50 font-medium mb-2">Category</h5>
          <div className="flex flex-wrap gap-1.5">
            {CATEGORIES.map((c) => (
              <button
                key={c.id}
                onClick={() =>
                  setFilters((f) => ({
                    ...f,
                    category: f.category === c.id ? undefined : c.id,
                  }))
                }
                className={`px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors min-h-[44px] ${
                  filters.category === c.id
                    ? "bg-amber-500/20 border border-amber-500/50 text-amber-400"
                    : "bg-white/5 border border-white/10 text-white/80 hover:bg-white/10"
                }`}
              >
                {c.icon} {c.label}
              </button>
            ))}
          </div>
        </section>

        {/* For Bats: Willow type, Weight, Player level */}
        {(filters.category === "bat" || !filters.category) && (
          <>
            <section className="mb-4">
              <h5 className="text-xs text-white/50 font-medium mb-2">
                Willow type
              </h5>
              <div className="flex flex-wrap gap-1.5">
                {WILLOW_TYPES.map((w) => (
                  <button
                    key={w.id}
                    onClick={() =>
                      setFilters((f) => ({
                        ...f,
                        willow_type: f.willow_type === w.id ? undefined : w.id,
                      }))
                    }
                    className={`px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors min-h-[44px] ${
                      filters.willow_type === w.id
                        ? "bg-amber-500/20 border border-amber-500/50 text-amber-400"
                        : "bg-white/5 border border-white/10 text-white/80 hover:bg-white/10"
                    }`}
                  >
                    {w.label}
                  </button>
                ))}
              </div>
            </section>

            <section className="mb-4">
              <h5 className="text-xs text-white/50 font-medium mb-2">
                Bat weight
              </h5>
              <div className="flex flex-wrap gap-1.5">
                {WEIGHT_RANGES.map((r) => (
                  <button
                    key={r.id}
                    onClick={() =>
                      setFilters((f) => ({
                        ...f,
                        weight_range:
                          f.weight_range === r.id ? undefined : r.id,
                      }))
                    }
                    className={`px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors min-h-[44px] ${
                      filters.weight_range === r.id
                        ? "bg-amber-500/20 border border-amber-500/50 text-amber-400"
                        : "bg-white/5 border border-white/10 text-white/80 hover:bg-white/10"
                    }`}
                  >
                    {r.label}
                  </button>
                ))}
              </div>
            </section>

            <section className="mb-4">
              <h5 className="text-xs text-white/50 font-medium mb-2">
                Player level
              </h5>
              <div className="flex flex-wrap gap-1.5">
                {PLAYER_LEVELS.map((l) => (
                  <button
                    key={l.id}
                    onClick={() =>
                      setFilters((f) => ({
                        ...f,
                        player_level:
                          f.player_level === l.id ? undefined : l.id,
                      }))
                    }
                    className={`px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors min-h-[44px] ${
                      filters.player_level === l.id
                        ? "bg-amber-500/20 border border-amber-500/50 text-amber-400"
                        : "bg-white/5 border border-white/10 text-white/80 hover:bg-white/10"
                    }`}
                  >
                    {l.label}
                  </button>
                ))}
              </div>
            </section>
          </>
        )}
      </div>

      <div className="p-4 border-t border-white/10 flex gap-2">
        <button
          onClick={onClose}
          className="flex-1 py-2.5 rounded-lg border border-white/20 text-white text-sm font-medium hover:bg-white/10 transition-colors min-h-[44px]"
        >
          Cancel
        </button>
        <button
          onClick={handleApply}
          className="flex-1 py-2.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-[#1A1A1A] text-sm font-bold transition-colors min-h-[44px]"
        >
          Apply filters
        </button>
      </div>
    </div>
  );
};

export default CricketFilterMegaMenu;
