import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createI18n } from 'vue-i18n'
import en from '../locales/en.json'
import zhCN from '../locales/zh-CN.json'

function flatten(value: unknown, path = ''): Record<string, string> {
  if (typeof value === 'string') return { [path]: value }
  return Object.fromEntries(Object.entries(value as Record<string, unknown>).flatMap(
    ([key, child]) => Object.entries(flatten(child, path ? `${path}.${key}` : key)),
  ))
}

const english = flatten(en)
const chinese = flatten(zhCN)

describe('Chinese catalog', () => {
  it('covers every English message, including nested arrays', () => {
    expect(Object.keys(chinese).sort()).toEqual(Object.keys(english).sort())
  })

  it('preserves interpolation parameters and plural branches in every message', () => {
    for (const [key, original] of Object.entries(english)) {
      const translated = chinese[key]!
      expect(translated.match(/\{[^{}]+\}/g)?.sort() ?? [], key)
        .toEqual(original.match(/\{[^{}]+\}/g)?.sort() ?? [])
      expect(translated.split(' | ').length, key).toBe(original.split(' | ').length)
      if (original.trim()) expect(translated.trim(), key).not.toBe('')
      expect(translated, key).not.toContain('\uFFFD')
      expect(translated, key).not.toContain('????')
    }
  })

  it('compiles every message without malformed interpolation syntax', () => {
    const onError = vi.fn()
    const instance = createI18n({
      legacy: false, locale: 'zh-CN', fallbackLocale: false,
      messages: { 'zh-CN': zhCN }, onError,
    })
    const parameters = Object.fromEntries(
      Object.values(chinese).flatMap((text) => [...text.matchAll(/\{(\w+)\}/g)]
        .map((match) => [match[1]!, '2'])),
    )
    for (const key of Object.keys(chinese)) instance.global.t(key, parameters)
    expect(onError).not.toHaveBeenCalled()
  })
})

describe('UI locale persistence', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.resetModules()
  })
  afterEach(() => {
    localStorage.clear()
    vi.restoreAllMocks()
  })

  it('switches to Chinese and restores it on a new page load', async () => {
    const first = await import('../index')
    first.setLocale('zh-CN')
    expect(first.default.global.t('auth.login.tokenTitle')).toBe('管理员登录')
    expect(document.documentElement.lang).toBe('zh-CN')
    expect(localStorage.getItem('agora.locale')).toBe('zh-CN')
    vi.resetModules()
    const reloaded = await import('../index')
    expect(reloaded.currentLocale()).toBe('zh-CN')
    expect(reloaded.default.global.t('common.save')).toBe('保存')
  })

  it('keeps the existing default and ignores unsupported languages', async () => {
    localStorage.setItem('agora.locale', 'invalid')
    const locale = await import('../index')
    expect(locale.currentLocale()).toBe('de')
    locale.setLocale('zh-CN')
    locale.setLocale('invalid')
    expect(locale.currentLocale()).toBe('zh-CN')
  })

  it('switches without crashing when browser storage is unavailable', async () => {
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => { throw new Error('blocked') })
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => { throw new Error('blocked') })
    const locale = await import('../index')
    locale.setLocale('zh-CN')
    expect(locale.currentLocale()).toBe('zh-CN')
    expect(document.documentElement.lang).toBe('zh-CN')
  })
})
