// Nav rail Eclipse: 64px, só ícones. Monograma da marca no topo (3 barras mint),
// itens principais e Metodologia ancorada na base (mt-auto). Item ativo = quadrado
// mint. Sempre visível (inclusive mobile — é estreito). Labels via aria-label/title.

import { BookOpen, LayoutDashboard, Umbrella, Wallet, type LucideIcon } from 'lucide-react'

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

const RODAPE: ItemDef = { id: 'metodologia', label: 'Metodologia', Icone: BookOpen }

export function NavRail({ aba, onSelect }: { aba: Aba; onSelect: (a: Aba) => void }) {
  return (
    <aside className="flex w-16 shrink-0 flex-col items-center gap-2 border-r border-hairline bg-chrome py-[18px]">
      <div
        className="mb-3.5 flex h-[26px] items-end gap-[2.5px] rounded-lg border border-brand/35 bg-brand/15 p-1.5"
        aria-hidden="true"
      >
        <span className="block w-[3px] rounded-sm bg-brand" style={{ height: 7 }} />
        <span className="block w-[3px] rounded-sm bg-brand" style={{ height: 11 }} />
        <span className="block w-[3px] rounded-sm bg-brand" style={{ height: 15 }} />
      </div>

      {PRINCIPAIS.map((it) => (
        <Item key={it.id} {...it} ativo={aba === it.id} onClick={() => onSelect(it.id)} />
      ))}

      <Item
        {...RODAPE}
        ativo={aba === RODAPE.id}
        onClick={() => onSelect(RODAPE.id)}
        className="mt-auto"
      />
    </aside>
  )
}

function Item({
  label,
  Icone,
  ativo,
  onClick,
  className = '',
}: ItemDef & { ativo: boolean; onClick: () => void; className?: string }) {
  return (
    <button
      onClick={onClick}
      aria-label={label}
      aria-current={ativo ? 'page' : undefined}
      title={label}
      className={`flex h-10 w-10 items-center justify-center rounded-[11px] border transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-brand/60 ${
        ativo
          ? 'border-brand/30 bg-brand/10 text-brand'
          : 'border-transparent text-content-muted hover:bg-surface hover:text-content-body'
      } ${className}`}
    >
      <Icone size={18} aria-hidden="true" />
    </button>
  )
}
