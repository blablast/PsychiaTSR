"""Digital Signal Processing utilities for audio."""

from typing import Iterable, Union
import numpy as np

WEBRTC_SAMPLE_RATE = 48000


def resample_to_48k_mono_int16(samples: np.ndarray, src_rate: int, channels: int) -> np.ndarray:
    """
    Resample audio to 48kHz mono int16 format for WebRTC.

    Args:
        samples: Input audio samples
        src_rate: Source sample rate
        channels: Number of channels (1=mono, 2=stereo)

    Returns:
        Resampled audio as int16 mono @ 48kHz
    """
    if samples.size == 0:
        return samples.astype(np.int16)

    # Convert stereo to mono by taking left channel
    if channels == 2:
        samples = samples.reshape(-1, 2)[:, 0]

    # If already at target rate, just convert type
    if src_rate == WEBRTC_SAMPLE_RATE:
        return samples.astype(np.int16)

    # Normalize to float32 [-1, 1]
    x = samples.astype(np.float32) / 32768.0
    n_src = x.shape[0]
    n_dst = int(np.round(n_src * WEBRTC_SAMPLE_RATE / src_rate))

    if n_src == 0 or n_dst == 0:
        return np.empty((0,), dtype=np.int16)

    # Linear interpolation resampling
    src_idx = np.linspace(0, n_src - 1, num=n_src, dtype=np.float32)
    dst_idx = np.linspace(0, n_src - 1, num=n_dst, dtype=np.float32)
    y = np.interp(dst_idx, src_idx, x)

    # Clip and convert back to int16
    y = np.clip(y, -1.0, 1.0)
    return (y * 32767.0).astype(np.int16)


def _iter_chunks(obj: Union[bytes, bytearray, Iterable[bytes]]) -> Iterable[bytes]:
    """Iterate over chunks from bytes or iterable of bytes."""
    if isinstance(obj, (bytes, bytearray)):
        yield bytes(obj)
    else:
        for chunk in obj:
            if chunk:
                yield chunk


def wav_iterable_to_pcm48(
    obj: Union[bytes, bytearray, Iterable[bytes]], fallback_sr: int = 22050
) -> Iterable[np.ndarray]:
    """
    Convert WAV format data to PCM int16 @ 48kHz mono.

    Handles streaming WAV data from ElevenLabs SDK.

    Args:
        obj: WAV data as bytes or iterable of bytes
        fallback_sr: Sample rate to use if WAV header parsing fails

    Yields:
        PCM samples as int16 arrays @ 48kHz mono
    """
    header_needed = 44  # Standard WAV header size
    header_buf = bytearray()
    sample_rate = fallback_sr
    channels = 1

    for raw_chunk in _iter_chunks(obj):
        if header_needed > 0:
            header_buf.extend(raw_chunk)

            if len(header_buf) < header_needed:
                continue

            # Parse WAV header
            header = header_buf[:44]
            data = header_buf[44:]

            try:
                # Extract sample rate (bytes 24-27) and channels (bytes 22-23)
                sample_rate = int.from_bytes(header[24:28], "little")
                channels = int.from_bytes(header[22:24], "little")
                bits_per_sample = int.from_bytes(header[34:36], "little")

                if bits_per_sample != 16:
                    # Fallback for non-16-bit audio
                    sample_rate, channels = fallback_sr, 1

            except Exception:
                # If header parsing fails, use fallback values
                sample_rate, channels = fallback_sr, 1

            # Process initial data after header
            if data:
                # Ensure even number of bytes for int16 conversion
                n = (len(data) // 2) * 2
                if n > 0:
                    arr = np.frombuffer(data[:n], dtype=np.int16)
                    yield resample_to_48k_mono_int16(arr, sample_rate, channels)

            header_needed = 0

        else:
            # Process audio data chunks
            n = (len(raw_chunk) // 2) * 2
            if n > 0:
                arr = np.frombuffer(raw_chunk[:n], dtype=np.int16)
                yield resample_to_48k_mono_int16(arr, sample_rate, channels)
