import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: '#18323a',
        canvas: '#f7faf9',
        teal: {
          50: '#effcf9',
          100: '#d7f7f0',
          500: '#1b9c89',
          600: '#147c6f',
          700: '#12645b',
        },
        coral: '#ef7a68',
      },
      boxShadow: {
        card: '0 18px 48px -28px rgba(24, 50, 58, 0.35)',
      },
    },
  },
  plugins: [],
} satisfies Config
