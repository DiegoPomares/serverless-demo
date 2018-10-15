def handler(event, _context):
    name = event['params']['querystring'].get('name', '').upper() or 'World'
    return f'Hello {name}!'
