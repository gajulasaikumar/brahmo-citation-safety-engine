# BRAHMO Citation Safety Engine

A deterministic citation safety pipeline for Indian legal AI — verification, hallucination detection, section normalization (IPC→BNS), and side-by-side comparison UI.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up environment variables
cp .env.example .env
# Edit .env with your database credentials and API keys

# 3. Initialize database
mysql -u <user> -p <database> < sql/schema.sql
mysql -u <user> -p <database> < sql/seed.sql

# 4. Run the application
python app.py
# → http://localhost:5000

# Production:
gunicorn -w 4 -b 0.0.0.0:5000 app:application
```

## Architecture

```
Lawyer Query
  → Section Normalizer (IPC→BNS, deterministic, ~5ms)
  → LLM API (legal memo with citations)
  → Citation Safety Engine (~2-3s, deterministic):
    ├── Citation Extractor (6 regex patterns for Indian legal citations)
    ├── Hallucination Detector (4 rules: future year, impossible volume, impossible page, pre-1900)
    ├── Citation Verifier (Indian Kanoon API lookup, parallel, cached)
    └── Citation Annotator (✅ verified / ⚠️ corrected / ❌ removed)
  → Annotated output shown side-by-side with generic AI
  → Citation verification report
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3 + Flask |
| Database | MySQL (via SQLAlchemy ORM) |
| Frontend | Jinja2 + Tailwind CSS (CDN) + Vanilla JS |
| LLM | OpenAI-compatible API (via Drytis gateway) |
| Citation Verification | Indian Kanoon API |
| Server | Gunicorn (production) |

## Demo Scenarios

1. **The Hallucinated Citation** — 2 fabricated cases detected as ❌ REMOVED
2. **The Repealed Law Catastrophe** — 4 old IPC sections auto-converted to BNS
3. **The Impossible Citation** — Pre-filter catches future year + impossible volume without API call
4. **The Format Error** — 3 formatting corrections (capitalization, spacing, court code)

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Main demo page |
| POST | `/api/ask` | Full citation verification pipeline |
| POST | `/api/ask-generic` | Generic AI response (no verification) |
| POST | `/api/normalize-sections` | Normalize section references |
| POST | `/api/verify-citation` | Verify a single citation |
| GET | `/api/matters` | List all legal matters |
| GET | `/api/stats` | Database statistics |
| GET | `/health` | Health check |

## Database

- **6 citation patterns** — SCC, AIR, SCC OnLine, Cri LJ, SCR, MANU
- **30 section mappings** — IPC→BNS (21), CrPC→BNSS (8), IEA→BSA (1)
- **8 legal matters** — 4 demo scenarios + 4 general
- **Verification cache** — TTL-based MySQL cache for IK API results

## Innovation

1. **Cost Tracking** — Per-query IK API cost with pre-filter savings
2. **UNVERIFIED vs REMOVED** — Critical distinction: "not in IK" ≠ "hallucinated"
3. **Smart Caching** — 7-day TTL cache avoids re-verifying the same citation
4. **Alert Fatigue Management** — Verified citations collapsed by default; problems shown prominently
5. **Extensibility** — New citation format = 1 DB row; new section mapping = 1 INSERT; no code changes

## Key Design Decisions

- **Citation patterns in DB, not hardcoded** — Scalable to thousands of patterns
- **Pre-filter before API** — Saves cost and catches obvious fakes instantly
- **Parallel verification** — `ThreadPoolExecutor` for concurrent IK API calls
- **Deterministic safety** — Regex + DB lookups, never uses AI to verify AI
- **Unverified ≠ Hallucinated** — IK doesn't have every case; honest status reporting

## Testing

```bash
pytest tests/
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| DB_HOST | Yes | MySQL host |
| DB_PORT | Yes | MySQL port |
| DB_NAME | Yes | Database name |
| DB_USER | Yes | Database user |
| DB_PASSWORD | Yes | Database password |
| LLM_API_KEY | No | OpenAI-compatible API key |
| LLM_BASE_URL | No | API base URL |
| LLM_MODEL | No | Model name (default: gpt-4o-mini) |
| IK_API_KEY | No | Indian Kanoon API key |
| IK_BASE_URL | No | Indian Kanoon base URL |

## License

Assessment project for BRAHMO / Astroum AI.