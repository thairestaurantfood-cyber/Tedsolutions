import os
import sys
import sqlite3
import argparse
from datetime import datetime

DB_PATH = os.path.expanduser('~/.jarvis/invoicechaser.db')

def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT NOT NULL,
            amount REAL NOT NULL,
            issue_date TEXT NOT NULL,
            due_date TEXT NOT NULL,
            status TEXT NOT NULL,
            notes TEXT
        )
    ''')
    conn.commit()
    conn.close()

    def add_invoice(client_name, amount, issue_date, due_date, status, notes):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO invoices (client_name, amount, issue_date, due_date, status, notes)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (client_name, amount, issue_date, due_date, status, notes))
        conn.commit()
        conn.close()

        def list_invoices():
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM invoices')
            invoices = cursor.fetchall()
            conn.close()

            if not invoices:
                print("No invoices found.")
                return

            print(f"{'ID':<5}{'Client':<20}{'Amount':<10}{'Issue Date':<15}{'Due Date':<15}{'Status':<10}{'Notes':<20}")
            print("-" * 90)
            for invoice in invoices:
                print(f"{invoice[0]:<5}{invoice[1]:<20}{invoice[2]:<10}{invoice[3]:<15}{invoice[4]:<15}{invoice[5]:<10}{invoice[6]:<20}")

                def generate_report():
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute('SELECT status, COUNT(*) FROM invoices GROUP BY status')
                    reports = cursor.fetchall()
                    conn.close()

                    if not reports:
                        print("No report data found.")
                        return

                    print(f"{'Status':<10} {'Count'}")
                    print("-" * 35)
                    for report in reports:
                        print(f"{report[0]:<10} {report[1]}")

                        def notify_overdue_invoices():
                            now = datetime.now().strftime('%Y-%m-%d')
                            conn = sqlite3.connect(DB_PATH)
                            cursor = conn.cursor()
                            cursor.execute('SELECT client_name, due_date FROM invoices WHERE status="Pending" AND due_date<?', (now,))
                            overdue_invoices = cursor.fetchall()
                            conn.close()

                            if not overdue_invoices:
                                print("No overdue invoices.")
                                return

                            for invoice in overdue_invoices:
                                print(f"Overdue Invoice: {invoice[0]} - Due Date: {invoice[1]}")

                                def demo():
                                    if os.path.exists(DB_PATH):
                                        os.remove(DB_PATH)

                                        init_db()

                                        invoices_data = [
                                        ("Client A", 100.00, "2023-01-01", "2023-01-15", "Paid", "Payment received"),
                                        ("Client B", 150.00, "2023-01-05", "2023-01-20", "Pending", "Awaiting payment"),
                                        ("Client C", 200.00, "2023-01-10", "2023-01-25", "Overdue", "Payment overdue")
                                        ]

                                        for invoice in invoices_data:
                                            add_invoice(*invoice)

                                            list_invoices()
                                            print("\nReport:")
                                            generate_report()
                                            print("\nNotifications:")
                                            notify_overdue_invoices()
                                            sys.exit(0)

                                            def main():
                                                pre, _ = parser.parse_known_args()
                                                if pre.demo:
                                                    demo()
                                                    return

                                                parser = argparse.ArgumentParser(description='InvoiceChaser - Track and manage invoices.')
                                                subparsers = parser.add_subparsers(dest='command')

                                                add_parser = subparsers.add_parser('add', help='Add a new invoice')
                                                add_parser.add_argument('--client', required=True, help='Client name')
                                                add_parser.add_argument('--amount', type=float, required=True, help='Invoice amount')
                                                add_parser.add_argument('--issue-date', required=True, help='Issue date (YYYY-MM-DD)')
                                                add_parser.add_argument('--due-date', required=True, help='Due date (YYYY-MM-DD)')
                                                add_parser.add_argument('--status', required=True, help='Invoice status')
                                                add_parser.add_argument('--notes', help='Additional notes')

                                                list_parser = subparsers.add_parser('list', help='List all invoices')

                                                report_parser = subparsers.add_parser('report', help='Generate invoice report')

                                                notify_parser = subparsers.add_parser('notify', help='Notify overdue invoices')

                                                args = parser.parse_args()
                                                if not args.command:
                                                    parser.print_help()
                                                    return

                                                if __name__ == "__main__":
                                                    main()