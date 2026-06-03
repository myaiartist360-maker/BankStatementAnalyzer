# App

**Type:** module
**File:** `frontend/src/App.jsx`
**Layer:** api

## What it does
The React application shell and router. Renders the top bar and routes `/` to [[UploadPage]] and `/results/:requestId` to [[ResultsPage]].

## Depends on
- [[UploadPage]] — upload + analyse route
- [[ResultsPage]] — results route

## Used by
- `main.jsx` — mounts `<App/>`

## Notes
Thin shell; all logic lives in the two pages. Talks to [[FastAPIApp]] via the Vite dev proxy (`/api` → `:8000`).
