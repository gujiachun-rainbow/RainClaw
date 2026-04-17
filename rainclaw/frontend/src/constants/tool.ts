/**
 * Tool function mapping
 */
export const TOOL_FUNCTION_MAP: {[key: string]: string} = {
  // Shell tools
  "shell_exec": "Executing command",
  "shell_view": "Viewing command output",
  "shell_wait": "Waiting for command completion",
  "shell_write_to_process": "Writing data to process",
  "shell_kill_process": "Terminating process",
  
  // File tools
  "file_read": "Reading file",
  "file_write": "Writing file",
  "file_str_replace": "Replacing file content",
  "file_find_in_content": "Searching file content",
  "file_find_by_name": "Finding file",
  
  // Browser tools
  "browser_view": "Viewing webpage",
  "browser_navigate": "Navigating to webpage",
  "browser_restart": "Restarting browser",
  "browser_click": "Clicking element",
  "browser_input": "Entering text",
  "browser_move_mouse": "Moving mouse",
  "browser_press_key": "Pressing key",
  "browser_select_option": "Selecting option",
  "browser_scroll_up": "Scrolling up",
  "browser_scroll_down": "Scrolling down",
  "browser_console_exec": "Executing JS code",
  "browser_console_view": "Viewing console output",
  
  // Search tools
  "info_search_web": "Searching web",

  // Python/Skills tools
  "read_file": "Reading file",
  "write_file": "Writing file",
  "run_python_script": "Running Python script",
  
  // Sandbox tools
  "sandbox_exec": "Executing command",
  "sandbox_read_file": "Reading file",
  "sandbox_write_file": "Writing file",
  "sandbox_find_files": "Finding files",
  "execute": "Executing command",
  "find_files": "Finding files",
  "edit_file": "Editing file",
  "web_crawl": "Crawling webpage",
  
  // Message tools
  "message_notify_user": "Sending notification",
  "message_ask_user": "Asking question",
  "web_search": "Searching web",
  "ls": "Listing files",
  "grep": "Searching text",
  "write": "Writing file",

  // MCP Sandbox: terminal tools
  "terminal_execute": "Executing command",
  "terminal_session": "Terminal session",
  "terminal_kill": "Terminating process",

  // MCP Sandbox: file tools
  "file_list": "Listing files",
  "file_search": "Searching files",
  "file_replace": "Replacing in file",

  // MCP Sandbox: browser tools (only keys not already defined above)
  "browser_extract": "Extracting page",
  "browser_screenshot": "Taking screenshot",
  "browser_close": "Closing browser",
  "browser_get_markdown": "Getting page markdown",
  "browser_get_text": "Getting page text",
  "browser_read_links": "Reading links",
  "browser_tab_list": "Listing tabs",
  "browser_switch_tab": "Switching tab",
  "browser_go_back": "Going back",
  "browser_go_forward": "Going forward",
  "browser_form_input_fill": "Filling form",
  "browser_get_clickable_elements": "Getting elements",
  "browser_get_download_list": "Getting downloads",

  // MCP Sandbox: document tools
  "markitdown_extract": "Extracting document",
  "markitdown_convert": "Converting to markdown",

  // MCP Sandbox: actual tool names from sandbox MCP server
  "sandbox_execute_bash": "Executing bash command",
  "sandbox_execute_code": "Executing code",
  "sandbox_file_operations": "File operations",
  "sandbox_str_replace_editor": "Editing file",
  "sandbox_get_context": "Getting context",
  "sandbox_get_packages": "Getting packages",
  "sandbox_convert_to_markdown": "Converting to markdown",
  "sandbox_get_browser_info": "Getting browser info",
  "sandbox_browser_screenshot": "Taking screenshot",
  "sandbox_browser_execute_action": "Browser action",
};

/**
 * Display name mapping for tool function parameters
 */
