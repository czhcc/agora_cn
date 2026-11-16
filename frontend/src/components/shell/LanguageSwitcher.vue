<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { UI_LOCALES } from '@/contracts/locale'
import { setLocale } from '@/i18n'

const { t, locale } = useI18n()

function changeLanguage(event: Event): void {
  setLocale((event.target as HTMLSelectElement).value)
}
</script>

<template>
  <label class="language-switcher">
    <span class="language-switcher__label">{{ t('language.label') }}</span>
    <select
      :value="locale"
      :aria-label="t('language.label')"
      data-testid="language-switcher"
      @change="changeLanguage"
    >
      <option v-for="option in UI_LOCALES" :key="option.value" :value="option.value" :lang="option.value">
        {{ option.label }}
      </option>
    </select>
  </label>
</template>

<style scoped>
.language-switcher {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--fg-muted);
  font-size: 12px;
}
.language-switcher select {
  max-width: 130px;
  min-height: 32px;
  padding: 4px 8px;
  border: 1px solid var(--rule-strong);
  border-radius: var(--r-sm, 6px);
  background: var(--surface-base, white);
  color: var(--fg, inherit);
  font: inherit;
  cursor: pointer;
}
.language-switcher select:focus-visible {
  outline: 2px solid var(--accent, #6d3fd1);
  outline-offset: 2px;
}
@media (max-width: 600px) {
  .language-switcher__label { display: none; }
}
</style>
