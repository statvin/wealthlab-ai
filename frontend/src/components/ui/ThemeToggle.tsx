// Alterna entre tema claro e escuro: aplica a classe `dark` no <html> e persiste
// a escolha em localStorage. O padrão (1ª visita) vem do script anti-FOUC no
// index.html (preferência do sistema).

import { useEffect, useState } from 'react'

export function ThemeToggle() {
  const [tema, setTema] = useState<'light' | 'dark'>(() =>
    document.documentElement.classList.contains('dark') ? 'dark' : 'light',
  )

  useEffect(() => {
    document.documentElement.classList.toggle('dark', tema === 'dark')
    try {
      localStorage.setItem('wl-theme', tema)
    } catch {
      /* ignora storage indisponível */
    }
  }, [tema])

  return (
    <button
      type="button"
      onClick={() => setTema((t) => (t === 'dark' ? 'light' : 'dark'))}
      aria-label={tema === 'dark' ? 'Mudar para tema claro' : 'Mudar para tema escuro'}
      className="rounded-lg p-2 text-content-muted transition-colors hover:bg-surface hover:text-content focus:outline-none focus-visible:ring-2 focus-visible:ring-brand/60"
    >
      {tema === 'dark' ? <SolIcon /> : <LuaIcon />}
    </button>
  )
}

function SolIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41" />
    </svg>
  )
}

function LuaIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
    </svg>
  )
}
