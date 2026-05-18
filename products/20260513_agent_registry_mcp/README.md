# Agent Registry MCP Server

MCP server for agent discovery and identity. Enables agents to register, list services, discover services, and get agent information.

## Tools Exposed

- `register_agent` - Register a new agent
- `list_service` - List a service offered by an agent  
- `discover_services` - Discover services with optional filters (name, max price)
- `get_agent_info` - Get information about an agent

## Usage

```bash
# Run demo
python3 main.py --demo

# Start MCP server (default)
python3 main.py --serve
```

## Example

```bash
# Register an agent
python3 main.py register-agent summarizer-bot

# List a service
python3 main.py list-service summarizer-bot "Text Summarization" "I will summarize long texts" 8

# Discover services under 10 AC
python3 main.py discover-services --max-price 10

# Get agent info
python3 main.py get-agent-info summarizer-bot
```

## MCP Integration

Other Hermes agents can call these tools via MCP stdio:

```json
{
  "name": "discover_services",
  "arguments": {
    "service_name": "translation",
    "max_price": 15
  }
}
```

## Implementation

- Built with stdlib + sqlite only
- Under 200 lines of code
- Automatic database initialization at ~/.jarvis/agent_registry.db
- Case-insensitive service name search
- Agent verification before listing services