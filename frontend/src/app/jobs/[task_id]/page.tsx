"use client"
import { useParams } from 'next/navigation'
import { useEffect } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { api, type JobStatusResponse } from '@/lib/api'

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, string> = {
    SUCCESS: 'bg-green-100 text-green-700',
    FAILURE: 'bg-red-100 text-red-700',
    PENDING: 'bg-gray-100 text-gray-700',
    STARTED: 'bg-blue-100 text-blue-700',
    RETRY: 'bg-yellow-100 text-yellow-700',
    REVOKED: 'bg-gray-100 text-gray-700',
  }
  return <span className={`inline-flex items-center px-2 py-1 rounded-md text-xs ${map[status] || 'bg-gray-100 text-gray-700'}`}>{status}</span>
}

export default function JobDetailPage() {
  const params = useParams<{ task_id: string }>()
  const taskId = params.task_id
  const qc = useQueryClient()
  const q = useQuery({ queryKey: ['job', taskId], queryFn: () => api.jobStatus(taskId), refetchInterval: 3000 })

  // Stop polling when terminal
  useEffect(() => {
    if (!q.data) return
    const terminal = ['SUCCESS', 'FAILURE', 'REVOKED']
    if (terminal.includes(q.data.status)) {
      qc.setQueryDefaults(['job', taskId], { refetchInterval: false })
    }
  }, [q.data, qc, taskId])

  const data: JobStatusResponse | undefined = q.data

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-semibold">Job Detail</h1>
        <code className="text-xs bg-gray-100 rounded px-2 py-1">{taskId}</code>
        {data && <StatusBadge status={data.status} />}
      </div>

      {q.isLoading && <div>Loading...</div>}
      {q.isError && <div className="text-red-600">Error loading job</div>}

      {data?.result && (
        <div className="rounded-lg border p-4 space-y-3">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <div className="text-xs text-gray-500">Return code</div>
              <div className="font-medium">{data.result.returncode}</div>
            </div>
            <div>
              <div className="text-xs text-gray-500">Started</div>
              <div className="font-medium">{data.result.started_at || '—'}</div>
            </div>
            <div>
              <div className="text-xs text-gray-500">Ended</div>
              <div className="font-medium">{data.result.ended_at || '—'}</div>
            </div>
          </div>

          {data.result.error_message && (
            <div className="rounded-md bg-red-50 border border-red-200 p-3 text-sm text-red-700">{data.result.error_message}</div>
          )}

          <div>
            <div className="text-sm font-medium mb-2">Files</div>
            {data.result.files.length === 0 ? (
              <div className="text-sm text-gray-500">No files</div>
            ) : (
              <ul className="list-disc pl-5 text-sm">
                {data.result.files.map((f) => (
                  <li key={f} className="break-all">
                    <code>{f}</code>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

