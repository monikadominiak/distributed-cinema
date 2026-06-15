from cassandra.cluster import Cluster

cluster = Cluster(["localhost"])
session = cluster.connect()

session.execute("""
CREATE KEYSPACE IF NOT EXISTS cinema
WITH replication = {
    'class': 'SimpleStrategy',
    'replication_factor': 3
}
""")

session.set_keyspace("cinema")

session.execute("""
CREATE TABLE IF NOT EXISTS reservations (
    seat_number text PRIMARY KEY,
    reservation_id text,
    customer_name text,
    customer_email text,
    movie_id text,
    status text
)
""")

print("Database initialized")