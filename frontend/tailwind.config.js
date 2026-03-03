/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    screens: {
      xs: "400px",
      sm: "640px",
      md: "768px",
      lg: "1024px",
      xl: "1280px",
      "2xl": "1536px",
    },
    extend: {
      colors: {
        primary: {
          DEFAULT: '#1A1A1A',
          50: '#f5f5f5',
          100: '#e5e5e5',
          200: '#cccccc',
          300: '#b3b3b3',
          400: '#808080',
          500: '#4d4d4d',
          600: '#333333',
          700: '#262626',
          800: '#1A1A1A',
          900: '#0d0d0d',
        },
        accent: {
          white: '#FFFFFF',
          silver: '#C0C0C0',
          gold: '#D4AF37',
          red: '#C41E3A',
          'deep-blue': '#1e3a5f',
          'forest-green': '#228B22',
        },
        cta: {
          green: '#22c55e',
          'green-hover': '#16a34a',
          red: '#dc2626',
          'red-hover': '#b91c1c',
        },
        cricket: {
          green: '#228B22',
          brown: '#8b4513',
        },
      },
      fontFamily: {
        sans: ['Inter', 'Roboto', 'system-ui', 'sans-serif'],
        heading: ['Montserrat', 'Inter', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        sharp: '4px',
        card: '6px',
        button: '6px',
      },
      borderWidth: {
        subtle: '1px',
      },
      lineHeight: {
        relaxed: '1.625',
        loose: '1.75',
      },
      boxShadow: {
        subtle: '0 1px 2px 0 rgb(0 0 0 / 0.04)',
        card: '0 1px 3px 0 rgb(0 0 0 / 0.06)',
        default: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
        'card-2': '0 4px 6px -1px rgb(0 0 0 / 0.15), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
        /* Premium depth system */
        'premium-sm': '0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.08)',
        'premium': '0 4px 12px rgba(0,0,0,0.15), 0 2px 6px rgba(0,0,0,0.08)',
        'premium-lg': '0 12px 28px rgba(0,0,0,0.2), 0 4px 12px rgba(0,0,0,0.1)',
        'premium-glow': '0 0 24px rgba(245,158,11,0.15)',
      },
      borderColor: {
        stroke: 'rgba(255, 255, 255, 0.1)',
        strokedark: 'rgba(255, 255, 255, 0.05)',
      },
      spacing: {
        'safe-top': 'env(safe-area-inset-top)',
        'safe-bottom': 'env(safe-area-inset-bottom)',
        'safe-left': 'env(safe-area-inset-left)',
        'safe-right': 'env(safe-area-inset-right)',
      },
      maxWidth: {
        'chat': '44rem',
      },
      animation: {
        'fade-in': 'fadeIn 0.2s ease-out',
        'slide-up': 'slideUp 0.25s ease-out',
      },
      keyframes: {
        fadeIn: { '0%': { opacity: '0' }, '100%': { opacity: '1' } },
        slideUp: { '0%': { opacity: '0', transform: 'translateY(8px)' }, '100%': { opacity: '1', transform: 'translateY(0)' } },
      },
    },
  },
  plugins: [],
};
