import { useEffect, useRef, useState } from 'react'
import { Terminal } from '@xterm/xterm'
import { FitAddon } from '@xterm/addon-fit'
import { WebLinksAddon } from '@xterm/addon-web-links'
import { motion, AnimatePresence } from 'framer-motion'
import '@xterm/xterm/css/xterm.css'

const CLI_COLORS  = { claude: '#cc785c', gemini: '#4f8ef7' }
const CLI_ICONS   = { claude: '◆', gemini: '✦' }
const MODE_LABELS = { yolo: { claude: 'skip-perms', gemini: '--yolo' } }

export default function TerminalPane({ pane, onClose }) {
  const containerRef = useRef(null)
  const termRef      = useRef(null)
  const fitRef       = useRef(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const term = new Terminal({
      disableStdin: false,
      theme: {
        background:          'transparent',
        foreground:          'rgba(229,225,230,0.9)',
        cursor:              '#acc7ff',
        cursorAccent:        '#0e0e11',
        selectionBackground: 'rgba(172,199,255,0.15)',
        black:   '#1b1b1e', red:     '#ffb4ab', green:   '#27c93f',
        yellow:  '#ffbd2e', blue:    '#4f8ef7', magenta: '#c678dd',
        cyan:    '#56b6c2', white:   'rgba(229,225,230,0.85)',
        brightBlack: 'rgba(229,225,230,0.3)', brightWhite: '#ffffff',
      },
      fontFamily: '"JetBrains Mono", "Fira Code", monospace',
      fontSize:   12,
      lineHeight: 1.6,
      cursorBlink: true,
      cursorStyle: 'bar',
      allowTransparency: true,
      scrollback: 5000,
    })

    const fitAddon = new FitAddon()
    term.loadAddon(fitAddon)
    term.loadAddon(new WebLinksAddon())
    termRef.current = term
    fitRef.current  = fitAddon

    let ptyStarted = false
    let cleanupPty = () => {}
    let rafId = null

    // Wait until the container has real layout dimensions before opening
    // xterm — calling open() on a 0×0 element crashes its Viewport and
    // silently breaks keyboard input.
    function tryOpen() {
      const el = containerRef.current
      if (!el) return

      const { width, height } = el.getBoundingClientRect()
      if (width === 0 || height === 0) {
        rafId = requestAnimationFrame(tryOpen)
        return
      }

      if (term._disposed) return
      term.open(el)
      fitAddon.fit()

      // Focus the textarea xterm uses for input
      el.querySelector('textarea')?.focus({ preventScroll: true })

      if (!ptyStarted) {
        ptyStarted = true

        window.nexus.pty.create({
          paneId:  pane.id,
          cwd:     pane.projectPath,
          command: pane.command,
          args:    pane.args
        })

        // First data from PTY → hide loading overlay
        let firstData = true
        cleanupPty = window.nexus.pty.onData(pane.id, data => {
          if (firstData) {
            firstData = false
            setLoading(false)
          }
          term.write(data)
        })

        term.onData(data => window.nexus.pty.write(pane.id, data))
      }
    }

    rafId = requestAnimationFrame(tryOpen)

    // Re-focus xterm when window regains focus
    const onWindowFocus = () =>
      containerRef.current?.querySelector('textarea')?.focus({ preventScroll: true })
    window.addEventListener('focus', onWindowFocus)

    // Resize
    const observer = new ResizeObserver(() => {
      if (!fitRef.current || !termRef.current || termRef.current._disposed) return
      try {
        fitRef.current.fit()
        const { cols, rows } = termRef.current
        if (cols > 0 && rows > 0) {
          window.nexus.pty.resize(pane.id, cols, rows)
        }
      } catch {}
    })
    if (containerRef.current) observer.observe(containerRef.current)

    return () => {
      if (rafId) cancelAnimationFrame(rafId)
      cleanupPty()
      observer.disconnect()
      window.removeEventListener('focus', onWindowFocus)
      term.dispose()
      if (termRef.current) termRef.current._disposed = true
      window.nexus.pty.kill(pane.id)
    }
  }, [pane.id])

  const color     = CLI_COLORS[pane.cli] || CLI_COLORS.claude
  const icon      = CLI_ICONS[pane.cli]  || '◆'
  const modeLabel = pane.mode === 'yolo' ? (MODE_LABELS.yolo[pane.cli] || 'yolo') : null

  return (
    <div
      className="flex flex-col h-full overflow-hidden relative"
      style={{ background: 'rgba(19,19,22,0.70)', border: '1px solid rgba(66,71,83,0.2)', borderRadius: '0.25rem' }}
    >
      {/* Pane header */}
      <div
        className="flex items-center justify-between px-3 py-1.5 shrink-0"
        style={{ background: 'rgba(42,42,45,0.80)', borderBottom: '1px solid rgba(66,71,83,0.15)' }}
      >
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-xs shrink-0" style={{ color }}>{icon}</span>
          <span className="text-xs font-bold text-on-surface truncate">{pane.projectName}</span>
          <span className="text-[10px] font-mono truncate" style={{ color: 'rgba(194,198,213,0.4)' }}>
            {pane.displayPath}
          </span>
          {modeLabel && (
            <span className="text-[9px] font-mono px-1.5 py-0.5 shrink-0"
              style={{ background: `${color}18`, color, border: `1px solid ${color}30`, borderRadius: '0.125rem' }}>
              {modeLabel}
            </span>
          )}
          {/* Loading indicator in header */}
          <AnimatePresence>
            {loading && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex items-center gap-1"
              >
                {[0, 1, 2].map(i => (
                  <motion.span
                    key={i}
                    className="block w-1 h-1 rounded-full"
                    style={{ background: color }}
                    animate={{ opacity: [0.2, 1, 0.2] }}
                    transition={{ duration: 1.2, repeat: Infinity, delay: i * 0.2 }}
                  />
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
        <button onClick={onClose} className="text-[10px] shrink-0 ml-2 px-1 transition-colors"
          style={{ color: 'rgba(229,225,230,0.2)' }}
          onMouseEnter={e => e.currentTarget.style.color = '#ffb4ab'}
          onMouseLeave={e => e.currentTarget.style.color = 'rgba(229,225,230,0.2)'}>
          ✕
        </button>
      </div>

      {/* Terminal area */}
      <div
        ref={containerRef}
        onMouseDown={() => containerRef.current?.querySelector('textarea')?.focus({ preventScroll: true })}
        style={{ flex: 1, minHeight: 0, cursor: 'text', overflow: 'hidden' }}
      />

      {/* Full-pane loading overlay — fades out when first PTY data arrives */}
      <AnimatePresence>
        {loading && (
          <motion.div
            initial={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.6, ease: 'easeInOut' }}
            className="absolute inset-0 flex flex-col items-center justify-center gap-4 pointer-events-none z-20"
            style={{ background: 'rgba(13,13,16,0.96)', top: '32px', backdropFilter: 'blur(4px)' }}
          >
            {/* Pulsing ring around the icon */}
            <div className="relative flex items-center justify-center">
              <motion.div
                animate={{ scale: [1, 1.5, 1], opacity: [0.3, 0, 0.3] }}
                transition={{ duration: 2, repeat: Infinity, ease: 'easeOut' }}
                className="absolute w-12 h-12 rounded-full border"
                style={{ borderColor: color }}
              />
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 8, repeat: Infinity, ease: 'linear' }}
                className="absolute w-16 h-16 rounded-full border border-dashed opacity-10"
                style={{ borderColor: color }}
              />
              <motion.div
                animate={{ scale: [0.9, 1.1, 0.9] }}
                transition={{ duration: 1.6, repeat: Infinity, ease: 'easeInOut' }}
                className="text-4xl select-none relative z-10"
                style={{ color, textShadow: `0 0 20px ${color}44` }}
              >
                {icon}
              </motion.div>
            </div>

            <div className="flex flex-col items-center gap-2">
              <div className="flex items-center gap-1.5">
                {[0, 1, 2].map(i => (
                  <motion.span
                    key={i}
                    className="block w-1.5 h-1.5 rounded-full"
                    style={{ background: color }}
                    animate={{ 
                      opacity: [0.15, 1, 0.15], 
                      scale: [0.8, 1.2, 0.8],
                      y: [0, -4, 0]
                    }}
                    transition={{ 
                      duration: 1, 
                      repeat: Infinity, 
                      delay: i * 0.15, 
                      ease: 'easeInOut' 
                    }}
                  />
                ))}
              </div>

              <motion.span 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-[11px] font-mono tracking-[0.2em] uppercase"
                style={{ color: 'rgba(194,198,213,0.5)' }}
              >
                Initializing {pane.cli}
              </motion.span>
              
              <LoadingSubtext cli={pane.cli} />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

function LoadingSubtext({ cli }) {
  const [text, setText] = useState('Starting shell...')
  
  useEffect(() => {
    const sequence = [
      'Starting shell...',
      `Loading ${cli} environment...`,
      'Configuring terminal...',
      'Readying session...'
    ]
    let i = 0
    const interval = setInterval(() => {
      i = (i + 1) % sequence.length
      setText(sequence[i])
    }, 1200)
    return () => clearInterval(interval)
  }, [cli])

  return (
    <motion.span 
      key={text}
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -4 }}
      className="text-[9px] font-mono"
      style={{ color: 'rgba(194,198,213,0.25)' }}
    >
      {text}
    </motion.span>
  )
}
