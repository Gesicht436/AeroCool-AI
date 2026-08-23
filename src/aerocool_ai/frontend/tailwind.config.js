/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#0B0F17',
        surface: '#111827',
        'surface-card': '#1E293B',
        'surface-border': 'rgba(255, 255, 255, 0.08)',
        accent: {
          cyan: '#38BDF8',
          blue: '#3B82F6',
          indigo: '#6366F1',
          emerald: '#10B981',
          coral: '#F43F5E',
          amber: '#F59E0B',
        },
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
    },
  },
  plugins: [],
}
