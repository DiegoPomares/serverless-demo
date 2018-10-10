def handler(event, _context):
    name = event['params']['querystring'].get('name', 'World')
    return f'Hello {name}!'
