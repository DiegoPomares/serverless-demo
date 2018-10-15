import os

from troposphere import Template, Parameter, Ref, Output, GetAtt, Join
from troposphere.awslambda import Function, Code, Version
from troposphere.iam import Role, Policy
from troposphere.cloudformation import AWSCustomObject

CUSTOM_LAMBDA_VERSION_PATH = "../custom_resources/lambda_version.py"


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

        artifacts_bucket_name = self.t.add_parameter(Parameter(
            "ArtifactsBucketName",
            Description="Name of the S3 bucket to store Lambda function artifacts",
            AllowedPattern="[a-z0-9][a-z0-9.-]{2,62}",
            Type="String"
        ))

        lambda_iam_policy_arn = self.t.add_parameter(Parameter(
            "LambdaIAMPolicyARN",
            Description="ARN of the base IAM policy for Lambda functions",
            Type="String"
        ))

        lambda_role = self.t.add_resource(Role(
            "LambdaRole",
            AssumeRolePolicyDocument={
                "Version": "2012-10-17",
                "Statement": [{
                    "Action": ["sts:AssumeRole"],
                    "Effect": "Allow",
                    "Principal": {
                        "Service": ["lambda.amazonaws.com"]
                    }
                }]
            },
            ManagedPolicyArns=[
                Ref(lambda_iam_policy_arn),
            ],
        ))

        custom_lambda_version_role = self.t.add_resource(Role(
            "CustomLambdaVersionRole",
            AssumeRolePolicyDocument={
                "Version": "2012-10-17",
                "Statement": [{
                    "Action": ["sts:AssumeRole"],
                    "Effect": "Allow",
                    "Principal": {
                        "Service": ["lambda.amazonaws.com"]
                    }
                }]
            },
            ManagedPolicyArns=[
                Ref(lambda_iam_policy_arn),
            ],
            Policies=[Policy(
                PolicyName="PublishLambdaVersion",
                PolicyDocument={
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": ["lambda:PublishVersion"],
                            "Resource": "*",
                        },
                    ]
                })
            ],
        ))

        self.custom_lambda_version_lambda = self.t.add_resource(Function(
            f"CustomLambdaVersionLambda",
            FunctionName="CustomLambdaVersionLambda",
            Handler="index.handler",
            Runtime="python3.6",
            Role=GetAtt(custom_lambda_version_role, "Arn"),
            Code=Code(
                ZipFile=self.get_custom_lambda_version_code()
            )
        ))

        for l in lambda_names:
            self.add_lambda(l, artifacts_bucket_name, lambda_role)


    def get_custom_lambda_version_code(self):
        script_path = os.path.dirname(os.path.realpath(__file__))
        code_path = os.path.join(script_path, CUSTOM_LAMBDA_VERSION_PATH)

        with open(code_path) as f:
            return f.read()

    def add_lambda(self, name, s3_bucket, role):
        s3_key = self.t.add_parameter(Parameter(
            f"{name}KeyS3",
            Description=f"S3 key for lambda function: {name}",
            Type="String"
        ))

        s3_version = self.t.add_parameter(Parameter(
            f"{name}ObjectVersionS3",
            Description=f"S3 object version ID for lambda function: {name}",
            Type="String"
        ))

        function = self.t.add_resource(Function(
            f"{name}Lambda",
            FunctionName=name,
            Handler="index.handler",
            Runtime="python3.6",
            Role=GetAtt(role, "Arn"),
            Code=Code(
                S3Bucket=Ref(s3_bucket),
                S3Key=Ref(s3_key),
                S3ObjectVersion=Ref(s3_version)
            )
        ))

        # version = self.t.add_resource(Version(
        #     f"{name}LambdaVersion",
        #     FunctionName=Ref(function)
        # ))

        version = self.t.add_resource(CustomLambdaVersion(
            f"{name}LambdaVersion",
            ServiceToken=GetAtt(self.custom_lambda_version_lambda, "Arn"),
            FunctionName=Ref(function),
            S3ObjectVersion=Ref(s3_version)
        ))

        uri = Join('', [
                'arn:aws:apigateway:',
                Ref('AWS::Region'),
                ':lambda:path/2015-03-31/functions/arn:aws:lambda:',
                Ref('AWS::Region'),
                ':',
                Ref('AWS::AccountId'),
                ':function:',
                Ref(function),
                '/invocations?Qualifier=',
                GetAtt(version, "Version"),
        ])

        self.t.add_output(Output(
            f"{name}LambdaURI",
            Value=uri,
            Description=f"{name}LambdaURI"
        ))
