/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Paleta do tema escuro (fintech).
        base: {
          900: '#0b0f17',
          800: '#121826',
          700: '#1b2333',
          600: '#27314a',
        },
        accent: {
          DEFAULT: '#34d399', // verde
          soft: '#10b981',
        },
      },
    },
  },
  plugins: [],
}
