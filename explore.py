import sqlite3

conn = sqlite3.connect('tasks.db')
cur = conn.cursor()

cur.execute("SELECT * FROM tasks")
print(cur.fetchall())

print("\n", "*"*50)

cur.execute("SELECT * FROM tasks where id = 1")
print(cur.fetchone())
print("\n", "*"*50)

cur.execute("SELECT COUNT(*) FROM tasks")
print(cur.fetchone())
print("\n", "*"*50)

conn.close()