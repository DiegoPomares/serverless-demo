import traceback, json
import boto3
import cfnresponse


def handler(event, context):
    status = cfnresponse.SUCCESS
    response = {}
    pid = None

    try:
        function_name = event['ResourceProperties']['FunctionName']

        if event['RequestType'] in ['Create', 'Update']:
            version = create_version(function_name)
            pid = f'{function_name}:{version}'
            response['Version'] = version

        if event['RequestType'] == 'Delete':
            # Do nothing, Lambda versions will be deleted when the Lambda function is deleted
            pass

    except Exception as err:
        print(json.dumps({
            'event': event,
            'error': traceback.format_exc().splitlines(),
        }))
        status = cfnresponse.FAILED

    finally:
        cfnresponse.send(event, context, status, response, pid)


def create_version(function_name):
    client = boto3.client('lambda')

    response = client.publish_version(
        FunctionName=function_name
    )

    return response['Version']
