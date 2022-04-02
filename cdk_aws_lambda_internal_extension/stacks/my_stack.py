from datetime import datetime, timedelta
from pathlib import Path
from constructs import Construct
from aws_cdk import RemovalPolicy, Stack
from aws_cdk.aws_ssm import StringListParameter
from aws_cdk.aws_dynamodb import Attribute, AttributeType, BillingMode, Table
from aws_cdk.aws_lambda_python_alpha import PythonLayerVersion
from aws_cdk.aws_lambda import Code, Function, Runtime
from aws_cdk.aws_iam import (
    Effect,
    ManagedPolicy,
    PolicyDocument,
    PolicyStatement,
    Role,
    ServicePrincipal,
)


def get_maintenance_window():
    today = datetime.now()
    tomorrow = today + timedelta(days=1)

    today_datetime_str = today.strftime("%Y-%m-%dT00:00:00Z")
    tomorrow_datetime_str = tomorrow.strftime("%Y-%m-%dT00:00:00Z")

    return [today_datetime_str, tomorrow_datetime_str]


class MyStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        StringListParameter(
            self,
            "MaintenanceWindow",
            parameter_name="maintenance-window",
            string_list_value=get_maintenance_window(),
        )

        Table(
            self,
            "MaintenanceWindowEventsTable",
            table_name="maintenance-window-events-table",
            partition_key=Attribute(
                name="timestamp",
                type=AttributeType.STRING,
            ),
            billing_mode=BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # Build Python Lambda layer inside Docker
        maintenance_window_lambda_layer = PythonLayerVersion(
            self,
            "MaintenanceWindowLambdaLayer",
            layer_version_name="maintenance-window-layer",
            description="Wrapper script + Forked awslambdaric",
            entry=str(
                Path(__file__).parent / ".." / "layers" / "maintenance-window"
            ),
            compatible_runtimes=[Runtime.PYTHON_3_9],
            removal_policy=RemovalPolicy.DESTROY,
        )

        lambda_pre_handler_policy_document = PolicyDocument(
            statements=[
                PolicyStatement(
                    effect=Effect.ALLOW,
                    actions=[
                        "dynamodb:PutItem",
                        "ssm:GetParameter",
                    ],
                    resources=["*"],
                )
            ]
        )

        lambda_pre_handler_policy = ManagedPolicy(
            self,
            "LambdaPreHandlerPolicy",
            managed_policy_name="lambda-pre-handler-policy",
            description="Lambda pre-handler customer managed policy",
            document=lambda_pre_handler_policy_document,
        )

        test_lambda_role = Role(
            self,
            "TestLambdaRole",
            role_name="test-lambda-role",
            assumed_by=ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                lambda_pre_handler_policy,
                ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                ),
            ],
        )

        Function(
            self,
            "TestLambda",
            function_name="test-lambda",
            description="Lambda for testing maintenance window",
            code=Code.from_asset(
                str(Path(__file__).parent / ".." / "functions" / "test")
            ),
            handler="index.handler",
            runtime=Runtime.PYTHON_3_9,
            role=test_lambda_role,
            environment={"AWS_LAMBDA_EXEC_WRAPPER": "/opt/python/wrapper-script"},
            layers=[maintenance_window_lambda_layer],
        )
