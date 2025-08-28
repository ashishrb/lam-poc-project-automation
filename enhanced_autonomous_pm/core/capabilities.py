#!/usr/bin/env python3
"""Capability detection for optional dependencies and runtime features.

This module centralizes feature flags so callers don't scatter try/except imports.
"""

from typing import Dict, Any
import os
import logging

try:
    import torch  # type: ignore
    TORCH_AVAILABLE = True
except Exception:
    TORCH_AVAILABLE = False
    torch = None  # type: ignore

try:
    import transformers  # type: ignore
    TRANSFORMERS_AVAILABLE = True
except Exception:
    TRANSFORMERS_AVAILABLE = False

try:
    import ollama  # type: ignore
    OLLAMA_AVAILABLE = True
except Exception:
    OLLAMA_AVAILABLE = False
    ollama = None  # type: ignore

try:
    import chromadb  # type: ignore
    CHROMADB_AVAILABLE = True
except Exception:
    CHROMADB_AVAILABLE = False


def summarize() -> Dict[str, Any]:
    """Return a snapshot of capability flags and basic runtime info."""
    cuda = False
    cuda_devices = 0
    if TORCH_AVAILABLE and hasattr(torch, 'cuda'):
        try:
            cuda = bool(torch.cuda.is_available())
            cuda_devices = torch.cuda.device_count() if cuda else 0
        except Exception:
            pass

    return {
        "torch": TORCH_AVAILABLE,
        "transformers": TRANSFORMERS_AVAILABLE,
        "ollama": OLLAMA_AVAILABLE,
        "chromadb": CHROMADB_AVAILABLE,
        "cuda": cuda,
        "cuda_devices": cuda_devices,
        "env": {
            "debug": os.getenv('DEBUG', 'False'),
            "port": os.getenv('PORT', '5000')
        }
    }

