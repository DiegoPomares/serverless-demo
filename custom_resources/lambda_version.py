import json
import boto3
import cfnresponse


def handler(event, context):
    response = {
        'event': event,
        'context': context,
        'responseStatus': cfnresponse.SUCCESS,
        'responseData': {},
        'physicalResourceId': None,
        'noEcho': False,
    }

    try:
        function_name = event['ResourceProperties']['FunctionName']

        if event['RequestType'] in ['Create', 'Update']:
            version = create_version(function_name)
            response['responseData']['Version'] = version
            response['physicalResourceId'] = f'{function_name}:{version}'

        if event['RequestType'] == 'Delete':
            # Do nothing, Lambda versions will be deleted when the Lambda function is deleted
            pass

    except Exception as err:
        msg = f'{err.__class__.__name__}: {str(err)}'
        print(msg)
        response['Error'] = msg
        response['responseStatus'] = cfnresponse.FAILED

    finally:
        cfnresponse.send(**response)


def create_version(function_name):
    client = boto3.client('lambda')

    response = client.publish_version(
        FunctionName=function_name
    )

    return response['Version']
