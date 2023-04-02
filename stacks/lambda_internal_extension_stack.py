from aws_cdk import (
    RemovalPolicy,
    Stack,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_lambda_python_alpha as _alambda,
    aws_ssm as ssm,
)
from constructs import Construct


class LambdaInternalExtensionStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create StringList parameter in SSM Parameter Store
        parameter = ssm.StringListParameter(
            self,
            "SSMParameter_maintenance-window",
            parameter_name="maintenance-window",
            string_list_value=["2023-04-01T02:00:00Z", "2023-04-01T06:00:00Z"],
        )

        # Create On-Demand table in DynamoDB
        table = dynamodb.Table(
            self,
            "DynamoDBTable_maintenance-window-events-table",
            table_name="maintenance-window-events-table",
            partition_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.STRING,
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # Create lambda layer
        lambda_layer = _alambda.PythonLayerVersion(
            self,
            "LambdaLayer_maintenance-window-layer",
            layer_version_name="maintenance-window-layer",
            description="Wrapper script + forked awslambdaric",
            entry="lambda/layers/maintenance-window-layer",
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_9],
            removal_policy=RemovalPolicy.DESTROY,
        )

        # Create policy document
        lambda_pre_handler_policy_document = iam.PolicyDocument(
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "dynamodb:PutItem",
                        "ssm:GetParameter",
                    ],
                    resources=["*"],
                )
            ]
        )

        # Create customer managed policy
        lambda_pre_handler_policy = iam.ManagedPolicy(
            self,
            "Policy_lambda-pre-handler-policy",
            managed_policy_name="lambda-pre-handler-policy",
            description="Lambda pre-handler customer managed policy",
            document=lambda_pre_handler_policy_document,
        )

        # Create lambda execution role
        test_lambda_execution_role = iam.Role(
            self,
            "Role_test-lambda-execution-role",
            role_name="test-lambda-execution-role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                lambda_pre_handler_policy,
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                ),
            ],
        )

        # Create lambda function
        test_lambda = _lambda.Function(
            self,
            "LambdaFunction_maintenance-window-test-lambda",
            function_name="maintenance-window-test-lambda",
            description="Lambda for testing maintenance window",
            code=_lambda.Code.from_asset("lambda/functions/maintenance-window-test-lambda"),
            handler="lambda_function.lambda_handler",
            runtime=_lambda.Runtime.PYTHON_3_9,
            role=test_lambda_execution_role,
            environment={"AWS_LAMBDA_EXEC_WRAPPER": "/opt/python/wrapper-script"},
            layers=[lambda_layer],
        )
