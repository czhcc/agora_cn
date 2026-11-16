import { afterEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import i18n, { setLocale } from '@/i18n'
import LanguageSwitcher from '../LanguageSwitcher.vue'
import LoginView from '@/views/auth/LoginView.vue'

const signInWithToken = vi.hoisted(() => vi.fn())
vi.mock('@/store/auth', () => ({
  useAuthStore: () => ({ jwtEnabled: false, signInWithToken }),
}))
vi.mock('vue-router', () => ({
  useRouter: () => ({ replace: vi.fn() }),
  useRoute: () => ({ query: {} }),
}))

afterEach(() => { setLocale('de'); localStorage.clear() })

describe('LanguageSwitcher', () => {
  it('also translates an already-visible rejected-token error', async () => {
    setLocale('de')
    signInWithToken.mockRejectedValue(new Error('rejected'))
    const wrapper = mount({
      components: { LanguageSwitcher, LoginView },
      template: '<LanguageSwitcher /><LoginView />',
    }, { global: { plugins: [i18n], stubs: { RouterLink: true } } })
    await wrapper.get('#login-token').setValue('invalid-test-token')
    await wrapper.get('form').trigger('submit')
    await flushPromises()
    expect(wrapper.get('[role="alert"]').text()).toContain('Das Token wurde abgelehnt')
    await wrapper.get('select').setValue('zh-CN')
    expect(wrapper.get('[role="alert"]').text()).toBe('令牌无效，请检查输入的值。')
    expect(wrapper.get('h1').text()).toBe('管理员登录')
    wrapper.unmount()
  })
  it('offers Chinese, English and German and immediately translates the interface', async () => {
    setLocale('de')
    const wrapper = mount(LanguageSwitcher, { global: { plugins: [i18n] } })
    const select = wrapper.get('select')
    expect(wrapper.findAll('option').map((option) => option.text()))
      .toEqual(['Deutsch', 'English', '简体中文'])
    await select.setValue('zh-CN')
    expect(select.attributes('aria-label')).toBe('界面语言')
    expect(i18n.global.t('auth.login.submit')).toBe('登录')
    expect(localStorage.getItem('agora.locale')).toBe('zh-CN')
    expect(document.documentElement.lang).toBe('zh-CN')
    await select.setValue('en')
    expect(i18n.global.t('auth.login.submit')).toBe('Sign in')
    expect(select.attributes('aria-label')).toBe('Language')
    setLocale('de')
    await nextTick()
    expect((select.element as HTMLSelectElement).value).toBe('de')
    wrapper.unmount()
  })
})
