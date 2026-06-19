// Barra de navegação à esquerda (a moldura do app). No desktop fica fixa; no
// mobile vira um drawer. Marca + itens com ícone; Metodologia num grupo
// "referência" mais quieto (é documentação). Toggle de tema no rodapé.

import { BookOpen, LayoutDashboard, Umbrella, Wallet, type LucideIcon } from 'lucide-react'

import { ThemeToggle } from './ui/ThemeToggle'

export type Aba = 'dashboard' | 'carteira' | 'aposentadoria' | 'metodologia'

interface ItemDef {
  id: Aba
  label: string
  Icone: LucideIcon
}

const PRINCIPAIS: ItemDef[] = [
  { id: 'dashboard', label: 'Dashboard', Icone: LayoutDashboard },
  { id: 'carteira', label: 'Carteira', Icone: Wallet },
  { id: 'aposentadoria', label: 'Aposentadoria', Icone: Umbrella },
]

const REFERENCIA: ItemDef[] = [{ id: 'metodologia', label: 'Metodologia', Icone: BookOpen }]

interface Props {
  aba: Aba
  onSelect: (a: Aba) => void
  open: boolean
  onClose: () => void
}

export function NavRail({ aba, onSelect, open, onClose }: Props) {
  const escolher = (a: Aba) => {
    onSelect(a)
    onClose()
  }

  const conteudo = (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-2.5 px-5 py-5">
        <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand text-sm font-bold text-on-brand">
          W
        </span>
        <span className="text-base">
          <span className="font-semibold text-content">WealthLab</span>{' '}
          <span className="font-light text-content-muted">AI</span>
        </span>
      </div>

      <nav className="flex-1 space-y-1 px-3" aria-label="Navegação principal">
        {PRINCIPAIS.map((it) => (
          <Item key={it.id} {...it} ativo={aba === it.id} onClick={() => escolher(it.id)} />
        ))}
        <p className="px-3 pb-1 pt-5 text-[11px] uppercase tracking-wider text-content-subtle">
          Referência
        </p>
        {REFERENCIA.map((it) => (
          <Item key={it.id} {...it} ativo={aba === it.id} onClick={() => escolher(it.id)} />
        ))}
      </nav>

      <div className="flex items-center justify-between border-t border-border px-4 py-3">
        <span className="text-xs text-content-subtle">Conta · em breve</span>
        <ThemeToggle />
      </div>
    </div>
  )

  return (
    <>
      {/* Desktop: rail fixo. */}
      <aside className="hidden w-[212px] shrink-0 border-r border-border bg-surface lg:block">
        {conteudo}
      </aside>

      {/* Mobile: drawer. */}
      {open && (
        <div className="fixed inset-0 z-40 lg:hidden" role="dialog" aria-modal="true">
          <div className="absolute inset-0 bg-black/40" onClick={onClose} aria-hidden="true" />
          <aside className="absolute left-0 top-0 h-full w-[260px] max-w-[85vw] border-r border-border bg-surface">
            {conteudo}
          </aside>
        </div>
      )}
    </>
  )
}

function Item({ label, Icone, ativo, onClick }: ItemDef & { ativo: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      aria-current={ativo ? 'page' : undefined}
      className={`flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-brand/60 ${
        ativo ? 'bg-brand/10 font-medium text-brand' : 'text-content-body hover:bg-canvas'
      }`}
    >
      <Icone size={18} aria-hidden="true" />
      {label}
    </button>
  )
}
