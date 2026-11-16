// S1 (Evidence-Pipeline v2) — Markdown-Sanitizer-Coverage.
//
// `renderMarkdown` muss XSS-Vektoren aus untrusted Markdown rauspulen,
// bevor das Ergebnis via `v-html` ins DOM geht. Default-DOMPurify reicht;
// Tests sichern die wichtigsten OWASP-Patterns ab und schützen gegen
// Regression beim Wechsel von marked-Optionen.

import { describe, it, expect } from 'vitest'
import { renderMarkdown } from '../markdown'

describe('renderMarkdown', () => {
  it('keeps simulated quote details collapsed and the quote body visible', () => {
    const markdown = '> **模拟人物发言** | 外媒_898\n> 这是模拟发言。\n>\n> <details>\n> <summary>引用详情</summary>\n>\n> 人物标识（persona_id）: 外媒_898<br>\n> 证据编号（seed_anchor）: ev_123\n>\n> </details>'
    const element = document.createElement('div')
    element.innerHTML = renderMarkdown(markdown)
    const details = element.querySelector('details')!
    expect(details).not.toBeNull()
    expect(details.hasAttribute('open')).toBe(false)
    expect(details.querySelector('summary')?.textContent).toBe('引用详情')
    expect(details.textContent).toContain('ev_123')
    expect(details.textContent).not.toContain('这是模拟发言。')
    expect(element.querySelector('blockquote')?.textContent).toContain('这是模拟发言。')
  })

  it('rendert Standard-Markdown', () => {
    const html = renderMarkdown('# Title\n\n**bold**')
    expect(html).toContain('<h1>')
    expect(html).toContain('Title')
    expect(html).toContain('<strong>bold</strong>')
  })

  it('liefert leeren String für falsy Input', () => {
    expect(renderMarkdown('')).toBe('')
    expect(renderMarkdown(null)).toBe('')
    expect(renderMarkdown(undefined)).toBe('')
  })

  it('strippt <script>-Tags aus inline-HTML', () => {
    const html = renderMarkdown('Hallo <script>alert(1)</script> Welt')
    expect(html).not.toContain('<script')
    expect(html).not.toContain('alert(1)')
    expect(html).toContain('Hallo')
    expect(html).toContain('Welt')
  })

  it('strippt onerror-Attribute aus <img>', () => {
    const html = renderMarkdown('![](x.png "x")<img src=x onerror=alert(1)>')
    expect(html).not.toMatch(/onerror=/i)
    expect(html).not.toContain('alert(1)')
  })

  it('strippt <iframe>', () => {
    const html = renderMarkdown('<iframe src="https://evil.example/"></iframe>')
    expect(html).not.toContain('<iframe')
    expect(html).not.toContain('evil.example')
  })

  it('entfernt javascript:-Links', () => {
    const html = renderMarkdown('[klick](javascript:alert(1))')
    expect(html).not.toMatch(/href="javascript:/i)
    expect(html).not.toContain('alert(1)')
  })

  it('strippt <style>', () => {
    const html = renderMarkdown('<style>body{display:none}</style>Text')
    expect(html).not.toContain('<style')
    expect(html).toContain('Text')
  })

  it('behält normale HTTP/HTTPS-Links', () => {
    const html = renderMarkdown('[link](https://example.org/foo)')
    expect(html).toContain('href="https://example.org/foo"')
  })

  it('behält Code-Blöcke', () => {
    const html = renderMarkdown('```js\nconsole.log("ok")\n```')
    expect(html).toMatch(/<pre>.*<code/s)
    expect(html).toContain('console.log')
  })

  it('rendert Confidence-Marker als Badge-Spans', () => {
    const html = renderMarkdown(
      '<span class="conf-badge conf-low">⚠️ Low-Confidence-Hinweis (score=0.15)</span>: Claim'
    )

    expect(html).toContain('conf-badge')
    expect(html).toContain('conf-low')
    expect(html).toContain('Low-Confidence-Hinweis')
  })
})
