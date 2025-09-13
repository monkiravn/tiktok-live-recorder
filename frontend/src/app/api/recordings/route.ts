import { NextRequest } from 'next/server'
import { proxyJson } from '../_utils'

export async function POST(req: NextRequest) {
  const body = await req.json().catch(() => ({}))
  return proxyJson('/recordings', body, 'POST')
}

