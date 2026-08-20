interface AppIconProps {
  name: 'home' | 'progress' | 'practice' | 'review' | 'profile' | 'arrow' | 'check'
  className?: string
}

const paths: Record<AppIconProps['name'], string> = {
  home: 'M3 10.5 12 3l9 7.5V21a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1V10.5Z',
  progress: 'M4 19V9m8 10V4m8 15v-7',
  practice: 'M8 5h8m-8 5h8m-8 5h5M6 2h12a2 2 0 0 1 2 2v16a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2Z',
  review: 'M4 4h16v14H7l-3 3V4Zm4 5h8m-8 4h5',
  profile: 'M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8Zm7 10a7 7 0 0 0-14 0',
  arrow: 'm9 18 6-6-6-6',
  check: 'm5 12 4 4L19 6',
}

export function AppIcon({ name, className = 'h-5 w-5' }: AppIconProps) {
  return (
    <svg
      aria-hidden="true"
      className={className}
      fill="none"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="2"
      viewBox="0 0 24 24"
    >
      <path d={paths[name]} />
    </svg>
  )
}
