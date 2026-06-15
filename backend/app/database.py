from cassandra.cluster import Cluster

cluster = Cluster(
    ["127.0.0.1"],
    connect_timeout=10,
    control_connection_timeout=10
)

session = cluster.connect("cinema")
session.default_timeout = 10