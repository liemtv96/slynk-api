from aws_lambda_handlers import enrich_session_geolocation_handler


def main() -> None:
    result = enrich_session_geolocation_handler({}, None)
    print(
        "processed {processed} sessions, enriched {enriched}, skipped {skipped}, failed {failed}".format(
            processed=result["processed"],
            enriched=result["enriched"],
            skipped=result["skipped"],
            failed=result["failed"],
        )
    )


if __name__ == "__main__":
    main()
