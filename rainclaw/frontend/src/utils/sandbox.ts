/**
 * Sandbox URL utilities.
 *
 * The agent-infra/sandbox container exposes port 8080 internally,
 * mapped to 18080 on the host via docker-compose.
 */

const SANDBOX_PORT = 18080;

export function getSandboxBaseUrl(): string {
  return `${window.location.protocol}//${window.location.hostname}:${SANDBOX_PORT}`;
}

export function getSandboxVncUrl(): string {
  return `${getSandboxBaseUrl()}/vnc/index.html?autoconnect=true&resize=scale&view_only=true`;
}

export function getSandboxTerminalWsUrl(): string {
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${proto}//${window.location.hostname}:${SANDBOX_PORT}/v1/shell/ws`;
}

export function getSandboxScreenshotUrl(): string {
  return `${getSandboxBaseUrl()}/vnc/screenshot`;
}

export type SandboxPreviewMode = 'terminal' | 'browser' | 'none';

/**
 * Tools that trigger the terminal preview panel.
 * Includes both deepagents built-in tools and legacy sandbox tool names.
 */
const TERMINAL_TOOLS = new Set([
  // deepagents built-in
  'execute',
  // legacy MCP sandbox (kept for backward compatibility)
  'sandbox_execute_bash',
  'sandbox_execute_code',
  'sandbox_file_operations',
  'sandbox_str_replace_editor',
  'sandbox_get_context',
  'sandbox_get_packages',
  'sandbox_convert_to_markdown',
  'sandbox_exec',
]);

/**
 * Tools that trigger the browser preview panel.
 */
const BROWSER_TOOLS = new Set([
  'sandbox_get_browser_info',
  'sandbox_browser_screenshot',
  'sandbox_browser_execute_action',
]);

/**
 * Determine the preview mode for a given tool function name.
 * When isSandboxProxy is true, the tool executes in the sandbox via a proxy,
 * so it should always trigger the terminal preview.
 */
export function getPreviewMode(toolFunction: string, isSandboxProxy = false): SandboxPreviewMode {
  if (!toolFunction) return 'none';
  if (isSandboxProxy) return 'terminal';
  if (TERMINAL_TOOLS.has(toolFunction)) return 'terminal';
  if (BROWSER_TOOLS.has(toolFunction)) return 'browser';
  if (toolFunction.startsWith('terminal_')) return 'terminal';
  if (toolFunction.startsWith('browser_')) return 'browser';
  if (toolFunction.startsWith('sandbox_')) return 'terminal';
  return 'none';
}
