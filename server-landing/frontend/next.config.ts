import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'standalone',
  experimental: {
    // Enable optimizations for production
  },
};

export default nextConfig;
