import { NextRequest } from 'next/server'
import { proxyGet } from '../_utils'

export const dynamic = 'force-dynamic'

export async function GET(req: NextRequest) {
  return proxyGet('/ready', req)
}

