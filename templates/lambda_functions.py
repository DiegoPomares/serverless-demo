from troposphere import Template, Parameter, Ref, Output, GetAtt, Join
from troposphere.awslambda import Function, Code, Version
from troposphere.iam import Role, Policy

from consts import DEFAULTS


class MainTemplate:
    def __init__(self, lambda_names):
        self.t = Template()

        artifacts_bucket_name = self.t.add_parameter(Parameter(
            "ArtifactsBucketName",
            Description="Name of the S3 bucket to store Lambda function artifacts",
            AllowedPattern="[a-z0-9][a-z0-9.-]{2,62}",
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
            Path="/",
            Policies=[Policy(
                PolicyName="CloudWatchLogs",
                PolicyDocument={
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": ["iam:ListAccountAliases"],
                            "Resource": "*",
                        },
                        {
                            "Effect": "Allow",
                            "Action": ["logs:CreateLogGroup"],
                            "Resource": Join(
                                ":",
                                ["arn:aws:logs", Ref("AWS::Region"), Ref("AWS::AccountId"), "*"]
                            ),
                        },
                        {
                            "Effect": "Allow",
                            "Action": ["logs:CreateLogStream", "logs:PutLogEvents"],
                            "Resource": Join(
                                ":",
                                ["arn:aws:logs", Ref("AWS::Region"), Ref("AWS::AccountId"), "log-group", "/aws/lambda/*", "*"]
                            ),
                        }
                    ]
                })
            ],
        ))

        for l in lambda_names:
            self.add_lambda(l, artifacts_bucket_name, lambda_role)

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

        version = self.t.add_resource(Version(
            f"{name}LambdaVersion",
            FunctionName=Ref(function)
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


def sceptre_handler(_sceptre_user_data=None):
    template = MainTemplate(DEFAULTS['LambdaNames'])
    yaml = template.t.to_yaml()
    return yaml


if __name__ == '__main__':
    print(sceptre_handler())
