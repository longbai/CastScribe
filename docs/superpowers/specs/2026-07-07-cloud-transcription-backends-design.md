# Cloud Transcription Backends Design

## Goal

Add cloud transcription support to CastScribe without changing the existing download, subtitle, local transcription, and output behavior. The first cloud implementation will fully support Azure Speech, AWS Transcribe, and Google Cloud Speech-to-Text. Tencent Cloud and Alibaba Cloud will have provider stubs, CLI choices, documentation, and explicit runtime errors until their API details are finalized.

## Scope

The feature applies only when CastScribe must transcribe a media file. Subtitle-first behavior remains unchanged: if a source has downloadable subtitles, CastScribe converts those subtitles and does not call a transcription backend.

Supported backends in this phase:

- `local`: current behavior, macOS uses `yap`; other platforms use `faster-whisper`.
- `azure`: Azure Speech SDK conversation transcription from local file, including speaker IDs when available.
- `aws`: AWS Transcribe batch transcription with speaker labels. Requires the audio to be available in S3.
- `google`: Google Cloud Speech-to-Text diarization using Application Default Credentials or normal Google client configuration.
- `tencent`: reserved provider with configuration validation and explicit not-yet-implemented error.
- `aliyun`: reserved provider with configuration validation and explicit not-yet-implemented error.

## CLI

Add these options:

```bash
--backend local|azure|aws|google|tencent|aliyun
--language LANG
--min-speakers N
--max-speakers N
--speaker-count N
--cloud-uri URI
--cloud-output-uri URI
--cloud-region REGION
--poll-interval SECONDS
--timeout SECONDS
```

Defaults:

- `--backend local`
- `--language` defaults to `en-US` for cloud backends and remains optional for local/yap.
- `--min-speakers 2`
- `--max-speakers 10`
- `--speaker-count` maps to fixed speaker count where a provider expects one number.
- `--poll-interval 5`
- `--timeout 3600`

`--cloud-uri` is required for AWS because AWS Transcribe expects an S3 media URI. Local upload automation is intentionally out of scope for the first version, because it requires provider-specific storage permissions and cleanup behavior.

## Architecture

Create a transcription backend abstraction:

```python
@dataclass
class TranscriptionOptions:
    backend: str
    model: str
    output_format: str
    language: str | None
    locale: str | None
    min_speakers: int
    max_speakers: int
    speaker_count: int | None
    cloud_uri: str | None
    cloud_output_uri: str | None
    cloud_region: str | None
    poll_interval: float
    timeout: float
```

All provider modules expose a function compatible with:

```python
def transcribe(media_path: Path, output_path: Path, options: TranscriptionOptions) -> None:
    ...
```

Provider modules:

- `castscribe.transcription.local`: wraps current `yap` and `faster-whisper` logic.
- `castscribe.transcription.azure`: imports `azure.cognitiveservices.speech` lazily.
- `castscribe.transcription.aws`: imports `boto3` lazily and parses returned transcript JSON.
- `castscribe.transcription.google`: imports `google.cloud.speech` lazily.
- `castscribe.transcription.tencent`: raises an explicit implementation error.
- `castscribe.transcription.aliyun`: raises an explicit implementation error.

The existing `pipeline.py` will stop importing `transcribe_media` directly. It will receive `TranscriptionOptions` and call the backend dispatcher. This keeps source downloading independent from transcription provider details.

## Credentials

No credentials are accepted through CLI flags.

Credential sources:

- Azure: `SPEECH_KEY` and `ENDPOINT`, matching Azure Speech SDK examples.
- AWS: normal `boto3` credential chain, plus `--cloud-region`.
- Google: Application Default Credentials.
- Tencent and Alibaba: documented environment variables only, but provider functions will not call APIs yet.

The repository must not contain `.env`, cookie files, tokens, service account JSON files, or downloaded credential exports. `.gitignore` already blocks common private names; this feature will add provider-specific credential patterns if needed.

## Output

Plain text output uses speaker turns when available:

```text
Speaker 1: first utterance
Speaker 2: reply
Speaker 1: next utterance
```

SRT output uses provider timestamps when available. If a provider response has no timestamps, CastScribe writes plain text for `txt` and raises a clear error for `srt` instead of producing misleading timings.

## Error Handling

Missing optional SDKs fail with install hints:

- Azure: `python3 -m pip install 'castscribe[azure]'`
- AWS: `python3 -m pip install 'castscribe[aws]'`
- Google: `python3 -m pip install 'castscribe[google]'`

Provider configuration errors fail before network calls where possible. Examples:

- AWS backend without `--cloud-uri`
- Azure backend without `SPEECH_KEY` or `ENDPOINT`
- invalid speaker count range

CastScribe continues to write `failures.jsonl` and respects `--stop-on-error`.

## Packaging

Add optional dependency groups:

```toml
[project.optional-dependencies]
azure = ["azure-cognitiveservices-speech"]
aws = ["boto3"]
google = ["google-cloud-speech"]
cloud = [
  "azure-cognitiveservices-speech",
  "boto3",
  "google-cloud-speech",
]
whisper = ["faster-whisper"]
```

Cloud SDKs are optional to avoid forcing users of local transcription to install large or credentialed dependencies.

## Tests

Unit tests will mock all cloud SDK imports and clients. No test will call a real cloud API or read real credentials.

Test coverage:

- CLI parses backend and cloud options.
- Pipeline passes transcription options through to the dispatcher.
- Local backend preserves existing `yap` and `faster-whisper` behavior.
- Azure backend requires env vars and writes speaker-labeled transcript from mocked events.
- AWS backend requires S3 URI, starts a mocked job, polls completion, fetches mocked JSON, and writes speaker-labeled text.
- Google backend builds diarization config and writes speaker-labeled text from mocked words.
- Tencent and Alibaba providers raise explicit not-yet-implemented errors.
- `.gitignore` blocks common credential filenames.
