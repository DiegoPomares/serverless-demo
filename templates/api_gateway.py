import os
import yaml

from troposphere import Template, Parameter, Ref, Output, GetAtt, Join
from troposphere.awslambda import Function, Code, Version
from troposphere.apigateway import Deployment, Stage, RestApi
from troposphere.iam import Role, Policy
from troposphere.cloudformation import AWSCustomObject

SWAGGER_TEMPLATE_PATH = "../src/swagger.cloudformation.yaml"
MAPPING_TEMPLATE = '#set($allParams=$input.params()){"body-json":$input.json("$"),"params":{#foreach($type in $allParams.keySet())#set($params=$allParams.get($type)) "$type":{#foreach($paramName in $params.keySet())"$paramName":"$util.escapeJavaScript($params.get($paramName))"#if($foreach.hasNext),#end#end}#if($foreach.hasNext),#end#end},"stage-variables":{#foreach($key in $stageVariables.keySet())"$key":"$util.escapeJavaScript($stageVariables.get($key))"#if($foreach.hasNext),#end#end}}'
CUSTOM_APIGW_DEPLOYMENT_PATH = "../custom_resources/apigw_deployment.py"


def sceptre_handler(sceptre_user_data=None):
    sceptre_user_data = sceptre_user_data or {}

    template = MainTemplate(sceptre_user_data.get('LambdaFunctionNames', []))
    yaml = template.t.to_yaml()
    return yaml


class CustomLambdaVersion(AWSCustomObject):
    resource_type = "Custom::LambdaVersion"

    props = {
        'ServiceToken': (str, True),
        'FunctionName': (str, True),
        'S3ObjectVersion': (str, True),
    }


class MainTemplate:
    def __init__(self, lambda_names):
        self.t = Template()

        json_mapping_template = self.t.add_parameter(Parameter(
            "MappingTemplate",
            Description="Mapping template for request body, uri and body params, and stage variables",
            Default=MAPPING_TEMPLATE,
            Type="String"
        ))

        for l in lambda_names:
            self.add_lambda_uri_parameters(l)

        apigw_role = self.t.add_resource(Role(
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

        apigw = self.t.add_resource(RestApi(
            "APIGW",
            Body=self.get_swagger()
        ))

        apigw_deployment = self.t.add_resource(Deployment(
            "APIGWDeployment",
            RestApiId=Ref(apigw)
        ))

        apigw_stage_latest = self.t.add_resource(Stage(
            "APIGWStage",
            StageName='latest',
            RestApiId=Ref(apigw),
            DeploymentId=Ref(apigw_deployment)
        ))

        self.t.add_output(Output(
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

    def add_lambda_uri_parameters(self, name):
        parameter_name = f"{name}LambdaURI"
        self.t.add_parameter(Parameter(
            parameter_name,
            Type="String"
    ))

    def get_swagger(self):
        script_path = os.path.dirname(os.path.realpath(__file__))
        swagger_path = os.path.join(script_path, SWAGGER_TEMPLATE_PATH)

        def ref_constructor(loader, node):
            element = loader.construct_scalar(node)
            return Ref(element)

        def getatt_constructor(loader, node):
            element, attribute = loader.construct_scalar(node).split('.')
            return GetAtt(element, attribute)

        yaml.add_constructor('!Ref', ref_constructor)
        yaml.add_constructor('!GetAtt', getatt_constructor)

        with open(swagger_path) as f:
            return yaml.load(f.read())

    def get_custom_apigw_deployment_code(self):
        script_path = os.path.dirname(os.path.realpath(__file__))
        code_path = os.path.join(script_path, CUSTOM_APIGW_DEPLOYMENT_PATH)

        with open(code_path) as f:
            return f.read()
