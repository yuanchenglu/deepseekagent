/**
 * Deep Agent — Electron Forge / electron-builder configuration
 *
 * This is used by electron-builder (configured via the "build" field in
 * package.json) to package the webui/ as a standalone desktop application.
 *
 * See also: scripts/package-electron.sh
 */

const path = require('path')

/** @type {import('electron-builder').Configuration} */
const config = {
  appId: 'com.deepagent.desktop',
  productName: 'Deep Agent',
  copyright: `Copyright © ${new Date().getFullYear()} Deep Agent Contributors`,

  directories: {
    output: 'dist/electron-output',
    buildResources: 'electron/build',
    app: '.',
  },
  extraMetadata: {
    main: 'electron/main.js',
  },

  directories: {
    output: 'dist/electron-output',
    buildResources: 'electron/build',
  },

  files: [
    'electron/**/*',
    'package.json',
  ],

  /**
   * extraResources includes the built web client (dist/).
   * The Electron main process resolves dist/client/index.html
   * via process.resourcesPath.
   * 
   * NOTE: electron-output/ MUST be excluded to prevent recursive nesting
   * when electron-builder copies extraResources into the app bundle.
   */
  extraResources: [
    {
      from: 'dist',
      to: 'dist',
      filter: ['client/**/*', 'server/**/*', 'mcu/**/*'],
    },
  ],

  /* Node native addons (node-pty etc.) must be unpacked from asar */
  asarUnpack: ['**/*.node'],

  /* macOS target */
  mac: {
    target: [
      { target: 'dmg', arch: ['arm64', 'x64'] },
      { target: 'zip', arch: ['arm64', 'x64'] },
    ],
    category: 'public.app-category.developer-tools',
    hardenedRuntime: true,
    artifactName: 'Deep.Agent-${version}-${arch}.${ext}',
  },

  /* Linux target */
  linux: {
    target: [
      { target: 'AppImage', arch: ['x64', 'arm64'] },
      { target: 'deb', arch: ['x64'] },
    ],
    category: 'Development',
    artifactName: 'deep-agent-${version}-${arch}.${ext}',
  },
}

module.exports = config
