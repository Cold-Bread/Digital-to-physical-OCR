frontend changes:

pagnation:

- change row selector to Fill (show rows to bottom of screen, no scroll) or All (show all results, scroll is fine)

table changes:

- cell size should be fit to largest entry instead of current dynamic state (abrivate col names if needed)
- remove comma from year joined, last DOS, and shred year entries.
- revamp row highlighting:
  - red: no match (defualt if no OCR response or .5 or lower confidence)
  - Orange: itermediate match (.5-.75)
  - Green: best or perfect match (.76-.999~)

Control Panel:

- new button layout should be as follows:
  boxNum text input, getBox button, image input button, send image, vertical divider, undo, undo all, vertical divider, submit to sheet, view image (hugs right wall)

Normailization:

- add chronos and other lightweight library for easier and better data handling

Bugs:

---

BACKEND FETURE REQUESTS:

- remove all instances of ocr1-3. change to paddle OCR (make seperate branch and fix both front and backend)
