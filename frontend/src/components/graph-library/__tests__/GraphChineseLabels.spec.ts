import { flushPromises, mount } from '@vue/test-utils'
import { computed, defineComponent, h, nextTick } from 'vue'
import { createI18n } from 'vue-i18n'
import { describe, expect, it } from 'vitest'
import GraphReader from '../GraphReader.vue'
import { provideGraphTypeLabels } from '@/composables/graph-library/useGraphTypeLabel'
import { buildReaderModel } from '@/composables/graph-library/graphReaderModel'
import { CanvasStub, graphFixture, makeRouter } from './fixtures'
import zh from '@/i18n/locales/zh-CN.json'
import en from '@/i18n/locales/en.json'

describe('Chinese graph labels', () => {
  it('uses ontology metadata, preserves filter identifiers and switches locale reactively', async () => {
    const data = graphFixture()
    data.nodes[2]!.name = '黄仁勋'
    data.nodes[2]!.attributes = { aliases: ['Jensen Huang'] }
    const ontology = { entity_types: [{ name: 'Organisation', display_name_zh: '议事组织' }],
      edge_types: [{ name: 'KENNT', display_name_zh: '认识' }] }
    const Host = defineComponent({ setup() {
      provideGraphTypeLabels(computed(() => ontology))
      return () => h(GraphReader, { model: buildReaderModel(data), graphData: data })
    } })
    const router = makeRouter()
    await router.push('/graphs/proj_1')
    const i18n = createI18n({ legacy: false, locale: 'zh-CN', messages: { 'zh-CN': zh, en } })
    const wrapper = mount(Host, { global: { plugins: [i18n, router], stubs: { GraphCanvas: CanvasStub } } })
    await flushPromises()
    expect(wrapper.get('[data-type="Organisation"]').text()).toContain('议事组织')
    expect(wrapper.get('[data-type="Person"]').text()).toContain('人物')
    expect(wrapper.get('[data-type="Ort"]').text()).toContain('Ort')
    await wrapper.get('[data-type="Person"]').trigger('click')
    await wrapper.get('input[type="search"]').setValue('Jensen Huang')
    expect(wrapper.findAll('.gr__itemname').map(n => n.text())).toEqual(['黄仁勋'])
    expect(wrapper.get('[data-type="Person"]').attributes('aria-pressed')).toBe('true')
    i18n.global.locale.value = 'en'
    await nextTick()
    expect(wrapper.get('[data-type="Person"]').text()).toContain('Person')
    expect(data.nodes[2]!.labels).toEqual(['Person'])
    wrapper.unmount()
  })
})
