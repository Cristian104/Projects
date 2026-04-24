import { app, BrowserWindow, ipcMain } from 'electron'
import { join } from 'path'
import { fileURLToPath } from 'url'
import { scanner } from './scanner.js'
import { ptyManager } from './pty.js'

const __dirname = fileURLToPath(new URL('.', import.meta.url))

let mainWindow

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 900,
    minHeight: 600,
    frame: false,
    transparent: true,
    backgroundColor: '#00000000',
    titleBarStyle: 'hidden',
    webPreferences: {
      preload: join(__dirname, '../preload/index.mjs'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false
    },
    show: false
  })

  mainWindow.once('ready-to-show', () => {
    mainWindow.show()
    mainWindow.focus()
    mainWindow.webContents.focus()
  })

  // Dev: load Vite dev server. Prod: load built index.html
  if (process.env.ELECTRON_RENDERER_URL) {
    mainWindow.loadURL(process.env.ELECTRON_RENDERER_URL)
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }
}

// Window controls
ipcMain.on('window:minimize', () => mainWindow.minimize())
ipcMain.on('window:maximize', () => {
  mainWindow.isMaximized() ? mainWindow.unmaximize() : mainWindow.maximize()
})
ipcMain.on('window:close', () => mainWindow.close())

// Scanner IPC
ipcMain.handle('scan:projects', async () => {
  return scanner.scan()
})

// PTY IPC
ipcMain.handle('pty:create', async (_, { paneId, cwd, command, args }) => {
  return ptyManager.create(paneId, cwd, command, args, (data) => {
    mainWindow.webContents.send(`pty:data:${paneId}`, data)
  })
})

ipcMain.on('pty:write', (_, { paneId, data }) => {
  ptyManager.write(paneId, data)
})

ipcMain.on('pty:resize', (_, { paneId, cols, rows }) => {
  ptyManager.resize(paneId, cols, rows)
})

ipcMain.on('pty:kill', (_, { paneId }) => {
  ptyManager.kill(paneId)
})

app.whenReady().then(createWindow)

app.on('window-all-closed', () => {
  ptyManager.killAll()
  if (process.platform !== 'darwin') app.quit()
})

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow()
})
