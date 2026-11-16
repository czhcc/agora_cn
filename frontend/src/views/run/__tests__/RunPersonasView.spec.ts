import { beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { ref } from 'vue'
import { createPinia } from 'pinia'
import RunPersonasView from '../personas/RunPersonasView.vue'
import { readPendingRunParams } from '@/composables/new-run/pendingRunParams'

const mocks = vi.hoisted(() => ({ push: vi.fn(), crumbs: vi.fn() }))
const data = ref<{ projectId: string | null }>({ projectId: 'proj_1' })
vi.mock('@/composables/run/useRunWorkspace', () => ({
  useRunWorkspaceContext: () => ({ data }),
}))
vi.mock('vue-router', () => ({
  useRouter: () => ({ push: mocks.push }),
  useRoute: () => ({ query: {} }),
}))
vi.mock('@/composables/useShellBreadcrumbs', () => ({
  useShellBreadcrumbs: mocks.crumbs,
  crumbForId: (id: string) => ({ label: id }),
}))
vi.mock('vue-i18n', () => ({ useI18n: () => ({ t: (key: string) => key }) }))

function render() {
  return mount(RunPersonasView, {
    props: { simulationId: 'sim_personas' },
    global: {
      plugins: [createPinia()],
      mocks: { $t: (key: string) => key },
      stubs: {
        PipelineStepper: true,
        PageHeader: true,
        StepModelOverrideChip: true,
        Step2EnvSetup: {
          name: 'Step2EnvSetup', props: ['simulationId'],
          emits: ['next-step', 'go-back'], template: '<div data-testid="profiles" />',
        },
      },
    },
  })
}

describe('Run personas inside the workspace', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    data.value = { projectId: 'proj_1' }
    localStorage.clear()
  })

  it('loads the concrete simulation and preserves the workspace header and breadcrumbs', () => {
    const wrapper = render()
    expect(wrapper.getComponent({ name: 'Step2EnvSetup' }).props('simulationId')).toBe('sim_personas')
    expect(wrapper.find('pipeline-stepper-stub').exists()).toBe(false)
    expect(wrapper.find('page-header-stub').exists()).toBe(false)
    expect(wrapper.find('h2').text()).toBe('views.stepEnvSetup.title')
    expect(mocks.crumbs).not.toHaveBeenCalled()
  })

  it('returns to the graph tab of the same run', async () => {
    const wrapper = render()
    await wrapper.getComponent({ name: 'Step2EnvSetup' }).vm.$emit('go-back')
    expect(mocks.push).toHaveBeenCalledWith({ name: 'RunGraph', params: { simulationId: 'sim_personas' } })
  })

  it('hands the configured start parameters to the simulation tab', async () => {
    const wrapper = render()
    await wrapper.getComponent({ name: 'Step2EnvSetup' }).vm.$emit('next-step', {
      simulationId: 'sim_personas', maxRounds: 12, simulationDays: 2,
    })
    expect(mocks.push).toHaveBeenCalledWith({ name: 'RunSimulationFeed', params: { simulationId: 'sim_personas' } })
    expect(readPendingRunParams('sim_personas')).toMatchObject({ maxRounds: 12, simulationDays: 2 })
  })

  it('shows missing project information instead of loading profiles for the wrong ID', () => {
    data.value = { projectId: null }
    const wrapper = render()
    expect(wrapper.find('[data-testid="profiles"]').exists()).toBe(false)
    expect(wrapper.get('[role="alert"]').text()).toBe('views.run.disabled.noProject')
  })
})
