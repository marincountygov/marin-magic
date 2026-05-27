# MarinMagic SpecOps

## 1. Overview

MarinMagic is a browser-based utility that converts structured tabular data into CMS-ready rich text and HTML. It accepts CSV, XLSX/XLS, and JSON files, lets users map fields to headings and list items, then generates sorted HTML output that can be copied as rich text, copied as source HTML, or downloaded as an HTML file.

The tool is intended for County of Marin content editors who need to transform spreadsheet-style content into clean, repeatable CMS text-section content without manually formatting each item.

## 2. Primary users

* CMS content editors
* Digital services staff
* Department content owners preparing structured public information
* Support staff converting spreadsheets into web-ready content

## 3. User goals

Users should be able to:

1. Upload a supported data file.
2. Select which column becomes the heading for each generated section.
3. Select the heading level used for generated headings.
4. Select which columns become list items.
5. Drag selected list columns into the desired display order.
6. Preview the generated result as rendered rich text.
7. Preview the generated source HTML.
8. Copy rich text for CMS pasting.
9. Copy raw HTML source.
10. Download the generated HTML.
11. Reset the tool and start over.
12. View help instructions.
13. View recent GitHub commit updates when available.
14. Submit feedback through the linked Asana form.

## 4. Supported input formats

### CSV

CSV files are parsed client-side. The parser supports:

* Comma-separated fields
* Quoted fields
* Escaped double quotes inside quoted fields
* Windows, Unix, and old Mac line endings
* Filtering out fully blank rows

### XLSX/XLS

Spreadsheet files are parsed client-side using the XLSX library. The first worksheet is used. The sheet is converted into a two-dimensional table where the first row is treated as the header row.

### JSON

JSON input must be an array of objects. MarinMagic derives the header list from all unique object keys, then converts each object into a row ordered by those keys.

Invalid JSON, or JSON that is not an array of objects, should show a readable failure status.

## 5. Data model

MarinMagic uses three primary state values:

* `headers`: first row of the loaded table, used as field labels
* `rows`: all non-empty rows after the header row
* `output`: generated HTML string

A loaded file is considered usable only when both headers and at least one non-empty data row are present.

## 6. Core workflow

### 6.1 Initial state

On page load:

* Home tab is visible.
* Text preview tab is visible.
* File type defaults to CSV.
* Upload input accepts CSV files.
* Status reads: `Select a file to begin.`
* Mapping panel is hidden.
* Preview and HTML source panes are empty.

### 6.2 File type selection

When the user changes file type:

* File input accept rules update to match the selected type.
* Existing selected file is cleared.
* Preview output is cleared.
* HTML output is cleared.
* Mapping panel is hidden.
* Internal state is reset.
* Preview mode returns to Text.
* Status returns to `Select a file to begin.`

### 6.3 File upload and parse

When a user selects a file:

1. The selected file type controls the parsing method.
2. Status updates to indicate the file is being read.
3. The file is parsed client-side.
4. Parsed data is loaded into the shared table model.
5. The first row becomes headers.
6. Non-empty remaining rows become data rows.
7. If data is usable, mapping controls render and preview is generated automatically.
8. If data is not usable, mapping and preview remain hidden/empty and status reports no usable data.

### 6.4 Field mapping

When a usable file is loaded:

* Each header is added to the heading-column selector.
* Each header is also added as a draggable checkbox row.
* Checkbox rows default to checked except for the first column.
* The selected heading column is excluded from generated list items even if its checkbox is checked.
* Blank header labels are displayed as `Column N` in the UI.

### 6.5 Drag ordering

Users can drag column checkbox rows to control the order of generated list items.

Operational behavior:

* Dragging adds a visual dragging state.
* Drag-over adds a visual target state.
* Dropping before or after a target reorders the checkbox row.
* The generated list item order follows the current DOM order of checked checkbox rows.

### 6.6 Generate preview

When preview is generated:

1. The selected heading column is read.
2. The selected heading level is read.
3. Checked list columns are collected in current visual order.
4. The heading column is removed from list columns.
5. Rows with blank heading values are excluded.
6. Remaining records are sorted alphabetically by heading, case-insensitive.
7. Each record becomes one heading and one unordered list.
8. Empty list item values are omitted.
9. Generated HTML is stored as `output`.
10. Rendered preview receives `output` as HTML.
11. HTML preview receives `output` as escaped text.
12. Status updates to `Preview generated.`

## 7. Output rules

For each valid row, MarinMagic generates:

```html
<HEADING_TAG>Heading value</HEADING_TAG><ul><li>Column label: Cell value</li></ul>
```

Where:

* `HEADING_TAG` is one of `h2`, `h3`, `h4`, `h5`, or `h6`.
* Heading value comes from the selected heading column.
* List item labels come from the selected column headers.
* List item values come from the corresponding row cells.
* Blank list item values are skipped.
* Blank heading rows are skipped entirely.
* Records are sorted by heading.

## 8. Escaping and content safety

Generated output escapes user-provided data before injecting it into generated HTML. The escaping routine converts:

* `&` to `&amp;`
* `<` to `&lt;`
* `>` to `&gt;`
* `"` to `&quot;`

This reduces the risk of uploaded file content becoming executable HTML or script in the generated preview/output.

## 9. Copy and download operations

### Rich text copy

The rich text copy button:

