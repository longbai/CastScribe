import json
import os
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from castscribe.transcription.options import TranscriptionOptions


class CloudBackendTests(unittest.TestCase):
    def test_azure_requires_speech_environment(self):
        from castscribe.transcription import azure

        with (
            mock.patch.dict(os.environ, {}, clear=True),
            self.assertRaisesRegex(RuntimeError, "SPEECH_KEY"),
        ):
            azure.transcribe(Path("a.wav"), Path("a.txt"), TranscriptionOptions(backend="azure"))

    def test_azure_writes_speaker_labeled_text_from_mocked_events(self):
        from castscribe.transcription import azure

        with TemporaryDirectory() as tmp:
            output = Path(tmp) / "out.txt"
            fake_sdk = build_fake_azure_sdk(
                [
                    SimpleNamespace(
                        result=SimpleNamespace(
                            reason="recognized",
                            text="Hello there.",
                            speaker_id="Guest-1",
                        )
                    ),
                    SimpleNamespace(
                        result=SimpleNamespace(
                            reason="recognized",
                            text="Reply.",
                            speaker_id="Guest-2",
                        )
                    ),
                ]
            )

            with (
                mock.patch.dict(os.environ, {"SPEECH_KEY": "x", "ENDPOINT": "https://example.test"}),
                mock.patch.object(azure, "import_azure_speech", return_value=fake_sdk),
            ):
                azure.transcribe(Path("a.wav"), output, TranscriptionOptions(backend="azure"))

            self.assertEqual(output.read_text(encoding="utf-8"), "Speaker Guest-1: Hello there.\nSpeaker Guest-2: Reply.\n")

    def test_aws_requires_cloud_uri(self):
        from castscribe.transcription import aws

        with self.assertRaisesRegex(RuntimeError, "--cloud-uri"):
            aws.transcribe(Path("a.mp3"), Path("a.txt"), TranscriptionOptions(backend="aws"))

    def test_aws_polls_and_writes_speaker_labeled_text(self):
        from castscribe.transcription import aws

        transcript = {
            "results": {
                "items": [
                    {"start_time": "0.0", "end_time": "0.4", "type": "pronunciation", "alternatives": [{"content": "hello"}]},
                    {"type": "punctuation", "alternatives": [{"content": "."}]},
                    {"start_time": "0.5", "end_time": "0.8", "type": "pronunciation", "alternatives": [{"content": "reply"}]},
                ],
                "speaker_labels": {
                    "segments": [
                        {"speaker_label": "spk_0", "start_time": "0.0", "end_time": "0.4", "items": [{"start_time": "0.0"}]},
                        {"speaker_label": "spk_1", "start_time": "0.5", "end_time": "0.8", "items": [{"start_time": "0.5"}]},
                    ]
                },
            }
        }
        client = mock.Mock()
        client.start_transcription_job.return_value = None
        client.get_transcription_job.return_value = {
            "TranscriptionJob": {
                "TranscriptionJobStatus": "COMPLETED",
                "Transcript": {"TranscriptFileUri": "https://example.test/transcript.json"},
            }
        }
        fake_boto3 = mock.Mock(client=mock.Mock(return_value=client))

        with TemporaryDirectory() as tmp:
            output = Path(tmp) / "out.txt"
            with (
                mock.patch.object(aws, "import_boto3", return_value=fake_boto3),
                mock.patch.object(aws, "read_json_url", return_value=transcript),
            ):
                aws.transcribe(
                    Path("a.mp3"),
                    output,
                    TranscriptionOptions(
                        backend="aws",
                        cloud_uri="s3://bucket/audio.mp3",
                        cloud_region="us-west-2",
                        poll_interval=0.01,
                    ),
                )

            text = output.read_text(encoding="utf-8")

        self.assertIn("Speaker spk_0: hello.", text)
        self.assertIn("Speaker spk_1: reply", text)
        client.start_transcription_job.assert_called_once()

    def test_google_writes_speaker_labeled_text_from_mocked_words(self):
        from castscribe.transcription import google

        words = [
            SimpleNamespace(word="hello", speaker_label="1", start_offset=SimpleNamespace(total_seconds=lambda: 0.0), end_offset=SimpleNamespace(total_seconds=lambda: 0.4)),
            SimpleNamespace(word="again", speaker_label="1", start_offset=SimpleNamespace(total_seconds=lambda: 0.5), end_offset=SimpleNamespace(total_seconds=lambda: 0.8)),
            SimpleNamespace(word="reply", speaker_label="2", start_offset=SimpleNamespace(total_seconds=lambda: 1.0), end_offset=SimpleNamespace(total_seconds=lambda: 1.4)),
        ]
        response = SimpleNamespace(results=[SimpleNamespace(alternatives=[SimpleNamespace(words=words)])])
        client = mock.Mock()
        client.recognize.return_value = response
        fake_speech = build_fake_google_speech(client)

        with TemporaryDirectory() as tmp:
            media = Path(tmp) / "a.wav"
            media.write_bytes(b"fake")
            output = Path(tmp) / "out.txt"
            with mock.patch.object(google, "import_google_speech", return_value=fake_speech):
                google.transcribe(
                    media,
                    output,
                    TranscriptionOptions(backend="google", language="en-US", min_speakers=2, max_speakers=4),
                )

            text = output.read_text(encoding="utf-8")

        self.assertEqual(text, "Speaker 1: hello again\nSpeaker 2: reply\n")
        config = client.recognize.call_args.kwargs["config"]
        self.assertEqual(config.diarization_config.min_speaker_count, 2)
        self.assertEqual(config.diarization_config.max_speaker_count, 4)

    def test_tencent_and_aliyun_raise_explicit_not_implemented_errors(self):
        from castscribe.transcription import aliyun, tencent

        with self.assertRaisesRegex(NotImplementedError, "Tencent"):
            tencent.transcribe(Path("a.wav"), Path("a.txt"), TranscriptionOptions(backend="tencent"))
        with self.assertRaisesRegex(NotImplementedError, "Alibaba"):
            aliyun.transcribe(Path("a.wav"), Path("a.txt"), TranscriptionOptions(backend="aliyun"))


