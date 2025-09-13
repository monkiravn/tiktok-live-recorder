"use client"
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { zodResolver } from '@hookform/resolvers/zod'
import { useRouter } from 'next/navigation'
import { useState } from 'react'
import { api, type CreateRecordingRequest } from '@/lib/api'

const schema = z
  .object({
    room_id: z.string().trim().optional().nullable(),
    url: z.string().trim().url().optional().nullable(),
    duration: z.coerce.number().int().min(1).optional().nullable(),
    proxy: z.string().trim().optional().nullable(),
    cookies: z.string().trim().optional().nullable(),
  })
  .refine((d) => (d.room_id && !d.url) || (d.url && !d.room_id), {
    message: 'Cần nhập room_id hoặc url (chỉ một trong hai)',
    path: ['room_id'],
  })

type FormData = z.infer<typeof schema>

export default function RecordNowPage() {
  const router = useRouter()
  const [error, setError] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({ resolver: zodResolver(schema) })

  async function onSubmit(values: FormData) {
    setError(null)
    const payload: CreateRecordingRequest = {
      room_id: values.room_id || undefined,
      url: values.url || undefined,
      duration: values.duration || undefined,
      options: { proxy: values.proxy || undefined, cookies: values.cookies || undefined },
    }
    try {
      const res = await api.createRecording(payload)
      router.push(`/jobs/${res.task_id}`)
    } catch (e: any) {
      setError(e?.error_message || e?.message || 'Gửi yêu cầu thất bại')
    }
  }

  return (
    <div className="max-w-xl">
      <h1 className="text-2xl font-semibold mb-4">Record Now</h1>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <label className="block text-sm font-medium">Room ID</label>
          <input className="mt-1 w-full rounded-md border px-3 py-2" placeholder="123456789" {...register('room_id')} />
          {errors.room_id && <p className="text-sm text-red-600 mt-1">{errors.room_id.message}</p>}
        </div>
        <div>
          <label className="block text-sm font-medium">URL</label>
          <input className="mt-1 w-full rounded-md border px-3 py-2" placeholder="https://www.tiktok.com/@user/live" {...register('url')} />
          {errors.url && <p className="text-sm text-red-600 mt-1">{errors.url.message}</p>}
        </div>
        <div>
          <label className="block text-sm font-medium">Duration (seconds)</label>
          <input type="number" className="mt-1 w-full rounded-md border px-3 py-2" placeholder="1800" {...register('duration')} />
          {errors.duration && <p className="text-sm text-red-600 mt-1">{errors.duration.message}</p>}
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium">Proxy (optional)</label>
            <input className="mt-1 w-full rounded-md border px-3 py-2" placeholder="http://user:pass@host:port" {...register('proxy')} />
          </div>
          <div>
            <label className="block text-sm font-medium">Cookies path (optional)</label>
            <input className="mt-1 w-full rounded-md border px-3 py-2" placeholder="/path/to/cookies.json" {...register('cookies')} />
          </div>
        </div>
        {error && <div className="rounded-md bg-red-50 border border-red-200 p-3 text-sm text-red-700">{error}</div>}
        <button disabled={isSubmitting} className="inline-flex items-center rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50">
          {isSubmitting ? 'Submitting...' : 'Start Recording'}
        </button>
      </form>
    </div>
  )
}

