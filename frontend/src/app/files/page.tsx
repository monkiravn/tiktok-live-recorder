"use client"
import { useSearchParams, useRouter } from 'next/navigation'
import { useQuery, keepPreviousData } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { formatBytes } from '@/lib/utils'
import { Suspense, useMemo } from 'react'

function FilesView() {
  const sp = useSearchParams()
  const router = useRouter()
  const page = Number(sp.get('page') || 1)
  const page_size = Number(sp.get('page_size') || 20)
  const room_id = sp.get('room_id') || ''

  const q = useQuery({
    queryKey: ['files', { page, page_size, room_id }],
    queryFn: () => api.listFiles({ page, page_size, room_id: room_id || undefined }),
    placeholderData: keepPreviousData,
  })

  const totalPages = useMemo(() => (q.data ? Math.max(1, Math.ceil(q.data.total / q.data.page_size)) : 1), [q.data])

  function setParam(k: string, v: string | number | null) {
    const url = new URL(window.location.href)
    if (v === null || v === '' || v === 0) url.searchParams.delete(k)
    else url.searchParams.set(k, String(v))
    router.push(url.pathname + url.search)
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Files</h1>

      <div className="rounded-md border p-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <div>
            <label className="block text-sm font-medium">Room ID</label>
            <input className="mt-1 w-full rounded-md border px-3 py-2" value={room_id} onChange={(e) => setParam('room_id', e.target.value)} />
          </div>
          <div>
            <label className="block text-sm font-medium">Page size</label>
            <input
              type="number"
              className="mt-1 w-full rounded-md border px-3 py-2"
              value={page_size}
              onChange={(e) => setParam('page_size', e.target.value)}
              min={1}
              max={200}
            />
          </div>
          <div className="self-end">
            <button className="rounded-md border px-3 py-2" onClick={() => setParam('page', 1)}>
              Apply Filters
            </button>
          </div>
        </div>
      </div>

      <div className="rounded-lg border overflow-hidden">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left p-2">Name</th>
              <th className="text-left p-2">Size</th>
              <th className="text-left p-2">Modified</th>
              <th className="text-left p-2">Path</th>
            </tr>
          </thead>
        {q.isLoading ? (
          <tbody>
            <tr>
              <td className="p-3" colSpan={4}>Loading...</td>
            </tr>
          </tbody>
        ) : q.isError ? (
          <tbody>
            <tr>
              <td className="p-3 text-red-600" colSpan={4}>Failed to load files</td>
            </tr>
          </tbody>
        ) : (
          <tbody>
            {q.data?.items?.length ? (
              q.data.items.map((it) => (
                <tr key={it.path} className="border-t">
                  <td className="p-2 break-all">{it.name}</td>
                  <td className="p-2">{formatBytes(it.size)}</td>
                  <td className="p-2">{new Date(it.mtime * 1000).toLocaleString()}</td>
                  <td className="p-2 break-all">
                    <code>{it.path}</code>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td className="p-3 text-gray-500" colSpan={4}>No files</td>
              </tr>
            )}
          </tbody>
        )}
        </table>
      </div>

      <div className="flex items-center gap-2">
        <button className="rounded-md border px-3 py-2" disabled={page <= 1} onClick={() => setParam('page', page - 1)}>
          Previous
        </button>
        <div className="text-sm">
          Page {page} / {totalPages}
        </div>
        <button className="rounded-md border px-3 py-2" disabled={page >= totalPages} onClick={() => setParam('page', page + 1)}>
          Next
        </button>
      </div>
    </div>
  )
}

export default function FilesPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <FilesView />
    </Suspense>
  )
}
