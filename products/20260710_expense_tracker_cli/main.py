#!/usr/bin/env python3
"""
ExpenseTracker CLI - Simple, private expense tracking for freelancers and small businesses.
"""

import argparse
import sqlite3
import os
import sys
from datetime import datetime, date

DB_NAME = "expenses.db"
DEFAULT_CATEGORIES = [
    "food", "transport", "office", "travel", "entertainment", 
    "utilities", "healthcare", "education", "software", "marketing"
]

def init_db(db_path):
    """Initialize the expenses database with required tables."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            payment_method TEXT,
            receipt_number TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            color TEXT DEFAULT '#6366f1'
        )
    """)
    
    # Insert default categories if they don't exist
    for category in DEFAULT_CATEGORIES:
        cursor.execute(
            "INSERT OR IGNORE INTO categories (name) VALUES (?)",
            (category,)
        )
    
    conn.commit()
    conn.close()

def add_expense(date, description, amount, category, payment_method=None, receipt_number=None, notes=None):
    """Add a new expense to the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO expenses (date, description, amount, category, payment_method, receipt_number, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (date, description, amount, category, payment_method, receipt_number, notes))
    conn.commit()
    conn.close()

def get_expenses(start_date=None, end_date=None, category=None):
    """Retrieve expenses with optional filtering."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    query = "SELECT id, date, description, amount, category, payment_method, receipt_number, notes FROM expenses"
    params = []
    
    conditions = []
    if start_date:
        conditions.append("date >= ?")
        params.append(start_date)
    if end_date:
        conditions.append("date <= ?")
        params.append(end_date)
    if category:
        conditions.append("category = ?")
        params.append(category)
        
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += " ORDER BY date DESC, id DESC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_total_amount(start_date=None, end_date=None, category=None):
    """Calculate total expenses with optional filtering."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    query = "SELECT SUM(amount) FROM expenses"
    params = []
    
    conditions = []
    if start_date:
        conditions.append("date >= ?")
        params.append(start_date)
    if end_date:
        conditions.append("date <= ?")
        params.append(end_date)
    if category:
        conditions.append("category = ?")
        params.append(category)
        
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    cursor.execute(query, params)
    result = cursor.fetchone()[0]
    conn.close()
    return result if result is not None else 0.0

def format_expenses(expenses):
    """Format expenses as a nice table."""
    if not expenses:
        return "No expenses found."
    
    headers = ["ID", "DATE", "DESCRIPTION", "AMOUNT", "CATEGORY", "PAYMENT", "RECEIPT", "NOTES"]
    # Initialize column widths with header lengths
    col_widths = [len(h) for h in headers]
    
    # Calculate max width for each column
    for row in expenses:
        for i, cell in enumerate(row):
            if i == 3:  # amount column - format as currency
                cell_str = f"${float(cell):.2f}"
            else:
                cell_str = str(cell) if cell is not None else ""
            col_widths[i] = max(col_widths[i], len(cell_str))
    
    # Create header
    header_line = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    separator_line = "-+-".join("-" * w for w in col_widths)
    
    # Create rows
    rows = []
    for row in expenses:
        formatted_cells = []
        for i, cell in enumerate(row):
            if i == 3:  # amount column
                cell_str = f"${float(cell):.2f}"
            else:
                cell_str = str(cell) if cell is not None else ""
            formatted_cells.append(cell_str.ljust(col_widths[i]))
        rows.append(" | ".join(formatted_cells))
    
    return "\n".join([header_line, separator_line] + rows)

def run_demo():
    """Run a demonstration of the expense tracker with sample data."""
    print("Running demo mode...")
    
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
        print(f"Deleted existing database: {DB_NAME}")
    
    init_db(DB_NAME)
    print("Database initialized.")
    
    print("Inserting demo expense data...")
    # Add some realistic demo expenses
    demo_expenses = [
        ("2024-01-15", "Lunch with client at Downtown Cafe", 24.50, "food", "credit_card", "RCPT001", "Client meeting about website redesign"),
        ("2024-01-18", "Uber to client meeting", 18.75, "transport", "credit_card", None, "Across town"),
        ("2024-01-19", "Notebook and pens for work", 12.99, "office", "debit_card", "RCPT003", "Moleskine notebook"),
        ("2024-01-20", "Electricity bill for home office", 67.50, "utilities", "bank_transfer", None, "Monthly bill"),
        ("2024-01-22", "Gym membership (health)", 45.00, "healthcare", "credit_card", None, "Monthly membership"),
        ("2024-01-23", "Book: 'The Lean Startup'", 18.99, "education", "credit_card", "RCPT004", "Kindle version"),
        ("2024-01-24", "Client dinner", 89.00, "food", "credit_card", "RCPT005", "Celebrated project completion"),
        ("2024-01-25", "New ergonomic mouse", 45.00, "office", "credit_card", None, "Wrist pain relief"),
        ("2024-01-26", "Monthly Adobe Creative Cloud subscription", 54.99, "software", "credit_card", None, "Annual plan billed monthly"),
        ("2024-01-27", "Flight to conference", 345.00, "travel", "credit_card", "RCPT006", "Round trip to tech conference"),
        ("2024-01-28", "Hotel stay for conference", 180.00, "travel", "credit_card", "RCPT007", "2 nights at downtown hotel"),
        ("2024-01-29", "Conference ticket", 299.00, "education", "credit_card", "RCPT008", "Tech conference 2024"),
        ("2024-01-30", "Client thank you gifts", 75.00, "marketing", "credit_card", "RCPT009", "Custom branded mugs")
    ]
    
    for expense_data in demo_expenses:
        add_expense(*expense_data)
    
    print("Demo data inserted.")
    
    print("\n" + "="*70)
    print("EXPENSE TRACKER DEMO - ALL EXPENSES")
    print("="*70)
    expenses = get_expenses()
    print(format_expenses(expenses))
    
    total = get_total_amount()
    print(f"\nTotal Expenses: ${total:.2f}")
    
    print("\n" + "-"*70)
    print("EXPENSES BY CATEGORY (JANUARY 2024)")
    print("-"*70)
    for category in ["food", "transport", "office", "travel", "software"]:
        cat_total = get_total_amount("2024-01-01", "2024-01-31", category)
        if cat_total > 0:
            print(f"{category.capitalize():<12}: ${cat_total:>8.2f}")
    
    print("\n" + "="*70)
    print("Demo completed. Try these commands:")
    print("  expense add --description 'Coffee meeting' --amount 5.50 --category food")
    print("  expense list")
    print("  expense summary")
    print("="*70)
    
    sys.exit(0)

def main():
    parser = argparse.ArgumentParser(
        description="ExpenseTracker CLI - Simple, private expense tracking for freelancers and small businesses",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  expense add --description "Lunch with client" --amount 24.50 --category food
  expense list --limit 10
  expense summary --month 1 --year 2024
  expense export --format csv --output expenses.csv
        """
    )
    
    # Define a temporary parser for --demo to use parse_known_args
    demo_parser = argparse.ArgumentParser(add_help=False)
    demo_parser.add_argument('--demo', action='store_true', help='Run in demo mode with sample data')
    
    args, remaining_argv = demo_parser.parse_known_args()
    
    if args.demo:
        run_demo()
    
    # Now build the full parser with subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Add command
    add_parser = subparsers.add_parser('add', help='Add a new expense')
    add_parser.add_argument('--date', help='Date of expense (YYYY-MM-DD, defaults to today)')
    add_parser.add_argument('--description', required=True, help='Description of the expense')
    add_parser.add_argument('--amount', type=float, required=True, help='Amount spent')
    add_parser.add_argument('--category', required=True, choices=DEFAULT_CATEGORIES, 
                          help=f'Expense category (choose from: {", ".join(DEFAULT_CATEGORIES)})')
    add_parser.add_argument('--payment-method', choices=['cash', 'credit_card', 'debit_card', 'bank_transfer', 'paypal', 'other'],
                          help='Payment method used')
    add_parser.add_argument('--receipt-number', help='Receipt or invoice number')
    add_parser.add_argument('--notes', help='Additional notes about the expense')
    add_parser.set_defaults(func=lambda args: add_expense(
        args.date or date.today().isoformat(),
        args.description,
        args.amount,
        args.category,
        args.payment_method,
        args.receipt_number,
        args.notes
    ) or print(f"Added expense: {args.description} - ${args.amount:.2f}"))
    
    # List command
    list_parser = subparsers.add_parser('list', help='List expenses')
    list_parser.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    list_parser.add_argument('--end-date', help='End date (YYYY-MM-DD)')
    list_parser.add_argument('--category', choices=DEFAULT_CATEGORIES, help='Filter by category')
    list_parser.add_argument('--limit', type=int, default=50, help='Maximum number of results to show')
    list_parser.set_defaults(func=lambda args: print(format_expenses(
        get_expenses(args.start_date, args.end_date, category=args.category)[:args.limit]
    )))
    
    # Summary command
    summary_parser = subparsers.add_parser('summary', help='Show summary statistics')
    summary_parser.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    summary_parser.add_argument('--end-date', help='End date (YYYY-MM-DD)')
    summary_parser.add_argument('--category', choices=DEFAULT_CATEGORIES, help='Filter by category')
    summary_parser.add_argument('--month', type=int, help='Month (1-12)')
    summary_parser.add_argument('--year', type=int, help='Year (YYYY)')
    summary_parser.set_defaults(func=lambda args: show_summary(
        args.start_date, args.end_date, args.category, args.month, args.year
    ))
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export expenses to file')
    export_parser.add_argument('--format', choices=['csv', 'json'], default='csv', help='Export format')
    export_parser.add_argument('--output', required=True, help='Output file path')
    export_parser.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    export_parser.add_argument('--end-date', help='End date (YYYY-MM-DD)')
    export_parser.add_argument('--category', choices=DEFAULT_CATEGORIES, help='Filter by category')
    export_parser.set_defaults(func=lambda args: export_expenses(
        args.format, args.output, args.start_date, args.end_date, args.category
    ))
    
    # Categories command
    cat_parser = subparsers.add_parser('categories', help='Manage expense categories')
    cat_parser.add_argument('--list', action='store_true', help='List all available categories')
    cat_parser.add_argument('--add', help='Add a new category')
    cat_parser.set_defaults(func=lambda args: manage_categories(args))
    
    # If no command is given, show help
    if not remaining_argv:
        parser.print_help()
        sys.exit(0)
    
    # Parse the remaining arguments with the full parser
    args = parser.parse_args(remaining_argv)
    
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()

