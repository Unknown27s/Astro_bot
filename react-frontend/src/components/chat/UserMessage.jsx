import { motion } from 'framer-motion';

export default function UserMessage({ content, timestamp }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="flex justify-end"
    >
      <div className="max-w-[85%] space-y-2 md:max-w-[75%]">
        <div className="flex items-center justify-end gap-2">
          {timestamp && (
            <span className="text-xs text-slate-300">
              {new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </span>
          )}
          <span className="font-astro-headline text-xs font-bold tracking-wide text-cyan-100">YOU</span>
        </div>

        <div className="rounded-2xl rounded-br-sm bg-gradient-to-br from-blue-500/95 via-cyan-500/90 to-emerald-500/85 px-4 py-3 text-sm text-white shadow-lg shadow-cyan-500/20 md:px-5 md:py-4 md:text-[15px]">
          <p className="break-words leading-relaxed">{content}</p>
        </div>
      </div>
    </motion.div>
  );
}
