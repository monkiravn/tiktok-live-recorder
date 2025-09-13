import { NextRequest, NextResponse } from 'next/server'

function getEnv() {
  const base = process.env.API_BASE_URL
  const key = process.env.API_KEY
  if (!base) throw new Error('API_BASE_URL is not set')
  if (!key) throw new Error('API_KEY is not set')
  return { base, key }
}

export async function proxyGet(path: string, req: NextRequest) {
  const { base, key } = getEnv()
  const url = new URL(path, base)
  url.search = req.nextUrl.search
  const res = await fetch(url, {
    headers: { 'X-API-Key': key },
    cache: 'no-store',
  })
  return passthrough(res)
}

export async function proxyJson(path: string, body: unknown, method: 'POST' | 'DELETE' | 'PUT' = 'POST') {
  const { base, key } = getEnv()
  const url = new URL(path, base)
  const res = await fetch(url, {
    method,
    headers: { 'X-API-Key': key, 'content-type': 'application/json' },
    body: JSON.stringify(body ?? {}),
    cache: 'no-store',
  })
  return passthrough(res)
}

export async function proxyDelete(path: string) {
  const { base, key } = getEnv()
  const url = new URL(path, base)
  const res = await fetch(url, {
    method: 'DELETE',
    headers: { 'X-API-Key': key },
    cache: 'no-store',
  })
  return passthrough(res)
}

async function passthrough(res: Response) {
  const ct = res.headers.get('content-type') || ''
  const status = res.status
  if (ct.includes('application/json')) {
    const data = await res.json()
    if (!res.ok) {
      return NextResponse.json(
        {
          error_code: data?.error_code || 'UPSTREAM_ERROR',
          error_message: data?.detail || data?.error_message || res.statusText,
          correlation_id: res.headers.get('x-correlation-id') || undefined,
        },
        { status }
      )
    }
    return NextResponse.json(data, { status })
  }
  const text = await res.text()
  if (!res.ok) {
    return NextResponse.json({ error_code: 'UPSTREAM_ERROR', error_message: text || res.statusText }, { status })
  }
  return new NextResponse(text, { status, headers: { 'content-type': ct || 'text/plain' } })
}

