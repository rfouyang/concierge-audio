"""Persistent generated WAVs and their searchable metadata."""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from uuid import uuid4


class TtsHistory:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.lock = RLock()

    def directory(self, provider):
        if provider not in {"minimax", "byteplus"}:
            raise ValueError("Unknown provider")
        directory = self.root / provider
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def path(self, provider, record_id, suffix):
        if not re.fullmatch(r"[a-f0-9]{32}", record_id):
            raise ValueError("Invalid record ID")
        return self.directory(provider) / (record_id + suffix)

    def save(self, provider, audio, request, record_id=None):
        record_id = record_id or uuid4().hex
        with self.lock:
            metadata_path = self.path(provider, record_id, ".json")
            if metadata_path.exists():
                return record_id
            metadata = {
                "id": record_id, "provider": provider,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "text": request.get("text", ""), "voice_id": request.get("voice_id", ""),
                "duration_seconds": audio.wav_info.duration_seconds,
                "size_bytes": len(audio.audio),
            }
            if audio.synthesis_details is not None:
                metadata["synthesis_details"] = audio.synthesis_details
            self.path(provider, record_id, ".wav").write_bytes(audio.audio)
            temporary = self.path(provider, record_id, ".tmp")
            temporary.write_text(json.dumps(metadata, ensure_ascii=False), encoding="utf-8")
            temporary.replace(metadata_path)
        return record_id

    def list(self, provider):
        with self.lock:
            records = []
            for path in self.directory(provider).glob("*.json"):
                if path.with_suffix(".wav").is_file():
                    records.append(json.loads(path.read_text(encoding="utf-8")))
            return sorted(records, key=lambda item: item["created_at"], reverse=True)

    def delete(self, provider, record_id):
        with self.lock:
            wav = self.path(provider, record_id, ".wav")
            if not wav.exists():
                raise FileNotFoundError(record_id)
            wav.unlink()
            self.path(provider, record_id, ".json").unlink(missing_ok=True)

    def remember_task(self, task_id, request):
        with self.lock:
            path = self.directory("minimax") / "tasks.json"
            tasks = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
            tasks[str(task_id)] = {"id": uuid4().hex, "request": request}
            temporary = path.with_suffix(".tmp")
            temporary.write_text(json.dumps(tasks, ensure_ascii=False), encoding="utf-8")
            temporary.replace(path)

    def save_task(self, task_id, audio):
        with self.lock:
            path = self.directory("minimax") / "tasks.json"
            tasks = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
            task = tasks.get(str(task_id))
            if task:
                return self.save("minimax", audio, task["request"], task["id"])
        return None
