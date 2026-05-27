# MarinMagic

Convert spreadsheet data into structured rich text for your content management system (CMS).

MarinMagic is a browser-based utility that:

* uploads CSV, XLSX, or JSON files
* converts rows into structured HTML
* previews rendered content and raw HTML
* supports rich text copy/paste into CMS editors
* allows drag-and-drop field ordering
* includes in-app Help and Updates tabs

---

# Features

## File support

* `.csv`
* `.xlsx`
* `.json`

## Structured output

Generate:

* `h2`–`h6` headings
* unordered lists (`ul` / `li`)
* clean CMS-ready HTML

## Preview modes

### Text preview

Rendered rich text preview for CMS copy/paste.

### HTML preview

Raw HTML output for source/code editing.

## Copy tools

### Copy rich text

Copies rendered content for visual CMS editors.

### Copy HTML source

Copies exact HTML markup.

## Field mapping

* choose heading column
* choose heading level
* select included fields
* drag/drop reorder list items

## GitHub updates tab

Displays latest commits from:

[https://github.com/marincountygov/marinmagic](https://github.com/marincountygov/marinmagic)

Includes:

* commit title
* commit description
* date/time
* GitHub commit link

## Accessibility improvements

Includes:

* improved color contrast
* larger touch targets
* keyboard focus styles
* ARIA tab semantics
* reduced motion support

---

# How it works

## Example input

| Name               | Address              | Phone        |
| ------------------ | -------------------- | ------------ |
| Marin Civic Center | 3501 Civic Center Dr | 415-555-1234 |

## Example output

```html
<h2>Marin Civic Center</h2>
<ul>
  <li>Address: 3501 Civic Center Dr</li>
  <li>Phone: 415-555-1234</li>
</ul>
```

---

# Usage

## 1. Prepare your spreadsheet

* remove formulas
* use plain text values
* ensure headers are labeled clearly
* export/save as CSV if needed

## 2. Upload file

Supported formats:

* CSV
* XLSX
* JSON

## 3. Configure field mapping

### Select heading column

Used as the generated heading.

### Select heading level

Choose:

* h2
* h3
* h4
* h5
* h6

### Select columns for list

Choose which columns appear as list items.

### Reorder list items

Drag/drop rows to change output order.

## 4. Generate preview

Click:

`Generate preview`

## 5. Copy output

### Visual CMS editor

Use:

`Copy rich text`

### Source/code editor

Use:

`Copy HTML source`

---

# Tabs

## Home

Main conversion tool.

## Help

Displays workflow instructions for CMS publishing.

## Updates

Loads latest GitHub commits via GitHub API.

---

# Technical notes

## Frontend stack

* HTML
* CSS
* Vanilla JavaScript
* SheetJS (`xlsx`)
* Font Awesome
* Google Fonts

## External libraries

### SheetJS

[https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js](https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js)

### Font Awesome

[https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css](https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css)

---

# GitHub API

Updates tab uses:

```text
https://api.github.com/repos/marincountygov/marinmagic/commits?per_page=10
```

---

# CMS notes

Some CMS editors sanitize pasted HTML.

Recommended workflow:

## Visual editor

Use:

* Copy rich text

## Source/code editor

Use:

* Copy HTML source

---

# Accessibility

MarinMagic includes:

* WCAG-conscious contrast
* keyboard focus indicators
* large touch targets
* semantic tab roles
* reduced motion support

---

# License

County of Marin
