import hashlib

# Configuration
ID_BITS = 16  # Number of bits in the node ID
ID_SPACE = 2**ID_BITS  # Size of the ID space
ROUTING_TABLE_ROWS = 4  # Number of rows in the routing table (simplified)
ROUTING_TABLE_COLS = 2**4  # Number of columns per row (simplified)
LEAF_SET_SIZE = 4  # Number of nodes in each leaf set (simplified)

def hash_key(key: str) -> int:
    """Hash a key to get its position in the ID space."""
    hash_obj = hashlib.sha1(key.encode())
    # Take first 16 bits (2 bytes) of the hash
    hash_bytes = hash_obj.digest()[:2]
    return int.from_bytes(hash_bytes, byteorder='big')