import type { ButtonHTMLAttributes } from 'react'

type Variant = 'primary' | 'secondary' | 'approve' | 'edit' | 'postpone' | 'reject' | 'ghost'

const VARIANTS: Record<Variant, string> = {
  primary: 'bg-brand-purple text-white hover:bg-brand-purpleDark',
  secondary: 'bg-brand-lime font-bold text-brand-purpleDark hover:brightness-95',
  approve: 'border border-[#B9DDB0] bg-tag-subir text-ink hover:brightness-95',
  edit: 'border border-[#EAD9A0] bg-tag-revisar text-ink hover:brightness-95',
  postpone: 'border border-[#DDDDDD] bg-tag-manter text-ink hover:brightness-95',
  reject: 'border border-[#F0B8B5] bg-tag-baixar text-ink hover:brightness-95',
  ghost: 'border border-brand-purpleLine bg-surface text-brand-purple hover:bg-brand-purpleLight',
}

// eslint-disable-next-line react-refresh/only-export-components
export function buttonClass(variant: Variant = 'primary', className = ''): string {
  return `inline-flex h-8 items-center justify-center gap-1.5 whitespace-nowrap rounded px-3 text-[13px] font-semibold transition disabled:cursor-not-allowed disabled:opacity-50 ${VARIANTS[variant]} ${className}`
}

export function Button({
  variant = 'primary',
  className = '',
  type = 'button',
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant }) {
  return <button type={type} className={buttonClass(variant, className)} {...props} />
}
