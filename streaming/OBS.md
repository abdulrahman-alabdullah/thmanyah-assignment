# OBS to AWS Elemental MediaLive

Assessment acceptance status (30 September 2026): OBS was installed temporarily on Apple Silicon and the installed build exposed a VideoToolbox HEVC encoder. A local test clip and profile were prepared, but OBS output was not verified and no stream was sent to MediaLive. The local OBS application has since been removed. No live failure was captured, so there is no evidence that isolates OBS, SRT, MediaLive, or S3 as the cause. A live broadcast and S3 archive are still open acceptance checks.

1. Install OBS Studio from the [official download page](https://obsproject.com/download) on macOS. Add a screen capture, camera or a moving test clip and an audio source. macOS may require screen-recording permission.
2. In Video, set canvas and output resolution to 1920 × 1080 and FPS to 25.
3. Set Advanced Output. Select an HEVC encoder that the installed macOS OBS build exposes, preferably Apple VideoToolbox HEVC. Set video bitrate to 12000 kbps, keyframe interval to 2 seconds, AAC audio to 192 kbps, stereo at 48 kHz.
4. Set Stream service to Custom. Use the allocated MediaLive SRT listener endpoint on port 5050, for example `srt://HOST:5050?mode=caller&latency=1000000&pbkeylen=32&passphrase=YOUR_PASSPHRASE`. Stream key stays empty. This URL contains a secret; do not include it in screenshots or logs.
5. If HEVC is unavailable for normal streaming in this OBS build, use Advanced Output → Recording → Custom Output (FFmpeg), output to URL, MPEG-TS, HEVC video, 12000 kbps, AAC 192 kbps. This path is triggered by Start Recording, despite targeting a network URL. Confirm the actual codec before calling the task complete. If the installed build exposes neither usable HEVC path, install a compatible encoder/build; an H.264 stream does not meet the assessment.
6. Start MediaLive first and wait for RUNNING, then start OBS output. Confirm incoming video/audio, no sustained input loss, and a steady bitrate in the channel metrics.
7. After several archive rollover intervals, list S3 objects in `recordings/`. Download a `.ts` object and run `ffprobe -show_streams -show_format -of json FILE.ts`. Verify HEVC, 1920 × 1080, 25 fps and AAC. Use packet byte counts over timestamps to measure each elementary stream's actual average bitrate; container bitrate includes audio and TS overhead.
8. Save redacted OBS settings, channel state, CloudWatch metrics and ffprobe output as evidence. Stop the channel after the test and delete unused input/channel resources. Keep the report and code accessible for the review period.

At 25 fps, `BPP = 12,000,000 / (1920 × 1080 × 25) = 0.23148 bits per pixel per frame`.
This is a normalization metric, not a perceptual quality guarantee. Motion, encoder efficiency, GOP, noise and chroma matter too. Keep the required 12 Mbps floor.

Video plus audio is 12.192 Mbps before TS and SRT overhead. Allow at least 20 Mbps stable upstream headroom. Nominal archive growth is about 5.49 GB/hour before container overhead. Regional availability, pricing, account quotas and the installed OBS encoder must be confirmed before deployment.

Sources: [OBS SRT guide](https://obsproject.com/kb/srt-protocol-streaming-guide), [MediaLive input codecs](https://docs.aws.amazon.com/medialive/latest/ug/inputs-supported-codecs-by-input-type.html), [SRT listener setup](https://docs.aws.amazon.com/medialive/latest/ug/input-listener-srt-setup.html), [Archive codecs](https://docs.aws.amazon.com/medialive/latest/ug/outputs-supported-codecs.html).
