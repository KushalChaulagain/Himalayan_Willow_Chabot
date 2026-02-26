/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
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
      },
    },
  },
  plugins: [],
};
