# AC Sync

HTTP server for AC wallet ledger, exposing the AC wallet functionality over HTTP.

## Endpoints

- `POST /wallet/create` - Create a new wallet
- `GET /wallet/balance?agent_id=x` - Get wallet balance
- `POST /wallet/send` - Send AC from one agent to another
- `GET /wallet/history?agent_id=x` Get transaction history
- `POST /wallet/faucet` - Fund an wallet (for testing)

## Usage

```bash
# Start the server
python3 main.py --port 8080

# Or run the demo (starts server and runs example requests)
python3 main.py --demo
```

## Example (from demo)

```bash
# Create wallets
curl -X POST http://localhost:8080/wallet/create -H "Content-Type: application/json" -d '{"agent_id":"alice"}'
curl -X POST http://localhost:8080/wallet/create -H "Content-Type: application/json" -d '{"agent_id":"bob"}'

# Fund via faucet (100 AC each)
curl -X POST http://localhost:8080/wallet/faucet -H "Content-Type: application/json" -d '{"agent_id":"alice","amount":100}'
curl -X POST http://localhost:8080/wallet/faucet -H "Content-Type: application/json" -d '{"agent_id":"bob","amount":100}'

# Check balances
curl http://localhost:8080/wallet/balance?agent_id=alice
curl http://localhost:8080/wallet/balance?agent_id=bob

# Send 30 AC from alice to bob
curl -X POST http://localhost:8080/wallet/send -H "Content-Type: application/json" -d '{"from_agent":"alice","to_agent":"bob","amount":30}'

# Check balances after transfer
curl http://localhost:8080/wallet/balance?agent_id=alice
curl http://localhost:8080/wallet/balance?agent_id=bob

# View transaction history
curl http://localhost:8080/wallet/history?agent_id=alice
curl http://localhost:8080/wallet/history?agent_id=bob
```

## Implementation

- Built with Python standard library only (`http.server`, `sqlite3`, `json`, `threading`, `time`, `urllib.parse`)
- Under 200 lines of code
- Uses SQLite for persistence at `~/.jarvis/ac_wallet.db`
- Thread-safe HTTP server

## Responses

All endpoints return JSON.

Success responses:
- `201 Created` for wallet creation
- `200 OK` for other successful operations

Error responses:
- `400 Bad Request` for missing or invalid parameters
- `404 Not Found` for unknown endpoints or missing wallets
- `409 Conflict` for trying to create an existing wallet

Error response format:
```json
{"error": "error message"}
```

Success response examples:
- Wallet creation: `{"message": "Wallet created for 'alice' with starting balance 0 AC."}`
- Balance: `{"agent_id": "alice", "balance": 100}`
- Send: `{"message": "Sent 30 AC from 'alice' to 'bob'."}`
- History: `{"agent_id": "alice", "history": [{"from": "bob", "to": "alice", "amount": 30, "time": "2026-05-14 10:30:00"}]}`
- Faucet: `{"message": "Faucet funded 'alice' with 100 AC."}`

## Demo

The `--demo` mode starts the server on port 8080 and runs a series of requests showing:
1. Wallet creation
2. Initial balance check (0 AC)
3. Funding via faucet (100 AC each)
4. Balance check after funding
5. Transfer of 30 AC from alice to bob
6. Balance check after transfer
7. Transaction history for both agents

## Notes

- The server runs on `localhost` only for security.
- The demo mode is intended for testing and demonstration.
- For production use, consider running behind a reverse proxy or adding authentication.

---
*Part of the AC Agent Economy Stack*