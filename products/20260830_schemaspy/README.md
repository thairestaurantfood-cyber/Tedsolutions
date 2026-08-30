# SchemaSpy

A CLI tool to visualize and document database schemas. Inspect SQLite databases and display formatted table output of tables, columns, data types, and relationships.

## Installation

No installation required. Simply copy `main.py` to your desired location and run with Python 3.6+.

## Usage

```bash
# Show help
python3 main.py --help

# Run demo with sample database
python3 main.py --demo

# List tables in a database
python3 main.py list /path/to/database.db

# Show schema for a specific table
python3 main.py schema /path/to/database.db table_name

# Show foreign keys for a specific table
python3 main.py foreign-keys /path/to/database.db table_name
```

## Example Output

### Demo Mode
```
$ python3 main.py --demo

Users Table:
ID   Name      Email               Age  Active   
-------------------------------------------------------
1    Alice     alice@example.com   30   1         
2    Bob       bob@example.com     25   0         
3    Charlie   charlie@example.com 35   1         

Orders Table:
ID   User ID   Product        Price     Order Date   
------------------------------------------------------------
1    1         Laptop         999.99    2023-01-15   
2    1         Mouse          19.99     2023-01-16   
3    2         Keyboard       49.99     2023-02-20   
4    3         Monitor        199.99    2023-03-10   

Products Table:
ID   Name           Category       Price     Stock    
-------------------------------------------------------
1    Laptop         Electronics    999.99    10       
2    Mouse          Accessories    19.99     50       
3    Keyboard       Accessories    49.99     30       
4    Monitor        Electronics    199.99    15       

Schema for table: users
Column         Type      Not Null  Default   Primary Key   
------------------------------------------------------------
id             INTEGER   False     None      True          
name           TEXT      True      None      False         
email          TEXT      True      None      False         
age            INTEGER   False     None      False         
is_active      BOOLEAN   False     None      False         

Schema for table: orders
Column         Type      Not Null  Default   Primary Key   
------------------------------------------------------------
id             INTEGER   False     None      True          
user_id        INTEGER   False     None      False         
product        TEXT      True      None      False         
price          REAL      True      None      False         
order_date     TEXT      True      None      False         

Schema for table: products
Column         Type      Not Null  Default   Primary Key   
------------------------------------------------------------
id             INTEGER   False     None      True          
name           TEXT      True      None      False         
category       TEXT      True      None      False         
price          REAL      True      None      False         
stock          INTEGER   True      None      False         

Foreign keys for table: orders
ID   Sequence  Table          From           To            
------------------------------------------------------------
0    0         users          user_id        id            
```

### List Command
```
$ python3 main.py list sample.db
Tables in database:
- users
- orders
- products
```

### Schema Command
```
$ python3 main.py schema sample.db users

Schema for table: users
Column         Type      Not Null  Default   Primary Key   
------------------------------------------------------------
id             INTEGER   False     None      True          
name           TEXT      True      None      False         
email          TEXT      True      None      False         
age            INTEGER   False     None      False         
is_active      BOOLEAN   False     None      False         
```

### Foreign Keys Command
```
$ python3 main.py foreign-keys sample.db orders

Foreign keys for table: orders
ID   Sequence  Table          From           To            
------------------------------------------------------------
0    0         users          user_id        id            
```

## Tech Stack

- Python standard library only: `os`, `sys`, `sqlite3`, `argparse`
- No external dependencies
- Works offline with any SQLite database

## Built by JARVIS

Date: 2026-08-30
Score: 13/12 (BuildGuard)
Phases: [1, 2, 3]
Built offline: True