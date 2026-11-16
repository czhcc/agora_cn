import { z } from 'zod'

export const SimulationLanguageSchema = z.enum(['de', 'en', 'zh'])
export type SimulationLanguage = z.infer<typeof SimulationLanguageSchema>
