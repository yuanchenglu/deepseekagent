const SAFE_CHILD_ENV_NAMES = [
  'PATH', 'Path', 'HOME', 'USERPROFILE', 'TMPDIR', 'TMP', 'TEMP',
  'LANG', 'LC_ALL', 'LC_CTYPE', 'SHELL', 'SystemRoot', 'ComSpec', 'PATHEXT',
  'SSL_CERT_FILE', 'SSL_CERT_DIR', 'NODE_EXTRA_CA_CERTS',
] as const

export function safeChildEnvironment(extra: NodeJS.ProcessEnv = {}): NodeJS.ProcessEnv {
  const env: NodeJS.ProcessEnv = {}
  for (const name of SAFE_CHILD_ENV_NAMES) {
    if (process.env[name]) env[name] = process.env[name]
  }
  return { ...env, ...extra }
}
