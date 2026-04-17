
import DOMPurify from 'dompurify';

export const transformSrc = (src: string) => {
  if (!src) return '';
  // If it's already an API URL or external URL, leave it alone
  if (src.startsWith('http') || src.startsWith('https') || src.startsWith('/api/')) {
    return src;
  }
  // If it looks like an absolute file path (starts with /), convert to download API
  // This handles paths like /tmp/... or /app/...
  if (src.startsWith('/')) {
    // Remove query params if any, though usually file paths don't have them yet
    // But to be safe for molecule viewer logic
    const cleanPath = src.split('?')[0]; 
    return `/api/v1/file/download?path=${encodeURIComponent(cleanPath)}`;
  }
  return src;
};

export const domPurifyConfig = {
  ADD_TAGS: ['molecule-viewer', 'html-viewer'],
  ADD_ATTR: [
    'src', 'alt',
    // Mermaid attributes
    'data-mermaid-id', 'data-mermaid-code', 'id',
    // KaTeX attributes (allow all data-* and aria-* attributes)
    'aria-hidden', 'aria-label', 'role',
    // SVG attributes
    'viewbox', 'preserveaspectratio', 'd', 'fill', 'stroke', 'stroke-width',
    'stroke-linecap', 'stroke-linejoin', 'transform', 'x', 'y', 'width', 'height',
    'cx', 'cy', 'r', 'rx', 'ry', 'x1', 'x2', 'y1', 'y2', 'points', 'xmlns',
    // Additional SVG and KaTeX attributes
    'xmlns:xlink', 'xlink:href', 'style', 'class', 'tabindex', 'mathbackground',
    'mathcolor', 'displaystyle', 'scriptlevel'
  ],
  // Allow data-* attributes (for KaTeX and custom components)
  ALLOW_DATA_ATTR: true,
  // Allow safe SVG elements
  ADD_URI_SAFE_ATTR: ['xlink:href']
};

export const sanitizeHtml = (html: string) => {
  DOMPurify.setConfig(domPurifyConfig);
  return DOMPurify.sanitize(html);
};
