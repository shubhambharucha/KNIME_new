# legacy/

Move your current `Backend/Scripts/*` (all the `validate_*.py` / `*_load.py`
files), the old `Backend/main.py`, and `Backend/debug.py` in here, untouched.

Nothing in this folder is imported by the new app. It exists purely as a
reference while the remaining 9 entities get ported into
`backend/app/entities/<name>/` following the Customer pattern — i.e. for
each entity:

1. Copy the mandatory-field list and any field-rule table into
   `entities/<name>/config.py`.
2. Strip the openpyxl/workbook code out of the old `validate_<name>.py`,
   keep only the per-row checks, return a list of error strings ->
   `entities/<name>/validator.py`.
3. Strip the workbook/file-loop code out of the old `<name>_load.py`,
   keep `build_payload` + the QAD API calls + a single `load_row(record, tm)`
   function -> `entities/<name>/loader.py`.
4. Register it in `app/core/registry.py`.

Once all ten are ported, delete this folder.
