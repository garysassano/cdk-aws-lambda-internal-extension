import json
from datetime import (
    datetime,
    timezone,
)
import boto3


def pre_handler_function(event_request):
    try:
        # Get current datetime
        current_datetime = datetime.now(timezone.utc)

        # Set up Boto3 client for SSM Parameter Store
        ssm = boto3.client("ssm")

        # Retrieve `maintenance-window` parameter
        response = ssm.get_parameter(Name="maintenance-window")

        # Convert Parameter Store StringList to Python list
        string_list = response["Parameter"]["Value"].split(",")

        # Extract maintenance window dates
        maint_date_start_str = string_list[0]
        maint_date_end_str = string_list[1]

        # Convert maintenance window dates to datetime objects
        maint_date_start = datetime.strptime(maint_date_start_str, "%Y-%m-%dT%H:%M:%S%z")
        maint_date_end = datetime.strptime(maint_date_end_str, "%Y-%m-%dT%H:%M:%S%z")

        # Check if maintenance window is active
        if maint_date_start <= current_datetime <= maint_date_end:
            print("WARNING: Maintenance Window ON")

            # Store lambda invocation event to DynamoDB
            req_timestamp = current_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")
            req_event_body = json.loads(event_request.event_body)
            req_invoke_id = event_request.invoke_id
            req_invoked_function_arn = event_request.invoked_function_arn

            dynamodb_record = dict()
            dynamodb_record.update({"timestamp": req_timestamp})
            dynamodb_record.update({"event_body": req_event_body})
            dynamodb_record.update({"invoke_id": req_invoke_id})
            dynamodb_record.update({"invoked_function_arn": req_invoked_function_arn})

            dynamodb = boto3.resource("dynamodb")
            table = dynamodb.Table("maintenance-window-events-table")
            table.put_item(Item=dynamodb_record)

            # Send warning to the user
            raise UserWarning(
                "Lambda invocation disabled during maintenance window. The event was stored to DynamoDB. "
                f"Current maintenance window set FROM {maint_date_start_str} TO {maint_date_end_str}"
            )

    except ValueError:
        print(
            "Parameter `maintenance-window` is in the wrong format. Please amend it in SSM Parameter Store."
        )
