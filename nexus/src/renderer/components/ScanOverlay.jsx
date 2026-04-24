import { motion } from 'framer-motion'

export default function ScanOverlay() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 flex flex-col items-center justify-center gap-3 z-40 pointer-events-none"
    >
      <motion.span
        animate={{ rotate: 360 }}
        transition={{ duration: 2.5, repeat: Infinity, ease: 'linear' }}
        className="text-2xl select-none"
        style={{ color: 'rgba(172,199,255,0.3)' }}
      >
        ⬡
      </motion.span>
      <p className="text-[10px] font-mono tracking-widest uppercase" style={{ color: 'rgba(229,225,230,0.2)' }}>
        Scanning for AI projects...
      </p>
    </motion.div>
  )
}
