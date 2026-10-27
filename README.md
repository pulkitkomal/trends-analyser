<img src="assets/icon.svg" width="64" height="64" alt="">

# trends-analyser

Topic-based trends dashboard: GitHub, Hacker News, RSS, Bluesky, and Google Trends — with keyword analysis, comment insights, and an exportable community digest. Reddit/X adapters can plug in later.

**Live:** [https://topics.k4mik4ge.xyz](https://topics.k4mik4ge.xyz)

**Stack:** FastAPI (`apps/api`) + Next.js (`apps/web`).

## Features

- Follow a topic and ingest posts from GitHub, Hacker News, RSS, Bluesky, and Google Trends
- Keyword stats, recurring themes, comment insights, and a Markdown community digest
- Discovery map of related surfaces you can enable or edit
- Account register / login so each user’s topics stay private
- Optional OpenAI summaries when `OPENAI_API_KEY` is set

## Docker (stays up for the Cloudflare tunnel)

```bash
docker compose up --build -d
```

Serves the UI on port **8678**. Point the tunnel at `http://127.0.0.1:8678`. Public host: `https://topics.k4mik4ge.xyz`.

## Quick start (local, without Docker)

### API

```bash
cd apps/api
cp .env.example .env   # optional GITHUB_TOKEN and OPENAI_API_KEY
uv venv .venv && uv pip install -e ".[dev]"
source .venv/bin/activate
uvicorn app.main:app --reload --port 8001
```

### Web

```bash
cd apps/web
cp .env.local.example .env.local
npm install
npm run dev   # http://localhost:8678
```

Open [http://localhost:8678](http://localhost:8678). Create an account, follow a topic, then **Refresh** to ingest.

Cloudflare tunnel: Next.js 16 blocks unknown hosts. Quick tunnels (`*.trycloudflare.com`) are already allowed. For a named hostname, set `TUNNEL_HOST` in `apps/web/.env.local` and restart `npm run dev`. The tunnel origin must be `http://127.0.0.1:8678` (or `http://localhost:8678`) while both the API and web servers are running.

The web app proxies `/api` to FastAPI (`API_URL`, default `http://127.0.0.1:8001`).

## API surface

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/auth/register` | Create an account |
| POST | `/api/auth/login` | Sign in |
| GET/POST | `/api/topics` | List / create topics |
| GET | `/api/topics/{id}` | Dashboard payload |
| POST | `/api/topics/{id}/refresh` | Ingest + analyze |
| GET/POST | `/api/topics/{id}/surfaces` | Discovery map |
| PATCH | `/api/topics/surfaces/{id}` | Enable/edit surface |
| GET | `/api/topics/{id}/digest` | Latest Markdown digest |

## Notes

- Google Trends uses unofficial `pytrends` (cache / empty on failure).
- Bluesky uses the public AppView search API.
- GitHub works without a token at low volume; set `GITHUB_TOKEN` for reliability.
- Copy `.env.example` files rather than committing real keys. Chat history and the SQLite database live under `data/` and stay local.

## Credits

Built by [Pulkit Komal](https://github.com/pulkitkomal), **co-authored with [Cursor](https://cursor.com)**. The Cursor AI coding agent pair-programmed the ingest adapters, analysis, dashboard UI, and Docker/tunnel setup. Every change was reviewed and directed by the project owner.

## License

MIT
