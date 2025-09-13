"use client"
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { api, type CreateWatcherRequest } from '@/lib/api'

const schema = z
  .object({
    room_id: z.string().trim().optional().nullable(),
    url: z.string().trim().url().optional().nullable(),
    poll_interval: z.coerce.number().int().min(10).default(60),
    proxy: z.string().trim().optional().nullable(),
    cookies: z.string().trim().optional().nullable(),
  })
  .refine((d) => (d.room_id && !d.url) || (d.url && !d.room_id), {
    message: 'Cần nhập room_id hoặc url (chỉ một trong hai)',
    path: ['room_id'],
  })

type FormData = z.infer<typeof schema>

export default function WatchersPage() {
  const [msg, setMsg] = useState<string | null>(null)
  const [err, setErr] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({ resolver: zodResolver(schema), defaultValues: { poll_interval: 60 } })

  async function onSubmit(values: FormData) {
    setMsg(null)
    setErr(null)
    const payload: CreateWatcherRequest = {
      room_id: values.room_id || undefined,
      url: values.url || undefined,
      poll_interval: values.poll_interval,
      options: { proxy: values.proxy || undefined, cookies: values.cookies || undefined },
    }
    try {
      await api.createWatcher(payload)
      setMsg('Tạo watcher thành công')
      reset({ room_id: '', url: '', poll_interval: 60, proxy: '', cookies: '' })
    } catch (e: any) {
      setErr(e?.error_message || e?.message || 'Tạo watcher thất bại')
    }
  }

  const [delKey, setDelKey] = useState('')
  const [delMsg, setDelMsg] = useState<string | null>(null)
  const [delErr, setDelErr] = useState<string | null>(null)
  const [delBusy, setDelBusy] = useState(false)
  async function doDelete() {
    setDelMsg(null)
    setDelErr(null)
    setDelBusy(true)
    try {
      await api.deleteWatcher(delKey)
      setDelMsg('Đã xóa watcher')
      setDelKey('')
    } catch (e: any) {
      setDelErr(e?.error_message || e?.message || 'Xóa watcher thất bại')
    } finally {
      setDelBusy(false)
    }
  }

  return (
    <div className="space-y-6 max-w-3xl">
      <h1 className="text-2xl font-semibold">Watchers</h1>

      <div className="rounded-lg border p-4 space-y-3">
        <h2 className="font-medium">Tạo watcher</h2>
        <form onSubmit={handleSubmit(onSubmit)} className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium">Room ID</label>
            <input className="mt-1 w-full rounded-md border px-3 py-2" {...register('room_id')} />
            {errors.room_id && <p className="text-sm text-red-600 mt-1">{errors.room_id.message}</p>}
          </div>
          <div>
            <label className="block text-sm font-medium">URL</label>
            <input className="mt-1 w-full rounded-md border px-3 py-2" {...register('url')} />
            {errors.url && <p className="text-sm text-red-600 mt-1">{errors.url.message}</p>}
          </div>
          <div>
            <label className="block text-sm font-medium">Poll interval (s)</label>
            <input type="number" className="mt-1 w-full rounded-md border px-3 py-2" {...register('poll_interval', { valueAsNumber: true })} />
            {errors.poll_interval && <p className="text-sm text-red-600 mt-1">{errors.poll_interval.message}</p>}
          </div>
          <div>
            <label className="block text-sm font-medium">Proxy (optional)</label>
            <input className="mt-1 w-full rounded-md border px-3 py-2" {...register('proxy')} />
          </div>
          <div>
            <label className="block text-sm font-medium">Cookies path (optional)</label>
            <input className="mt-1 w-full rounded-md border px-3 py-2" {...register('cookies')} />
          </div>
          <div className="self-end">
            <button disabled={isSubmitting} className="rounded-md bg-blue-600 text-white px-4 py-2 disabled:opacity-50">{isSubmitting ? 'Đang tạo…' : 'Tạo watcher'}</button>
          </div>
        </form>
        {msg && <div className="rounded-md bg-green-50 border border-green-200 p-3 text-sm text-green-700">{msg}</div>}
        {err && <div className="rounded-md bg-red-50 border border-red-200 p-3 text-sm text-red-700">{err}</div>}
      </div>

      <div className="rounded-lg border p-4 space-y-3">
        <h2 className="font-medium">Xóa watcher theo key (room_id hoặc url)</h2>
        <div className="flex gap-2">
          <input className="flex-1 rounded-md border px-3 py-2" value={delKey} onChange={(e) => setDelKey(e.target.value)} placeholder="room_id hoặc url" />
          <button onClick={doDelete} disabled={!delKey || delBusy} className="rounded-md border px-3 py-2 disabled:opacity-50">
            {delBusy ? 'Đang xóa…' : 'Xóa'}
          </button>
        </div>
        {delMsg && <div className="rounded-md bg-green-50 border border-green-200 p-3 text-sm text-green-700">{delMsg}</div>}
        {delErr && <div className="rounded-md bg-red-50 border border-red-200 p-3 text-sm text-red-700">{delErr}</div>}
        <div className="text-sm text-gray-600">Lưu ý: Backend hiện chưa cung cấp API liệt kê watchers.</div>
      </div>
    </div>
  )
}

