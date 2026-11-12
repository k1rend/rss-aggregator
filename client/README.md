# RSS Aggregator — client

Vue 3 (Composition API + Vue Router) single page app talking to the Express API in
[`../src`](../src) with Axios.

## Features

- **Auth screen** (`/auth`) — log in (`POST /api/auth/signin`) or sign up (`POST /api/auth/signup`).
  The JWT is kept in `localStorage` and sent as `Authorization: Bearer <token>` by an Axios
  request interceptor. A `401` response clears the session and returns the user to the auth screen.
- **Main screen** (`/`) — a list of article titles in the centre of the screen:
  - green dot = unread, gray dot = read (based on the `viewed` flag from the API),
  - chevron on the right expands the article; expanding an unread article marks it as read
    optimistically and stores the view in Redis via `POST /api/articles/:id/view`,
  - the expanded article ends with a **Share** button that copies the article source link to the
    clipboard (with an `execCommand` fallback for non-secure contexts) plus an "Open source" link.
- **Left side panel** — feed type selector (all / local / country / world), exact RSS feed
  selector (with article counts), viewing history toggle and log out.
- **Viewing history** — `GET /api/history`, newest read first, reusing the same expandable rows.
- Pagination through `limit`/`offset` with a "Load more articles" button.

Feed content is third-party HTML, so it is sanitized with DOMPurify before `v-html`.

## Requirements
- Node.js 20+
- The API server (`npm start` in the repository root) and Redis running.

## Scripts

```bash
npm install
npm run dev      # http://localhost:5173
npm run build    # production bundle in ./dist
npm run preview  # serve ./dist on http://localhost:4173
```

## API location

The Express server does not enable CORS, so the dev/preview servers proxy API calls to
`http://localhost:3000` (see `vite.config.js`):

- `/api/*` and `/health` → `http://localhost:3000`

Override the proxy target with `VITE_PROXY_TARGET`, or point the client at another origin by
creating a `.env` file with:

```
VITE_API_BASE_URL=http://localhost:3000
```

(only needed when the client is served from the same origin as the API or CORS is enabled).
