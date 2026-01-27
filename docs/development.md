# Development Guide

## Project Structure

```
PROXIMUS/
├── src/proximus/          # Python backend
│   ├── agent/             # LiveKit voice agent
│   ├── api/               # FastAPI REST API
│   ├── ai/                # AI provider abstraction
│   ├── context/           # Resume parsing & phone mapping
│   ├── sip/               # SIP configuration helpers
│   ├── cli.py             # CLI commands
│   ├── config.py          # Settings management
│   └── __main__.py        # Entry point
├── web/                   # React frontend
│   └── src/
│       ├── components/    # React components
│       ├── hooks/         # Custom hooks
│       ├── pages/         # Route pages
│       ├── services/      # API client
│       └── types/         # TypeScript types
├── docs/                  # Documentation
└── tests/                 # Test suite
```

## Running Locally

### Backend

```bash
source .venv/bin/activate
python -m proximus api          # API with hot reload
python -m proximus agent dev    # Agent in dev mode
```

### Frontend

```bash
cd web
npm run dev                     # Vite dev server with HMR
npm run build                   # Production build
npm run preview                 # Preview production build
```

The Vite dev server proxies `/api` requests to `http://localhost:8000`.

## Code Style

### Python
- Formatter/linter: [Ruff](https://docs.astral.sh/ruff/)
- Type checker: [mypy](https://mypy-lang.org/) (strict mode)
- Line length: 100

```bash
ruff check src/
ruff format src/
mypy src/
```

### TypeScript
- Strict TypeScript with Vite defaults
- No additional linting configured (add ESLint as needed)

```bash
cd web
npx tsc --noEmit
```

## Testing

```bash
pytest                          # Run all tests
pytest -v                       # Verbose output
pytest tests/test_specific.py   # Single file
```

## Adding a New API Endpoint

1. Add the route in `src/proximus/api/main.py`
2. Add Pydantic request/response models as needed
3. Add the corresponding TypeScript type in `web/src/types/index.ts`
4. Add the API call in `web/src/services/api.ts`
5. Create or update the React component/page

## Adding a New AI Provider

1. Create `src/proximus/ai/newprovider.py` implementing `AIProvider` from `base.py`
2. Add it to the factory in `src/proximus/ai/__init__.py`
3. Add the provider option to `config.py` (`ai_provider` literal type)
4. Add the LLM string mapping in `agent/voice.py` → `get_llm_string()`

## Building for Production

### Backend
```bash
pip install build
python -m build
# Output: dist/proximus-0.1.0-py3-none-any.whl
```

### Frontend
```bash
cd web
npm run build
# Output: web/dist/
```

The built frontend can be served by FastAPI using `StaticFiles` or deployed to a CDN.
