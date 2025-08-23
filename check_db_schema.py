import sqlite3

# Connect to database and show schema
conn = sqlite3.connect('disaster_analysis.db')
cursor = conn.cursor()

print("=== DATABASE SCHEMA ===")
cursor.execute('PRAGMA table_info(disaster_posts)')
schema = cursor.fetchall()
for column in schema:
    print(f"{column[1]}: {column[2]}")

print("\n=== SAMPLE DATA ===")
cursor.execute('SELECT * FROM disaster_posts LIMIT 3')
sample_data = cursor.fetchall()

# Get column names
column_names = [description[0] for description in cursor.description]
print("Columns:", column_names)

print("\nSample records:")
for i, row in enumerate(sample_data):
    print(f"\nRecord {i+1}:")
    for j, value in enumerate(row):
        print(f"  {column_names[j]}: {value}")

conn.close()
