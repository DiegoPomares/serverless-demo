from troposphere import Template, Parameter, Ref, Output, GetAtt, Join
from troposphere.awslambda import Function, Code, Version
from troposphere.iam import Role, Policy

from consts import DEFAULTS


template = Template()
lambda_parameters = {}
lambda_functions = {}
lambda_versions = {}
lambda_uris = {}

artifacts_bucket_name = template.add_parameter(Parameter(
    "ArtifactsBucketName",
    Description="Name of the S3 bucket to store Lambda function artifacts",
    AllowedPattern="[a-z0-9][a-z0-9.-]{2,62}",
    Type="String"
))

lambda_role = template.add_resource(Role(
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


def add_lambda(name):
    parameter_names = [f"{name}KeyS3", f"{name}ObjectVersionS3"]
    for n in parameter_names:
        lambda_parameters[n] = template.add_parameter(Parameter(
            n,
            Type="String"
        ))

    lambda_functions[f"{name}Lambda"] = function = template.add_resource(Function(
        f"{name}Lambda",
        FunctionName=name,
        Handler="index.handler",
        Runtime="python3.6",
        Role=GetAtt(lambda_role, "Arn"),
        Code=Code(
            S3Bucket=Ref(artifacts_bucket_name),
            S3Key=Ref(lambda_parameters[f"{name}KeyS3"]),
            S3ObjectVersion=Ref(lambda_parameters[f"{name}ObjectVersionS3"])
        )
    ))

    lambda_versions[f"{name}LambdaVersion"] = version = template.add_resource(Version(
        f"{name}LambdaVersion",
        FunctionName=Ref(function)
    ))

    lambda_uris[f"{name}LambdaVersion"] = uri = Join('', [
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

    template.add_output(Output(
        f"{name}LambdaURI",
        Value=uri,
        Description=f"{name}LambdaURI"
    ))


for l in DEFAULTS['LambdaNames']:
    add_lambda(l)


def sceptre_handler(_sceptre_user_data=None):
    return template.to_yaml()


if __name__ == '__main__':
    print(sceptre_handler())
