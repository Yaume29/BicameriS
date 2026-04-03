export default function BrainSVG({ size = 80 }: { size?: number }) {
  return (
    <svg viewBox="0 0 120 100" width={size} height={size * 0.83} className="animate-brainwave">
      <defs>
        <filter id="glow-cyan">
          <feGaussianBlur stdDeviation="2" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
        <filter id="glow-magenta">
          <feGaussianBlur stdDeviation="2" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
        <linearGradient id="corpus-grad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#8b5cf6" />
          <stop offset="100%" stopColor="#6d28d9" />
        </linearGradient>
      </defs>

      <path
        d="M58 15 C30 12, 8 25, 10 50 C12 72, 30 85, 55 82 C58 80, 58 75, 58 70"
        fill="none"
        stroke="#00d4ff"
        strokeWidth="1.5"
        opacity="0.7"
        filter="url(#glow-cyan)"
      />
      <path d="M20 30 C30 28, 40 32, 50 30" fill="none" stroke="#00d4ff" strokeWidth="0.8" opacity="0.4" />
      <path d="M15 45 C28 42, 40 48, 52 44" fill="none" stroke="#00d4ff" strokeWidth="0.8" opacity="0.4" />
      <path d="M18 60 C30 56, 42 62, 52 58" fill="none" stroke="#00d4ff" strokeWidth="0.8" opacity="0.4" />
      <path d="M25 72 C35 68, 45 74, 54 70" fill="none" stroke="#00d4ff" strokeWidth="0.8" opacity="0.3" />

      <path
        d="M62 15 C90 12, 112 25, 110 50 C108 72, 90 85, 65 82 C62 80, 62 75, 62 70"
        fill="none"
        stroke="#ff006e"
        strokeWidth="1.5"
        opacity="0.7"
        filter="url(#glow-magenta)"
      />
      <path d="M70 30 C80 28, 90 32, 100 30" fill="none" stroke="#ff006e" strokeWidth="0.8" opacity="0.4" />
      <path d="M68 45 C80 42, 92 48, 105 44" fill="none" stroke="#ff006e" strokeWidth="0.8" opacity="0.4" />
      <path d="M68 60 C80 56, 92 62, 102 58" fill="none" stroke="#ff006e" strokeWidth="0.8" opacity="0.4" />
      <path d="M66 72 C75 68, 85 74, 95 70" fill="none" stroke="#ff006e" strokeWidth="0.8" opacity="0.3" />

      <path
        d="M55 40 C57 38, 63 38, 65 40"
        fill="none"
        stroke="url(#corpus-grad)"
        strokeWidth="2.5"
        opacity="0.9"
      />
      <path
        d="M55 50 C57 48, 63 48, 65 50"
        fill="none"
        stroke="url(#corpus-grad)"
        strokeWidth="2"
        opacity="0.7"
      />
      <path
        d="M55 60 C57 58, 63 58, 65 60"
        fill="none"
        stroke="url(#corpus-grad)"
        strokeWidth="2"
        opacity="0.7"
      />

      <circle cx="10" cy="50" r="3" fill="#00d4ff" opacity="0.8" className="animate-socket-pulse" />
      <circle cx="10" cy="50" r="6" fill="none" stroke="#00d4ff" strokeWidth="0.5" opacity="0.3" />

      <circle cx="110" cy="50" r="3" fill="#ff006e" opacity="0.8" className="animate-socket-pulse" />
      <circle cx="110" cy="50" r="6" fill="none" stroke="#ff006e" strokeWidth="0.5" opacity="0.3" />

      <circle cx="60" cy="30" r="2.5" fill="#8b5cf6" opacity="0.6" className="animate-socket-pulse" />
      <circle cx="60" cy="70" r="2.5" fill="#8b5cf6" opacity="0.6" className="animate-socket-pulse" />

      <circle cx="30" cy="35" r="1.5" fill="#00d4ff" opacity="0.6" className="animate-socket-pulse" style={{ animationDelay: '0.5s' }} />
      <circle cx="40" cy="55" r="1.5" fill="#00d4ff" opacity="0.6" className="animate-socket-pulse" style={{ animationDelay: '1s' }} />
      <circle cx="90" cy="35" r="1.5" fill="#ff006e" opacity="0.6" className="animate-socket-pulse" style={{ animationDelay: '0.3s' }} />
      <circle cx="80" cy="55" r="1.5" fill="#ff006e" opacity="0.6" className="animate-socket-pulse" style={{ animationDelay: '0.8s' }} />
    </svg>
  );
}
