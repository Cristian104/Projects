import { readdir } from 'fs/promises'
import { join } from 'path'
import { homedir } from 'os'
import { existsSync, readdirSync, readFileSync } from 'fs'

const HOME = homedir()

// Directories to skip during scan
const SKIP_DIRS = new Set([
  'node_modules', '.git', 'dist', 'build', 'out', '__pycache__',
  '.cache', '.npm', '.nvm', '.cargo', '.rustup', 'vendor',
  'venv', '.venv', 'env', '.env', 'proc', 'sys', 'dev',
  'Library', 'Applications', 'Music', 'Movies', 'Pictures',
  '.Trash', 'snap', 'flatpak'
])

const MAX_DEPTH = 5

/**
 * Reverse-map ~/.claude/projects slugs to real filesystem paths.
 * Claude converts /home/user/foo/bar → -home-user-foo-bar
 */
function getClaudeProjects() {
  const claudeProjectsDir = join(HOME, '.claude', 'projects')
  if (!existsSync(claudeProjectsDir)) return []

  const projects = []

  try {
    const slugs = readdirSync(claudeProjectsDir)

    for (const slug of slugs) {
      // Convert slug back to path: -home-jorg-stacks → /home/jorg/stacks
      const realPath = slug.replace(/^-/, '/').replace(/-/g, '/')
      const conversations = getConversationsForProject(join(claudeProjectsDir, slug))

      if (conversations.length > 0) {
        projects.push({
          path: realPath,
          name: realPath.split('/').filter(Boolean).pop() || realPath,
          displayPath: realPath.replace(HOME, '~'),
          cli: 'claude',
          source: 'claude-index',
          conversations,
          lastActive: conversations[0]?.timestamp || null
        })
      }
    }
  } catch (e) {
    console.error('Claude project scan error:', e)
  }

  return projects
}

function getConversationsForProject(projectDir) {
  const conversations = []

  try {
    const files = readdirSync(projectDir)
    const jsonlFiles = files.filter(f => f.endsWith('.jsonl'))

    for (const file of jsonlFiles) {
      const filePath = join(projectDir, file)
      try {
        const content = readFileSync(filePath, 'utf8')
        const lines = content.trim().split('\n').filter(Boolean)
        if (lines.length === 0) continue

        // Get first user message for preview
        let preview = ''
        let timestamp = null

        for (const line of lines) {
          try {
            const entry = JSON.parse(line)
            if (entry.timestamp && !timestamp) timestamp = entry.timestamp
            if (entry.type === 'user' && entry.message?.content && !preview) {
              const content = entry.message.content
              preview = typeof content === 'string'
                ? content.slice(0, 80)
                : Array.isArray(content)
                  ? content.find(c => c.type === 'text')?.text?.slice(0, 80) || ''
                  : ''
            }
          } catch {}
        }

        conversations.push({
          id: file.replace('.jsonl', ''),
          file: filePath,
          preview: preview || '(no preview)',
          timestamp: timestamp ? new Date(timestamp) : null,
          messageCount: lines.length
        })
      } catch {}
    }
  } catch {}

  // Sort by most recent first
  return conversations.sort((a, b) => {
    if (!a.timestamp) return 1
    if (!b.timestamp) return -1
    return b.timestamp - a.timestamp
  })
}

/**
 * Walk the filesystem from HOME looking for CLAUDE.md or .gemini/ markers
 */
async function walkForMarkers(dir, depth = 0, results = []) {
  if (depth > MAX_DEPTH) return results

  let entries
  try {
    entries = await readdir(dir, { withFileTypes: true })
  } catch {
    return results
  }

  let hasClaude = false
  let hasGemini = false

  for (const entry of entries) {
    if (entry.name === 'CLAUDE.md') hasClaude = true
    if (entry.name === '.gemini' && entry.isDirectory()) hasGemini = true
    if (entry.name === 'GEMINI.md') hasGemini = true
  }

  if (hasClaude || hasGemini) {
    const clis = []
    if (hasClaude) clis.push('claude')
    if (hasGemini) clis.push('gemini')

    results.push({
      path: dir,
      name: dir.split('/').filter(Boolean).pop(),
      displayPath: dir.replace(HOME, '~'),
      cli: clis.length === 1 ? clis[0] : 'both',
      clis,
      source: 'filesystem',
      conversations: [],
      lastActive: null
    })
  }

  // Recurse into subdirectories
  for (const entry of entries) {
    if (!entry.isDirectory()) continue
    if (SKIP_DIRS.has(entry.name)) continue
    if (entry.name.startsWith('.') && entry.name !== '.gemini') continue

    await walkForMarkers(join(dir, entry.name), depth + 1, results)
  }

  return results
}

export const scanner = {
  async scan() {
    console.log('[scanner] Starting project scan...')

    // Fast path: Claude projects from index
    const claudeProjects = getClaudeProjects()
    const claudePaths = new Set(claudeProjects.map(p => p.path))

    // Filesystem walk for Gemini + any Claude projects not in index
    const fsProjects = await walkForMarkers(HOME)

    // Merge: filesystem walk may add Gemini projects or Claude projects
    // that don't have conversations yet
    const merged = [...claudeProjects]

    for (const fsp of fsProjects) {
      const existing = merged.find(p => p.path === fsp.path)
      if (existing) {
        // Enrich with filesystem-detected CLI info
        if (fsp.clis?.includes('gemini')) {
          existing.hasGemini = true
        }
      } else {
        merged.push(fsp)
      }
    }

    // Sort: most recently active first
    merged.sort((a, b) => {
      if (!a.lastActive) return 1
      if (!b.lastActive) return -1
      return new Date(b.lastActive) - new Date(a.lastActive)
    })

    console.log(`[scanner] Found ${merged.length} projects`)
    return merged
  }
}
