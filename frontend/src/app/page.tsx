"use client"
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'

function HealthChip({ label, ok }: { label: string; ok: boolean }) {
  return (
    <span className={`inline-flex items-center px-2 py-1 rounded-md text-xs ${ok ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
      <span className={`mr-1 h-2 w-2 rounded-full ${ok ? 'bg-green-500' : 'bg-red-500'}`} /> {label}: {ok ? 'OK' : 'DOWN'}
    </span>
  )
}

export default function DashboardPage() {
  const health = useQuery({ queryKey: ['healthz'], queryFn: api.healthz, retry: 1, refetchInterval: 10000 })
  const ready = useQuery({ queryKey: ['ready'], queryFn: api.ready, retry: 1, refetchInterval: 10000 })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <div className="flex gap-2">
          <HealthChip label="API" ok={health.isSuccess && health.data === 'ok'} />
          <HealthChip label="Workers" ok={ready.isSuccess && ready.data === 'ready'} />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        {["Active Watchers", "Running Jobs", "Success 24h", "Failures 24h"].map((t) => (
          <div key={t} className="rounded-lg border p-4">
            <div className="text-sm text-gray-500">{t}</div>
            <div className="mt-2 text-3xl font-bold">—</div>
          </div>
        ))}
      </div>

      <div className="rounded-lg border p-6">
        <div className="text-sm text-gray-500 mb-2">Jobs per hour (placeholder)</div>
        <div className="h-40 grid place-items-center text-gray-400">Chart coming soon</div>
      </div>
    </div>
  )
}

