# mcp-il-professionals

<!-- mcp-name: io.github.olegsher-ds-2025/mcp-il-professionals -->

Verify licensed professionals in Israel for AI agents: real-estate brokers, registered contractors, appraisers, CPAs, surveyors, private investigators — live from data.gov.il.

**אימות בעלי מקצוע מורשים: מתווכים, קבלנים רשומים, שמאים, רואי חשבון, מודדים, חוקרים פרטיים**

An [MCP](https://modelcontextprotocol.io) server that lets Claude and other AI assistants query official Israeli
government open data in plain language. No API key, no scraping — every call goes to the public
[data.gov.il](https://data.gov.il) CKAN API and returns the source with each answer.

## Tools

| Tool | What it does |
|---|---|
| `list_professions` | Which registries are available, and how to verify electricians / engineers / lawyers |
| `verify_professional` | Check a licence by name or number in one registry |
| `find_contractors` | Registered contractors by city, branch (שיפוצים, בניה, חשמלאות…), classification |
| `contractor_profile` | All branches & classifications of one contractor |
| `search_all_registries` | One name across every registry |
| `health` | Connectivity check |

## Try asking

- “Is the real-estate broker דורית גריצר licensed?”
- “Find registered renovation contractors in Modiin recognized for government work.”
- “Check CPA licence 5005603.”
- “What licences does this person hold across all registries?”

## Install

No install needed with [uv](https://docs.astral.sh/uv/):

```bash
uvx mcp-il-professionals
```

Claude Desktop / Claude Code (`.mcp.json`):

```json
{ "mcpServers": { "il-professionals": { "command": "uvx", "args": ["mcp-il-professionals"] } } }
```

Or `pip install mcp-il-professionals`, or from source: `pip install git+https://github.com/olegsher-ds-2025/mcp-il-professionals`.

Also listed in the official MCP Registry as `io.github.olegsher-ds-2025/mcp-il-professionals`.

Run over HTTP (for remote hosting):

```bash
MCP_TRANSPORT=http PORT=8000 mcp-il-professionals   # → http://localhost:8000/mcp
```

Docker: `docker build -t mcp-il-professionals . && docker run -p 8000:8000 mcp-il-professionals`.

Prefect Horizon entrypoint: `server.py:mcp`.

## Verify the package

Releases are built and published by GitHub Actions with PyPI Trusted Publishing — no stored tokens.
Each release carries PyPI (PEP 740) attestations and a GitHub build-provenance attestation:

```bash
pip download mcp-il-professionals --no-deps -d dl && gh attestation verify dl/*.whl -R olegsher-ds-2025/mcp-il-professionals
```

## Data sources

- Licensed real-estate brokers (Ministry of Justice)
- Registered contractors (Registrar of Contractors)
- Real-estate appraisers
- Certified public accountants (CPA Council)
- Vehicle appraisers (Ministry of Transport)
- Licensed surveyors (Survey of Israel)
- Private investigators & investigation firms

All data © the publishing Israeli government authority, via data.gov.il. This project is independent and not
affiliated with the Government of Israel. Registry data can lag; verify critical facts with the authority.

## Development

```bash
pip install -e ".[dev]"
pytest            # offline tests
pytest -m live    # hits data.gov.il
```

## Roadmap

- [ ] Electricians licence search (Ministry of Labor — not open data; investigate official lookup)
- [ ] Engineers & architects registry
- [ ] Insurance agents (Capital Market Authority)
- [ ] Join contractors with mcp-il-companies due_diligence

## Related

Part of a family of Israeli public-data MCP servers by [Oleg Sher](https://linkedin.com/in/sheroleg):
mcp-il-companies · mcp-il-vehicles · mcp-il-health · mcp-il-professionals · mcp-cbs-places · mcp-mavat.

## License

MIT
