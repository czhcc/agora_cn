import { computed, inject, provide, type ComputedRef, type InjectionKey } from 'vue'
import { useI18n } from 'vue-i18n'
import { ontologyChineseLabels } from '@/contracts/ontologyDisplayContract'
import { chineseGraphTypeLabels } from '@/i18n/graphTypeLabels'

const labelsKey: InjectionKey<ComputedRef<Map<string, string>>> = Symbol('graphTypeLabels')

export function provideGraphTypeLabels(ontology: ComputedRef<Record<string, unknown> | null | undefined>) {
  provide(labelsKey, computed(() => ontologyChineseLabels(ontology.value)))
}

export function useGraphTypeLabel() {
  const { locale } = useI18n()
  const labels = inject(labelsKey, computed(() => new Map<string, string>()))
  return (identifier: string) => locale.value === 'zh-CN'
    ? labels.value.get(identifier) || chineseGraphTypeLabels[identifier] || identifier
    : identifier
}
