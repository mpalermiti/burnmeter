# 🔥 burnmeter

> **Know your burn. Build with confidence.**

Stop logging into 11 platform dashboards. Track infrastructure costs across Vercel, Neon, OpenAI, and 8 other platforms via Claude Code. Ask one question, get your total burn rate.

🌐 **[mpalermiti.github.io/burnmeter](https://mpalermiti.github.io/burnmeter/)**

Multi-cloud cost aggregator MCP server for indie builders shipping fast while watching their runway.

---

## The Problem

You're building. You're shipping. You're using Vercel for frontend, Neon for database, OpenAI for AI, Twilio for SMS, and five other services.

Every month, you spend 2 hours:
- Opening 11+ dashboards
- Exporting CSVs
- Building a spreadsheet
- Calculating your actual burn rate
- Discovering surprise bills too late

**There has to be a better way.**

## The Solution

Ask Claude: **"What's my burn rate this month?"**

Burnmeter aggregates costs across your entire stack in real-time. One command. One answer. Every platform you use.

```
You: "Am I over my $500/month budget?"

Claude: "You've spent $451.00 this month (90.2% of budget):
  - Vercel: $95.00 (functions + bandwidth)
  - Neon: $135.00 (compute + storage)
  - OpenAI: $165.00 (GPT-4 + embeddings)
  - Anthropic: $56.00 (Claude API)
  - Remaining: $49.00

  You're on track. Neon usage up 40% from last month."
```

No dashboards. No spreadsheets. Just answers.

---

## Supported Platforms (11)

Burnmeter connects to the platforms indie builders actually use:

### 🌐 Hosting & Infrastructure
- **Vercel** - Frontend hosting, serverless functions
- **DigitalOcean** - Droplets, App Platform, managed databases

### 🤖 AI APIs
- **OpenRouter** - AI gateway with 400+ models
- **OpenAI** - Direct GPT-4, embeddings, assistants
- **Anthropic** - Direct Claude API (requires Admin API key)

### 🗄️ Databases
- **Neon** - Serverless Postgres with autoscaling
- **PlanetScale** - MySQL with branching
- **Turso** - Edge SQLite for low-latency apps
- **MongoDB Atlas** - NoSQL, global clusters
- **Upstash** - Serverless Redis, Kafka, QStash

### 📱 Communications
- **Twilio** - SMS, voice, WhatsApp APIs

**Total addressable burn:** If you're a typical indie SaaS, this covers 80-95% of your monthly infrastructure spend.

---

## Why This Matters

### For Solopreneurs
You're watching runway. Every dollar counts. Burnmeter gives you real-time visibility without the overhead of enterprise FinOps tools.

### For Small Teams
Stop asking your engineer to "pull the numbers." Everyone on the team can ask Claude for cost data.

### For Builders Shipping Fast
You're adding services constantly. Burnmeter scales with you. New database? New AI provider? Add the API key, ask Claude.

### vs Alternatives

| Tool | Platforms | Integration | Cost |
|------|-----------|-------------|------|
| **burnmeter** | 11 (hosting, AI, DB, comms) | Claude Code MCP | Free, open source |
| AWS Cost Explorer | AWS only | Web dashboard | Included with AWS |
| SpendScope | 3 AI APIs only | Web dashboard | Paid service |
| CloudHealth | Enterprise clouds | Complex setup | $$$ |
| Manual spreadsheet | Any (if you export CSVs) | 2 hours/month | Your time |

**Burnmeter is the only tool that:**
- Aggregates indie builder stack (not just enterprise clouds)
- Lives in your dev environment (not another dashboard)
- Works with natural language (ask Claude, get answers)
- Costs $0

---

## Installation

### Prerequisites
- Python 3.10+ (MCP requires 3.10+)
- Claude Code or Claude Desktop
- API keys for platforms you want to track

### Setup

```bash
# Navigate to project
cd ~/ClaudeCode/burnmeter

# Install dependencies
pip install -e .

# Copy environment template
cp .env.example .env

# Add your API keys to .env
nano .env
```

### Configure Claude Code

Add to your `~/.claude/mcp_config.json`:

```json
{
  "mcpServers": {
    "burnmeter": {
      "command": "python3",
      "args": ["/Users/YOUR_USERNAME/ClaudeCode/burnmeter/src/server.py"],
      "env": {
        "PYTHONPATH": "/Users/YOUR_USERNAME/ClaudeCode/burnmeter/src"
      }
    }
  }
}
```

Replace `YOUR_USERNAME` with your actual username.

Restart Claude Code. You'll see burnmeter tools available.

---

## Configuration

Get API keys for each platform you want to track. **You only need keys for services you use** - skip the rest.

### 🌐 Hosting & Infrastructure

**Vercel**
- Dashboard: https://vercel.com/account/tokens
- Create token → Add to `.env` as `VERCEL_TOKEN`
- Permissions: Read billing data

**DigitalOcean**
- Dashboard: https://cloud.digitalocean.com/account/api/tokens
- Generate New Token → Add to `.env` as `DIGITALOCEAN_TOKEN`
- Scopes: Read billing history

### 🤖 AI APIs

**OpenRouter**
- Dashboard: https://openrouter.ai/keys
- Create API Key → Add to `.env` as `OPENROUTER_API_KEY`

**OpenAI**
- Dashboard: https://platform.openai.com/api-keys
- Create new secret key → Add to `.env` as `OPENAI_API_KEY`

**Anthropic**
- Dashboard: https://console.anthropic.com/settings/keys
- **Important:** Create **Admin API key** (starts with `sk-ant-admin-`)
- Regular API keys won't work - cost reporting requires admin key
- Add to `.env` as `ANTHROPIC_API_KEY`

### 🗄️ Databases

**Neon**
- Dashboard: https://console.neon.tech/app/settings/api-keys
- Generate New Key → Add to `.env` as `NEON_API_KEY`

**PlanetScale**
- Dashboard: https://app.planetscale.com/[org]/settings/service-tokens
- Create Service Token with `read_invoices` permission
- Add token to `.env` as `PLANETSCALE_SERVICE_TOKEN`
- Add org name to `.env` as `PLANETSCALE_ORG_NAME`

**Turso**
- CLI: `turso auth api-tokens create burnmeter`
- Add token to `.env` as `TURSO_API_TOKEN`
- Get org: `turso org list` → Add to `.env` as `TURSO_ORG_NAME`

**MongoDB Atlas**
- Dashboard: https://cloud.mongodb.com/v2/[org]/access/apiKeys
- Create API Key with Organization Read Only
- Add public key to `.env` as `MONGODB_ATLAS_PUBLIC_KEY`
- Add private key to `.env` as `MONGODB_ATLAS_PRIVATE_KEY`
- Get Org ID from URL → Add to `.env` as `MONGODB_ATLAS_ORG_ID`

**Upstash**
- Dashboard: https://console.upstash.com/account/api
- Create API Key → Add to `.env` as `UPSTASH_API_KEY`

### 📱 Communications

**Twilio**
- Dashboard: https://console.twilio.com/
- Get Account SID → Add to `.env` as `TWILIO_ACCOUNT_SID`
- Get Auth Token → Add to `.env` as `TWILIO_AUTH_TOKEN`

---

## Usage

Once configured, ask Claude about your costs in natural language:

### Quick Questions
```
"What did I spend this week?"
"What's my monthly burn rate?"
"Show me my top 3 costs"
"How much did I spend on AI this month?"
```

### Budget Management
```
"Am I over my $500 budget?"
"What's my burn rate trend?"
"Alert me if I go over $600 this month"
```

### Platform-Specific
```
"Show me Vercel costs for last 30 days"
"Break down my Neon spending"
"What's my OpenAI usage this month?"
"Compare my database costs"
```

### MCP Tools (Under the Hood)

Burnmeter exposes 4 tools to Claude:

**`get_total_costs(period, platforms)`**
- Aggregate costs across all or specific platforms
- `period`: `"7d"`, `"30d"`, `"mtd"`, `"current_cycle"`
- `platforms`: Optional list like `["vercel", "neon"]`
- Returns: Total USD + per-platform breakdown

**`get_platform_breakdown(platform, period)`**
- Detailed cost breakdown for one platform
- Shows service-level costs (e.g., Vercel functions, bandwidth, edge config)
- Returns: Line-item breakdown with usage metrics

**`check_budget(budget_usd, period)`**
- Compare actual spending vs budget
- Returns: Total spent, remaining, percentage used, over/under status
- Default period: month-to-date

**`list_platforms()`**
- Show all 11 platforms and their auth status
- Useful for debugging config issues
- Returns: Which platforms are configured and ready

---

## Architecture

### Project Structure

```
burnmeter/
├── src/
│   ├── server.py              # FastMCP server, 4 tools, 11 providers
│   ├── cache.py               # In-memory cache (1hr TTL)
│   ├── providers/
│   │   ├── base.py            # Abstract BaseProvider class
│   │   ├── vercel.py          # Vercel billing API
│   │   ├── digitalocean.py    # DigitalOcean billing history
│   │   ├── openrouter.py      # OpenRouter credits API
│   │   ├── openai.py          # OpenAI usage API
│   │   ├── anthropic.py       # Anthropic Admin API (cost reports)
│   │   ├── neon.py            # Neon consumption metrics
│   │   ├── planetscale.py     # PlanetScale invoices API
│   │   ├── turso.py           # Turso organization usage
│   │   ├── mongodb_atlas.py   # MongoDB Cost Explorer (polling)
│   │   ├── upstash.py         # Upstash stats API
│   │   └── twilio.py          # Twilio usage records
├── .env.example               # Template with all required keys
├── .gitignore
├── README.md
└── pyproject.toml
```

### How It Works

1. **Claude calls MCP tool** (e.g., `get_total_costs("30d")`)
2. **Burnmeter parses period** → start_date, end_date
3. **Fetch from cache** (1hr TTL) or API
4. **Each provider:**
   - Calls platform's billing API
   - Normalizes to common format (USD, breakdown by service)
   - Returns `NormalizedCost` object
5. **Aggregator combines** all platform costs
6. **Returns to Claude** as structured JSON
7. **Claude formats** natural language response

### Design Principles

**Normalized Data Model:**
Every provider returns the same structure:
```python
{
  "platform": "vercel",
  "period": "30d",
  "total_usd": 89.50,
  "breakdown": [
    {"service": "functions", "cost": 45.20},
    {"service": "bandwidth", "cost": 44.30}
  ],
  "cached_at": "2026-03-09T10:30:00Z"
}
```

**Caching:**
- Results cached for 1 hour
- Most billing APIs update hourly or daily
- Reduces API calls, respects rate limits
- Cache invalidates automatically

**Error Handling:**
- Missing API keys → gracefully skip platform
- API failures → return partial results + error list
- Invalid date ranges → clear error messages

**Provider Patterns:**
- **Simple REST** (Vercel, OpenAI, Twilio): Single GET request
- **Multi-endpoint** (PlanetScale, DigitalOcean): Get invoices + line items
- **Polling** (MongoDB Atlas): Async query, poll for results
- **Calculated** (Neon, Turso): Usage metrics → estimate costs

---

## Development

### Adding a New Provider

Want to add support for Railway? Fly.io? Stripe fees? Here's how:

**1. Check if the platform has a billing API**

Search docs for: `billing API`, `usage API`, `invoices API`, `cost API`

Required:
- Programmatic access to cost/usage data
- Date range filtering
- Breakdown by service (ideal)

**2. Create provider file**

```bash
touch src/providers/railway.py
```

```python
"""Railway cost provider."""

import os
from datetime import datetime
import httpx
from providers.base import BaseProvider, CostBreakdown, NormalizedCost


class RailwayProvider(BaseProvider):
    def __init__(self):
        super().__init__("railway")
        self.api_key = os.getenv("RAILWAY_API_KEY")
        self.base_url = "https://backboard.railway.com/graphql/v2"

    def validate_auth(self) -> bool:
        """Check if Railway API key is present."""
        return bool(self.api_key)

    async def get_costs(self, start_date: str, end_date: str) -> NormalizedCost:
        """
        Fetch Railway costs using GraphQL API.

        API: POST https://backboard.railway.com/graphql/v2
        Query: { billingUsage(startDate: "...", endDate: "...") }
        """
        if not self.validate_auth():
            raise ValueError("RAILWAY_API_KEY not set")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        query = """
        query GetUsage($startDate: String!, $endDate: String!) {
          billingUsage(startDate: $startDate, endDate: $endDate) {
            total
            breakdown {
              service
              cost
            }
          }
        }
        """

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.base_url,
                headers=headers,
                json={
                    "query": query,
                    "variables": {
                        "startDate": start_date,
                        "endDate": end_date,
                    },
                },
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()

            # Extract costs from response
            usage = data["data"]["billingUsage"]
            total = float(usage["total"])

            breakdown = [
                CostBreakdown(service=item["service"], cost=float(item["cost"]))
                for item in usage["breakdown"]
            ]

            return NormalizedCost(
                platform=self.name,
                period=self._get_period_label(start_date, end_date),
                total_usd=total,
                breakdown=breakdown,
                cached_at=datetime.now(),
                start_date=start_date,
                end_date=end_date,
            )
```

**3. Register in server.py**

```python
from providers.railway import RailwayProvider

PROVIDERS = {
    # ... existing providers
    "railway": RailwayProvider(),
}
```

**4. Add to .env.example**

```bash
# Railway
RAILWAY_API_KEY=
```

**5. Update README**

Add Railway to the platform list and configuration section.

**6. Test**

```bash
# Add your Railway API key to .env
RAILWAY_API_KEY=your_key_here

# Ask Claude
"What did I spend on Railway this month?"
```

### Provider Complexity Levels

**Level 1: Simple REST** (1-2 hours)
- Single GET endpoint
- Returns costs directly
- Examples: Vercel, OpenAI, Twilio

**Level 2: Multi-Endpoint** (2-3 hours)
- Multiple API calls needed
- Parse and aggregate results
- Examples: PlanetScale, DigitalOcean

**Level 3: Calculated Costs** (3-4 hours)
- API returns usage metrics, not costs
- Apply pricing formula
- Examples: Neon, Turso

**Level 4: Async/Polling** (4-5 hours)
- Query initiation + polling for results
- Handle timeouts and retries
- Examples: MongoDB Atlas

### Testing

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run linter
ruff check src/

# Format code
ruff format src/

# Run tests (coming soon)
pytest
```

---

## Contributing

Burnmeter is built for the indie builder community. Contributions welcome!

### High-Value Contributions

**Add Provider Support:**
- Railway (requested)
- Fly.io (requested)
- Render
- Supabase
- Netlify
- Cloudflare (dashboard-only currently)
- Stripe (transaction fees)
- GitHub Actions (compute minutes)

**Improve Existing Providers:**
- Upstash: Implement service-specific endpoints (currently placeholder)
- Cost estimation accuracy for usage-based providers
- Handle pagination for large result sets

**New Features:**
- Forecasting: "At this rate, what will I spend this month?"
- Trending: "Your Vercel costs are up 40% from last month"
- Alerts: Webhook when spending exceeds threshold
- Export: Generate CSV/PDF reports
- Comparison: Compare month-over-month, year-over-year

**Better Error Handling:**
- Retry logic for transient API failures
- More helpful error messages
- Fallback to cached data when API is down

### Contribution Guidelines

1. **Fork the repo**
2. **Create a feature branch** (`git checkout -b add-railway-provider`)
3. **Test your provider** with real API credentials
4. **Update README** with configuration instructions
5. **Submit PR** with:
   - Description of what the provider does
   - Link to the platform's billing API docs
   - Example response showing it works

### Code Style

- Use `ruff` for linting and formatting
- Type hints on all function parameters
- Docstrings on all public methods
- Follow existing provider patterns

---

## FAQ

**Q: Why MCP instead of a web dashboard?**
A: Because you're already in Claude Code. You're already asking Claude questions. "What did I spend?" is a natural question in that workflow. No context switch. No opening another browser tab.

**Q: Is this secure?**
A: API keys are stored locally in your `.env` file. No data is sent to external servers except the platform APIs you're querying. MCP runs locally on your machine.

**Q: What if a platform doesn't have a billing API?**
A: Some platforms (Cloudflare, Render, Fly.io) don't expose billing via API. For these, you'll need to check their dashboards manually. We're tracking which platforms add APIs.

**Q: Do I need all 11 API keys?**
A: No! Only configure platforms you actually use. Burnmeter will skip unconfigured platforms.

**Q: How accurate are the costs?**
A: Most providers return exact costs. A few (Neon, Turso) return usage metrics, so we apply their published pricing formulas. These are estimates and may differ slightly from your actual invoice due to discounts, credits, or overage calculations.

**Q: Can I use this for AWS/GCP/Azure?**
A: Not currently. Those platforms have enterprise-focused billing APIs (AWS Cost Explorer, etc.). Burnmeter focuses on the indie builder stack. If there's demand for big cloud support, we could add it.

**Q: Does this work with Claude Desktop?**
A: Yes! MCP works with both Claude Code (CLI) and Claude Desktop (GUI app).

**Q: Can I self-host this?**
A: It already is self-hosted - it runs locally on your machine. If you want to run it as an HTTP MCP server for team access, you can deploy to Railway/Render/Fly and expose the MCP endpoint.

---

## Comparison to Alternatives

### vs AWS Cost Explorer
- ❌ AWS only
- ❌ Complex UI, slow to load
- ❌ No natural language queries
- ✅ Free (if you use AWS)

**burnmeter:** Multi-cloud, instant answers via Claude

### vs SpendScope
- ✅ Tracks OpenAI/Anthropic/Google AI
- ❌ AI APIs only (no databases, hosting)
- ❌ Web dashboard, not CLI-native
- ❌ Paid service

**burnmeter:** 11 platforms, free, open source

### vs CloudHealth/Cloudability
- ✅ Enterprise-grade cost management
- ❌ Expensive ($$$)
- ❌ Complex setup
- ❌ Focused on AWS/Azure/GCP

**burnmeter:** Indie stack, zero config overhead

### vs Manual Spreadsheet
- ✅ Totally flexible
- ❌ 2 hours/month to update
- ❌ Out of date the moment you finish
- ❌ Error-prone

**burnmeter:** Real-time, automatic, accurate

---

## Roadmap

**v0.2 (Next)**
- [ ] Add Railway provider
- [ ] Add Fly.io provider (if API becomes available)
- [ ] Forecasting: "At this rate, you'll spend $X this month"
- [ ] Month-over-month comparison

**v0.3**
- [ ] Stripe provider (track processing fees)
- [ ] Supabase provider
- [ ] Export to CSV/PDF
- [ ] Budget alerts via webhook

**v1.0**
- [ ] Historical data storage (SQLite)
- [ ] Trending analysis
- [ ] Cost optimization recommendations
- [ ] Team collaboration features

---

## License

MIT License - see [LICENSE](LICENSE)

Free to use for personal and commercial projects.

---

## Author

Built by **Michael Palermiti** ([@mpalermiti](https://github.com/mpalermiti))
VP of Product at Microsoft, building [Amby](https://michaelp.ai) and [Glosignal](https://glosignal.com)

🌐 [michaelp.ai](https://michaelp.ai)

---

## Inspiration

This started with a simple question: **"What's my monthly burn?"**

As an indie builder running multiple projects (Amby, Glosignal, Outlook MCP), I found myself:
- Opening 11+ dashboards every month
- Exporting CSVs
- Building spreadsheets
- Calculating burn rate manually
- Getting surprised by bills

I wanted to ask Claude: "What did I spend this week?" and get an answer.

So I built burnmeter.

If you're watching your runway, tracking your burn, or just want to know where your money goes without the dashboard dance - this is for you.

**Know your burn. Build with confidence.**

---

## Support

- 🐛 **Issues:** [GitHub Issues](https://github.com/mpalermiti/burnmeter/issues)
- 💬 **Discussions:** [GitHub Discussions](https://github.com/mpalermiti/burnmeter/discussions)
- 📧 **Email:** [contact@michaelp.ai](mailto:contact@michaelp.ai)

**Star the repo** if burnmeter helps you track your burn rate 🔥
