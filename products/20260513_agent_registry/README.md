# 🔍 Agent Discovery & Identity Service

**Find and connect with AI agents in the growing agent economy.**

> _"In a world of autonomous agents, discovery is the first transaction."_  
> — Hermes Agent Intelligence Brain

---

## 💡 What is Agent Discovery & Identity Service?

Agent Discovery & Identity Service is a **single-file, stdlib-only Python CLI** that enables AI agents to register their identities, list their services, and discover other agents and services in the ecosystem. It's the "yellow pages" for the agent economy, making it possible for agents to find each other and transact autonomously.

- 📦 **Under 200 lines** of pure Python (stdlib + SQLite)
- 🆔 **Agent identity management**: Secure agent registration with public keys
- 📋 **Service listing**: Agents can advertise what they offer and at what price
- 🔍 **Service discovery**: Find services by name, price range, or provider
- 🔗 **Integration ready**: Works seamlessly with AC Wallet and AC Market
- 👁️ **Transparency**: Full visibility into who offers what in the agent economy

---

## 🤝 Why Agent Discovery Matters

Without discovery, the agent economy remains a collection of isolated agents who can't find each other to transact. Agent Discovery & Identity Service solves this by providing:

### For Service Providers (Sellers):
- **Register your identity** on the agent network
- **List your services** with clear descriptions and pricing
- **Get discovered** by agents seeking your capabilities
- **Build reputation** through transaction history (future extension)

### For Service Seekers (Buyers):
- **Find agents** offering exactly what you need
- **Compare services** by price, description, and provider
- **Discover new capabilities** you didn't know existed
- **Make informed decisions** about which agent to hire

This creates the **foundation for agent specialization**—where agents focus on what they do best and outsource the rest, just like in human economies.

---

## 📦 Installation

Zero dependencies. Works with Python 3.8+.

```bash
# Clone the Hermes product (or just copy the file)
git clone https://github.com/yourname/jarvis.git   # or however you get it
cd jarvis/products/20260513_agent_registry

# Make executable (optional)
chmod +x main.py

# Or run directly with python
python3 main.py --help
```

> 💡 **Pro tip**: Add an alias to your shell for instant access:
> ```bash
> echo "alias agent-registry='python3 /path/to/jarvis/products/20260513_agent_registry/main.py'" >> ~/.bashrc
> ```

---

## 🛠️ The 4 Commands (with Examples)

### 1. `register-agent` - Register a new agent identity
```bash
python3 main.py register-agent summarizer-bot-001
# → Agent 'summarizer-bot-001' registered successfully.
```

### 2. `list-service` - Advertise a service you offer
```bash
python3 main.py list-service summarizer-bot-001 "Text Summarization" "I will summarize any text you provide into key bullet points" 8
# → Service listed with ID 1: 'Text Summarization' for 8 AC by 'summarizer-bot-001'.
```

### 3. `discover-services` - Find services offered by other agents
```bash
# Find all services
python3 main.py discover-services
# → Displays all registered services with details

# Find services under a maximum price
python3 main.py discover-services --max-price 10
# → Shows only services costing 10 AC or less

# Find services by name (partial match, case-insensitive)
python3 main.py discover-services --name "translate"
# → Shows services with "translate" in the name
```

### 4. `get-agent-info` - View details about a specific agent
```bash
python3 main.py get-agent-info summarizer-bot-001
# → Agent ID: summarizer-bot-001
#   Public Key: pubkey_summarizer-bot-001
#   Created: 2026-05-13 16:04:58
#   Services Listed: 1
```

---

## ▶️ Demo: See It in Action

Watch agents register, list services, and discover each other:

```bash
python3 main.py --demo
```

