import { motion } from 'framer-motion';

/**
 * LoadingIndicator displays a circular spinner animation
 * while the output is being prepared from the backend.
 * 
 * Design: Circular SVG spinner with smooth rotation,
 * accompanied by "Output is getting ready..." text.
 * Maintains visual consistency with AstroBot's design system.
 */
export default function TypingIndicator() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="mb-6 flex gap-3"
    >
      {/* Bot Avatar */}
      <div className="astro-glow-cyan flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-cyan-300 to-blue-500 text-slate-900">
        <span className="text-sm font-bold">A</span>
      </div>

      {/* Loading Container */}
      <div className="astro-glass-heavy flex items-center gap-3 rounded-xl border border-white/15 px-4 py-3">
        {/* Circular Spinner Animation */}
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
          className="flex-shrink-0"
        >
          <svg
            className="h-5 w-5 text-cyan-300"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth="2.5"
          >
            <circle
              cx="12"
              cy="12"
              r="9"
              stroke="currentColor"
              strokeOpacity="0.2"
            />
            <path
              stroke="currentColor"
              strokeLinecap="round"
              d="M12 3a9 9 0 0 1 0 18"
            />
          </svg>
        </motion.div>

        {/* Loading Text */}
        <span className="text-sm text-slate-100">
          Output is getting ready
          <motion.span
            animate={{ opacity: [0.3, 1, 0.3] }}
            transition={{ duration: 1.4, repeat: Infinity }}
          >
            ...
          </motion.span>
        </span>
      </div>
    </motion.div>
  );
}
