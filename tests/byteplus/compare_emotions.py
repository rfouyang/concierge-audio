"""Fixed-text comparison. Preview by default; --generate spends API credits."""

import argparse
import json

import requests

from component.byteplus.models import ByteplusStyleConfig
from component.byteplus.presets import list_presets
from component.byteplus.prompt_mapper import build_byteplus_prompt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generate", action="store_true")
    parser.add_argument("--base-url", default="http://127.0.0.1:5000")
    parser.add_argument("--voice-id", default="zh_female_vv_uranus_bigtts")
    parser.add_argument("--text", default="来，靠近一点。看着我，我们再试一次，现在就开始。")
    args = parser.parse_args()
    presets = {p["id"]: p for p in list_presets()}
    for preset_id in (None, "098", "064", "042"):
        preset = presets.get(preset_id)
        style = {**preset["style"], "preset_id": preset_id} if preset else None
        name = preset["name"] if preset else "无语气基线"
        payload = {
            "text": args.text, "voice_id": args.voice_id,
            "speech_rate": 0, "loudness_rate": 0,
            "segments": [{"text": args.text, "style": style}],
        }
        prompt = build_byteplus_prompt(ByteplusStyleConfig.from_mapping(style)) if style else None
        print(json.dumps({"case": name, "request": payload, "prompt": prompt}, ensure_ascii=False))
        if args.generate:
            response = requests.post(f"{args.base_url.rstrip('/')}/api/byteplus/tts", json=payload, timeout=180)
            response.raise_for_status()
            print(f"{name}: {response.headers.get('X-Audio-Duration-Ms')} ms; saved in output/tts/byteplus (History)")


if __name__ == "__main__":
    main()