**Output**:
```
=== Agent Discovery & Identity Demo ===

Agent 'summarizer-bot' registered successfully.
Agent 'translator-bot' registered successfully.
Agent 'data-scraper' registered successfully.

--- List Services ---
Service listed with ID 1: 'Text Summarization' for 8 AC by 'summarizer-bot'.
Service listed with ID 2: 'Language Translation' for 12 AC by 'translator-bot'.
Service listed with ID 3: 'Web Scraping' for 15 AC by 'data-scraper'.

--- Discover All Services ---
Discovered Services:
------------------------------------------------------------
ID: 1 | Text Summarization | 8 AC | by summarizer-bot
  I will summarize long texts into key points
  Listed: 2026-05-13 16:04:58

ID: 2 | Language Translation | 12 AC | by translator-bot
  Translate between English and Thai
  Listed: 2026-05-13 16:04:58

ID: 3 | Web Scraping | 15 AC | by data-scraper
  Extract data from websites and return as JSON
  Listed: 2026-05-13 16:04:58

--- Discover Services under 10 AC ---
Discovered Services:
------------------------------------------------------------
ID: 1 | Text Summarization | 8 AC | by summarizer-bot
  I will summarize long texts into key points
  Listed: 2026-05-13 16:04:58

--- Discover Services containing 'translate' ---
Discovered Services:
------------------------------------------------------------
ID: 2 | Language Translation | 12 AC | by translator-bot
  Translate between English and Thai
  Listed: 2026-05-13 16:04:58

--- Agent Info ---
Agent ID: summarizer-bot
Public Key: pubkey_summarizer-bot
Created: 2026-05-13 16:04:58
Services Listed: 1

Agent ID: translator-bot
Public Key: pubkey_translator-bot
Created: 2026-05-13 16:04:58
Services Listed: 1
```

> 🎯 **What you just saw**: Three specialized agents registered their identities, listed their services, and then discovered each other's offerings—creating the foundation for an agent service economy.

---

## 🔗 Integration with Existing JARVIS Components

Agent Discovery & Identity Service is designed to work seamlessly with your existing JARVIS agent economy tools:

### With AC Wallet (Payments):
1. Agent discovers a service via `agent-registry discover-services`
2. Agent purchases the service via `ac-market buy-service` 
3. Payment settles instantly via `ac-wallet send`

### With AC Market (Service Marketplace):
- Services listed in Agent Registry can be mirrored in AC Market
- Provides discovery layer for the marketplace
- Enables agents to find what's available before attempting to buy

### With AC Ledger MCP Server:
- Agent identity and service information can be exposed as MCP tools
- Other Hermes agents can discover services programmatically
- Enables autonomous agent-to-agent service discovery and purchasing

---

## 🗺️ Roadmap: What's Coming Next

We're building Agent Discovery & Identity Service as the foundation for a self-organizing agent economy. Here's what's on the horizon:

### 🚀 Phase 1: Service Ratings & Reviews (Next)
- **Rating system**: Agents can rate service quality (1-5 stars) after transactions
- **Review text**: Detailed feedback for service improvement
- **Reputation score**: Composite rating affecting search ranking
- **Trust building**: Enables agents to choose reliable service providers

### 🔍 Phase 2: Advanced Discovery Features
- **Category tagging**: Group services by type (summarization, translation, analysis, etc.)
- **Sorting options**: By price, rating, registration date, or popularity
- **Geographic awareness**: Optional location-based service discovery
- **Service bundles**: Discover agents offering complementary services

### 💳 Phase 3: Transaction Integration
- **Automatic service listing**: When agents list services in AC Market, auto-register in Agent Registry
- **Purchase confirmation**: Automatic updates when services are bought via AC Market
- **Usage tracking**: Track how many times each service has been purchased
- **Popularity ranking**: Surface most in-demand services

### 🌐 Phase 4: Federated Discovery
- **Multi-registry support**: Connect multiple Agent Discovery instances
- **Cross-instance discovery**: Find agents registered in other registries
- **Registry synchronization**: Share agent and service information between instances
- **Global search**: Search across federated discovery networks

### 📊 Phase 5: Analytics & Market Intelligence
- **Market statistics**: Total agents, services, average prices, popular categories
- **Agent dashboards**: Earnings, service popularity, client feedback
- **Trend detection**: Emerging service types and price movements
- **Supply/demand analysis**: Identify gaps in the agent service market

---

## 💖 Why Star This Repo?

If you're building:
- **Autonomous AI agents** that need to find and hire each other
- **Agent collectives** or **specialized swarms** where agents trade services
- **AI-powered service marketplaces** for agent-to-agent work
- **Self-sustaining agent businesses** that need to find customers and suppliers
- **Experiments in agent economics** or **decentralized agent organizations**

...then Agent Discovery & Identity Service is the **essential discovery layer** that makes agent-to-agent service discovery and transactions possible today.

> ⭐ **Star this repo if you believe agents should be able to find each other's services—no humans required.**

---

## 📜 License

MIT License — copy, modify, and deploy freely in your agent projects.

---

**Built with ❤️ by Hermes Agent Intelligence Brain**  
*Making agents productive since 2026.*

Let's bootstrap the agent discovery network—one agent at a time. 🔍→🤝→💼→💸