def build_fake_azure_sdk(events):
    class EventHook:
        def __init__(self):
            self.callbacks = []

        def connect(self, callback):
            self.callbacks.append(callback)

        def fire(self, event):
            for callback in self.callbacks:
                callback(event)

    class ConversationTranscriber:
        def __init__(self, speech_config, audio_config):
            self.transcribed = EventHook()
            self.session_stopped = EventHook()
            self.canceled = EventHook()

        def start_transcribing_async(self):
            for event in events:
                self.transcribed.fire(event)
            self.session_stopped.fire(SimpleNamespace())
            return SimpleNamespace(get=lambda: None)

        def stop_transcribing_async(self):
            return SimpleNamespace(get=lambda: None)

    return SimpleNamespace(
        ResultReason=SimpleNamespace(RecognizedSpeech="recognized"),
        SpeechConfig=lambda subscription, endpoint: SimpleNamespace(speech_recognition_language=None),
        audio=SimpleNamespace(AudioConfig=lambda filename: SimpleNamespace(filename=filename)),
        transcription=SimpleNamespace(ConversationTranscriber=ConversationTranscriber),
        PropertyId=SimpleNamespace(SpeechServiceResponse_DiarizeIntermediateResults="diarize"),
    )


def build_fake_google_speech(client):
    return SimpleNamespace(
        SpeechClient=lambda: client,
        RecognitionAudio=lambda content: SimpleNamespace(content=content),
        SpeakerDiarizationConfig=lambda enable_speaker_diarization, min_speaker_count, max_speaker_count: SimpleNamespace(
            enable_speaker_diarization=enable_speaker_diarization,
            min_speaker_count=min_speaker_count,
            max_speaker_count=max_speaker_count,
        ),
        RecognitionConfig=lambda **kwargs: SimpleNamespace(**kwargs),
    )


if __name__ == "__main__":
    unittest.main()
