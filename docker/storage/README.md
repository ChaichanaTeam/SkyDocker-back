# Storage - SeaweedFS (S3 API)

Object storage for pilot documents and the wiki. Clients never get storage credentials:
documents are uploaded through the backend, downloads go through short-lived presigned URLs.

- `storage` - SeaweedFS all-in-one (master, volume, filer, S3 gateway). Only the S3 port `8333` is meant to be reachable from outside
- `storage-init` - one-shot job: creates buckets, enables default encryption and TTL. Safe to rerun

## Buckets and key tree

```
verification/                                   private, SSE-S3, objects expire after 30 days
  requests/{request_id}/{document_type}/{uuid}.{ext}
organizer/                                      private, SSE-S3, no expiration
  pilots/{pilot_id}/{uuid}.{ext}
wiki/                                           public read
  (layout is defined by the wiki ticket)
```

- `verification` - documents of a `verification_request`, visible only to the moderator who reviews it.
  `{document_type}` matches `verification_document_type` enum (`privilege_a1` ... `privilege_sts02`, `operator_number`).
  Rejected and withdrawn requests delete their documents explicitly, approved ones keep them until the pilot decides. TTL is a safety net
- `organizer` - pilot's personal documents, visible only to the pilot.
  After approval the pilot may keep verification documents: server-side copy from `verification/` to `organizer/`, then delete the original
- Object names are random UUIDs. Original file names live only in the database, keys contain no personal data
- `verification_document.document_path` stores the key without the bucket name

## Access model

| Identity    | Rights                                                    | Used by        |
|-------------|-----------------------------------------------------------|----------------|
| `admin`     | `Admin` on everything                                     | `storage-init` |
| `app`       | `Read`, `Write`, `List`, `Tagging` on the three buckets   | backend        |
| `anonymous` | `Read:wiki`                                               | everyone       |

`app` cannot create or delete buckets, nor change their encryption. Private buckets are never readable anonymously.
Which prefix a user may touch (`requests/{id}` for the assigned moderator, `pilots/{own id}` for the pilot) is decided by the backend before signing a URL.

## Uploads and downloads

- Uploads are multipart requests to the backend (`backend_src/storage/files.py`): up to 10 MB, PDF, JPEG or PNG detected by file signature, not by name or `Content-Type`
- Downloads are presigned GET URLs with lifetime up to 5 minutes
- URLs are signed for `STORAGE_PUBLIC_URL`, the backend itself talks to `STORAGE_URL`

## Secrets

Set in `.env`, see `.env.example`:

- `STORAGE_ADMIN_KEY` / `STORAGE_ADMIN_SECRET`, `STORAGE_APP_KEY` / `STORAGE_APP_SECRET` - S3 credentials, rendered into `s3.json` at start (`chmod 600`, never committed)
- `STORAGE_SSE_KEY` - master key for SSE-S3. **Losing or changing it makes encrypted objects unreadable**
- `STORAGE_FILER_JWT_KEY` - protects the filer IAM API. Without it anyone reaching the filer port can create users

## Production notes

- Put a reverse proxy with TLS in front of `8333`, SeaweedFS S3 serves plain HTTP here
- Do not publish master (`9333`), volume (`8080`) and filer (`8888`) ports
- Back up the `storage_data` volume together with `STORAGE_SSE_KEY`
