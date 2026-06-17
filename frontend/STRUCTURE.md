# frontend/ — restructuring guide

I haven't seen your actual Vite app's `src/` contents (only the static
`index.html` prototype), so I'm not rewriting your UI blind. This is the
target shape to grow into; `src/api/client.js` is included since it's a
safe, generic wrapper around the new endpoints that doesn't need to know
anything about your component internals.

```
src/
├── api/
│   └── client.js        # fetch wrappers — included, see that file
├── components/
│   ├── BatchList.jsx     # replaces the entity-card grid; one row per batch,
│   │                     #   not per entity, since an entity can have N batches
│   ├── BatchCard.jsx      # entity, count, status, created_at, click -> inspect
│   ├── RawJsonViewer.jsx  # renders GET /api/batch/{id}'s `raw` field, pretty-printed
│   ├── Terminal.jsx       # same idea as your current terminal, now keyed by batch_id
│   └── ActionBar.jsx      # Validate / Load buttons, operating on selected batch_ids
├── pages/
│   ├── Dashboard.jsx      # batch list + terminal, mirrors your current index.html layout
│   └── Settings.jsx       # your existing settings.html, ported to a component
└── hooks/
    └── useEventStream.js  # the SSE-parsing loop from your current <script>,
                            #   extracted into a reusable hook
```

Key UI model change: your current grid treats **entity = one slot**. The new
model needs **entity = one or more batches over time**, so `BatchList` should
support filtering by entity but list/select individual batches, not entities.

Once you confirm whether this is React/Vue/vanilla JS and share your current
`src/`, I can port the actual components rather than describe them.
