import { useMemo, useState } from 'react'
import type { ChangeEvent } from 'react'
import './App.css'

type EmployeeRow = {
  employee_id: string
  full_name: string
  employee_email: string
  position: string
  department: string
  latest_win: string
  recognition_category: string
  manager_name: string
  manager_position: string
  tone: string
  language: string
  gender: string
  photo_asset_id: string
}

/** Dedicated API port (avoid 8001 — often stacked stale listeners). Override with VITE_API_BASE_URL. */
const RECOGNITION_API_PORT = 8055

// Dev: same-origin /api → Vite proxy → http://127.0.0.1:8055
const API_BASE =
  import.meta.env.VITE_API_BASE_URL ??
  (import.meta.env.DEV ? '' : `http://127.0.0.1:${RECOGNITION_API_PORT}`)

function buildApiPath(path: string) {
  const base = (API_BASE || '').replace(/\/$/, '')
  const normalized = path.startsWith('/') ? path : `/${path}`
  return base ? `${base}${normalized}` : normalized
}

type GenerateCardPayload = {
  fingerprint?: string
  api_schema_version?: number
  photo_passed_to_model?: boolean
  photo_exact_overlay?: boolean
  photo_path_absolute?: string
  photo_path_used?: string
  project_root?: string
  prompt?: string
  image_base64?: string
}

const ORACLE_THEMES = ['Oracle Dark', 'Oracle Light']
const RECOGNITION_TYPES = [
  'Welcome',
  'Milestone',
  'Performance',
  'Team Contribution',
  'Culture & Values',
  'Promotion',
]
const SAMPLE_PHOTO_MAP: Record<string, string> = {
  E12345: '/employee-photos/sara-alfarsi.png',
  E12346: '/employee-photos/david-clarke.png',
  E12347: '/employee-photos/ana-rodrigues.png',
  photo_E12345_v1: '/employee-photos/sara-alfarsi.png',
}

