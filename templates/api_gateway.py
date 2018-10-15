import os
import yaml

from troposphere import Template, Parameter, Ref, Output, GetAtt, Join
from troposphere.awslambda import Function, Code, Version
from troposphere.apigateway import Deployment, Stage, RestApi
from troposphere.iam import Role, Policy

from consts import DEFAULTS


template = Template()


def sceptre_handler(_sceptre_user_data=None):
    return template.to_yaml()


lambda_parameters = {}

def ref_constructor(loader, node):
    element = loader.construct_scalar(node)
    return Ref(element)

def getatt_constructor(loader, node):
    element, attribute = loader.construct_scalar(node).split('.')
    return GetAtt(element, attribute)

yaml.add_constructor('!Ref', ref_constructor)
yaml.add_constructor('!GetAtt', getatt_constructor)

script_path = os.path.dirname(os.path.realpath(__file__))
swagger_path = os.path.join(script_path, '../src/swagger.cloudformation.yaml')
with open(swagger_path) as f:
    swagger = yaml.load(f.read())

json_mapping_template = template.add_parameter(Parameter(
    "MappingTemplate",
    Description="Mapping template for request body, uri and body params, and stage variables",
    Default=DEFAULTS['MappingTemplate'],
    Type="String"
))


def add_lambda_uri_parameters(name):
    parameter_name = f"{name}LambdaURI"
    lambda_parameters[parameter_name] = template.add_parameter(Parameter(
            parameter_name,
            Type="String"
    ))


for l in DEFAULTS['LambdaNames']:
    add_lambda_uri_parameters(l)

apigw_role = template.add_resource(Role(
    "APIGWRole",
    AssumeRolePolicyDocument={
        "Version": "2012-10-17",
        "Statement": [{
            "Action": ["sts:AssumeRole"],
            "Effect": "Allow",
            "Principal": {
                "Service": ["apigateway.amazonaws.com"]
            }
        }]
    },
    Path="/",
    Policies=[Policy(
        PolicyName="APIGateway",
        PolicyDocument={
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": ["lambda:InvokeFunction", "iam:PassRole"],
                    "Resource": "*",
                },
            ]
        })
    ],
))


apigw = template.add_resource(RestApi(
    "APIGW",
    Body=swagger
))

apigw_deployment = template.add_resource(Deployment(
    "APIGWDeployment",
    RestApiId=Ref(apigw)
))

apigw_stage_latest = template.add_resource(Stage(
    "APIGWStage",
    StageName='latest',
    RestApiId=Ref(apigw),
    DeploymentId=Ref(apigw_deployment)
))

template.add_output(Output(
    "URL",
    Value=Join('', [
        'https://',
        Ref(apigw),
        '.execute-api.',
        Ref('AWS::Region'),
        '.amazonaws.com/',
        Ref(apigw_stage_latest),
    ]),
    Description="API Gateway URL, 'latest' stage"
))
