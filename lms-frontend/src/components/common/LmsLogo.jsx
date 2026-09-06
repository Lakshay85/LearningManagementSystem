const LmsLogo = ({ size = 36, className = "" }) => {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 512 512"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={`shrink-0 shadow-md shadow-indigo-950/20 rounded-xl ${className}`}
      aria-label="LMS Enterprise Logo"
    >
      <defs>
        <linearGradient id="lmsBgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#0F172A" />
          <stop offset="50%" stopColor="#1E1B4B" />
          <stop offset="100%" stopColor="#2563EB" />
        </linearGradient>
        <linearGradient id="lmsSparkGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#67E8F9" />
          <stop offset="100%" stopColor="#38BDF8" />
        </linearGradient>
        <linearGradient id="lmsWhiteGrad" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#FFFFFF" />
          <stop offset="100%" stopColor="#E2E8F0" />
        </linearGradient>
        <radialGradient id="lmsCenterGlow" cx="50%" cy="40%" r="50%">
          <stop offset="0%" stopColor="#6366F1" stopOpacity="0.35" />
          <stop offset="100%" stopColor="#6366F1" stopOpacity="0" />
        </radialGradient>
      </defs>

      {/* Squircle Base with ambient glow */}
      <rect x="16" y="16" width="480" height="480" rx="112" fill="url(#lmsBgGrad)" />
      <rect x="16" y="16" width="480" height="480" rx="112" fill="url(#lmsCenterGlow)" />
      <rect
        x="17"
        y="17"
        width="478"
        height="478"
        rx="111"
        fill="none"
        stroke="rgba(255, 255, 255, 0.18)"
        strokeWidth="3"
      />

      {/* EMBLEM: Graduation Mortarboard + Open Pages + AI Spark */}
      <g transform="translate(0, 8)">
        {/* Graduation Cap: Diamond Top */}
        <path d="M 256 96 L 416 176 L 256 256 L 96 176 Z" fill="url(#lmsWhiteGrad)" />

        {/* Cap Underside / Band */}
        <path
          d="M 160 216 L 160 268 C 160 308, 352 308, 352 268 L 352 216 C 324 236, 288 248, 256 248 C 224 248, 188 236, 160 216 Z"
          fill="#CBD5E1"
        />

        {/* Cap Tassel */}
        <path
          d="M 390 190 Q 428 230, 420 280"
          fill="none"
          stroke="url(#lmsSparkGrad)"
          strokeWidth="12"
          strokeLinecap="round"
        />
        <circle cx="420" cy="286" r="14" fill="#38BDF8" />

        {/* Open Knowledge Book Pages */}
        {/* Left Page */}
        <path
          d="M 240 318 C 196 298, 142 306, 106 324 C 98 328, 92 336, 92 346 L 92 414 C 92 422, 100 428, 108 424 C 146 406, 196 400, 240 416 Z"
          fill="url(#lmsWhiteGrad)"
        />

        {/* Right Page */}
        <path
          d="M 272 318 C 316 298, 370 306, 406 324 C 414 328, 420 336, 420 346 L 420 414 C 420 422, 412 428, 404 424 C 366 406, 316 400, 272 416 Z"
          fill="url(#lmsWhiteGrad)"
        />

        {/* Center Spine Accent */}
        <path d="M 256 314 L 256 422" stroke="#60A5FA" strokeWidth="8" strokeLinecap="round" />

        {/* AI Sparkle / Star of Innovation */}
        <path
          d="M 408 82 Q 408 106, 432 106 Q 408 106, 408 130 Q 408 106, 384 106 Q 408 106, 408 82 Z"
          fill="url(#lmsSparkGrad)"
        />
        <circle cx="408" cy="106" r="4" fill="#FFFFFF" />
      </g>
    </svg>
  );
};

export default LmsLogo;
