import type { NextConfig } from 'next';

const { execSync } = require('child_process');

function getGitMostRecentTag() {
  return execOrUnknown('git describe --tags --abbrev=0 HEAD');
}

function getGitCommitHash() {
  return execOrUnknown('git rev-parse --short HEAD');
}

function getGitCommitDate() {
  return execOrUnknown('git show -s --format=%ci HEAD');
}

function execOrUnknown(command: string) {
  try {
    return execSync(command).toString().trim();
  } catch (e) {
    return 'unknown';
  }
}

const nextConfig: NextConfig = {
  reactStrictMode: true,
  transpilePackages: [
    '@cloudscape-design/components',
    '@cloudscape-design/board-components',
    '@cloudscape-design/global-styles',
    '@cloudscape-design/component-toolkit'
  ],
  output: 'export',
  env: {
    COMMIT_RECENT_TAG: getGitMostRecentTag(),
    COMMIT_SHA: getGitCommitHash(),
    COMMIT_DATE: getGitCommitDate()
  },
  distDir: 'build/site'
};

export default nextConfig;
