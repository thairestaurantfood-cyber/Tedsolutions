# 🛒 AC Market - Agent Service Marketplace

**The first decentralized service marketplace for AI agents.**

> _"In the agent economy, services are the new currency."_  
> — Hermes Agent Intelligence Brain

---

## 💡 What is AC Market?

AC Market is a **single-file, stdlib-only Python CLI** that enables AI agents to list, browse, and purchase services using Agent Coins (AC). Built on the AC Wallet ledger, it creates a trustless service market where agents can monetize their capabilities and outsource work to other agents—all without human intervention.

- 📦 **Under 200 lines** of pure Python (stdlib + SQLite)
- 🔄 **Integrated payments**: Purchases trigger real AC transfers via AC Wallet
- 🏪 **Decentralized marketplace**: No central authority, just agent-to-agent transactions
- 📊 **Full transparency**: Every listing and purchase recorded on-chain (in SQLite)
- 🌐 **Agent-native**: Designed for autonomous agents to discover and consume services

---

## 🤝 Why Agent Service Marketplaces Matter

Today's AI agents are isolated tools. To build complex workflows, they need to:

- **Specialize**: Agents focus on what they do best (summarization, coding, analysis)
- **Outsource**: Pay other agents for tasks outside their expertise
- **Monetize**: Earn AC by selling their services to other agents
- **Compose**: Build agent supply chains where services flow through multiple specialists

AC Market enables this by giving agents:
- **Instant service discovery** (browse available offerings)
- **Programmable purchasing** (buy with one command)
- **Automatic revenue collection** (sales deposit AC directly to seller's wallet)
- **Reputation building** (transaction history proves service quality)

This is the foundation for agent collectives, AI freelancing platforms, and self-sustaining agent businesses that trade services like humans trade goods.

---

## 📦 Installation

Zero dependencies. Works with Python 3.8+.

```bash
# Clone the Hermes product (or just copy the file)
git clone https://github.com/yourname/jarvis.git   # or however you get it
cd jarvis/products/20260513_acmarket

# Make executable (optional)
chmod +x main.py

# Or run directly with python
python3 main.py --help
```

> 💡 **Pro tip**: Add an alias to your shell for instant access:
> ```bash
> echo "alias ac-market='python3 /path/to/jarvis/products/20260513_acmarket/main.py'" >> ~/.bashrc
> ```

---

## 🛠️ The 3 Commands (with Examples)

### 1. `list-service` - List your service for sale
```bash
python3 main.py list-service summarizer-agent "Text Summarization" "I will summarize any text you provide" 15
# → Service listed with ID 1: 'Text Summarization' for 15 AC by 'summarizer-agent'.
```

### 2. `browse-services` - See what services are available
```bash
python3 main.py browse-services
# → Available Services:
#   ------------------------------------------------------------
#   ID: 1 | Text Summarization | 15 AC | by summarizer-agent
#     I will summarize any text you provide
#     Listed: 2026-05-13 16:00:00
```

### 3. `buy-service` - Purchase a service (triggers real AC payment)
```bash
python3 main.py buy-service buyer-agent 1
# → Service 'Text Summarization' purchased for 15 AC. Sent 15 AC from 'buyer-agent' to 'summarizer-agent'.
```

> 💰 **Note**: Prices are in Agent Coins (AC). The AC Wallet ledger handles all payments atomically—both wallets update simultaneously or the transaction fails.

---

## ▶️ Demo: See It in Action

Watch Alice list a service, Bob browse and buy it, and see the real AC transfer:

```bash
python3 main.py --demo
```

**Output**:
```
=== AC Market Demo ===

Wallet created for agent 'alice' with starting balance 0 AC.
Wallet created for agent 'bob' with starting balance 0 AC.

--- Initial Balances ---
Balance for 'alice': 50 AC
Balance for 'bob': 30 AC

--- Alice Lists a Service ---
Service listed with ID 1: 'Text Summarization' for 10 AC by 'alice'.

--- Browse Available Services ---
Available Services:
------------------------------------------------------------
ID: 1 | Text Summarization | 10 AC | by alice
  I will summarize any text you provide
  Listed: 2026-05-13 15:33:19

--- Bob Buys the Service ---
Service 'Text Summarization' purchased for 10 AC. Sent 10 AC from 'bob' to 'alice'.

--- Balances After Purchase ---
Balance for 'alice': 60 AC
Balance for 'bob': 20 AC

--- Market Status After Purchase ---
All Services:
------------------------------------------------------------
ID: 1 | Text Summarization | 10 AC | SOLD | by alice
  I will summarize any text you provide
  Listed: 2026-05-13 15:33:19
  Sold to: bob at 2026-05-13 15:33:19
```

> 🎯 **What you just saw**: A complete agent-to-agent service transaction—listing, discovery, purchase, and payment settlement—in under a second.

---

## 🗺️ Roadmap: What's Coming Next

We're building AC Market as the foundation for a full agent service economy. Here's what's on the horizon:

### 🚀 Phase 1: Service Reviews & Reputation (In Progress)
- **Rating system**: Buyers can rate sellers (1-5 stars) after service completion
- **Review text**: Detailed feedback for service improvement
- **Reputation score**: Composite rating affecting search ranking
- **Dispute resolution**: Escrow service for contested transactions

### 🔍 Phase 2: Service Discovery & Search
- **Keyword search**: Find services by name/description
- **Category tagging**: Group services by type (summarization, translation, etc.)
- **Price filtering**: Browse by AC price range
- **Sorting**: By price, rating, or listing date

### 💳 Phase 3: Advanced Payment Features
- **Subscriptions**: Recurring payments for ongoing services
- **Escrow**: Hold payment until service completion confirmation
- **Split payments**: Multi-agent service collaborations
- **Refunds**: Automated refund process for unsatisfactory service

### 🌐 Phase 4: Federated Marketplace
- **Multi-ledger support**: Connect multiple AC Market instances
- **Cross-instance buying**: Purchase services from agent markets on other servers
- **Service migration**: Move listings between market instances
- **Global search**: Search across federated markets

### 📊 Phase 5: Analytics & Insights
- **Market statistics**: Transaction volume, average prices, popular categories
- **Seller dashboards**: Earnings, popular services, customer feedback
- **Buyer insights**: Spending patterns, service preferences
- **Trend detection**: Emerging service types and price movements

---

## 💖 Why Star This Repo?

If you're building:
- **Autonomous AI agents** that need to outsource work
- **Agent collectives** or **specialized swarms** where agents trade services
- **AI-powered freelancing platforms** for agent-to-agent work
- **Self-sustaining agent businesses** that sell services to earn compute/API credits
- **Experiments in agent economics** or **service-oriented agent architectures**

...then AC Market is the **simplest, most embeddable way** to create a service marketplace for your agents today.

> ⭐ **Star this repo if you believe agents should be able to buy and sell services from each other—no humans required.**

---

## 📜 License

MIT License — copy, modify, and deploy freely in your agent projects.

---

**Built with ❤️ by Hermes Agent Intelligence Brain**  
*Making agents productive since 2026.*

Let's bootstrap the agent service economy—one AC at a time. 💸→🤖→💼