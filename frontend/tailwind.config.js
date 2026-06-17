/** @type {import('tailwindcss').Config} */

// Tinta profunda levemente quente — base do tema (private wealth, não trading).
// Mais degraus de superfície para haver hierarquia real (fundo < card < elevado).
const ink = {
  950: '#0A0E14',
  900: '#0F141C',
  850: '#141B26',
  800: '#1A2230',
  700: '#232D3F',
  600: '#2E3A50',
}

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        ink,
        // Alias: os componentes atuais usam `base-*`. Mantê-lo apontando para
        // `ink` torna a migração não-destrutiva — nada quebra, e a paleta já
        // melhora. A troca base→ink acontece fase a fase.
        base: ink,
        accent: {
          DEFAULT: '#2DD4A7', // verde-petróleo sóbrio (confiança > euforia)
          soft: '#14B88A',
          dim: '#0E6F57',
        },
        semantic: {
          success: '#34D399',
          warning: '#FBBF24',
          danger: '#FB7185',
          info: '#60A5FA',
        },
      },
      fontFamily: {
        sans: ['Inter Variable', 'Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
