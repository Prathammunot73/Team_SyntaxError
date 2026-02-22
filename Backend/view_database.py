#!/usr/bin/env python3
"""
View Database Contents
Quick script to view all tables and data in database.db
"""

import sqlite3

def view_database():
    print("\n" + "="*70)
    print("  DATABASE VIEWER - database.db")
    print("="*70)
    
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    
    print(f"\n📊 Found {len(tables)} tables:\n")
    
    for table in tables:
        table_name = table['name']
        print(f"\n{'='*70}")
        print(f"  TABLE: {table_name}")
        print('='*70)
        
        # Get column info
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        print("\nColumns:")
        for col in columns:
            print(f"  • {col['name']} ({col['type']})")
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"\nTotal Rows: {count}")
        
        # Show sample data (first 5 rows)
        if count > 0:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
            rows = cursor.fetchall()
            
            print("\nSample Data (first 5 rows):")
            for i, row in enumerate(rows, 1):
                print(f"\n  Row {i}:")
                for key in row.keys():
                    value = row[key]
                    if value is not None and len(str(value)) > 50:
                        value = str(value)[:50] + "..."
                    print(f"    {key}: {value}")
    
    conn.close()
    
    print("\n" + "="*70)
    print("  END OF DATABASE")
    print("="*70 + "\n")

if __name__ == '__main__':
    view_database()
