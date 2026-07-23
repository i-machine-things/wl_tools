# Standards & Practices — CodeRabbit Review Log

<!--
Add entries here each time a CodeRabbit or human review surfaces a new finding.
Format:

## YYYY-MM-DD — `path/to/file` (short description)

**Review:** WHAT WAS FLAGGED
**Result:** outcome / resolution

### Findings

1. **Title**
   - Detail
   - Fix applied
-->

## 2026-07-23 — `public/index.html` (widget span defaults, resize cols, innerHTML XSS)

**Review:** CodeRabbit PR #8 — 3 findings in index.html (sample_dashboard.html comments were moot after deprecation commit)
**Result:** All three fixed in the same commit

### Findings

1. **Default widget span ignores per-widget defaults**
   - `applyWidgetSpans` used `wSpans[wid] || 1` for every widget; `w-forecast` should default to span4 on first load with no localStorage
   - Fix: added `DEFAULT_SPANS = {'w-forecast': 4}` and `_resolveSpan(wid)` helper used in `applyWidgetSpans`, `cycleWidgetSpan`, and the span indicator in `_renderOverlays`

2. **`startCardResize` hardcodes `cols = 4`**
   - Drag-resize column math was wrong at responsive breakpoints (≤900px = 2 cols, ≤480px = 1 col)
   - Fix: derive cols from `getComputedStyle(row).gridTemplateColumns.split(' ').length` at drag start

3. **`saved.label` interpolated directly into `innerHTML`**
   - `saved.label` comes from Nominatim's `display_name` and could contain `<`/`>` characters
   - Fix: leave `#fc-loc-status` empty in innerHTML template, then set via `statusEl.textContent`

## 2026-07-23 — `public/index.html` (resize curSpan, mock subtitle, err.message XSS)

**Review:** CodeRabbit second-pass on PR #8 fixes commit
**Result:** All three fixed

### Findings

1. **`startCardResize` initializes `curSpan` to 1, ignoring resolved default**
   - `wSpans[wid] || 1` doesn't account for `DEFAULT_SPANS`; a click-without-drag on w-forecast persists span=1, collapsing the full-row card
   - Fix: use `_resolveSpan(wid)` to initialise `curSpan`

2. **Mock-mode `fetchForecast` doesn't update `#fc-subtitle`**
   - Subtitle would stay "Loading…" indefinitely when in mock mode
   - Fix: call `_updateFcSubtitle('Sample Data')` before `renderForecast(MOCK_FORECAST)`

3. **`err.message` interpolated into `innerHTML` in connection error block**
   - API error messages are untrusted and could contain HTML
   - Fix: set innerHTML without the message, then write via `document.getElementById('err-msg').textContent`
