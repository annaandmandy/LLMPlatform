/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  experimental: {
    serverActions: true,
  },
  // Ensure CSS is properly loaded for Microsoft Clarity recordings
  compiler: {
    removeConsole: process.env.NODE_ENV === "production" ? { exclude: ["error"] } : false,
  },
  // Optimize CSS loading
  optimizeFonts: true,
};

module.exports = nextConfig;
