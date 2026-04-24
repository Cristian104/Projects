/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/renderer/**/*.{js,jsx,html}'],
  theme: {
    extend: {
      colors: {
        // Surface hierarchy — from Stitch design
        bg:                    '#0e0e11',
        surface:               '#131316',
        'surface-low':         '#1b1b1e',
        'surface-high':        '#2a2a2d',
        'surface-highest':     '#353438',
        'surface-bright':      '#39393c',
        // Text
        'on-surface':          '#e5e1e6',
        'on-surface-dim':      '#c2c6d5',
        // Borders
        outline:               '#8c909e',
        'outline-dim':         '#424753',
        // CLI accent colors
        claude:                '#cc785c',
        'claude-dim':          'rgba(204,120,92,0.15)',
        gemini:                '#4f8ef7',
        'gemini-dim':          'rgba(79,142,247,0.15)',
        // Errors
        error:                 '#ffb4ab',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', '"Fira Code"', 'monospace']
      },
      borderRadius: {
        DEFAULT: '0.125rem',
        sm:      '0.125rem',
        md:      '0.25rem',
        lg:      '0.375rem',
        xl:      '0.5rem',
        '2xl':   '0.75rem',
      },
      backdropBlur: {
        xs: '4px',
        glass: '20px'
      }
    }
  },
  plugins: []
}
