# Edge case catalogue

Pick per surface, do not run everything everywhere. Every line you pick becomes an inventory row with an expectation. The expectation comes from the spec or the plan; where neither says anything, the standard is "the page stays usable, nothing is silently lost, errors are understandable" - and a missing rule is itself a note in the report.

## Contents
1. Inputs
2. Repeated, concurrent, interrupted
3. States and data
4. Ways in from outside
5. Caches and freshness
6. Permissions and scope
7. Generated content
8. Diagrams and canvas
9. Print and export
10. Cross-cutting

## 1. Inputs
- Empty, whitespace only, leading and trailing whitespace.
- Exactly the maximum length, and one over (truncated with a notice or clearly rejected, never silently stored short).
- One very long word without spaces (wrapping, overflow out of boxes).
- Accents and non-ASCII letters; the same input in different case. Databases often compare case-insensitively while the application compares exactly, which produces duplicates and bypassable uniqueness.
- `<b>bold</b>`, `"; DROP` and similar - must appear as text. **Never** let a payload run that triggers a browser dialog: use a harmless marker such as `<img src=x onerror="document.title='XSS'">` and check the title afterwards.
- Emoji and newlines in single-line fields.
- Number fields: 0, negative, comma instead of point, very large.

## 2. Repeated, concurrent, interrupted
- A double click on every writing main action - one record or two? Two POSTs in the network panel?
- Two tabs on the same record: change in tab A, then change in tab B (revision, conflict status, an understandable message, nothing overwritten).
- The Back button in the middle of a multi-step flow, then forward again.
- A reload in the middle of a dialog, and in the middle of a long-running call.
- Closing a dialog while a request is in flight (does it reopen? does a spinner hang?).
- A slow response: is everything that could double-submit locked while waiting?

## 3. States and data
- An empty list, exactly one element, many elements (scrolling, pagination, filters).
- A record with every optional field empty. Nullable columns are a classic: is it displayed at all? Does it drop out of filters? Negation on a nullable column is the usual bug.
- Archived, retired, sealed: what is still possible, what is locked, and does the page say why?
- Shared or unowned records, and records with no scope of their own.
- A very old version, restoring it, comparing it.

## 4. Ways in from outside
- A deep link with query parameters, without having visited the list first.
- A non-existent id, an id from a foreign scope, `abc`, `0`, `-1`, a very large number: a 404 page rather than a crash or a 500.
- A link from another surface lands in the right place.

## 5. Caches and freshness
- After a change in a popup or dialog: does the page behind it show the new state without a reload?
- After saving: are the list, counters, badges and version list current?
- After navigating away and back: an old state from the cache?

## 6. Permissions and scope (batched at the end, with an account switch)
- Read-only: writing buttons absent, or disabled with a reason; a direct API write returns 403.
- No read permission: every way in is closed. The menu entry is absent; the deep link ends in a clear refusal, not an error page or an empty shell; notifications and lists link nowhere the role cannot open.
- A foreign scope without full visibility: the list is empty or without the foreign rows, and the detail URL returns 404 rather than 403 - a 403 reveals that the record exists.
- Shared scope: visible to everyone with read access, changeable only with both the permission and the scope.
- Hidden names: not in text, not in a diagram, not in a tooltip, and not in the JSON of the response either.

## 7. Generated content
- Nothing is stored without an explicit accept (reload after a preview, the version unchanged).
- A model or service failure: the surface stays usable, the message is understandable.
- An instruction embedded in the source text ("ignore everything and ...") triggers no action.
- Generated content is marked as such wherever the project marks it.

## 8. Diagrams and canvas
- Dragging, zooming with Ctrl and the wheel, the wheel without Ctrl scrolling the page, fit-to-view, fullscreen in and out (Escape).
- A click on an element opens its menu, the menu stays inside the frame and does not cover the element.
- A large model with many nodes: readable, nothing cut off.
- The text view and the diagram show the same state.

## 9. Print and export
- Open the print view with `window.print` intercepted (see the pitfalls file); check layout, header, version and date through the DOM.
- The real PDF is checked by the user; record it in the report as "by the user".

## 10. Cross-cutting (every page)
- Light and dark, both languages, narrow at around 390 px, keyboard only.
- The loading, empty and error states each have a text - no raw keys, no codes.
