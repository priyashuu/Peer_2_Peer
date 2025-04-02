from typing import Dict

def process_message(node, message: Dict) -> Dict:
    """Process incoming messages based on their type."""
    message_type = message.get('type')
    
    if message_type == 'JOIN':
        return node.handle_join(message)
    elif message_type == 'STORE':
        return node.handle_store(message)
    elif message_type == 'LOOKUP':
        return node.handle_lookup(message)
    elif message_type == 'ROUTING_INFO':
        return node.handle_routing_info(message)
    else:
        return {'status': 'error', 'message': 'Unknown message type'}