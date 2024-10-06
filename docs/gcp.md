# Google Cloud Platform (GCP)

All of your data is stored in your private cloud project on GCP.
Here is the list of services need be enabled to run Miyoka:

- [BigQuery](https://cloud.google.com/bigquery?hl=en) ... Database to manage your replay records.
- [Cloud Storage](https://cloud.google.com/storage?hl=en) (a.k.a. GCS) ... Object storage to store your replay videos (mp4 format).
- [Cloud Vision](https://cloud.google.com/vision?hl=en) ... OCR for reading texts from an image.
- [Cloud Run](https://cloud.google.com/run?hl=en) ... Serverless service to host your replay viewer.
- [Secret Manager](https://cloud.google.com/security/products/secret-manager?hl=en) ... Managing secrets for letting replay viewer access your data on private cloud.
- [IAM Service Account Credentials API](https://cloud.google.com/iam/docs/reference/credentials/rest) ... Create service account token for generating a signed URL to replays.
- (Optional) [Artifact Registry](https://cloud.google.com/artifact-registry) ... Docker registry to manage images of Replay analyzer and viewer. It's not necessary by default.

You will be charged by Google as you use these services. Miyoka is carefully designed to minimize the running cost.
In general, the monthly cost would be between $5 to $20. Again, Miyoka itself is free and we don't receive any of the payment from you.
