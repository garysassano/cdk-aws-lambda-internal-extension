import datetime


def lambda_handler(event, context):
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return {
        "statusCode": 200,
        "body": current_time,
    }
