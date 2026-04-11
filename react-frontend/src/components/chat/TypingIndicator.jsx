import { motion } from 'framer-motion';

export default function TypingIndicator() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="mb-6 flex gap-3"
    >
      <div className="astro-glow-cyan flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-cyan-300 to-blue-500 text-slate-900">
        <span className="text-sm font-bold">A</span>
      </div>
      <div className="astro-glass-heavy flex items-center gap-2 rounded-xl border border-white/15 px-4 py-3">
        <span className="text-sm text-slate-100">AstroBot is typing</span>
        <motion.div
          animate={{ opacity: [0.3, 1, 0.3] }}
          transition={{ duration: 1.4, repeat: Infinity }}
          className="flex gap-1"
        >
          <span className="h-2 w-2 rounded-full bg-cyan-200" />
          <span className="h-2 w-2 rounded-full bg-cyan-200" />
          <span className="h-2 w-2 rounded-full bg-cyan-200" />
        </motion.div>
      </div>
    </motion.div>
  );
}
