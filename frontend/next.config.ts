import type { NextConfig } from 'next';
const nextConfig: NextConfig = {
  transpilePackages: [
    '@cloudscape-design/components',
    '@cloudscape-design/component-toolkit'
  ],
  output: 'export',
  env: {
  },
  distDir: 'build/site'
};

export default nextConfig;
