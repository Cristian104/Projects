import { useState, useEffect } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import Titlebar from './components/Titlebar.jsx'
import Sidebar from './components/Sidebar.jsx'
import WorkspaceLayout from './components/WorkspaceLayout.jsx'
import LaunchModal from './components/LaunchModal.jsx'
import ScanOverlay from './components/ScanOverlay.jsx'

export default function App() {
  const [projects, setProjects] = useState([])
  const [scanning, setScanning] = useState(true)
  const [panes, setPanes] = useState([])
  const [launchTarget, setLaunchTarget] = useState(null)

  useEffect(() => {
    window.nexus.scan.projects().then((results) => {
      setProjects(results)
      setScanning(false)
    })
  }, [])

  function handleProjectClick(project) {
    setLaunchTarget(project)
  }

  function handleLaunch({ project, cli, mode, command, args }) {
    setLaunchTarget(null)
    const id = `pane-${Date.now()}`
    const newPane = { id, projectName: project.name, projectPath: project.path, displayPath: project.displayPath, cli, mode, command, args }
    setPanes(prev => prev.length >= 4 ? [...prev.slice(1), newPane] : [...prev, newPane])
  }

  function handleClosePane(paneId) {
    window.nexus.pty.kill(paneId)
    setPanes(prev => prev.filter(p => p.id !== paneId))
  }

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden relative" style={{ background: '#0e0e11' }}>
      {/* Ambient background glows */}
      <div className="bg-glow-claude" />
      <div className="bg-glow-gemini" />

      <Titlebar />

      <div className="flex flex-1 overflow-hidden relative z-10">
        <Sidebar
          projects={projects}
          scanning={scanning}
          activePanes={panes}
          onProjectClick={handleProjectClick}
        />
        <main className="flex-1 overflow-hidden bg-bg p-2">
          {panes.length === 0
            ? <EmptyState scanning={scanning} />
            : <WorkspaceLayout panes={panes} onClosePane={handleClosePane} />
          }
        </main>
      </div>

      <AnimatePresence>
        {scanning && <ScanOverlay />}
      </AnimatePresence>

      <AnimatePresence>
        {launchTarget && (
          <LaunchModal
            project={launchTarget}
            onLaunch={handleLaunch}
            onClose={() => setLaunchTarget(null)}
          />
        )}
      </AnimatePresence>
    </div>
  )
}

function EmptyState({ scanning }) {
  if (scanning) return null
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="flex flex-col items-center justify-center h-full gap-3 select-none"
    >
      <div className="text-4xl text-on-surface opacity-10">⬡</div>
      <p className="text-xs font-medium tracking-widest uppercase text-on-surface opacity-20">
        Select a project to begin
      </p>
    </motion.div>
  )
}
