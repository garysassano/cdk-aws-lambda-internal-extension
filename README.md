# cdk-aws-lambda-internal-extension

CDK app that deploys a Lambda internal extension to modify the standard behaviour of AWS Lambda.

## Prerequisites

- **_AWS:_**
  - Must have authenticated with [Default Credentials](https://docs.aws.amazon.com/cdk/v2/guide/cli.html#cli_auth) in your local environment.
  - Must have completed the [CDK bootstrapping](https://docs.aws.amazon.com/cdk/v2/guide/bootstrapping.html) for the target AWS environment.
- **_Node.js + npm:_**
  - Must be [installed](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm) in your system.
- **_Poetry:_**
  - Must be [installed](https://python-poetry.org/docs/#installation) in your system.
- **_Docker:_**
  - Must be [installed](https://docs.docker.com/get-docker/) in your system and running at deployment.

## Installation

```sh
npx projen install
```

## Deployment

```sh
npx projen deploy
```

## Cleanup

```sh
npx projen destroy
```

## Architecture Diagram - High Level

![Architecture Diagram - High Level](./cdk_aws_lambda_internal_extension/assets/arch-hld.svg)

1. **Lambda Layer Creation**
   - A Lambda layer containing the internal extension is created and attached to the Lambda function.

2. **Triggering the Lambda Function**
   - The Lambda function can be triggered manually by the user or programmatically via a cron job using Amazon EventBridge.

3. **Executing the Wrapper Script**
   - Upon startup, the Lambda function is configured to execute a [wrapper script](https://docs.aws.amazon.com/lambda/latest/dg/runtimes-modify.html#runtime-wrapper) from the Lambda layer. This execution is specified by the `AWS_LAMBDA_EXEC_WRAPPER` environment variable, which points to the path of the wrapper script.

4. **Invoking the Forked `awslambdaric`**
   - The wrapper script then invokes a forked version of [awslambdaric](https://github.com/aws/aws-lambda-python-runtime-interface-client) (AWS Lambda Runtime Interface Client). This version is modified to include custom logic for reading the `maintenance-window` parameter from Parameter Store during the Lambda function `Invoke` phase.

5. **Checking the Maintenance Window**
   - The Lambda function checks whether the current datetime falls within the defined maintenance window:
     - If it falls within the window, the Lambda function handler is bypassed. Instead, the Lambda invocation event is stored in Amazon DynamoDB for future manual triggering.
     - If it falls outside the window, the Lambda function operates as usual, executing its handler.

## Architecture Diagram - Low Level

![Architecture Diagram - Low Level](./cdk_aws_lambda_internal_extension/assets/arch-lld.svg)

The way AWS Lambda works under the hood is by using [Firecracker](https://github.com/firecracker-microvm/firecracker), a virtual machine monitor (VMM) designed to rapidly spawn a fleet of microVMs in response to Lambda invocation events. When a new microVM is created, it reads and applies the settings you've configured for your Lambda function to set up the microVM environment accordingly. Additionally, your Lambda function code and any attached layers are copied into designated directories within the microVM.

With this knowledge, it's possible to alter a function's behaviour by configuring it to use a custom version of the Runtime Interface Client (RIC) instead of the official one provided by the AWS Lambda service within the microVM.
