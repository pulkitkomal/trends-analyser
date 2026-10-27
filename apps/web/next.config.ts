import type { NextConfig } from "next";

const tunnelHost = process.env.TUNNEL_HOST || "topics.k4mik4ge.xyz";

const nextConfig: NextConfig = {
  output: "standalone",
  devIndicators: false,
  allowedDevOrigins: [
    "topics.k4mik4ge.xyz",
    "*.k4mik4ge.xyz",
    "*.trycloudflare.com",
    "**.trycloudflare.com",
    tunnelHost,
  ],
  experimental: {
    serverActions: {
      allowedOrigins: ["topics.k4mik4ge.xyz", tunnelHost, "localhost:8678"],
    },
  },
  async rewrites() {
    const api = process.env.API_URL || "http://127.0.0.1:8001";
    return [{ source: "/api/:path*", destination: `${api}/api/:path*` }];
  },
};

export default nextConfig;
