/** @type {import('tailwindcss').Config} */

// Tokens semânticos mapeados para CSS variables (canais RGB), o que permite
// opacidade no Tailwind e troca de valor entre tema claro (:root) e escuro (.dark).
const tok = (name) => `rgb(var(${name}) / <alpha-value>)`

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        canvas: tok('--canvas'),
        surface: tok('--surface'),
        'surface-raised': tok('--surface-raised'),
        chrome: tok('--chrome'),
        border: tok('--border'),
        hairline: tok('--hairline'),
        content: tok('--content'),
        'content-body': tok('--content-body'),
        'content-muted': tok('--content-muted'),
        'content-subtle': tok('--content-subtle'),
        brand: tok('--brand'),
        'brand-strong': tok('--brand-strong'),
        'on-brand': tok('--on-brand'),
        // Semânticos de DADO (só colados a valores): ganho/perda.
        gain: tok('--gain'),
        loss: tok('--loss'),
        // Estados auxiliares (badges/insights/erros de UI).
        warning: tok('--warning'),
        info: tok('--info'),
      },
      fontFamily: {
        sans: ['Space Grotesk Variable', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
