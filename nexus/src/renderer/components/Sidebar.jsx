import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

const CLI_COLORS = { claude: '#cc785c', gemini: '#4f8ef7', both: '#a78bfa' }

export default function Sidebar({ projects, scanning, activePanes, onProjectClick }) {
  const [search, setSearch] = useState('')

  const filtered = projects.filter(p =>
    p.displayPath.toLowerCase().includes(search.toLowerCase()) ||
    p.name.toLowerCase().includes(search.toLowerCase())
  )

  const activeProjectPaths = new Set(activePanes.map(p => p.projectPath))

  return (
    <aside
      className="w-60 shrink-0 flex flex-col overflow-hidden z-10"
      style={{
        background: 'rgba(27, 27, 30, 0.90)',
        backdropFilter: 'blur(20px)',
        borderRight: '1px solid rgba(66, 71, 83, 0.25)'
      }}
    >
      {/* Search */}
      <div className="px-3 pt-3 pb-2 shrink-0">
        <input
          type="text"
          placeholder="Filter projects..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="w-full text-xs px-3 py-2 outline-none font-mono"
          style={{
            background: '#0e0e11',
            border: '1px solid rgba(66,71,83,0.4)',
            borderRadius: '0.125rem',
            color: 'rgba(229,225,230,0.7)',
          }}
        />
      </div>

      {/* Count */}
      <div className="px-4 pb-2 shrink-0">
        <span className="text-xs font-mono" style={{ color: 'rgba(194,198,213,0.35)' }}>
          {scanning ? 'scanning...' : `${filtered.length} projects`}
        </span>
      </div>

      {/* Project list */}
      <nav className="flex-1 overflow-y-auto px-2 space-y-0.5 pb-4">
        <AnimatePresence>
          {filtered.map((project, i) => (
            <ProjectRow
              key={project.path}
              project={project}
              index={i}
              isActive={activeProjectPaths.has(project.path)}
              onClick={() => onProjectClick(project)}
            />
          ))}
        </AnimatePresence>

        {!scanning && filtered.length === 0 && (
          <p className="text-xs px-2 py-6 text-center" style={{ color: 'rgba(229,225,230,0.2)' }}>
            No projects found
          </p>
        )}
      </nav>

      {/* New session button */}
      <div className="p-3 shrink-0" style={{ borderTop: '1px solid rgba(66,71,83,0.2)' }}>
        <button
          className="w-full py-2 text-xs font-bold tracking-tight transition-opacity hover:opacity-80"
          style={{
            background: '#2a2a2d',
            color: 'rgba(172,199,255,0.7)',
            borderRadius: '0.125rem'
          }}
        >
          + New Session
        </button>
      </div>
    </aside>
  )
}

function ProjectRow({ project, index, isActive, onClick }) {
  const isBoth = project.cli === 'both' || (project.clis && project.clis.length > 1)
  const claudeColor = CLI_COLORS.claude
  const geminiColor = CLI_COLORS.gemini

  return (
    <motion.div
      initial={{ opacity: 0, x: -12 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ 
        delay: index * 0.012, 
        duration: 0.3,
        type: 'spring',
        stiffness: 300,
        damping: 30
      }}
      layout
    >
      <div
        onClick={onClick}
        className="flex items-center justify-between px-3 py-2.5 cursor-pointer transition-all duration-200 group relative"
        style={{
          background: isActive ? 'rgba(42, 42, 45, 0.8)' : 'transparent',
          borderRadius: '0.375rem',
          margin: '0 4px'
        }}
        onMouseEnter={e => { if (!isActive) e.currentTarget.style.background = 'rgba(42,42,45,0.4)' }}
        onMouseLeave={e => { if (!isActive) e.currentTarget.style.background = 'transparent' }}
      >
        {isActive && (
          <motion.div
            layoutId="active-pill"
            className="absolute left-0 w-1 h-4 rounded-r-full"
            style={{ background: isBoth ? `linear-gradient(to bottom, ${claudeColor}, ${geminiColor})` : CLI_COLORS[project.cli] }}
          />
        )}

        <div className="flex flex-col min-w-0 pl-1">
          <div className="flex items-center gap-2">
            {isBoth ? (
              <div className="flex gap-0.5 shrink-0">
                <span className="w-1.5 h-1.5 rounded-full" style={{ background: claudeColor, opacity: isActive ? 1 : 0.6 }} />
                <span className="w-1.5 h-1.5 rounded-full" style={{ background: geminiColor, opacity: isActive ? 1 : 0.6 }} />
              </div>
            ) : (
              <span
                className="w-1.5 h-1.5 rounded-full shrink-0"
                style={{ background: CLI_COLORS[project.cli] || claudeColor, opacity: isActive ? 1 : 0.5 }}
              />
            )}
            <span
              className="text-xs font-semibold tracking-tight truncate transition-colors"
              style={{ color: isActive ? '#fff' : 'rgba(229,225,230,0.5)' }}
            >
              {project.name}
            </span>
          </div>
          <span
            className="text-[10px] font-mono mt-0.5 truncate pl-3.5 opacity-40 group-hover:opacity-70 transition-opacity"
            style={{ color: 'rgba(194,198,213,1)' }}
          >
            {project.displayPath}
          </span>
        </div>

        {isActive && (
          <motion.div 
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            className="w-1 h-1 rounded-full shrink-0 ml-2" 
            style={{ background: isBoth ? geminiColor : CLI_COLORS[project.cli] }} 
          />
        )}
      </div>
    </motion.div>
  )
}
