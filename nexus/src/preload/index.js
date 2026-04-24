import { contextBridge, ipcRenderer } from 'electron'

contextBridge.exposeInMainWorld('nexus', {
  // Window controls
  window: {
    minimize: () => ipcRenderer.send('window:minimize'),
    maximize: () => ipcRenderer.send('window:maximize'),
    close: () => ipcRenderer.send('window:close')
  },

  // Project scanner
  scan: {
    projects: () => ipcRenderer.invoke('scan:projects')
  },

  // PTY / terminal
  pty: {
    create: (opts) => ipcRenderer.invoke('pty:create', opts),
    write: (paneId, data) => ipcRenderer.send('pty:write', { paneId, data }),
    resize: (paneId, cols, rows) => ipcRenderer.send('pty:resize', { paneId, cols, rows }),
    kill: (paneId) => ipcRenderer.send('pty:kill', { paneId }),
    onData: (paneId, callback) => {
      const channel = `pty:data:${paneId}`
      ipcRenderer.on(channel, (_, data) => callback(data))
      return () => ipcRenderer.removeAllListeners(channel)
    }
  }
})