def show_summary(start_date=None, end_date=None, category=None, month=None, year=None):
    """Show summary statistics for expenses."""
    # Handle month/year filtering
    if month and year:
        start_date = f"{year:04d}-{month:02d}-01"
        if month == 12:
            end_date = f"{year+1:04d}-01-01"
        else:
            end_date = f"{year:04d}-{month+1:02d}-01"
    elif month and not year:
        # Assume current year if only month provided
        current_year = date.today().year
        start_date = f"{current_year:04d}-{month:02d}-01"
        if month == 12:
            end_date = f"{current_year+1:04d}-01-01"
        else:
            end_date = f"{current_year:04d}-{month+1:02d}-01"
    
    total = get_total_amount(start_date, end_date, category)
    count = len(get_expenses(start_date, end_date, category))
    
    print("EXPENSE SUMMARY")
    print("="*50)
    if start_date and end_date:
        print(f"Period: {start_date} to {end_date}")
    elif month and year:
        print(f"Period: {year}-{month:02d}")
    else:
        print("Period: All time")
    
    if category:
        print(f"Category: {category}")
    print(f"Total Expenses: ${total:.2f}")
    print(f"Number of Transactions: {count}")
    if count > 0:
        print(f"Average per Transaction: ${total/count:.2f}")
    
    # Show breakdown by category if no category filter
    if not category:
        print("\nBREAKDOWN BY CATEGORY:")
        print("-"*30)
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Build date filter for the query
        date_params = []
        if start_date and end_date:
            date_filter = "date >= ? AND date <= ?"
            date_params = [start_date, end_date]
        elif start_date:
            date_filter = "date >= ?"
            date_params = [start_date]
        elif end_date:
            date_filter = "date <= ?"
            date_params = [end_date]
        else:
            date_filter = "1=1"
            date_params = []
        
        cursor.execute(f"""
            SELECT category, SUM(amount) as total, COUNT(*) as count 
            FROM expenses 
            WHERE {date_filter}
            GROUP BY category 
            ORDER BY total DESC
        """, date_params)
        
        for cat, cat_total, cat_count in cursor.fetchall():
            print(f"{cat.capitalize():<12}: ${cat_total:>8.2f} ({cat_count} transactions)")
        conn.close()