export const TOOL_FUNCTION_ARG_MAP: {[key: string]: string} = {
  "shell_exec": "command",
  "shell_view": "shell",
  "shell_wait": "shell",
  "shell_write_to_process": "input",
  "shell_kill_process": "shell",
  "file_read": "file",
  "file_write": "file",
  "file_str_replace": "file",
  "file_find_in_content": "file",
  "file_find_by_name": "path",
  "browser_view": "page",
  "browser_navigate": "url",
  "browser_restart": "url",
  "browser_click": "element",
  "browser_input": "text",
  "browser_move_mouse": "position",
  "browser_press_key": "key",
  "browser_select_option": "option",
  "browser_scroll_up": "page",
  "browser_scroll_down": "page",
  "browser_console_exec": "code",
  "browser_console_view": "console",
  "info_search_web": "query",
  "read_file": "file_path",
  "write_file": "file_path",
  "run_python_script": "script_path",
  "message_notify_user": "message",
  "message_ask_user": "question",
  // Sandbox tools (legacy)
  "sandbox_exec": "command",
  "sandbox_read_file": "file_path",
  "sandbox_write_file": "file_path",
  "sandbox_find_files": "pattern",
  "execute": "command",
  "find_files": "pattern",
  "edit_file": "file_path",
  "web_search": "query",
  "web_crawl": "url",
  // MCP Sandbox tools (only keys not already defined above)
  "terminal_execute": "command",
  "terminal_session": "session_id",
  "terminal_kill": "session_id",
  "file_list": "path",
  "file_search": "file",
  "file_replace": "file",
  "browser_extract": "url",
  "browser_screenshot": "url",
  "browser_get_markdown": "url",
  "browser_get_text": "url",
  "browser_read_links": "url",
  "browser_form_input_fill": "element",
  "markitdown_extract": "file",
  "markitdown_convert": "file",
  // MCP Sandbox: actual tool names
  "sandbox_execute_bash": "command",
  "sandbox_execute_code": "code",
  "sandbox_file_operations": "path",
  "sandbox_str_replace_editor": "path",
  "sandbox_get_context": "context",
  "sandbox_get_packages": "packages",
  "sandbox_convert_to_markdown": "file",
  "sandbox_get_browser_info": "url",
  "sandbox_browser_screenshot": "url",
  "sandbox_browser_execute_action": "action",
};

/**
 * Tool name mapping
 */
export const TOOL_NAME_MAP: {[key: string]: string} = {
  "shell": "Terminal",
  "file": "File",
  "browser": "Browser",
  "info": "Information",
  "search": "Information",
  "message": "Message",
  "mcp": "MCP Tool",
  "read_file": "File",
  "write_file": "File",
  "run_python_script": "Python",
  "web_search": "Web Search",
  "web_crawl": "Web Crawl",
  "ls": "File List",
  "grep": "Grep",
  "write": "Write File",
  // Sandbox tools (legacy)
  "execute": "Terminal",
  "sandbox_exec": "Terminal",
  "sandbox_read_file": "File",
  "sandbox_write_file": "File",
  "sandbox_find_files": "File",
  "find_files": "File",
  "edit_file": "File",
  // MCP Sandbox tools
  "terminal_execute": "Terminal",
  "terminal_session": "Terminal",
  "terminal_kill": "Terminal",
  "file_list": "File List",
  "file_search": "File Search",
  "file_replace": "File Edit",
  "browser_navigate": "Browser",
  "browser_click": "Browser",
  "browser_type": "Browser",
  "browser_extract": "Browser",
  "browser_screenshot": "Browser",
  "browser_close": "Browser",
  "browser_get_markdown": "Browser",
  "browser_get_text": "Browser",
  "browser_read_links": "Browser",
  "browser_tab_list": "Browser",
  "browser_switch_tab": "Browser",
  "browser_go_back": "Browser",
  "browser_go_forward": "Browser",
  "browser_hover": "Browser",
  "browser_select": "Browser",
  "browser_form_input_fill": "Browser",
  "browser_get_clickable_elements": "Browser",
  "browser_get_download_list": "Browser",
  "markitdown_extract": "Document",
  "markitdown_convert": "Document",
  // MCP Sandbox: actual tool names
  "sandbox_execute_bash": "Terminal",
  "sandbox_execute_code": "Code Runner",
  "sandbox_file_operations": "File",
  "sandbox_str_replace_editor": "File Edit",
  "sandbox_get_context": "Context",
  "sandbox_get_packages": "Packages",
  "sandbox_convert_to_markdown": "Document",
  "sandbox_get_browser_info": "Browser",
  "sandbox_browser_screenshot": "Browser",
  "sandbox_browser_execute_action": "Browser",
};

import SearchIcon from '../components/icons/SearchIcon.vue';
import EditIcon from '../components/icons/EditIcon.vue';
import BrowserIcon from '../components/icons/BrowserIcon.vue';
import ShellIcon from '../components/icons/ShellIcon.vue';

/**
 * Tool icon mapping
 */
