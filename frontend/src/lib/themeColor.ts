// Lê uma CSS variable de cor (canais RGB espaço-separados, ex.: "246 244 239")
// e devolve uma string rgb()/rgba() — para passar cores do tema atual ao Plotly,
// que não entende CSS variables nativamente.

export function cssRGB(varName: string, alpha = 1): string {
  if (typeof document === 'undefined') return `rgba(0,0,0,${alpha})`
  const raw = getComputedStyle(document.documentElement).getPropertyValue(varName).trim()
  const parts = raw.split(/\s+/)
  if (parts.length < 3) return `rgba(0,0,0,${alpha})`
  const [r, g, b] = parts
  return alpha >= 1 ? `rgb(${r}, ${g}, ${b})` : `rgba(${r}, ${g}, ${b}, ${alpha})`
}
