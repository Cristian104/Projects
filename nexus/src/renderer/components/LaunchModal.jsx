import { motion, AnimatePresence } from 'framer-motion'
import { useState } from 'react'

const CLI_COLORS = { claude: '#cc785c', gemini: '#4f8ef7' }

const LAUNCH_OPTIONS = {
  claude: [
    { mode: 'normal',   label: 'New Session',       cmd: 'claude',                                     args: [] },
    { mode: 'yolo',     label: 'Skip Permissions',   cmd: 'claude --dangerously-skip-permissions',      args: ['--dangerously-skip-permissions'] },
    { mode: 'continue', label: 'Continue Last',       cmd: 'claude --continue',                          args: ['--continue'] },
  ],
  gemini: [
    { mode: 'normal',   label: 'New Session',        cmd: 'gemini',                                     args: [] },
    { mode: 'yolo',     label: 'Yolo',               cmd: 'gemini --yolo',                              args: ['--yolo'] },
    { mode: 'continue', label: 'Continue Last',       cmd: 'gemini --resume',                            args: ['--resume'] },
  ]
}

export default function LaunchModal({ project, onLaunch, onClose }) {
  const hasBoth      = project.cli === 'both' || project.hasGemini
  const clis         = hasBoth ? ['claude', 'gemini'] : [project.cli || 'claude']
  const [selectedCli, setSelectedCli]     = useState(clis[0])
  const [showResume,  setShowResume]      = useState(false)

  const conversations = project.conversations || []
  const color = CLI_COLORS[selectedCli]

  function launch(mode, resumeId = null) {
    const base = LAUNCH_OPTIONS[selectedCli].find(o => o.mode === mode)
    let args = [...base.args]
    if (resumeId) args = ['--resume', resumeId]
    onLaunch({ project, cli: selectedCli, mode, command: selectedCli, args })
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.15 }}
      className="fixed inset-0 flex items-center justify-center z-50"
      style={{ background: 'rgba(0,0,0,0.65)', backdropFilter: 'blur(10px)' }}
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.96, y: 6, opacity: 0 }}
        animate={{ scale: 1,    y: 0, opacity: 1 }}
        exit={{    scale: 0.96, y: 6, opacity: 0 }}
        transition={{ type: 'spring', stiffness: 450, damping: 32 }}
        className="w-[310px] p-5 space-y-4"
        style={{
          background: 'rgba(19, 19, 22, 0.97)',
          border: '1px solid rgba(66,71,83,0.4)',
          borderRadius: '0.5rem',
          boxShadow: '0 32px 80px rgba(0,0,0,0.7)'
        }}
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div>
          <p className="text-[10px] font-mono mb-1" style={{ color: 'rgba(194,198,213,0.4)' }}>
            Open session in
          </p>
          <h2 className="text-sm font-semibold text-on-surface truncate">{project.displayPath}</h2>
        </div>

        {/* CLI toggle */}
        {clis.length > 1 && (
          <div className="flex gap-2">
            {clis.map(cli => {
              const active = selectedCli === cli
              const c = CLI_COLORS[cli]
              return (
                <button
                  key={cli}
                  onClick={() => { setSelectedCli(cli); setShowResume(false) }}
                  className="flex-1 py-1.5 text-xs font-medium transition-all"
                  style={{
                    background: active ? `${c}18` : 'rgba(42,42,45,0.6)',
                    border: `1px solid ${active ? c + '44' : 'rgba(66,71,83,0.3)'}`,
                    color:  active ? c : 'rgba(229,225,230,0.35)',
                    borderRadius: '0.125rem'
                  }}
                >
                  {cli === 'claude' ? '◆ Claude' : '✦ Gemini'}
                </button>
              )
            })}
          </div>
        )}

        {/* Launch options */}
        <AnimatePresence mode="wait">
          {!showResume ? (
            <motion.div
              key="options"
              initial={{ opacity: 0, x: -6 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -6 }}
              className="space-y-1.5"
            >
              {LAUNCH_OPTIONS[selectedCli].map(opt => (
                <button
                  key={opt.mode}
                  onClick={() => opt.mode === 'continue' && conversations.length > 1
                    ? setShowResume(true)
                    : launch(opt.mode)
                  }
                  className="w-full flex items-center justify-between px-3 py-2.5 text-left transition-colors"
                  style={{
                    background: 'rgba(42,42,45,0.5)',
                    border: '1px solid rgba(66,71,83,0.2)',
                    borderRadius: '0.125rem'
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = 'rgba(53,52,56,0.8)'}
                  onMouseLeave={e => e.currentTarget.style.background = 'rgba(42,42,45,0.5)'}
                >
                  <div>
                    <div className="text-xs font-medium" style={{ color: opt.mode === 'continue' ? color : '#e5e1e6' }}>
                      {opt.label}
                    </div>
                    <div className="text-[10px] font-mono mt-0.5" style={{ color: 'rgba(194,198,213,0.35)' }}>
                      {opt.cmd}
                    </div>
                  </div>
                  <span className="text-xs" style={{ color: 'rgba(229,225,230,0.2)' }}>
                    {opt.mode === 'continue' && conversations.length > 1 ? '↓' : '→'}
                  </span>
                </button>
              ))}
            </motion.div>
          ) : (
            <motion.div
              key="resume"
              initial={{ opacity: 0, x: 6 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 6 }}
              className="space-y-1.5"
            >
              <button
                onClick={() => setShowResume(false)}
                className="flex items-center gap-1.5 text-[10px] mb-2 transition-colors"
                style={{ color: 'rgba(194,198,213,0.4)' }}
                onMouseEnter={e => e.currentTarget.style.color = 'rgba(194,198,213,0.7)'}
                onMouseLeave={e => e.currentTarget.style.color = 'rgba(194,198,213,0.4)'}
              >
                ← back
              </button>

              <p className="text-[10px] font-mono mb-2" style={{ color: 'rgba(194,198,213,0.35)' }}>
                Pick a session to resume
              </p>

              <div className="space-y-1 max-h-48 overflow-y-auto">
                {/* Continue last (shortcut) */}
                <button
                  onClick={() => launch('continue')}
                  className="w-full flex items-center justify-between px-3 py-2 text-left transition-colors"
                  style={{
                    background: `${color}12`,
                    border: `1px solid ${color}25`,
                    borderRadius: '0.125rem'
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = `${color}20`}
                  onMouseLeave={e => e.currentTarget.style.background = `${color}12`}
                >
                  <div>
                    <div className="text-xs font-medium" style={{ color }}>Most Recent</div>
                    <div className="text-[10px] font-mono mt-0.5" style={{ color: 'rgba(194,198,213,0.35)' }}>
                      {selectedCli === 'claude' ? '--continue' : '--resume'}
                    </div>
                  </div>
                  <span className="text-xs" style={{ color }}>→</span>
                </button>

                {/* Specific sessions */}
                {conversations.slice(0, 8).map((conv, i) => (
                  <button
                    key={conv.id}
                    onClick={() => launch('resume', conv.id)}
                    className="w-full flex items-center justify-between px-3 py-2 text-left transition-colors"
                    style={{
                      background: 'rgba(42,42,45,0.5)',
                      border: '1px solid rgba(66,71,83,0.2)',
                      borderRadius: '0.125rem'
                    }}
                    onMouseEnter={e => e.currentTarget.style.background = 'rgba(53,52,56,0.8)'}
                    onMouseLeave={e => e.currentTarget.style.background = 'rgba(42,42,45,0.5)'}
                  >
                    <div className="min-w-0 flex-1">
                      <div className="text-[10px] text-on-surface truncate">
                        {conv.preview || `Session ${i + 1}`}
                      </div>
                      <div className="text-[9px] font-mono mt-0.5" style={{ color: 'rgba(194,198,213,0.3)' }}>
                        {conv.timestamp ? new Date(conv.timestamp).toLocaleDateString() : '—'}
                        {' · '}
                        {conv.id.slice(0, 8)}...
                      </div>
                    </div>
                    <span className="text-xs ml-2 shrink-0" style={{ color: 'rgba(229,225,230,0.2)' }}>→</span>
                  </button>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        <button
          onClick={onClose}
          className="w-full text-center text-[10px] transition-colors py-1"
          style={{ color: 'rgba(229,225,230,0.2)' }}
          onMouseEnter={e => e.currentTarget.style.color = 'rgba(229,225,230,0.45)'}
          onMouseLeave={e => e.currentTarget.style.color = 'rgba(229,225,230,0.2)'}
        >
          Cancel
        </button>
      </motion.div>
    </motion.div>
  )
}
