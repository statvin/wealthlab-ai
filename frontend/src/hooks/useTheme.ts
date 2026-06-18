// Tema atual ('light' | 'dark'), reativo à classe `dark` no <html>. Usado por
// componentes que precisam recalcular cores (gráficos Plotly) ao alternar o tema.

import { useEffect, useState } from 'react'

function lerTema(): 'light' | 'dark' {
  return document.documentElement.classList.contains('dark') ? 'dark' : 'light'
}

export function useTheme(): 'light' | 'dark' {
  const [tema, setTema] = useState<'light' | 'dark'>(lerTema)

  useEffect(() => {
    const obs = new MutationObserver(() => setTema(lerTema()))
    obs.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })
    return () => obs.disconnect()
  }, [])

  return tema
}
