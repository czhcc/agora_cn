<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import StepEnvSetupView from '@/views/v4/steps/StepEnvSetupView.vue'
import { useRunWorkspaceContext } from '@/composables/run/useRunWorkspace'
import { PersonaSetTestId } from '@/contracts/testIds'

defineProps<{ simulationId: string }>()
const { t } = useI18n()
const ws = useRunWorkspaceContext()
const projectId = computed(() => ws.data.value?.projectId)
</script>

<template>
  <section :data-testid="PersonaSetTestId.runRoot">
    <StepEnvSetupView
      v-if="projectId"
      :key="simulationId"
      :project-id="projectId"
      :simulation-id="simulationId"
      embedded
    />
    <p v-else role="alert">{{ t('views.run.disabled.noProject') }}</p>
  </section>
</template>
