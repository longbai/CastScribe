# Cloud Transcription Backends Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add selectable cloud transcription backends for Azure Speech, AWS Transcribe, and Google Cloud Speech-to-Text while preserving CastScribe's existing local transcription behavior.

**Architecture:** Introduce a `castscribe.transcription` package with a shared `TranscriptionOptions` dataclass and dispatcher. The pipeline will receive options from the CLI and call the dispatcher only when media must be transcribed. Cloud SDKs are optional and imported lazily inside provider modules.

**Tech Stack:** Python 3.10+, unittest mocks, optional `azure-cognitiveservices-speech`, `boto3`, and `google-cloud-speech`.

---

### Task 1: Core Transcription Abstraction

**Files:**
- Create: `src/castscribe/transcription/__init__.py`
- Create: `src/castscribe/transcription/options.py`
- Create: `src/castscribe/transcription/formatting.py`
- Create: `src/castscribe/transcription/local.py`
- Modify: `src/castscribe/transcriber.py`
- Test: `tests/test_transcription_core.py`

- [ ] Add tests for `TranscriptionOptions`, speaker-turn text formatting, SRT formatting, backend validation, and local backend compatibility.
- [ ] Move the current local/yap/faster-whisper implementation into `transcription/local.py`.
- [ ] Keep `src/castscribe/transcriber.py` as a compatibility wrapper exporting the old constants and functions.

### Task 2: CLI and Pipeline Integration

**Files:**
- Modify: `src/castscribe/cli.py`
- Modify: `src/castscribe/pipeline.py`
- Modify: `tests/test_media_to_text.py`
- Test: `tests/test_cli_entrypoint.py`

- [ ] Add CLI arguments: `--backend`, `--language`, `--min-speakers`, `--max-speakers`, `--speaker-count`, `--cloud-uri`, `--cloud-output-uri`, `--cloud-region`, `--poll-interval`, and `--timeout`.
- [ ] Build `TranscriptionOptions` in the CLI and pass it through `process_source` and `process_local_source`.
- [ ] Preserve existing positional URL, subtitle-first, and output behavior.

### Task 3: Azure Backend

**Files:**
- Create: `src/castscribe/transcription/azure.py`
- Test: `tests/test_cloud_backends.py`

- [ ] Add tests that missing `SPEECH_KEY` or `ENDPOINT` raises a clear error.
- [ ] Add tests that mocked Azure conversation events write speaker-labeled text.
- [ ] Implement lazy import of `azure.cognitiveservices.speech`, environment-variable validation, event collection, and txt output.
- [ ] For SRT output, raise a clear error until reliable timestamps are available from provider events.

### Task 4: AWS Backend

**Files:**
- Create: `src/castscribe/transcription/aws.py`
- Test: `tests/test_cloud_backends.py`

- [ ] Add tests that `--cloud-uri` is required.
- [ ] Add tests for mocked `start_transcription_job`, polling, transcript JSON retrieval, speaker-label parsing, and txt output.
- [ ] Implement lazy import of `boto3`, job creation, polling with timeout, transcript JSON fetch through `urllib.request`, and speaker-turn formatting.
- [ ] Support `--cloud-output-uri` as an S3 output bucket/key hint where AWS accepts it.

### Task 5: Google Backend

**Files:**
- Create: `src/castscribe/transcription/google.py`
- Test: `tests/test_cloud_backends.py`

- [ ] Add tests that mocked Google client receives diarization config with min/max speakers.
- [ ] Add tests that mocked word speaker labels write speaker-labeled text.
- [ ] Implement lazy import of `google.cloud.speech`, local-file content recognition, diarization config, and txt output.
- [ ] For SRT output, raise a clear error unless segment timings are available.

### Task 6: Tencent and Alibaba Provider Stubs

**Files:**
- Create: `src/castscribe/transcription/tencent.py`
- Create: `src/castscribe/transcription/aliyun.py`
- Test: `tests/test_cloud_backends.py`

- [ ] Add tests that both providers are selectable and raise explicit not-yet-implemented errors.
- [ ] Document expected environment variable names in provider error messages and README.

### Task 7: Packaging, Docs, and Privacy Rules

**Files:**
- Modify: `pyproject.toml`
- Modify: `README.md`
- Modify: `.gitignore`
- Test: `tests/test_privacy_ignore.py`

- [ ] Add optional dependency groups for `azure`, `aws`, `google`, and `cloud`.
- [ ] Document cloud backend commands and credential sources without real secrets.
- [ ] Add provider credential file patterns to `.gitignore`.
- [ ] Add a test that important credential patterns are present in `.gitignore`.

### Task 8: Verification and Push

**Files:**
- All changed project files.

- [ ] Run `python3 -m unittest discover -s tests`.
- [ ] Run `PYTHONPATH=src python3 -m py_compile media_to_text.py src/castscribe/*.py src/castscribe/transcription/*.py tests/*.py`.
- [ ] Run `PYTHONPATH=src python3 -m castscribe --help`.
- [ ] Commit and push to `origin/main`.
