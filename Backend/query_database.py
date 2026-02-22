#!/usr/bin/env python3
"""
Query Database - Run custom SQL queries
"""

import sqlite3
import sys

def run_query(query):
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        cursor.execute(query)
        
        # If SELECT query, fetch and display results
        if query.strip().upper().startswith('SELECT'):
            rows = cursor.fetchall()
            
            if rows:
                print(f"\n✅ Found {len(rows)} rows:\n")
                
                # Print column headers
                headers = rows[0].keys()
                print(" | ".join(headers))
                print("-" * (len(" | ".join(headers))))
                
                # Print rows
                for row in rows:
                    values = [str(row[key]) if row[key] is not None else 'NULL' for key in headers]
                    print(" | ".join(values))
            else:
                print("\n⚠️  No results found")
        else:
            # For INSERT, UPDATE, DELETE
            conn.commit()
            print(f"\n✅ Query executed successfully")
            print(f"   Rows affected: {cursor.rowcount}")
    
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
    
    finally:
        conn.close()

def main():
    print("\n" + "="*70)
    print("  DATABASE QUERY TOOL")
    print("="*70)
    
    if len(sys.argv) > 1:
        # Query provided as command line argument
        query = ' '.join(sys.argv[1:])
        print(f"\nQuery: {query}\n")
        run_query(query)
    else:
        # Interactive mode
        print("\nExamples:")
        print("  python query_database.py \"SELECT * FROM students\"")
        print("  python query_database.py \"SELECT * FROM marks WHERE exam='Insem-1'\"")
        print("  python query_database.py \"SELECT COUNT(*) FROM complaints\"")
        print("\nOr enter query now:")
        
        query = input("\nSQL Query: ")
        if query.strip():
            run_query(query)
        else:
            print("No query entered")
    
    print()

if __name__ == '__main__':
    main()
