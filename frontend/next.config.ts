import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  cacheComponents: true,
  partialPrefetching: true,
  // Using plain vanilla CSS — no Tailwind loader
};

export default nextConfig;
