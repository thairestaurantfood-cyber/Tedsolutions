# ExpenseTracker CLI

Simple, private expense tracking for freelancers, small businesses, and individuals who want to keep track of their spending without relying on cloud services or sharing their financial data.

## Features

- **Private & Secure**: All data stored locally in SQLite database on your machine
- **Simple CLI**: Easy-to-use command line interface
- **Flexible Categorization**: Predefined categories plus ability to add custom ones
- **Flexible Date Filtering**: View expenses by date range, month, or custom periods
- **Export Capabilities**: Export to CSV or JSON for backup or analysis in other tools
- **Demo Mode**: Try it out with sample data using `--demo` flag
- **Zero Dependencies**: Uses only Python standard library - no installation required beyond Python 3.6+

## Installation

Since this is a pure Python CLI tool with no external dependencies, you can simply:

1. Copy the `expense_tracker.py` file to your desired location
2. Make it executable: `chmod +x expense_tracker.py`
```bash
chmod +x expense_tracker.py
```

## Usage

### Initial Setup
On first run, the tool will automatically create an SQLite database (`expenses.db`) in the same directory.

### Adding Expenses
```bash
./expense_tracker.py add --description "Lunch with client" --amount 24.50 --category food
./expense_tracker.py add --description "Uber to meeting" --amount 18.75 --category transport --payment-method credit_card
```

### Listing Expenses
```bash
./expense_tracker.py list
./expense_tracker.py list --start-date 2024-01-01 --end-date 2024-01-31
./expense_tracker.py list --category food --limit 10
```

### Summary & Reports
```bash
./expense_tracker.py summary
./expense_tracker.py summary --month 1 --year 2024
./expense_tracker.py summary --category food
```

### Exporting Data
```bash
./expense_tracker.py export --format csv --output expenses.csv
./expense_tracker.py export --format json --output expenses.json --start-date 2024-01-01
```

### Managing Categories
```bash
./expense_tracker.py categories --list
./expense_tracker.py categories --add freelance_subscriptions
```

### Demo Mode
Try out the tool with sample data:
```bash
./expense_tracker.py demo
```

## Data Storage

- Database file: `expenses.db` (SQLite)
- Location: Same directory as the script (or specify via environment variable if needed)
- No data leaves your machine unless you explicitly export it

## Categories

Default categories include:
- food
- transport
- office
- travel
- entertainment
- utilities
- healthcare
- education
- software
- marketing

You can add custom categories using the `categories --add` command.

## Privacy & Security

- All financial data stays on your local machine
- No telemetry, no tracking, no internet connection required
- You control your data completely - backup, delete, or move the `.db` file as needed
- Optional password protection can be added via filesystem encryption if desired

## Requirements

- Python 3.6 or higher
- No external packages required (uses only standard library)

## License

MIT License - feel free to modify and distribute as needed.

---
*Built with the JARVIS autonomous product-building system*