import os
import aws_cdk as cdk
from stacks.lambda_internal_extension_stack import LambdaInternalExtensionStack

app = cdk.App()

LambdaInternalExtensionStack(
    app,
    "dev",
    stack_name="LambdaInternalExtensionStack-dev",
    env=cdk.Environment(
        account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
        region=os.environ.get("CDK_DEFAULT_REGION"),
    ),
)

app.synth()
