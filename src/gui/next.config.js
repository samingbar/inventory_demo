/** @type {import('next').NextConfig} */
// Keep the config minimal for demos. Server Actions are enabled mainly to allow
// easy future extension if needed.
const nextConfig = {
  experimental: { serverActions: { bodySizeLimit: '2mb' } }
};
module.exports = nextConfig;
