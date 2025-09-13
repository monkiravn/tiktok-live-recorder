import { NextRequest } from 'next/server'
import { proxyDelete } from '../../_utils'

export async function DELETE(_req: NextRequest, ctx: { params: { key: string } }) {
  const key = ctx.params.key
  return proxyDelete(`/watchers/${encodeURIComponent(key)}`)
}

