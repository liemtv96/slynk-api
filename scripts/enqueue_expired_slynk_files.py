from aws_lambda_handlers import enqueue_expired_sessions_handler


def main() -> None:
    result = enqueue_expired_sessions_handler({}, None)
    print(f"enqueued {result['enqueued']} expired community files")


if __name__ == "__main__":
    main()
