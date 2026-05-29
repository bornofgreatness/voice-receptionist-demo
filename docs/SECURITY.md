# Security & HIPAA-oriented design (demo only)

**This repository is a technical demo. It is not HIPAA compliant and does not process real PHI.**

## Demo boundaries

- Fictional practices and synthetic caller data only
- Phone numbers stored redacted (last four digits masked in DB)
- No BAAs, no production AWS BAA account configuration in this repo

## Production-oriented patterns (target architecture)

| Safeguard | Planned implementation |
|-----------|-------------------------|
| PHI detection | AWS Comprehend Medical + custom regex pre-filters before LLM |
| Encryption | TLS 1.2+ in transit; S3/KMS at rest |
| Access control | RBAC per practice tenant; least-privilege IAM |
| Audit | `audit_events` table + immutable log shipping (7-year retention policy) |
| Kill switch | Feature flag to disable agent + transfer all calls to human line |
| Tenant isolation | `practice_id` on all rows; separate config bundles per specialty |

## Logging

- Do not log full transcripts with identifiers in production
- Hash or truncate phone numbers in metrics pipelines
