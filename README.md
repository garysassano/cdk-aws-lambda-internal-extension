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

A Lambda layer containing our internal extension gets created and attached to a Lambda function. This Lambda function is configured to call the wrapper script inside the Lambda layer as soon as it starts, which in turn calls a forked [awslambdaric](https://github.com/aws/aws-lambda-python-runtime-interface-client) (Lambda Runtime API) that was modified so that it reads a parameter from SSM Parameter Store during the Lambda bootstrap process. If the current datetime falls inside the maintenance window defined by the parameter, the Lambda function handler doesn't get executed; instead, the Lambda invocation event gets stored in DynamoDB so that it can be triggered manually at a later time. Outside the defined maintenance window, the Lambda function keeps working normally.

## Architecture Diagram - Low Level

![Architecture Diagram - Low Level](./cdk_aws_lambda_internal_extension/assets/arch-lld.svg)

The way AWS Lambda works under the hood is by using [Firecracker](https://github.com/firecracker-microvm/firecracker), a virtual machine monitor (VMM) that is able to spawn a fleet of microVMs as Lambda invocation events come in. When a new microVM gets created, all the parameters you set in your AWS Lambda are read and used to apply the wanted configuration to the microVM environment. In addition, your Lambda function and any Lambda layer you attached to it get copied into specific directories of the microVM. With this knowledge, you can modify the behaviour of AWS Lambda by configuring it to use a custom version of the Lambda Runtime API instead of the official one provided by AWS inside the microVM.
