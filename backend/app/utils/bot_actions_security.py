from ipaddress import ip_network

BLOCKED_HOSTNAMES = frozenset(
    {
        "localhost",
        "0.0.0.0",
    }
)

BLOCKED_IP_NETWORKS = (
    ip_network("127.0.0.0/8"),
    ip_network("10.0.0.0/8"),
    ip_network("172.16.0.0/12"),
    ip_network("192.168.0.0/16"),
    ip_network("169.254.0.0/16"),
)

