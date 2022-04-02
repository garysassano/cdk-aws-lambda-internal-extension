from projen.awscdk import AwsCdkPythonApp

project = AwsCdkPythonApp(
    author_email="10464497+garysassano@users.noreply.github.com",
    author_name="Gary Sassano",
    cdk_version="2.162.1",
    module_name="cdk_aws_lambda_internal_extension",
    name="cdk-aws-lambda-internal-extension",
    poetry=True,
    version="0.1.0",
    ###
    deps=["aws-cdk.aws-lambda-python-alpha@^2.162.1a0"],
)

# Set Poetry local configuration for this project
poetry_toml = project.try_find_file("poetry.toml")
poetry_toml.add_override("virtualenvs.create", "true")
poetry_toml.add_override("virtualenvs.in-project", "true")

project.synth()