1. Creates a temporary hidden editable element.
2. Inserts the current generated HTML into it.
3. Selects the temporary content.
4. Uses `document.execCommand('copy')`.
5. Removes the temporary element.
6. Updates status to `Copied rich text for paste.` on success.
7. Updates status to `Rich copy failed.` on failure.

### HTML source copy

The HTML source copy button:

1. Writes the current `output` string to the clipboard.
2. Updates status to `Copied HTML source.` on success.
3. Updates status to `Copy failed.` on failure.

### Download HTML

The download button:

1. Creates a text/html Blob from the current output.
2. Creates a temporary object URL.
3. Downloads the file as `index.html`.
4. Updates status to `HTML file downloaded.`

## 10. Navigation tabs

MarinMagic has three main sections:

* Home
* Help
* Updates

Only one main section is visible at a time. Tab buttons update active state and `aria-selected` values.

## 11. Preview tabs

The preview card has two modes:

* Text: rendered rich text preview
* HTML: raw generated HTML source

Only one preview pane is visible at a time. Tab buttons update active state and `aria-selected` values.

## 12. Help content

The Help tab provides user-facing instructions for:

* Preparing CSV data
* Uploading data into MarinMagic
* Selecting heading and list columns
* Generating a preview
* Copying generated rich text
* Pasting into the CMS
* Reviewing and publishing the CMS page

## 13. Updates panel

When the Updates tab is selected for the first time, MarinMagic requests the 10 latest commits from:

`https://api.github.com/repos/marincountygov/marinmagic/commits?per_page=10`

Expected behavior:

* Show `Loading latest commits...` while loading.
* Show recent commit title, date, optional description, and commit link on success.
* Show `No recent commits found.` if the API returns no commits.
* Show `Could not load updates right now.` on error.
* Load commits only once per page session.

## 14. Feedback link

A fixed feedback button appears in the lower-right corner and opens the Asana feedback form in a new browser tab.

## 15. Accessibility requirements

The interface should preserve:

* Proper tab roles and tabpanel associations.
* `aria-selected` updates on active tabs.
* Visible focus outlines on links, buttons, inputs, and selects.
* Semantic headings and labels.
* Button text or accessible labels for icon-only copy buttons.

## 16. Error and empty-state handling

### File read errors

* CSV/JSON read failure: `Could not read the CSV/JSON file.`
* XLSX read failure: `Could not read the XLSX file.`

### Invalid or empty data

If parsed data has no headers or no usable data rows:

* Mapping panel is hidden.
* Preview panes are cleared.
* Status reads: `No usable data found.`

### Preview generation failure

If preview generation fails:

* Status reads: `Could not generate preview.`
* Error is logged to console.

### Updates load failure

If GitHub commit loading fails:

* Status reads: `Could not load updates right now.`
* Error is logged to console.

## 17. Operational constraints

* All file parsing happens in the browser.
* Uploaded files are not sent to a server by this application logic.
* GitHub commit data is fetched from the public GitHub API.
* The XLSX parser depends on the external SheetJS CDN script.
* Icons depend on Font Awesome CDN.
* Fonts depend on Google Fonts.
* If third-party CDN resources fail, related styling, icons, or XLSX parsing may be affected.

## 18. Acceptance criteria

### File upload

* Given a valid CSV, XLSX, or JSON file, when the user uploads it, then mapping controls appear and a preview is generated.
* Given an empty file or file without usable rows, when the user uploads it, then the app shows `No usable data found.`
* Given invalid JSON, when the user uploads it, then the app shows a JSON read failure.

### Mapping

* Given loaded data, when the user selects a heading column, then generated headings use that column.
* Given loaded data, when the user changes heading level, then generated heading tags use the selected level.
* Given checked list columns, when preview is generated, then those columns appear as list items.
* Given the heading column is checked as a list item, when preview is generated, then it is excluded from list items.

### Sorting and filtering

* Given rows with headings, when preview is generated, then records are sorted alphabetically by heading.
* Given rows with blank headings, when preview is generated, then those rows are omitted.
* Given blank list item values, when preview is generated, then those list items are omitted.

### Copy/download

* Given generated output, when the rich text copy button is selected, then the rendered HTML is copied for CMS paste.
* Given generated output, when the HTML copy button is selected, then raw HTML source is copied.
* Given generated output, when Download HTML is selected, then an `index.html` file is downloaded.

### Reset

* Given any loaded file and generated output, when Reset is selected, then file input, mapping panel, preview, HTML preview, and internal state are cleared.

### Updates

* Given network access to GitHub, when the Updates tab is opened, then the app displays up to 10 recent commits.
* Given GitHub is unavailable, when the Updates tab is opened, then the app shows a friendly error message.

## 19. Known improvement opportunities

* Revoke temporary object URLs after download to avoid unnecessary memory retention.
* Replace deprecated `document.execCommand('copy')` with the async Clipboard API where rich HTML clipboard support is available.
* Add validation for file type mismatch, such as selecting CSV but uploading JSON.
* Add keyboard-accessible reordering controls as an alternative to drag-and-drop.
* Add grouped preview output spacing for easier visual review.
* Add optional anchor-link generation if the CMS workflow later requires it.
* Add automated tests for CSV parsing edge cases, JSON conversion, field mapping, and HTML escaping.
* Add clearer handling for GitHub API rate limits.

## 20. Release/support notes

MarinMagic is a static, client-side utility. Operational support should focus on browser compatibility, CDN availability, user file quality, CMS paste behavior, and the availability of the GitHub commits endpoint used by the Updates panel.
