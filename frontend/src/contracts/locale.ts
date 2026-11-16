/** UI languages are independent of simulation and report languages. */
export const UI_LOCALES = [
  { value: 'de', label: 'Deutsch' },
  { value: 'en', label: 'English' },
  { value: 'zh-CN', label: '简体中文' },
] as const

export type UiLocale = typeof UI_LOCALES[number]['value']

export function isUiLocale(value: string): value is UiLocale {
  return UI_LOCALES.some((option) => option.value === value)
}
