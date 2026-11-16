import { z } from 'zod'

/** Additive presentation metadata; identifiers remain unchanged. */
export const OntologyDisplayTypeSchema = z.object({
  name: z.string(),
  display_name_zh: z.string().max(80).nullable().optional(),
}).passthrough()

export function ontologyChineseLabels(ontology: Record<string, unknown> | null | undefined) {
  const labels = new Map<string, string>()
  for (const field of ['entity_types', 'edge_types', 'relation_types']) {
    const types = ontology?.[field]
    if (!Array.isArray(types)) continue
    for (const item of types) {
      const parsed = OntologyDisplayTypeSchema.safeParse(item)
      if (parsed.success && parsed.data.display_name_zh?.trim()) {
        labels.set(parsed.data.name, parsed.data.display_name_zh.trim())
      }
    }
  }
  return labels
}
