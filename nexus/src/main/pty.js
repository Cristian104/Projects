import * as pty from 'node-pty'
import { platform, homedir } from 'os'
import { existsSync } from 'fs'

function getShell() {
  if (platform() === 'win32') return 'powershell.exe'
  
  const preferred = process.env.SHELL
  if (preferred && existsSync(preferred)) return preferred
  
  const fallbacks = ['/bin/bash', '/usr/bin/bash', '/bin/zsh', '/usr/bin/zsh', '/bin/sh']
  for (const f of fallbacks) {
    if (existsSync(f)) return f
  }
  
  return '/bin/sh'
}

const shell = getShell()
console.log(`[pty] Using shell: ${shell}`)

const instances = new Map()

export const ptyManager = {
  create(paneId, cwd, command, args = [], onData) {
    this.kill(paneId)

    const absoluteCwd = cwd || homedir()
    console.log(`[pty] Creating instance ${paneId} in ${absoluteCwd}`)

    // Use -l for login shell, more universal than --login
    const shellArgs = ['-l', '-i']

    try {
      const proc = pty.spawn(shell, shellArgs, {
        name: 'xterm-256color',
        cols: 120,
        rows: 36,
        cwd: absoluteCwd,
        env: {
          ...process.env,
          TERM: 'xterm-256color',
          COLORTERM: 'truecolor'
        }
      })

      proc.onData(onData)

      proc.onExit(({ exitCode, signal }) => {
        console.log(`[pty] Instance ${paneId} exited with code ${exitCode}, signal ${signal}`)
        instances.delete(paneId)
        onData(`\r\n[Process exited with code ${exitCode}${signal ? ` (signal ${signal})` : ''}]\r\n`)
      })

      instances.set(paneId, proc)

      // If a specific CLI command was requested, type it into the shell
      // after it finishes loading (~400ms is enough for bash/zsh init).
      if (command) {
        const cmdStr = args.length > 0
          ? `${command} ${args.join(' ')}`
          : command

        console.log(`[pty] Injecting command: ${cmdStr}`)
        setTimeout(() => {
          const active = instances.get(paneId)
          if (active) {
            active.write(cmdStr + '\r')
          }
        }, 500)
      }

      return { paneId, pid: proc.pid }
    } catch (err) {
      console.error(`[pty] Failed to spawn shell:`, err)
      onData(`\r\n[Failed to spawn shell: ${err.message}]\r\n`)
      return null
    }
  },

  write(paneId, data) {
    const proc = instances.get(paneId)
    if (proc && data) {
      try {
        proc.write(data)
      } catch (err) {
        console.error(`[pty] Write error for ${paneId}:`, err)
      }
    }
  },

  resize(paneId, cols, rows) {
    const proc = instances.get(paneId)
    if (proc) {
      if (!cols || !rows || cols < 1 || rows < 1) return
      try {
        proc.resize(Math.floor(cols), Math.floor(rows))
      } catch (err) {
        console.error(`[pty] Resize error for ${paneId}:`, err)
      }
    }
  },

  kill(paneId) {
    const proc = instances.get(paneId)
    if (proc) {
      console.log(`[pty] Killing instance ${paneId}`)
      try { proc.kill() } catch {}
      instances.delete(paneId)
    }
  },

  killAll() {
    for (const [id] of instances) this.kill(id)
  }
}
