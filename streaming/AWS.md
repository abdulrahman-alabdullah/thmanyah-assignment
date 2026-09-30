# MediaLive provisioning and archive verification

Assessment acceptance status (30 September 2026): AWS accepted creation of the SRT listener input and single-pipeline HEVC/archive channel configuration. The channel remained IDLE and was deleted without being started, so live ingest, MediaLive output, and a real S3 archive were not verified. The temporary input, channel, secret, role, buckets, and stack have been removed. This guide is the procedure for a future live check; it creates billable resources.

1. Choose a supported region and an S3 archive bucket with public access blocked and default encryption. Terraform's `media_buckets.archive` output provides a suitable bucket after deployment. The bucket name must contain no dots.
2. Create a Secrets Manager secret containing the SRT passphrase as a plaintext secret value, not a JSON key/value object, as required by MediaLive's SRT integration. Secrets Manager still encrypts the stored value. Use a 10-79 character high-entropy value and keep it out of screenshots, Git and shell history. Record the ARN, not the secret value, in configuration.
3. Create an IAM role trusted by `medialive.amazonaws.com` using `trust-policy.json`. Adapt `iam-policy.example.json` for the exact bucket prefix and secret ARN and attach it to the role. If using a customer-managed KMS key, add the relevant key policy and decrypt/encrypt permissions. The deployment identity also needs MediaLive administration permissions and `iam:PassRole` on this role.
4. Create an input security group permitting only the OBS sender's current public `/32` address. For example, with a configured AWS CLI:

```sh
aws medialive create-input-security-group \
  --whitelist-rules Cidr=YOUR_PUBLIC_IP/32
```

5. Run the request generator with the real role ARN, secret ARN, bucket name and input security group ID. Its default `/evidence` output can be overridden with `--output ./streaming/config` when running outside the provided container. The checked example JSON files under `docs/evidence/` contain placeholders and cannot deploy as-is.

```sh
aws medialive create-input --cli-input-json file://input.json
```

6. Save the returned input ID and SRT listener endpoint. Re-run the generator with `--input-id ACTUAL_ID` to create a channel request referencing the real input. Create the channel:

```sh
aws medialive create-channel --cli-input-json file://channel.json
aws medialive start-channel --channel-id CHANNEL_ID
aws medialive describe-channel --channel-id CHANNEL_ID
```

The channel is configured for one pipeline, HEVC HD input up to 20 Mbps, 1920×1080 at 25 fps, 12 Mbps HEVC output, AAC 192 kbps, and an Archive group rolling MPEG-TS objects to S3 every 60 seconds. SINGLE_PIPELINE limits the assessment cost but does not provide redundant pipelines.

7. Follow `OBS.md` to send an encrypted SRT MPEG-TS stream. The channel must reach RUNNING. Inspect MediaLive alerts and CloudWatch input/output metrics. Confirm video is moving, audio is present and timestamps are continuous.
8. After at least two rollover intervals, list the archive prefix:

```sh
aws s3 ls s3://BUCKET/recordings/ --recursive
aws s3 cp s3://BUCKET/recordings/ACTUAL_OBJECT.ts archive-check.ts
ffprobe -v error -show_streams -show_format -of json archive-check.ts
```

9. Verify that the file came from MediaLive's archive output and contains HEVC Full HD with AAC audio. Measure elementary-stream bitrates separately from the container bitrate. Store actual evidence before marking the broadcast task complete.
10. Stop the channel and wait for IDLE. Delete the channel, detach/delete its input, and remove an unused input security group. Retain submitted evidence for the review period. Review AWS billing and remove other unused resources.

```sh
aws medialive stop-channel --channel-id CHANNEL_ID
aws medialive delete-channel --channel-id CHANNEL_ID
aws medialive delete-input --input-id INPUT_ID
```

The request schema check catches parameter names and required fields. The service accepted the test channel configuration, but that does not prove ingest, encoder compatibility, successful output, or archive delivery. Do not claim the broadcast requirement as complete until an actual archived object has been inspected.

Sources: [SRT listener setup](https://docs.aws.amazon.com/medialive/latest/ug/input-listener-srt-setup.html), [CLI create-input](https://docs.aws.amazon.com/cli/latest/reference/medialive/create-input.html), [MediaLive archive output](https://docs.aws.amazon.com/medialive/latest/ug/outputs-supported-containers-downstream-systems.html).
