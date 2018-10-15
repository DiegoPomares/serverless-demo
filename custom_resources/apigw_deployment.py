import traceback, json
import boto3
import cfnresponse


def handler(event, context):
    status = cfnresponse.SUCCESS
    response = {}
    pid = None

    try:
        rest_api_id = event['ResourceProperties']['RestApiId']
        stage_name = event['ResourceProperties']['StageName']

        if event['RequestType'] in ['Create', 'Update']:
            deployment = create_deployment(rest_api_id, stage_name)
            pid = deployment

        if event['RequestType'] == 'Delete':
            # Do nothing, APIGW deployments will be deleted when the APIGW is deleted
            pass

    except Exception as err:
        print(json.dumps({
            'event': event,
            'error': traceback.format_exc().splitlines(),
        }))
        status = cfnresponse.FAILED

    finally:
        cfnresponse.send(event, context, status, response, pid)


def create_deployment(rest_api_id, stage_name):
    client = boto3.client('apigateway')

    response = client.create_deployment(
        restApiId=rest_api_id,
        stageName=stage_name
    )

    return response['id']
