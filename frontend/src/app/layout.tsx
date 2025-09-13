import type { Metadata } from 'next'
import './globals.css'
import Providers from '@/components/Providers'
import AppShell from '@/components/layout/AppShell'

export const metadata: Metadata = {
  title: 'TikTok Live Recorder — Dashboard',
  description: 'Internal dashboard for TikTok Live Recorder',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi">
      <body>
        <Providers>
          <AppShell>{children}</AppShell>
        </Providers>
      </body>
    </html>
  )
}

