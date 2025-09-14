import { proxyGet } from "../_utils";
import { NextRequest } from "next/server";

export const dynamic = 'force-dynamic'

export async function GET(req: NextRequest) {
  return proxyGet("/jobs", req);
}
