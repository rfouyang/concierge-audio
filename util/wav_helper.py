"""WAV inspection required before Unitree G1 playback."""

from __future__ import annotations

import io
import wave

from component.common.models import AudioValidationError, WavInfo


class WavHelper:
    """Validate generated WAV audio against the G1 playback contract."""

    def __init__(self, *, required_sample_rate: int, required_channels: int) -> None:
        self.required_sample_rate = required_sample_rate
        self.required_channels = required_channels

    def inspect(self, audio: bytes) -> WavInfo:
        if not audio:
            raise AudioValidationError("生成的 WAV 音频为空。")

        try:
            with wave.open(io.BytesIO(audio), "rb") as wav_file:
                sample_rate = wav_file.getframerate()
                channels = wav_file.getnchannels()
                sample_width_bytes = wav_file.getsampwidth()
                frame_count = wav_file.getnframes()
        except (EOFError, wave.Error) as error:
            raise AudioValidationError("语音服务返回的内容不是有效的 WAV 文件。") from error

        if sample_rate != self.required_sample_rate:
            raise AudioValidationError(
                f"WAV 采样率为 {sample_rate} Hz，不是 G1 要求的 "
                f"{self.required_sample_rate} Hz。"
            )
        if channels != self.required_channels:
            raise AudioValidationError(
                f"WAV 声道数为 {channels}，不是要求的 {self.required_channels}。"
            )
        if frame_count <= 0:
            raise AudioValidationError("生成的 WAV 文件没有音频帧。")

        return WavInfo(
            sample_rate=sample_rate,
            channels=channels,
            sample_width_bytes=sample_width_bytes,
            frame_count=frame_count,
            duration_seconds=frame_count / sample_rate,
        )

    def concatenate(self, audio_segments: list[bytes]) -> bytes:
        """Join verified PCM WAV segments without changing the G1 audio profile."""

        if not audio_segments:
            raise AudioValidationError("没有可拼接的 WAV 音频。")

        frames: list[bytes] = []
        sample_width: int | None = None
        compression_type: str | None = None
        for audio in audio_segments:
            self.inspect(audio)
            with wave.open(io.BytesIO(audio), "rb") as wav_file:
                if sample_width is None:
                    sample_width = wav_file.getsampwidth()
                    compression_type = wav_file.getcomptype()
                elif (
                    wav_file.getsampwidth() != sample_width
                    or wav_file.getcomptype() != compression_type
                ):
                    raise AudioValidationError("分段 WAV 的采样格式不一致，无法安全拼接。")
                frames.append(wav_file.readframes(wav_file.getnframes()))

        output = io.BytesIO()
        with wave.open(output, "wb") as wav_file:
            wav_file.setnchannels(self.required_channels)
            wav_file.setsampwidth(sample_width or 2)
            wav_file.setframerate(self.required_sample_rate)
            wav_file.writeframes(b"".join(frames))
        return output.getvalue()

    def from_pcm(self, pcm: bytes, *, sample_width_bytes: int = 2) -> bytes:
        """Wrap raw interleaved PCM in a G1-compatible WAV container."""

        if not pcm:
            raise AudioValidationError("生成的 PCM 音频为空。")
        frame_width = sample_width_bytes * self.required_channels
        if frame_width <= 0 or len(pcm) % frame_width:
            raise AudioValidationError("PCM 数据长度与采样格式不匹配。")
        output = io.BytesIO()
        with wave.open(output, "wb") as wav_file:
            wav_file.setnchannels(self.required_channels)
            wav_file.setsampwidth(sample_width_bytes)
            wav_file.setframerate(self.required_sample_rate)
            wav_file.writeframes(pcm)
        audio = output.getvalue()
        self.inspect(audio)
        return audio


def demo_wav_helper() -> None:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        wav_file.writeframes(b"\x00\x00" * 160)
    print(WavHelper(required_sample_rate=16000, required_channels=1).inspect(buffer.getvalue()))


def main() -> None:
    demo_wav_helper()


if __name__ == "__main__":
    main()
