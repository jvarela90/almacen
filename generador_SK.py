def generate_serial_key():
    """Generar serial key único"""
    import secrets
    import string
    
    # Formato: XXXX-XXXX-XXXX-XXXX
    chars = string.ascii_uppercase + string.digits
    blocks = []
    
    for _ in range(4):
        block = ''.join(secrets.choice(chars) for _ in range(4))
        blocks.append(block)
    
    return '-'.join(blocks)