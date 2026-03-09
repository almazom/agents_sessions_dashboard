/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Мягкие цвета для дашборда
        nexus: {
          50: '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
          400: '#94a3b8',
          500: '#64748b',
          600: '#475569',
          700: '#334155',
          800: '#1e293b',
          900: '#0f172a',
        },
        // Цвета агентов
        codex: '#10b981',    // зелёный
        kimi: '#f59e0b',     // оранжевый
        gemini: '#3b82f6',   // синий
        qwen: '#8b5cf6',     // фиолетовый
        claude: '#ec4899',   // розовый
        pi: '#06b6d4',       // бирюзовый
      },
    },
  },
  plugins: [],
}
