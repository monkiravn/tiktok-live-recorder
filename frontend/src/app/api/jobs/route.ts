import { proxyGet } from "../_utils";
import { NextRequest } from "next/server";

export async function GET(req: NextRequest) {
  return proxyGet("/jobs", req);
}
