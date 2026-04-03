export default function BrainSVG({ 
  size = 80, 
  thinking = { left: false, right: false, corpus: false },
  connected = false 
}: { 
  size?: number; 
  thinking?: { left: boolean; right: boolean; corpus: boolean };
  connected?: boolean;
}) {
  return (
    <svg viewBox="0 0 120 100" width={size} height={size * 0.83} className={connected ? "animate-brainwave" : "opacity-50"}>
      <defs>
        <filter id="glow-cyan-active">
          <feGaussianBlur stdDeviation="3" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
        <filter id="glow-magenta-active">
          <feGaussianBlur stdDeviation="3" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
        <filter id="glow-purple-active">
          <feGaussianBlur stdDeviation="3" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
        <linearGradient id="corpus-grad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#8b5cf6" />
          <stop offset="100%" stopColor="#6d28d9" />
        </linearGradient>
        <linearGradient id="corpus-active-grad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#a855f7" />
          <stop offset="100%" stopColor="#7c3aed" />
        </linearGradient>
      </defs>

      {/* Left Hemisphere - Glowing when thinking */}
      <path
        d="M58 15 C30 12, 8 25, 10 50 C12 72, 30 85, 55 82 C58 80, 58 75, 58 70"
        fill="none"
        stroke={thinking.left ? "#00ffff" : "#00d4ff"}
        strokeWidth={thinking.left ? "2.5" : "1.5"}
        opacity={thinking.left ? "1" : "0.7"}
        filter={thinking.left ? "url(#glow-cyan-active)" : "url(#glow-cyan)"}
        className={thinking.left ? "animate-pulse-glow" : ""}
      />
      {/* Left brain folds */}
      <path d="M20 30 C30 28, 40 32, 50 30" fill="none" stroke={thinking.left ? "#00ffff" : "#00d4ff"} strokeWidth="0.8" opacity={thinking.left ? "0.8" : "0.4"} />
      <path d="M15 45 C28 42, 40 48, 52 44" fill="none" stroke={thinking.left ? "#00ffff" : "#00d4ff"} strokeWidth="0.8" opacity={thinking.left ? "0.8" : "0.4"} />
      <path d="M18 60 C30 56, 42 62, 52 58" fill="none" stroke={thinking.left ? "#00ffff" : "#00d4ff"} strokeWidth="0.8" opacity={thinking.left ? "0.8" : "0.4"} />
      <path d="M25 72 C35 68, 45 74, 54 70" fill="none" stroke={thinking.left ? "#00ffff" : "#00d4ff"} strokeWidth="0.8" opacity={thinking.left ? "0.6" : "0.3"} />

      {/* Right Hemisphere - Glowing when thinking */}
      <path
        d="M62 15 C90 12, 112 25, 110 50 C108 72, 90 85, 65 82 C62 80, 62 75, 62 70"
        fill="none"
        stroke={thinking.right ? "#ff00ff" : "#ff006e"}
        strokeWidth={thinking.right ? "2.5" : "1.5"}
        opacity={thinking.right ? "1" : "0.7"}
        filter={thinking.right ? "url(#glow-magenta-active)" : "url(#glow-magenta)"}
        className={thinking.right ? "animate-pulse-glow" : ""}
      />
      {/* Right brain folds */}
      <path d="M70 30 C80 28, 90 32, 100 30" fill="none" stroke={thinking.right ? "#ff00ff" : "#ff006e"} strokeWidth="0.8" opacity={thinking.right ? "0.8" : "0.4"} />
      <path d="M68 45 C80 42, 92 48, 105 44" fill="none" stroke={thinking.right ? "#ff00ff" : "#ff006e"} strokeWidth="0.8" opacity={thinking.right ? "0.8" : "0.4"} />
      <path d="M68 60 C80 56, 92 62, 102 58" fill="none" stroke={thinking.right ? "#ff00ff" : "#ff006e"} strokeWidth="0.8" opacity={thinking.right ? "0.8" : "0.4"} />
      <path d="M66 72 C75 68, 85 74, 95 70" fill="none" stroke={thinking.right ? "#ff00ff" : "#ff006e"} strokeWidth="0.8" opacity={thinking.right ? "0.6" : "0.3"} />

      {/* Corpus Callosum - Glowing when synthesizing */}
      <path
        d="M55 40 C57 38, 63 38, 65 40"
        fill="none"
        stroke={thinking.corpus ? "url(#corpus-active-grad)" : "url(#corpus-grad)"}
        strokeWidth={thinking.corpus ? "3.5" : "2.5"}
        opacity={thinking.corpus ? "1" : "0.9"}
        filter={thinking.corpus ? "url(#glow-purple-active)" : undefined}
        className={thinking.corpus ? "animate-pulse-glow" : ""}
      />
      <path
        d="M55 50 C57 48, 63 48, 65 50"
        fill="none"
        stroke={thinking.corpus ? "url(#corpus-active-grad)" : "url(#corpus-grad)"}
        strokeWidth={thinking.corpus ? "3" : "2"}
        opacity={thinking.corpus ? "1" : "0.7"}
      />
      <path
        d="M55 60 C57 58, 63 58, 65 60"
        fill="none"
        stroke={thinking.corpus ? "url(#corpus-active-grad)" : "url(#corpus-grad)"}
        strokeWidth={thinking.corpus ? "3" : "2"}
        opacity={thinking.corpus ? "1" : "0.7"}
      />

      {/* Socket connections - Left */}
      <circle cx="10" cy="50" r={thinking.left ? "4" : "3"} fill={thinking.left ? "#00ffff" : "#00d4ff"} opacity={thinking.left ? "1" : "0.8"} className={thinking.left ? "animate-socket-pulse" : ""} />
      <circle cx="10" cy="50" r="6" fill="none" stroke={thinking.left ? "#00ffff" : "#00d4ff"} strokeWidth="0.5" opacity={thinking.left ? "0.6" : "0.3"} />

      {/* Socket connections - Right */}
      <circle cx="110" cy="50" r={thinking.right ? "4" : "3"} fill={thinking.right ? "#ff00ff" : "#ff006e"} opacity={thinking.right ? "1" : "0.8"} className={thinking.right ? "animate-socket-pulse" : ""} />
      <circle cx="110" cy="50" r="6" fill="none" stroke={thinking.right ? "#ff00ff" : "#ff006e"} strokeWidth="0.5" opacity={thinking.right ? "0.6" : "0.3"} />

      {/* Socket connections - Corpus top */}
      <circle cx="60" cy="30" r={thinking.corpus ? "3.5" : "2.5"} fill="#8b5cf6" opacity={thinking.corpus ? "1" : "0.6"} className={thinking.corpus ? "animate-socket-pulse" : ""} />
      {/* Socket connections - Corpus bottom */}
      <circle cx="60" cy="70" r={thinking.corpus ? "3.5" : "2.5"} fill="#8b5cf6" opacity={thinking.corpus ? "1" : "0.6"} className={thinking.corpus ? "animate-socket-pulse" : ""} />

      {/* Neural activity dots - Left */}
      <circle cx="30" cy="35" r="1.5" fill={thinking.left ? "#00ffff" : "#00d4ff"} opacity={thinking.left ? "1" : "0.6"} className={thinking.left ? "animate-socket-pulse" : ""} style={{ animationDelay: '0.5s' }} />
      <circle cx="40" cy="55" r="1.5" fill={thinking.left ? "#00ffff" : "#00d4ff"} opacity={thinking.left ? "1" : "0.6"} className={thinking.left ? "animate-socket-pulse" : ""} style={{ animationDelay: '1s' }} />
      
      {/* Neural activity dots - Right */}
      <circle cx="90" cy="35" r="1.5" fill={thinking.right ? "#ff00ff" : "#ff006e"} opacity={thinking.right ? "1" : "0.6"} className={thinking.right ? "animate-socket-pulse" : ""} style={{ animationDelay: '0.3s' }} />
      <circle cx="80" cy="55" r="1.5" fill={thinking.right ? "#ff00ff" : "#ff006e"} opacity={thinking.right ? "1" : "0.6"} className={thinking.right ? "animate-socket-pulse" : ""} style={{ animationDelay: '0.8s' }} />

      {/* Connection lines when corpus is active */}
      {thinking.corpus && (
        <>
          <path d="M10 50 Q60 30 60 50" fill="none" stroke="#8b5cf6" strokeWidth="0.5" opacity="0.4" strokeDasharray="2,2" className="animate-pulse" />
          <path d="M110 50 Q60 30 60 50" fill="none" stroke="#8b5cf6" strokeWidth="0.5" opacity="0.4" strokeDasharray="2,2" className="animate-pulse" />
          <path d="M10 50 Q60 70 60 70" fill="none" stroke="#8b5cf6" strokeWidth="0.5" opacity="0.4" strokeDasharray="2,2" className="animate-pulse" />
          <path d="M110 50 Q60 70 60 70" fill="none" stroke="#8b5cf6" strokeWidth="0.5" opacity="0.4" strokeDasharray="2,2" className="animate-pulse" />
        </>
      )}
    </svg>
  );
}
