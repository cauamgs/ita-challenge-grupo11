export function ApprovalIcon({ className = 'h-4 w-4' }: { className?: string }) {
  return (
    <svg viewBox="0 0 20 20" fill="none" className={className} aria-hidden>
      <path
        d="M10 2 3.5 4.5v5c0 4 2.8 7.2 6.5 8.5 3.7-1.3 6.5-4.5 6.5-8.5v-5L10 2Z"
        fill="#F1ECF7"
        stroke="#5E3A85"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
      <path d="M10 6.5v4.2M10 13.2v.3" stroke="#5E3A85" strokeWidth="1.7" strokeLinecap="round" />
    </svg>
  )
}

export function CloseIcon() {
  return (
    <svg viewBox="0 0 20 20" className="h-4 w-4" aria-hidden>
      <path
        d="m5 5 10 10M15 5 5 15"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
      />
    </svg>
  )
}

export function SortIcon({ direction }: { direction: 'asc' | 'desc' | null }) {
  return (
    <span aria-hidden className="ml-1 inline-block w-2 text-[10px] opacity-80">
      {direction === 'asc' ? '▲' : direction === 'desc' ? '▼' : '↕'}
    </span>
  )
}
