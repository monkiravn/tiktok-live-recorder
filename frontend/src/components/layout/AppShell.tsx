"use client"
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { PropsWithChildren } from 'react'
import { clsx } from 'clsx'

const nav = [
  { href: '/', label: 'Dashboard' },
  { href: '/watchers', label: 'Watchers' },
  { href: '/record', label: 'Record Now' },
  { href: '/jobs', label: 'Jobs' },
  { href: '/files', label: 'Files' },
  { href: '/settings', label: 'Settings' },
]

export default function AppShell({ children }: PropsWithChildren) {
  const pathname = usePathname()

  return (
    <div className="min-h-screen grid grid-cols-[240px_1fr]">
      <aside className="border-r border-gray-200 p-4">
        <div className="font-semibold text-lg mb-4">TikTok Live Recorder</div>
        <nav className="flex flex-col gap-1">
          {nav.map((n) => (
            <Link
              key={n.href}
              href={n.href}
              className={clsx(
                'rounded-md px-3 py-2 text-sm hover:bg-gray-100',
                pathname === n.href ? 'bg-gray-100 font-medium' : 'text-gray-700'
              )}
            >
              {n.label}
            </Link>
          ))}
        </nav>
      </aside>
      <main className="p-6">
        <div className="container">
          {children}
        </div>
      </main>
    </div>
  )
}

