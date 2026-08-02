"""Separate the vocals track from an audio file using demucs."""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import torch


def default_output(audio: str) -> str:
    """Return ``<name>_vocals.wav`` next to the input audio file."""
    path = Path(audio)
    return str(path.with_name(f"{path.stem}_vocals.wav"))


def pick_device() -> str:
    """Return 'cuda' when available, otherwise 'cpu'."""
    return "cuda" if torch.cuda.is_available() else "cpu"


def separate_vocals(
    audio: str,
    output: str,
    model: str = "htdemucs_ft",
    device: str = "auto",
    segment: int = 7,
) -> Path:
    """Separate vocals with demucs and save them to ``output``.

    ``segment`` must be an integer <= 7 (htdemucs transformers cap at 7.8s).
    """
    if not Path(audio).exists():
        raise OSError(f"audio file not found: {audio}")
    if device == "auto":
        device = pick_device()
    workdir = tempfile.mkdtemp(prefix="demucs_")
    try:
        env = {**os.environ, "PYTORCH_NO_CUDA_MEMORY_CACHING": "1"}
        subprocess.run(
            [
                sys.executable,
                "-m",
                "demucs",
                "-n",
                model,
                "--two-stems=vocals",
                "-d",
                device,
                "--segment",
                str(segment),
                "-o",
                workdir,
                audio,
            ],
            capture_output=True,
            text=True,
            check=True,
            env=env,
        )
        source = Path(workdir) / model / Path(audio).stem / "vocals.wav"
        if not source.exists():
            raise RuntimeError(
                f"demucs finished but vocals.wav was not created: {source}"
            )
        shutil.copy2(source, output)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
    return Path(output)
