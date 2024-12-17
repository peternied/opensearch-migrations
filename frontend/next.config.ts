import type { NextConfig } from 'next';

const { execSync } = require('child_process');

function getGitMostRecentTag() {
  try {
    return execSync('git describe --tags --abbrev=0 HEAD').toString().trim();
  } catch (e) {
    return 'unknown';
  }
}

function getGitCommitHash() {
  try {
    return execSync('git rev-parse --short HEAD').toString().trim();
  } catch (e) {
    return 'unknown';
  }
}

function getGitCommitDate() {
  try {
    return execSync('git show -s --format=%ci HEAD').toString().trim();
  } catch (e) {
    return 'unknown';
  }
}

const nextConfig: NextConfig = {
  transpilePackages: [
    '@cloudscape-design/components',
    '@cloudscape-design/component-toolkit'
  ],
  output: 'export',
  env: {
    COMMIT_RECENT_TAG: getGitMostRecentTag(),
    COMMIT_SHA: getGitCommitHash(),
    COMMIT_DATE: getGitCommitDate(),
  },
};

export default nextConfig;
