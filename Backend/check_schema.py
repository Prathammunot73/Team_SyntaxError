import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

print('Assignments table columns:')
cursor.execute('PRAGMA table_info(assignments)')
for row in cursor.fetchall():
    print(f'  - {row[1]} ({row[2]})')

print('\nTables in database:')
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
for row in cursor.fetchall():
    print(f'  - {row[0]}')

conn.close()
