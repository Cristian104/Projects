# Nexus — AI CLI Session Manager

Desktop app (Electron + React) for managing Claude and Gemini CLI sessions visually.

## Stack

- **Electron** — desktop container, frameless transparent window
- **React + Vite** — renderer (via electron-vite)
- **xterm.js** — terminal emulator (`@xterm/xterm`, `@xterm/addon-fit`)
- **node-pty** — real PTY process management
- **Framer Motion** — animations
- **Tailwind CSS** — styling

## Structure

```
src/
  main/
    index.js       ← Electron main process, IPC handlers, window config
    scanner.js     ← Scans ~/.claude/projects/ + filesystem for AI projects
    pty.js         ← node-pty PTY lifecycle management
  preload/
    index.js       ← contextBridge API exposed to renderer
  renderer/
    App.jsx        ← root component, pane state, launch flow
    components/
      Titlebar.jsx       ← frameless window controls
      Sidebar.jsx        ← project list with search
      WorkspaceLayout.jsx← 1/2/3/4 pane grid
      TerminalPane.jsx   ← xterm.js terminal + pane header
      LaunchModal.jsx    ← CLI + mode selector modal
      ScanOverlay.jsx    ← startup scan animation
    styles/
      globals.css        ← Tailwind base + xterm overrides
```

## Dev Commands

```bash
npm install
npm run dev       # Electron + Vite hot reload
npm run build     # Production build
```

## Key Design Decisions

- **Transparent window** (`transparent: true`, `frame: false`) — glassmorphism dark UI
- **Max 4 panes** — CSS grid auto-adjusts layout (1→2→3→4)
- **Scanner strategy:** fast-path from `~/.claude/projects/` index (reverse slug → path),
  then filesystem walk for Gemini / new Claude projects
- **IPC pattern:** main ↔ renderer via contextBridge, PTY data streams per pane ID
- **Colors:** Claude=#cc785c (warm orange), Gemini=#4f8ef7 (blue)

## Launch Modes

| CLI    | Normal | Permissive |
|--------|--------|------------|
| Claude | `claude` | `claude --dangerously-skip-permissions` |
| Gemini | `gemini` | `gemini --yolo` |

## Roadmap

- [ ] Resume specific conversation (`claude --resume <id>`)
- [ ] Pin/favourite projects
- [ ] File watcher for new projects (auto-add without rescan)
- [ ] Per-project remember last launch mode
- [ ] Conversation history panel in sidebar
- [ ] Keybindings (Ctrl+T new pane, Ctrl+W close, Ctrl+1-4 focus)
