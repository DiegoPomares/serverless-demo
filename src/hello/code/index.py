import json

def handler(event, _context):
    print(json.dumps(event))
    event['queryStringParameters'] = event['queryStringParameters'] or {}
    name = event['queryStringParameters'].get('name', '').upper() or 'World'

    return {
        'statusCode': 200,
        'body': f'Hello {name}!',
    }
