/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  // Skip building API routes during static export
  trailingSlash: false,
}

export default nextConfig