def export_expenses(format_type, output_file, start_date=None, end_date=None, category=None):
    """Export expenses to CSV or JSON format."""
    expenses = get_expenses(start_date, end_date, category)
    
    if not expenses:
        print("No expenses to export.")
        return
    
    if format_type == 'csv':
        import csv
        with open(output_file, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['ID', 'Date', 'Description', 'Amount', 'Category', 'Payment Method', 'Receipt Number', 'Notes'])
            for row in expenses:
                # Format amount as currency for CSV
                formatted_row = list(row)
                formatted_row[3] = f"{float(row[3]):.2f}"  # Amount column
                writer.writerow(formatted_row)
        print(f"Exported {len(expenses)} expenses to {output_file}")
    
    elif format_type == 'json':
        import json
        data = []
        for row in expenses:
            data.append({
                'id': row[0],
                'date': row[1],
                'description': row[2],
                'amount': float(row[3]),
                'category': row[4],
                'payment_method': row[5],
                'receipt_number': row[6],
                'notes': row[7]
            })
        
        with open(output_file, 'w') as jsonfile:
            json.dump(data, jsonfile, indent=2)
        print(f"Exported {len(expenses)} expenses to {output_file}")

def manage_categories(args):
    """Manage expense categories."""
    if args.list:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM categories ORDER BY name")
        categories = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        print("Available Categories:")
        for i, category in enumerate(categories, 1):
            print(f"  {i:2d}. {category}")
    
    elif args.add:
        category_name = args.add.lower().strip()
        if not category_name:
            print("Error: Category name cannot be empty.")
            return
            
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO categories (name) VALUES (?)", (category_name,))
            conn.commit()
            print(f"Added category: {category_name}")
        except sqlite3.IntegrityError:
            print(f"Category '{category_name}' already exists.")
        finally:
            conn.close()

if __name__ == "__main__":
    # Initialize database if it doesn't exist
    if not os.path.exists(DB_NAME):
        init_db(DB_NAME)
    
    main()