function resolvePhotoAssetPath(photoAssetId: string, employeeId: string): string {
  const raw = photoAssetId
    .replace(/[\u201c\u201d]/g, '"')
    .replace(/[\u2018\u2019]/g, "'")
    .replace(/[\u200b\ufeff]/g, '')
    .trim()
    .replace(/\\/g, '/')
    .replace(/^['"]+|['"]+$/g, '')
    .replace(/[.,;:]+$/g, '')
  if (!raw) return SAMPLE_PHOTO_MAP[employeeId] || ''
  if (
    raw.startsWith('http://') ||
    raw.startsWith('https://') ||
    raw.startsWith('data:') ||
    raw.startsWith('/')
  ) {
    return raw
  }
  if (SAMPLE_PHOTO_MAP[raw]) return SAMPLE_PHOTO_MAP[raw]
  if (raw.includes('.')) return `/employee-photos/${raw}`
  return `/employee-photos/${raw}.png`
}

function parseCsvLine(line: string): string[] {
  const values: string[] = []
  let current = ''
  let inQuotes = false
  for (let i = 0; i < line.length; i += 1) {
    const ch = line[i]
    if (ch === '"') {
      const next = line[i + 1]
      if (inQuotes && next === '"') {
        current += '"'
        i += 1
      } else {
        inQuotes = !inQuotes
      }
      continue
    }
    if (ch === ',' && !inQuotes) {
      values.push(current.trim())
      current = ''
      continue
    }
    current += ch
  }
  values.push(current.trim())
  return values
}

function parseCsv(content: string): EmployeeRow[] {
  const lines = content.split(/\r?\n/).filter((line) => line.trim().length > 0)
  if (lines.length < 2) return []
  const headers = parseCsvLine(lines[0]).map((h) => h.trim().toLowerCase())

  return lines.slice(1).map((line) => {
    const values = parseCsvLine(line)
    const get = (name: string) => values[headers.indexOf(name)] ?? ''
    return {
      employee_id: get('employee_id') || `ID-${Math.random().toString(36).slice(2, 7)}`,
      full_name: get('full_name') || get('first_name') || 'Employee',
      employee_email:
        get('employee_email') ||
        get('work_email') ||
        get('email') ||
        get('e_mail') ||
        '',
      position: get('position') || get('role') || 'Team Member',
      department: get('department') || 'General',
      latest_win: get('latest_win') || 'Outstanding contribution',
      recognition_category: get('recognition_category') || 'Recognition',
      manager_name: get('manager_name') || 'Manager',
      manager_position: get('manager_position') || `${get('department') || 'Team'} Manager`,
      tone: get('tone') || 'professional and warm',
      language: get('language') || 'English',
      gender: get('gender') || 'female',
      photo_asset_id: get('photo_asset_id') || '',
    }
  })
}

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

function buildCardFilename(row: EmployeeRow, recognitionTypeLabel: string): string {
  const safeName = row.full_name.replace(/[^a-z0-9]+/gi, '_').toLowerCase()
  const typeSlug = recognitionTypeLabel.replace(/\s+/g, '_').toLowerCase()
  return `recognition_${safeName}_${typeSlug}.png`
}

function dataUrlToPngBlob(dataUrl: string): Blob | null {
  const m = /^data:image\/png;base64,(.+)$/i.exec(dataUrl.trim())
  if (!m?.[1]) return null
  try {
    const bin = atob(m[1])
    const bytes = new Uint8Array(bin.length)
    for (let i = 0; i < bin.length; i += 1) bytes[i] = bin.charCodeAt(i)
    return new Blob([bytes], { type: 'image/png' })
  } catch {
    return null
  }
}

/**
 * Build a mailto: link that Outlook / OWA / Apple Mail all accept.
 *
 * Important: do **not** percent-encode the entire address as `user%40domain.com`. Microsoft clients
 * often leave the **To** field blank when the mailbox part is fully encoded. RFC 6068 allows an
 * unencoded addr-spec here; we only use URLSearchParams for subject/body.
 */
function buildMailtoHref(recipient: string, subject: string, body: string): string {
  const addr = recipient.trim()
  const params = new URLSearchParams()
  params.set('subject', subject)
  params.set('body', body)
  return `mailto:${addr}?${params.toString()}`
}

/**
 * `navigator.share({ files })` on **Windows** (Edge/Chrome → Outlook / OWA) is buggy: it opens a
 * draft with an **empty** attachment named "no_name" and may omit **To**. Skip file-sharing on
 * Windows and use download + mailto instead.
 */
function shouldSkipWebShareFiles(): boolean {
  if (typeof navigator === 'undefined') return true
  return /Windows NT/i.test(navigator.userAgent || '')
}

function App() {
  const [rows, setRows] = useState<EmployeeRow[]>([])
  const [selectedRowId, setSelectedRowId] = useState<string>('')
  const [recognitionType, setRecognitionType] = useState(RECOGNITION_TYPES[2])
  const [recognitionContext, setRecognitionContext] = useState('')
  const [selectedTheme, setSelectedTheme] = useState<string>(ORACLE_THEMES[0])
  const [isGenerating, setIsGenerating] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')
  const [generatedImage, setGeneratedImage] = useState('')
  const [generatedPrompt, setGeneratedPrompt] = useState('')
  const [photoDebug, setPhotoDebug] = useState('')
  const [generatedAt, setGeneratedAt] = useState<Date | null>(null)
  /** Preview panel is shown only after the user successfully clicks Generate at least once. */
  const [previewShown, setPreviewShown] = useState(false)
  const [emailError, setEmailError] = useState('')

  const selectedRow = useMemo(
    () => rows.find((row) => row.employee_id === selectedRowId) ?? rows[0],
    [rows, selectedRowId],
  )
  const hasRows = rows.length > 0
  const employeePhotoFromSheet = resolvePhotoAssetPath(
    selectedRow?.photo_asset_id || '',
    selectedRow?.employee_id || '',
  )

  async function onUploadCsv(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    if (!file) return
    const text = await file.text()
    const parsed = parseCsv(text)
    setRows(parsed)
    setSelectedRowId(parsed[0]?.employee_id ?? '')
    setGeneratedImage('')
    setGeneratedPrompt('')
    setPhotoDebug('')
    setPreviewShown(false)
    setGeneratedAt(null)
    setEmailError('')
    setErrorMessage(parsed.length ? '' : 'No valid rows found in the CSV file.')
  }

  async function generateCard() {
    if (!selectedRow) {
      setErrorMessage('Please upload a CSV and select an employee first.')
      return
    }
    try {
      setIsGenerating(true)
      setErrorMessage('')
      const endpoint = buildApiPath('/api/generate-card')
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          employee_name: selectedRow.full_name,
          manager_name: selectedRow.manager_name,
          manager_position: selectedRow.manager_position,
          recognition_type: recognitionType,
          theme: selectedTheme,
          has_photo: Boolean(employeePhotoFromSheet),
          photo_asset_id: employeePhotoFromSheet,
        }),
      })
      const payload = await response.json()
      if (!response.ok) {
        throw new Error(payload?.detail || 'Generation failed')
      }
      const p = payload as GenerateCardPayload
      setGeneratedImage(`data:image/png;base64,${p.image_base64 ?? ''}`)
      setGeneratedPrompt(p.prompt || '')
      setGeneratedAt(new Date())
      setPreviewShown(true)
      const exactOverlay = p.photo_exact_overlay === true
      setPhotoDebug(
        [
          `endpoint=${endpoint}`,
          `fingerprint=${p.fingerprint ?? '?'}`,
          `schema=${p.api_schema_version ?? '?'}`,
          `exact_overlay=${exactOverlay}`,
          `requested_photo=${employeePhotoFromSheet || '(none)'}`,
          `resolved=${p.photo_path_absolute || p.photo_path_used || '(none)'}`,
        ]
          .filter(Boolean)
          .join(' | '),
      )
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : 'Failed to generate card.')
    } finally {
      setIsGenerating(false)
    }
  }

  function downloadImage() {
    if (!generatedImage || !selectedRow) return
    const a = document.createElement('a')
    a.href = generatedImage
    a.download = buildCardFilename(selectedRow, recognitionType)
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
  }

  /**
   * Email flow:
   * - **Mobile / macOS (not Windows):** try Web Share with PNG attachment when supported.
   * - **Windows:** never use share-with-files (Outlook/OWA bug: empty "no_name" attachment, blank To).
   *   Always save the PNG, then open mailto with an **unencoded** address in `mailto:user@host?...`.
   * - **mailto cannot embed binary attachments** in the URL; the downloaded file must be attached manually
   *   on Windows after the draft opens (we say so in the body).
   */
  async function composeEmailWithCard() {
    if (!generatedImage || !selectedRow) return
    setEmailError('')
    const to = selectedRow.employee_email.trim()
    if (!to) {
      setEmailError(
        'No employee email for this row. Add an employee_email column (or email / work_email) to your CSV.',
      )
      return
    }
    if (!EMAIL_RE.test(to)) {
      setEmailError('Employee email in the CSV does not look valid. Check the employee_email field.')
      return
    }

    const filename = buildCardFilename(selectedRow, recognitionType)
    const blob = dataUrlToPngBlob(generatedImage)
    if (!blob || blob.size === 0) {
      setEmailError('Could not read the generated image data (empty file). Generate the card again.')
      return
    }
    const file = new File([blob], filename, { type: 'image/png' })

    const firstName = selectedRow.full_name.split(/\s+/)[0] || selectedRow.full_name
    const plainBody = [
      `Hi ${firstName},`,
      '',
      'Please find your recognition card attached.',
      '',
      'Best regards',
    ].join('\n')

    const plainSubject = `${recognitionType} recognition`

    const sharePayload: ShareData & { files?: File[] } = {
      files: [file],
      title: `Recognition — ${selectedRow.full_name}`,
      text: plainBody,
    }

    if (
      !shouldSkipWebShareFiles() &&
      navigator.share &&
      typeof navigator.canShare === 'function' &&
      navigator.canShare(sharePayload)
    ) {
      try {
        await navigator.share(sharePayload)
        return
      } catch (err: unknown) {
        const name = err instanceof Error ? err.name : ''
        if (name === 'AbortError') return
      }
    }

    downloadImage()
    const tipLines = shouldSkipWebShareFiles()
      ? [
          plainBody,
          '',
          '---',
          `Attach the PNG that was just downloaded: ${filename}`,
          '(Check your Downloads folder, then use Attach / Insert in Outlook.)',
        ]
      : [
          plainBody,
          '',
          '---',
          `Tip: attach "${filename}" from your Downloads folder (it was just saved).`,
        ]
    const mailtoHref = buildMailtoHref(to, plainSubject, tipLines.join('\n'))
    window.setTimeout(() => {
      window.location.href = mailtoHref
    }, 400)
  }

  const recipientEmail = (selectedRow?.employee_email ?? '').trim()
  const hasValidRecipientEmail = EMAIL_RE.test(recipientEmail)

  const step1Status = hasRows ? 'is-complete' : 'is-focus'
  const step2Status = hasRows ? 'is-focus' : ''

  return (
    <>
      <main className="page">
        <section className="hero">
          <h1>Generate recognition cards in one click.</h1>
          <p className="hero-subtitle">
            Upload your employee data, choose a recognition type and theme, and we will compose a
            polished card with the employee photo, headline and a warm personal note — ready to send.
          </p>
        </section>

        <section className="layout-stack">
          <aside className="panel control-panel" aria-label="Card configuration">
            <div className={`step ${step1Status}`}>
              <div className="step-header">
                <span className="step-num" aria-hidden>
                  1
                </span>
                <h3>Upload employee file</h3>
              </div>
              <p className="helper">
                CSV columns: name, role, manager, photo path, and{' '}
                <strong>employee_email</strong> (or <strong>email</strong> / work_email) for sending
                from your mail app.
              </p>

              <div className="field">
                <label className="field-label" htmlFor="csv-input">
                  CSV file
                </label>
                <input
                  id="csv-input"
                  className="file-input"
                  type="file"
                  accept=".csv"
                  onChange={onUploadCsv}
                />
              </div>

              <div className="field">
                <label className="field-label" htmlFor="employee-select">
                  Recipient
                </label>
                <select
                  id="employee-select"
                  className="select"
                  value={selectedRow?.employee_id ?? ''}
                  onChange={(event) => setSelectedRowId(event.target.value)}
                  disabled={!hasRows}
                >
                  {!hasRows ? (
                    <option value="">Upload a CSV to populate this list…</option>
                  ) : null}
                  {rows.map((row) => (
                    <option key={row.employee_id} value={row.employee_id}>
                      {row.full_name} — {row.department}
                    </option>
                  ))}
                </select>
              </div>

              {hasRows && selectedRow ? (
                recipientEmail ? (
                  <p className="email-hint">
                    Employee email: <strong>{recipientEmail}</strong>
                  </p>
                ) : (
                  <p className="email-hint is-warn">
                    Add an <code>employee_email</code> column to enable “Email card”.
                  </p>
                )
              ) : null}
            </div>

            <div className={`step ${step2Status}`}>
              <div className="step-header">
                <span className="step-num" aria-hidden>
                  2
                </span>
                <h3>Choose recognition &amp; theme</h3>
              </div>

              <div className="field">
                <label className="field-label" htmlFor="recognition-type">
                  Recognition type
                </label>
                <select
                  id="recognition-type"
                  className="select"
                  value={recognitionType}
                  onChange={(event) => setRecognitionType(event.target.value)}
                >
                  {RECOGNITION_TYPES.map((type) => (
                    <option key={type} value={type}>
                      {type}
                    </option>
                  ))}
                </select>
              </div>

              <div className="field">
                <label className="field-label" htmlFor="recognition-context">
                  Context (optional)
                </label>
                <input
                  id="recognition-context"
                  className="input"
                  value={recognitionContext}
                  onChange={(event) => setRecognitionContext(event.target.value)}
                  placeholder="e.g. led the Q3 platform migration"
                />
              </div>

              <div className="field">
                <label className="field-label" htmlFor="theme-select">
                  Theme
                </label>
                <select
                  id="theme-select"
                  className="select"
                  value={selectedTheme}
                  onChange={(event) => setSelectedTheme(event.target.value)}
                >
                  {ORACLE_THEMES.map((theme) => (
                    <option key={theme} value={theme}>
                      {theme}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <button
              className="btn btn-primary generate-btn"
              onClick={generateCard}
              disabled={isGenerating || !selectedRow}
            >
              {isGenerating ? (
                <>
                  <span className="btn-spinner" aria-hidden /> Generating…
                </>
              ) : (
                <>Generate card</>
              )}
            </button>

            {errorMessage ? (
              <p className="error" role="alert">
                {errorMessage}
              </p>
            ) : null}
          </aside>

          {previewShown ? (
            <article className="panel preview-panel" aria-label="Generated preview">
              <header className="preview-header">
                <h2>Your card</h2>
                {generatedAt ? (
                  <span className="preview-meta">
                    Generated{' '}
                    {generatedAt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                ) : null}
              </header>

              <div className="preview-stage">
                {isGenerating ? (
                  <div className="preview-loading">
                    <div className="loader-ring" aria-hidden />
                    <span>Updating your card…</span>
                  </div>
                ) : generatedImage ? (
                  <img
                    className="preview-image"
                    src={generatedImage}
                    alt={`Recognition card for ${selectedRow?.full_name ?? 'employee'}`}
                  />
                ) : null}
              </div>

              {generatedImage && !isGenerating ? (
                <>
                  <div className="preview-actions">
                    <button type="button" className="btn btn-primary" onClick={downloadImage}>
                      Download PNG
                    </button>
                    <button
                      type="button"
                      className="btn btn-primary"
                      onClick={() => void composeEmailWithCard()}
                      disabled={!hasValidRecipientEmail}
                      title={
                        hasValidRecipientEmail
                          ? 'Open mail or share sheet with the card attached where supported'
                          : 'Add employee_email to your CSV'
                      }
                    >
                      Email card
                    </button>
                    <button type="button" className="btn btn-ghost" onClick={generateCard} disabled={isGenerating}>
                      Regenerate
                    </button>
                  </div>
                  {emailError ? (
                    <p className="error" role="alert">
                      {emailError}
                    </p>
                  ) : null}
                </>
              ) : null}

              {generatedPrompt ? (
                <details className="prompt-box">
                  <summary>Prompt &amp; debug</summary>
                  <div className="prompt-box-body">
                    <p className="mono">{generatedPrompt}</p>
                    {photoDebug ? <p>{photoDebug}</p> : null}
                  </div>
                </details>
              ) : null}
            </article>
          ) : null}
        </section>
      </main>
    </>
  )
}

export default App
