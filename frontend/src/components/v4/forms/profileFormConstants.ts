/**
 * Client-seitige Vorprüf-Konstanten für den Avatar-Upload.
 *
 * Muss in Grenzwerten mit backend/app/contracts/user_profile_contract.py
 * (`ALLOWED_AVATAR_MIME_TYPES`, `MAX_AVATAR_BYTES`) übereinstimmen — die
 * serverseitige Prüfung (inkl. Magic-Bytes) bleibt die eigentliche
 * Autorität, das hier ist nur eine schnelle Client-Vorprüfung.
 */
export const ALLOWED_AVATAR_MIME_TYPES: ReadonlySet<string> = new Set([
  'image/png',
  'image/jpeg',
  'image/webp',
])

export const MAX_AVATAR_BYTES = 2 * 1024 * 1024

/** Browser/workstation timezone; persisted profiles always use an IANA identifier. */
export function systemTimezone(): string {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC'
  } catch {
    return 'UTC'
  }
}

/** Gängige IANA-Zeitzonen als Datalist-Vorschläge (Freitextfeld bleibt möglich). */
export const TIMEZONE_SUGGESTIONS: readonly string[] = [
  'Europe/Berlin',
  'Europe/Vienna',
  'Europe/Zurich',
  'Europe/London',
  'Europe/Paris',
  'Europe/Madrid',
  'America/New_York',
  'America/Los_Angeles',
  'America/Chicago',
  'Asia/Shanghai',
  'Asia/Tokyo',
  'Asia/Singapore',
  'Asia/Dubai',
  'Australia/Sydney',
  'UTC',
]
