import { Link } from 'react-router-dom'

interface BrandLogoProps {
  compact?: boolean
}

export function BrandLogo({ compact = false }: BrandLogoProps) {
  return (
    <Link className="inline-flex items-center gap-3" to="/dashboard">
      <span className="grid h-10 w-10 place-items-center rounded-2xl bg-teal-600 font-black text-white shadow-lg shadow-teal-600/20">
        N
      </span>
      {compact ? null : (
        <span className="text-xl font-extrabold tracking-tight text-ink">
          NCLEX <span className="text-teal-600">Daily</span>
        </span>
      )}
    </Link>
  )
}
