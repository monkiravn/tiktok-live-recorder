import { NextRequest } from 'next/server'
import { proxyGet } from '../_utils'

export async function GET(req: NextRequest) {
  return proxyGet('/ready', req)
}

