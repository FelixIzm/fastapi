import sqlite3
conn = sqlite3.connect("./db/all_fields.db")
conn.row_factory = lambda cursor, row: row[0]

cursor = conn.cursor()
ids = cursor.execute("SELECT * FROM search_ids WHERE flag=1").fetchall()
print(len(ids))


def split(a, n):
    k, m = divmod(len(a), n)
    return (a[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n))

def split_list(a_list):
    half = len(a_list)//2
    return a_list[:half], a_list[half:]

A = [1,2,3,4,5,6,7,8,9]
B, C = split_list(ids)

#print((B))
#print(len(C))

asd= list(split(A,4))
for i in asd:
    print(len(i))

#f=1013
#print(f//2)
#print(f%2)
