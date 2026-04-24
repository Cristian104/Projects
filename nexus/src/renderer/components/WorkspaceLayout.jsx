import { AnimatePresence, motion } from 'framer-motion'
import TerminalPane from './TerminalPane.jsx'

// Grid configs for 1-4 panes
const GRID_STYLES = {
  1: { gridTemplateColumns: '1fr', gridTemplateRows: '1fr' },
  2: { gridTemplateColumns: '1fr 1fr', gridTemplateRows: '1fr' },
  3: { gridTemplateColumns: '1fr 1fr', gridTemplateRows: '1fr 1fr' }, // 2+1
  4: { gridTemplateColumns: '1fr 1fr', gridTemplateRows: '1fr 1fr' }
}

export default function WorkspaceLayout({ panes, onClosePane }) {
  const count = panes.length
  const gridStyle = GRID_STYLES[Math.min(count, 4)] || GRID_STYLES[4]

  return (
    <motion.div 
      layout
      className="h-full w-full p-2 grid gap-2" 
      style={gridStyle}
    >
      <AnimatePresence mode="popLayout">
        {panes.map((pane, i) => (
          <motion.div
            key={pane.id}
            layout
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.8, filter: 'blur(10px)' }}
            transition={{ 
              type: 'spring',
              stiffness: 350,
              damping: 35,
              opacity: { duration: 0.2 }
            }}
            // 3-pane: last item spans full width
            style={count === 3 && i === 2 ? { gridColumn: '1 / -1' } : {}}
            className="min-h-0 min-w-0"
          >
            <TerminalPane
              pane={pane}
              onClose={() => onClosePane(pane.id)}
            />
          </motion.div>
        ))}
      </AnimatePresence>
    </motion.div>
  )
}
