
export async function copyToClipboard(text) {
  if (!text) throw new Error('Nothing to copy');

  if (navigator.clipboard?.writeText && window.isSecureContext) {
    await navigator.clipboard.writeText(text);
    return;
  }

  const textarea = document.createElement('textarea');
  textarea.value = text;
  textarea.setAttribute('readonly', '');
  textarea.style.position = 'fixed';
  textarea.style.top = '-1000px';
  textarea.style.opacity = '0';
  document.body.appendChild(textarea);
  try {
    textarea.select();
    const copied = document.execCommand('copy');
    if (!copied) throw new Error('Clipboard is not available in this browser');
  } finally {
    document.body.removeChild(textarea);
  }
}