export const TOOL_ICON_MAP: {[key: string]: any} = {
  "shell": ShellIcon,
  "file": EditIcon,
  "browser": BrowserIcon,
  "search": SearchIcon,
  "info": SearchIcon,
  "message": "",
  "mcp": SearchIcon,  // 暂时使用搜索图标，可以后续创建专门的MCP图标
  "read_file": EditIcon,
  "write_file": EditIcon,
  "run_python_script": ShellIcon,
  "web_search": SearchIcon,
  "web_crawl": BrowserIcon,
  "ls": EditIcon,
  "grep": SearchIcon,
  "write": EditIcon,
  // Sandbox tools (legacy)
  "execute": ShellIcon,
  "sandbox_exec": ShellIcon,
  "sandbox_read_file": EditIcon,
  "sandbox_write_file": EditIcon,
  "sandbox_find_files": EditIcon,
  "find_files": EditIcon,
  "edit_file": EditIcon,
  // MCP Sandbox tools
  "terminal_execute": ShellIcon,
  "terminal_session": ShellIcon,
  "terminal_kill": ShellIcon,
  "file_list": EditIcon,
  "file_search": SearchIcon,
  "file_replace": EditIcon,
  "browser_navigate": BrowserIcon,
  "browser_click": BrowserIcon,
  "browser_type": BrowserIcon,
  "browser_extract": BrowserIcon,
  "browser_screenshot": BrowserIcon,
  "browser_close": BrowserIcon,
  "browser_get_markdown": BrowserIcon,
  "browser_get_text": BrowserIcon,
  "browser_read_links": BrowserIcon,
  "browser_tab_list": BrowserIcon,
  "browser_switch_tab": BrowserIcon,
  "browser_go_back": BrowserIcon,
  "browser_go_forward": BrowserIcon,
  "browser_hover": BrowserIcon,
  "browser_select": BrowserIcon,
  "browser_form_input_fill": BrowserIcon,
  "browser_get_clickable_elements": BrowserIcon,
  "browser_get_download_list": BrowserIcon,
  "markitdown_extract": EditIcon,
  "markitdown_convert": EditIcon,
  // MCP Sandbox: actual tool names
  "sandbox_execute_bash": ShellIcon,
  "sandbox_execute_code": ShellIcon,
  "sandbox_file_operations": EditIcon,
  "sandbox_str_replace_editor": EditIcon,
  "sandbox_get_context": SearchIcon,
  "sandbox_get_packages": SearchIcon,
  "sandbox_convert_to_markdown": EditIcon,
  "sandbox_get_browser_info": BrowserIcon,
  "sandbox_browser_screenshot": BrowserIcon,
  "sandbox_browser_execute_action": BrowserIcon,
};

import ShellToolView from '@/components/toolViews/ShellToolView.vue';
import FileToolView from '@/components/toolViews/FileToolView.vue';
import SearchToolView from '@/components/toolViews/SearchToolView.vue';
import BrowserToolView from '@/components/toolViews/BrowserToolView.vue';
import McpToolView from '@/components/toolViews/McpToolView.vue';

/**
 * Mapping from tool names to components
 */
export const TOOL_COMPONENT_MAP: {[key: string]: any} = {
  "shell": ShellToolView,
  "file": FileToolView,
  "search": SearchToolView,
  "browser": BrowserToolView,
  "info": SearchToolView,
  "mcp": McpToolView,
  "read_file": FileToolView,
  "write_file": FileToolView,
  "run_python_script": ShellToolView,
  "web_search": SearchToolView,
  "web_crawl": SearchToolView,
  "ls": FileToolView,
  "grep": SearchToolView,
  "write": FileToolView,
  // Sandbox tools (legacy)
  "execute": ShellToolView,
  "sandbox_exec": ShellToolView,
  "sandbox_read_file": FileToolView,
  "sandbox_write_file": FileToolView,
  "sandbox_find_files": FileToolView,
  "find_files": FileToolView,
  "edit_file": FileToolView,
  // MCP Sandbox tools
  "terminal_execute": ShellToolView,
  "terminal_session": ShellToolView,
  "terminal_kill": ShellToolView,
  "file_list": FileToolView,
  "file_search": FileToolView,
  "file_replace": FileToolView,
  "browser_navigate": BrowserToolView,
  "browser_click": BrowserToolView,
  "browser_type": BrowserToolView,
  "browser_extract": BrowserToolView,
  "browser_screenshot": BrowserToolView,
  "browser_close": BrowserToolView,
  "browser_get_markdown": BrowserToolView,
  "browser_get_text": BrowserToolView,
  "browser_read_links": BrowserToolView,
  "browser_tab_list": BrowserToolView,
  "browser_switch_tab": BrowserToolView,
  "browser_go_back": BrowserToolView,
  "browser_go_forward": BrowserToolView,
  "browser_hover": BrowserToolView,
  "browser_select": BrowserToolView,
  "browser_form_input_fill": BrowserToolView,
  "browser_get_clickable_elements": BrowserToolView,
  "browser_get_download_list": BrowserToolView,
  "markitdown_extract": FileToolView,
  "markitdown_convert": FileToolView,
  // MCP Sandbox: actual tool names
  "sandbox_execute_bash": ShellToolView,
  "sandbox_execute_code": ShellToolView,
  "sandbox_file_operations": FileToolView,
  "sandbox_str_replace_editor": FileToolView,
  "sandbox_get_context": FileToolView,
  "sandbox_get_packages": FileToolView,
  "sandbox_convert_to_markdown": FileToolView,
  "sandbox_get_browser_info": BrowserToolView,
  "sandbox_browser_screenshot": BrowserToolView,
  "sandbox_browser_execute_action": BrowserToolView,
};
