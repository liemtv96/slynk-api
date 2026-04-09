# Slynk Lite | File Upload Sharing API

Minimal serverless backend for temporary file sharing with direct browser uploads to S3

## Demo

You can try a live demo here: [slynk.rilab.space](https://slynk.rilab.space)

## License

This project is licensed under Apache 2.0. See [LICENSE](LICENSE).

Forks and independent development are welcome. If you build on top of this
project, please keep a small acknowledgement to the original project and me (author)
where practical. See [NOTICE](NOTICE)
and [TRADEMARKS.md](TRADEMARKS.md).

## Support The Project

If this project helps you, saves you time, or gives you a useful starting point,
you can support its continued maintenance and development here:

- PayPal: [paypal.me/rintran137](https://www.paypal.me/rintran137)
- Ko-fi: [ko-fi.com/rintran](https://ko-fi.com/rintran)

Support is never required, but it is genuinely appreciated

## Project Layout

```text
app/
  application.py               # FastAPI app factory + route registration
  config.py                    # Environment-backed settings
  api/
    routes/slynk.py            # HTTP endpoints (thin layer)
    schemas/slynk.py           # Request/response models
  storage/s3.py                # S3 helper functions
  aws/
    dynamo.py                  # Dynamo client/resource access
    sqs.py                     # SQS client + enqueue helper
  repositories/
    slynk_sessions.py          # DynamoDB session reads/writes
    slynk_statistics.py        # Aggregate counters and analytics snapshots
  services/
    slynk_sharing.py           # Main sharing business logic
    ip_geolocation.py          # GeoIP enrichment service
  jobs/slynk_cleanup.py        # Expiry scan and delete queue handlers

main.py                        # Backward-compatible app entrypoint
lambda_http.py                 # Mangum adapter for Lambda/API Gateway
aws_lambda_handlers.py         # Backward-compatible lambda exports
scripts/
  enqueue_expired_slynk_files.py   # Local expiry scan runner
  process_delete_queue.py          # Local SQS delete worker runner
  enrich_session_geolocation.py    # Local geo enrichment runner
ipdb/                          # Local MaxMind GeoIP databases
template.yaml                  # AWS SAM template
cloudformation.yaml            # Plain CloudFormation template
tests/                         # Unit tests
```

The top-level `core/`, `routers/`, `schemas/`, and `storage/` modules remain as compatibility wrappers. New code should live under `app/`.

## Runtime Flow

1. `POST /lite/sessions` creates a pending upload session and presigned S3 upload URLs.
2. Browser uploads files directly to S3.
3. `POST /lite/sessions/{token}/complete` marks the session `active` and returns the share URL.
4. `GET /lite/shares/{token}` returns public share metadata.
5. `GET /lite/shares/{token}/files/{file_id}/download` returns a presigned S3 download URL.
6. Background job scans for expired active sessions and enqueues delete jobs.
7. Queue consumer deletes S3 objects and removes DynamoDB records.

## AWS Shape

- API Gateway or ALB -> FastAPI app
- S3 for object storage
- DynamoDB for session metadata
- SQS for deletion jobs
- EventBridge schedule for expiry scans
- Lambda or worker for queue processing

## Lambda Handlers

Handlers are exported from [aws_lambda_handlers.py](aws_lambda_handlers.py):

- `enqueue_expired_sessions_handler`
- `process_delete_queue_handler`

## Required Environment

- `SLYNK_CORS_ORIGINS`
- `SLYNK_S3_BUCKET`
- `SLYNK_S3_PREFIX`
- `SLYNK_S3_ENDPOINT_URL`
- `SLYNK_DYNAMO_COMMUNITY_TABLE`
- `SLYNK_SQS_DELETE_QUEUE_URL`
- `SLYNK_DEFAULT_FILE_TTL_HOURS=8`
- `SLYNK_PENDING_SESSION_STALE_HOURS=24`
- `SLYNK_MAX_UPLOAD_BYTES=3221225472`
- `SLYNK_DAILY_IP_CREATE_LIMIT=5`
- `SLYNK_PUBLIC_BASE_URL`
- `SLYNK_GEO_ENRICH_ENABLED=true`
- `SLYNK_GEO_ENRICH_BATCH_SIZE=25`
- `SLYNK_DYNAMO_STATISTICS_TABLE`
- `SLYNK_ANALYTICS_API_KEY`
- `SLYNK_CLOUDFRONT_ORIGIN_SECRET`
- `SLYNK_PRIVATE_BEARER_TOKEN`

## IP Daily Limit

- Session creation (`POST /lite/sessions`) is limited per client IP.
- Default limit is `5` session creates per IP per UTC day.
- Configure with `SLYNK_DAILY_IP_CREATE_LIMIT`.
- Client IP is resolved from `X-Forwarded-For` (first value), then `X-Real-IP`, then direct socket IP.

## Session Analytics

- Each created session stores request analytics in DynamoDB for dashboarding.
- Aggregate counters now live in a dedicated statistics table so totals survive session cleanup.
- Expired `active` sessions are cleaned up on the normal expiry schedule; `pending` sessions are only deleted after they remain unchanged past `SLYNK_PENDING_SESSION_STALE_HOURS`.
- Geolocation enrichment is designed for a local MaxMind GeoIP database rather than a remote IP API.
- Captured fields include `client_ip`, `ip_source`, `forwarded_for`, `real_ip`, `user_agent`, `referer`, `origin`, `request_id`, and `created_date`.
- Device-oriented fields are inferred from request headers: `browser`, `os`, `device_type`, `client_type`, `platform_hint`, and `mobile_hint`.
- These values are heuristics for dashboards. Browser headers can usually distinguish desktop vs mobile web and OS family, but not the exact physical machine model with high confidence.
- The daily IP quota still uses the resolved `client_ip` and remains separate from the session record.
- `GET /lite/analytics/overview` returns public-safe dashboard data with counts and recent session analytics, excluding raw IP/header fields from the response payload.
- If `SLYNK_ANALYTICS_API_KEY` is set, all API endpoints require the `X-API-Key` header.
- If `SLYNK_CLOUDFRONT_ORIGIN_SECRET` is set, `/lite` requests must arrive through CloudFront with the injected `X-Slynk-Origin-Secret` header. Direct API Gateway access is rejected with `403`.

## Geo Enrichment

- IP addresses are stored internally in DynamoDB and are not returned by the public analytics endpoint.
- A scheduled background job enriches stored sessions with `country`, `region`, `city`, `latitude`, and `longitude`.
- The local entrypoint is [enrich_session_geolocation.py](scripts/enrich_session_geolocation.py).
- Non-public IPs such as `127.0.0.1` or RFC1918 addresses are skipped and marked internally so they are not retried forever.
- The default provider configuration targets `https://ipapi.co/<ip>/json/`. Review provider limits before using this in production.

## Run Locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### PyCharm Run Configuration

- Run type: `Python`
- Module name: `uvicorn`
- Parameters: `main:app --reload --host 0.0.0.0 --port 8000`
- Working directory: project root
- Environment variables: load from `.env`

## Docker Compose

Files included:
- [Dockerfile](Dockerfile)
- [docker-compose.yml](docker-compose.yml)

Run:

```bash
docker compose up --build -d
docker compose logs -f api
```

Stop:

```bash
docker compose down
```

## AWS Lambda (SAM)

This repo now includes:
- [template.yaml](template.yaml) with:
  - `ApiFunction` (FastAPI via `lambda_http.handler`)
  - `EnqueueExpiredSessionsFunction` (scheduled scan)
  - `ProcessDeleteQueueFunction` (SQS consumer)
  - Managed `S3`, `DynamoDB`, `SQS`, and `HttpApi` resources
- [lambda_http.py](lambda_http.py) (`Mangum` adapter)

Build and deploy:

```bash
sam build
sam deploy --guided
```

Recommended guided answers:
- Stack name: `slynk-lite-api`
- Region: your AWS region
- Confirm changes before deploy: `Yes`
- Allow SAM CLI IAM role creation: `Yes`
- Save arguments to configuration file: `Yes`

After deploy:
- Read the `ApiCloudFrontUrl` output from CloudFormation stack outputs and use it as the frontend API base URL.
- Set `SLYNK_PUBLIC_BASE_URL` parameter to your frontend base URL for share links.

## AWS Lambda (Plain CloudFormation)

Template:
- [cloudformation.yaml](cloudformation.yaml)

This template is non-SAM and expects a prebuilt Lambda zip uploaded to S3.

1. Build deployment zip (example):

```bash
rm -rf build
mkdir -p build
pip install -r requirements.txt -t build
cp -r app core routers schemas storage scripts ipdb *.py build/
cd build && zip -r ../deployment.zip . && cd ..
```

2. Upload zip to S3:

```bash
aws s3 cp deployment.zip s3://<artifact-bucket>/<artifact-key>.zip
```

3. Deploy stack:

```bash
aws cloudformation deploy \
  --template-file cloudformation.yaml \
  --stack-name slynk-api-cfn \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    LambdaCodeS3Bucket=<artifact-bucket> \
    LambdaCodeS3Key=<artifact-key>.zip \
    CloudFrontOriginSecret=<long-random-secret> \
    Environment=prod
```

Use the `ApiCloudFrontUrl` stack output in the frontend. The raw `ApiUrl` is the direct API Gateway origin and should not be the browser-facing base URL once origin protection is enabled.

## Tests

```bash
pytest
```
