// Campo numérico que NÃO sofre dos vícios do <input type="number"> controlado:
//   - permite ficar VAZIO enquanto se edita (você consegue apagar tudo);
//   - aceita valores parciais como "4." sem "pular" o cursor;
//   - não trava zeros à esquerda ("04").
// Mantém um buffer de texto local; só propaga `onChange` quando o texto é um
// número válido. Resincroniza com o valor externo apenas quando ele muda de
// fato (não a cada tecla), preservando a digitação em andamento.

import { useEffect, useState } from 'react'

interface Props {
  value: number
  onChange: (n: number) => void
  step?: string
  min?: number
  placeholder?: string
  className?: string
}

const parse = (s: string): number => (s.trim() === '' ? NaN : Number(s))

export function NumberField({ value, onChange, step, min, placeholder, className }: Props) {
  const [text, setText] = useState(() => String(value))

  useEffect(() => {
    // Só resincroniza se o valor externo divergir de um número COMPLETO no buffer.
    // (Buffer vazio/parcial → NaN → não mexe, para não atrapalhar a edição.)
    const atual = parse(text)
    if (!Number.isNaN(atual) && atual !== value) {
      setText(String(value))
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value])

  return (
    <input
      type="number"
      inputMode="decimal"
      step={step}
      min={min}
      placeholder={placeholder}
      value={text}
      onChange={(e) => {
        const raw = e.target.value
        setText(raw)
        const n = parse(raw)
        if (!Number.isNaN(n)) onChange(n)
      }}
      onBlur={() => {
        // Ao sair do campo vazio/ inválido, restaura o último valor válido.
        if (Number.isNaN(parse(text))) setText(String(value))
      }}
      className={className}
    />
  )
}
