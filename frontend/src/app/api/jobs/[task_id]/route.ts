import { NextRequest } from 'next/server'
import { proxyGet } from '../../_utils'

export async function GET(req: NextRequest, ctx: { params: { task_id: string } }) {
  const taskId = ctx.params.task_id
  req.nextUrl.searchParams.set('id', taskId) // no-op for parity; not used upstream
  return proxyGet(`/jobs/${encodeURIComponent(taskId)}`, req)
}

