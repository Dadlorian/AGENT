// Cell-Plane code presenter. Turns a plain <pre><code> block into a labelled, line-numbered, syntax-coloured block using the site tokens.
// Usage: import { enhanceCode } from './cellplane-code.js'; enhanceCode(rootElement) after render. Idempotent.
const LANG_LABEL = { http: 'HTTP', shell: 'Shell', js: 'Node', json: 'JSON', yaml: 'YAML', text: 'Text', rego: 'Rego' };
const detect = s => /^(GET|POST|PUT|DELETE|PATCH) \//m.test(s) ? 'http' : /^(cp |npm |npx |#|\$ |export |curl )/m.test(s) ? 'shell' : /^(import |const |await |for await|let |export )/m.test(s) ? 'js' : /^\s*[{[]/.test(s) || /^\s*"\w+"\s*:/m.test(s) ? 'json' : /^[a-z_]+:\s/m.test(s) ? 'yaml' : /^(package|allow|deny) /m.test(s) ? 'rego' : 'text';
const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const C = { key: 'var(--park)', str: 'var(--run)', num: 'var(--wait)', method: 'var(--accent)', cmt: 'var(--faint)', punct: 'var(--muted)', url: 'var(--text)', kw: 'var(--accent)', arrow: 'var(--muted)' };
const span = (cls, s) => `<span style="color:${C[cls]}">${esc(s)}</span>`;
function tokenize(line, lang) {
  // comments first: a line that starts with # (any lang but json) or // is a comment
  if (lang !== 'json' && /^\s*#/.test(line)) return span('cmt', line);
  if (/^\s*\/\//.test(line)) return span('cmt', line);
  const cm = lang === 'js' ? line.match(/^(.*?)(\/\/.*)$/) : lang !== 'json' && lang !== 'http' ? line.match(/^(.*?)(#.*)$/) : null;
  if (cm && !/https?:\/\/[^\s]*#|"[^"]*#[^"]*"/.test(line)) return tokenize(cm[1], lang) + span('cmt', cm[2]);
  let out = '', rest = line;
  const rules = [
    [/^(GET|POST|PUT|DELETE|PATCH)(?=\s)/, 'method'],
    [/^(→|←|⇄|∈)/, 'arrow'],
    [/^(cp|npm|npx|curl|import|from|const|let|await|for|of|export|default|async|package|allow|deny|if|else|return|true|false|null)\b/, 'kw'],
    [/^"(?:[^"\\]|\\.)*"(?=\s*:)/, 'key'],
    [/^\((SSE|stream|async)\)/, 'cmt'],
    [/^[A-Za-z_][\w-]*(?=\s*:(?!\/\/))/, 'key'],
    [/^"(?:[^"\\]|\\.)*"|^'(?:[^'\\]|\\.)*'/, 'str'],
    [/^https?:\/\/[^\s"',)]+|^\/v1\/[^\s"',)]+|^\/[a-z][^\s"',)]*(?=\s|$)/, 'url'],
    [/^-?\d+(\.\d+)?(ms|s|m|h|%)?\b/, 'num'],
    [/^[{}\[\],:=&?;()]/, 'punct'],
    [/^\s+/, null],
    [/^[^\s{}\[\],:=&?;()"']+/, null]
  ];
  while (rest.length) { let hit = false; for (const [re, cls] of rules) { const m = rest.match(re); if (m && m[0].length) { out += cls ? span(cls, m[0]) : esc(m[0]); rest = rest.slice(m[0].length); hit = true; break; } } if (!hit) { out += esc(rest[0]); rest = rest.slice(1); } }
  return out;
}
export function enhanceCode(root) {
  (root || document).querySelectorAll('pre > code').forEach(code => {
    const pre = code.parentElement; if (pre.dataset.enhanced) return; pre.dataset.enhanced = '1';
    const raw = code.textContent.replace(/\s+$/, ''); const lang = pre.dataset.lang || detect(raw); const lines = raw.split('\n');
    const gutter = lines.length > 1;
    const body = lines.map((l, i) => `<div style="display:grid;grid-template-columns:${gutter ? '28px ' : ''}minmax(0,1fr);gap:12px;min-height:1.6em">${gutter ? `<span style="text-align:right;color:var(--faint);user-select:none;font-variant-numeric:tabular-nums">${i + 1}</span>` : ''}<span style="white-space:pre-wrap;overflow-wrap:anywhere">${tokenize(l, lang) || ' '}</span></div>`).join('');
    const wrap = document.createElement('div'); wrap.className = 'code-block';
    wrap.style.cssText = 'border:1px solid var(--border);border-radius:6px;background:var(--surface);overflow:hidden;margin:0';
    wrap.innerHTML = `<div style="display:flex;align-items:center;gap:10px;height:32px;padding:0 12px;border-bottom:1px solid var(--border);background:var(--surface2)"><span style="font-family:var(--font-mono,'JetBrains Mono',monospace);font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted)">${LANG_LABEL[lang] || lang}</span>${pre.dataset.title ? `<span style="font-family:var(--font-mono,'JetBrains Mono',monospace);font-size:11px;color:var(--faint);overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${esc(pre.dataset.title)}</span>` : ''}<span style="flex:1"></span><button type="button" style="height:22px;padding:0 8px;border-radius:4px;border:1px solid var(--border2);background:transparent;color:var(--muted);font:600 11px var(--font-ui,inherit);cursor:pointer">Copy</button></div><div style="padding:12px 14px;font-family:var(--font-mono,'JetBrains Mono',monospace);font-size:12px;line-height:1.6;color:var(--text)">${body}</div>`;
    const btn = wrap.querySelector('button'); btn.addEventListener('click', () => { try { navigator.clipboard.writeText(raw); btn.textContent = 'Copied'; setTimeout(() => btn.textContent = 'Copy', 1400); } catch (e) {} });
    pre.replaceWith(wrap);
  });
}
