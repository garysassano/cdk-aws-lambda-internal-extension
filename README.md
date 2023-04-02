# cdk-aws-lambda-internal-extension

CDK app that deploys a Lambda internal extension to modify the standard behaviour of AWS Lambda.

## Prerequisites

For this project you need an AWS account with the [CDK bootstrapping](https://docs.aws.amazon.com/cdk/v2/guide/bootstrapping.html) process completed. You also need Docker to be installed on your system since the Lambda layer gets built inside a container.

## Installation

Install CDK:

```sh
npm install -g aws-cdk
```

Install Poetry + dotenv plugin:

```sh
curl -sSL https://install.python-poetry.org | python3 -
poetry self add poetry-plugin-dotenv
```

Configure Poetry to create the virtualenv inside the project's root directory:

```sh
poetry config virtualenvs.in-project true
```

Create the virtualenv and install all the dependencies inside it:

```sh
poetry install
```

## Configuration

In order to deploy to AWS, you need to [set AWS CLI environment variables](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-envvars.html#envvars-set).

To do that, rename `.env.example` to `.env` and add your variables like in the following example:

```dotenv
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_DEFAULT_REGION=eu-west-1
```

## Deployment

Synthesize the CloudFormation stack and deploy it:

```sh
cdk deploy
```

## Cleanup

Destroy the CloudFormation stack:

```sh
cdk destroy
```

## Architecture Diagram - High Level

![lambda-internal-extension-arch-high](./assets/lambda-internal-extension-arch-high.svg)

A Lambda layer containing our internal extension gets created and attached to a Lambda function. This Lambda function is configured to call the wrapper script inside the Lambda layer as soon as it starts, which in turn calls a forked [awslambdaric](https://github.com/aws/aws-lambda-python-runtime-interface-client) (Lambda Runtime API) that was modified so that it reads a parameter from SSM Parameter Store during the Lambda bootstrap process. If the current datetime falls inside the maintenance window defined by the parameter, the Lambda function handler doesn't get executed; instead, the Lambda invocation event gets stored in DynamoDB so that it can be triggered manually at a later time. Outside the defined maintenance window, the Lambda function keeps working normally.

## Architecture Diagram - Low Level

![lambda-internal-extension-arch-low](./assets/lambda-internal-extension-arch-low.svg)

The way AWS Lambda works under the hood is by using [Firecracker](https://github.com/firecracker-microvm/firecracker), a virtual machine monitor (VMM) that is able to spawn a fleet of microVMs as Lambda invocation events come in. When a new microVM gets created, all the parameters you set in your AWS Lambda are read and used to apply the wanted configuration to the microVM environment. In addition, your Lambda function and any Lambda layer you attached to it get copied into specific directories of the microVM. With this knowledge, you can modify the behaviour of AWS Lambda by configuring it to use a custom version of the Lambda Runtime API instead of the official one provided by AWS inside the microVM.
