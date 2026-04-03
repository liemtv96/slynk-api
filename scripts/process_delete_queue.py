from core.sqs import get_sqs_client
from aws_lambda_handlers import process_delete_queue_handler
from core.config import settings


def main() -> None:
    if not settings.SQS_DELETE_QUEUE_URL:
        raise RuntimeError("SLYNK_SQS_DELETE_QUEUE_URL is required")

    sqs = get_sqs_client()
    response = sqs.receive_message(
        QueueUrl=settings.SQS_DELETE_QUEUE_URL,
        MaxNumberOfMessages=10,
        WaitTimeSeconds=10,
    )
    messages = response.get("Messages", [])
    event = {
        "Records": [
            {
                "body": message["Body"],
            }
            for message in messages
        ]
    }
    result = process_delete_queue_handler(event, None)

    for message in messages:
        sqs.delete_message(
            QueueUrl=settings.SQS_DELETE_QUEUE_URL,
            ReceiptHandle=message["ReceiptHandle"],
        )

    print(f"processed {result['processed']} delete jobs")


if __name__ == "__main__":
    main()
