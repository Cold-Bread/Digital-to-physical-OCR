frontend changes: ~~markthrough means completed~~
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
  boxNum text input, getBox button, image input button, send image, divider, undo, undo all, divider, submit to sheet, view image (hugs right wall)

Bugs:

- last row gets cut off (bug, adding padding-bottom)
- ensure rows from tables are inline with eachother for ease of mapping
- ~~ investigate send image button invokes Error: Cannot read properties of undefined (reading 'map')~~


Component Details:
- The code selection given is only a reference of the variables and paths needed. The goals is to move the image display to instead be a pop up window originating from a button.

  Description:
  - Window availble via "View Picture" button, temporary location is the far right of the controlPanel compenent
  - should display picture with similar background style as current UI
  - pop up should first appear hugging the right wall and displaying the full image. Follow project css (unsure if global padding)
  - On click, change the color and disable the view picture button.
  - When pop up is closed, change the view picture button color back and re-enable it

  Additonal pop up features:
  - click and drag icon in top left (allows pop up to be moved around, window is pinned in place otherwise)
  - Window resizing (image should not be resized along with the window, simply cut off. User sohuld be able to scroll around image if need be)
  - resize window to fit image button (Main usage is to reset the view after user resizes the window and potentially cuts off the image)

  Notes:
  - while the "View Picture" button exists within controlPanel.tsx, the onClick event should route to a seperate .tsx file whose purpose is the description of the new window
---

BACKEND FETURE REQUESTS:

- remove all instances of ocr1-3. change to paddle OCR (make seperate branch and fix both front and backend)
