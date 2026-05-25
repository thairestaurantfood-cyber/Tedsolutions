import os
import sys
import sqlite3
from datetime import datetime
import argparse

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

    def demo():
        if os.path.exists(DB_PATH): os.remove(DB_PATH)
        init_db()

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('''
        INSERT INTO invoices (client_name, amount, issue_date, due_date, status, notes)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', ('Client A', 100.00, '2023-10-01', '2023-11-01', 'Pending', 'Initial invoice'))

        cursor.execute('''
        INSERT INTO invoices (client_name, amount, issue_date, due_date, status, notes)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', ('Client B', 200.00, '2023-10-15', '2023-12-15', 'Paid', 'Recurring service'))

        cursor.execute('''
        INSERT INTO invoices (client_name, amount, issue_date, due_date, status, notes)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', ('Client C', 150.00, '2023-11-01', '2024-01-01', 'Pending', 'Product order'))

        conn.commit()
        conn.close()

        print(f"{'ID':<5} {'Client Name':<20} {'Amount':<10} {'Issue Date':<15} {'Due Date':<15} {'Status':<10} {'Notes':<20}")
        print("-" * 90)

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        invoices = cursor.fetchall()
        for invoice in invoices:
            print(f"{invoice[0]:<5}{invoice[1]:<20}{invoice[2]:<10}{invoice[3]:<15}{invoice[4]:<15}{invoice[5]:<10}{invoice[6]:<20}")

            conn.close()
            print("Demo complete.")

            def list_invoices():
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM invoices')
                invoices = cursor.fetchall()
                conn.close()

                if not invoices:
                    print("No invoices found.")
                    return

                print(f"{'ID':<5} {'Client Name':<20} {'Amount':<10} {'Issue Date':<15} {'Due Date':<15} {'Status':<10} {'Notes':<20}")
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

                                print("Overdue Invoices:")
                                for invoice in overdue_invoices:
                                    print(f"Client: {invoice[0]}, Due Date: {invoice[1]}")

                                    def main():
                                        parser = argparse.ArgumentParser(description="InvoiceChaser")
                                        parser.add_argument('--demo', action='store_true', help='Run demo')
                                        pre, _ = parser.parse_known_args()  # check --demo FIRST
                                        if pre.demo:
                                            demo()
                                            return
                                        subs = parser.add_subparsers(dest='command')  # NO required=True

                                        list_parser = subs.add_parser('list', help='List all invoices')
                                        list_parser.set_defaults(func=list_invoices)

                                        report_parser = subs.add_parser('report', help='Generate invoice status report')
                                        report_parser.set_defaults(func=generate_report)

                                        notify_parser = subs.add_parser('notify', help='Notify about overdue invoices')
                                        notify_parser.set_defaults(func=notify_overdue_invoices)

                                        args = parser.parse_args()
                                        if not args.command:
                                            parser.print_help()
                                            return
                                        else:
                                            args.func()

                                            if __name__ == "__main__":
                                                main()