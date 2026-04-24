export default function Titlebar() {
  return (
    <header
      className="drag-region flex items-center justify-between px-4 h-11 shrink-0 z-50"
      style={{
        background: 'rgba(19, 19, 22, 0.92)',
        backdropFilter: 'blur(20px)',
        borderBottom: '1px solid rgba(66, 71, 83, 0.25)'
      }}
    >
      {/* Traffic lights — left side */}
      <div className="no-drag flex items-center gap-2 group">
        <TrafficLight color="#ff5f56" onClick={() => window.nexus.window.close()} />
        <TrafficLight color="#ffbd2e" onClick={() => window.nexus.window.minimize()} />
        <TrafficLight color="#27c93f" onClick={() => window.nexus.window.maximize()} />
      </div>

      {/* App name — centered */}
      <div className="flex items-center gap-2 select-none">
        <span className="text-base" style={{ color: 'rgba(172, 199, 255, 0.5)' }}>⬡</span>
        <span className="text-xs font-black tracking-[-0.02em]" style={{ color: 'rgba(229, 225, 230, 0.5)' }}>
          NEXUS
        </span>
      </div>

      {/* Right spacer to keep name centered */}
      <div className="w-16" />
    </header>
  )
}

function TrafficLight({ color, onClick }) {
  return (
    <button
      onClick={onClick}
      className="w-3 h-3 rounded-full transition-opacity opacity-40 hover:opacity-100 no-drag"
      style={{ background: color }}
    />
  )
}
