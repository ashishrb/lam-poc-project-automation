#!/usr/bin/env python3
"""Model Manager - centralizes model loading/switching for orchestrator."""
from typing import Optional
import logging

try:
    from transformers import AutoModelForCausalLM, AutoTokenizer
    import torch
except Exception:
    AutoModelForCausalLM = None
    AutoTokenizer = None
    torch = None


class ModelManager:
    def __init__(self, xlam_model: str = "Salesforce/xLAM-1b-fc-r"):
        self.xlam_model_name = xlam_model
        self._xlam_model = None
        self._xlam_tokenizer = None

    def load_xlam(self):
        if self._xlam_model or not AutoModelForCausalLM:
            return self._xlam_model, self._xlam_tokenizer
        try:
            device = "cuda" if torch and torch.cuda.is_available() else "cpu"
            dtype = torch.float16 if device == "cuda" else torch.float32
            self._xlam_model = AutoModelForCausalLM.from_pretrained(
                self.xlam_model_name, trust_remote_code=True, torch_dtype=dtype
            )
            self._xlam_model = self._xlam_model.to(device)
            self._xlam_tokenizer = AutoTokenizer.from_pretrained(self.xlam_model_name)
        except Exception as e:
            logging.error(f"Failed to load xLAM: {e}")
        return self._xlam_model, self._xlam_tokenizer

