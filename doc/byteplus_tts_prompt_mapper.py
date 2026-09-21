from typing import Dict, List, Any

MAP = {
    "emotion": {
        "neutral": "平静",
        "happy": "开心",
        "excited": "兴奋",
        "relieved": "如释重负",
        "sad": "悲伤",
        "disappointed": "失望",
        "hurt": "受伤、委屈",
        "angry": "生气",
        "annoyed": "不耐烦",
        "afraid": "害怕",
        "nervous": "紧张",
        "surprised": "惊讶",
        "disgusted": "厌恶",
        "cold": "冷淡",
    },
    "intensity": {
        "subtle": "非常克制的",
        "mild": "轻微的",
        "moderate": "",
        "strong": "明显的",
        "intense": "强烈的",
    },
    "social_tone": {
        "neutral": "自然",
        "gentle": "温柔",
        "warm": "温暖亲切",
        "intimate": "亲密",
        "flirty": "暧昧",
        "cute": "带一点撒娇感",
        "comforting": "安慰人的",
        "reassuring": "让人安心的",
        "teasing": "俏皮调侃",
        "sarcastic": "略带讽刺",
        "firm": "坚定",
        "serious": "认真严肃",
        "argumentative": "像在争辩",
        "distant": "疏离冷淡",
        "professional": "专业",
        "casual": "自然随意",
    },
    "mental_state": {
        "calm": "内心平静",
        "hesitant": "有些犹豫",
        "shy": "带一点害羞",
        "expectant": "带着期待",
        "uncertain": "有些不确定",
        "restrained": "努力克制情绪",
        "hurt": "内心受伤",
        "exhausted": "显得疲惫",
        "desperate": "带着绝望感",
        "heartbroken": "有明显心碎感",
        "confident": "显得自信",
        "impatient": "有些不耐烦",
        "embarrassed": "略显尴尬",
        "confused": "有些困惑",
        "suspicious": "带着怀疑",
        "resigned": "像是已经无奈接受",
        "hopeful": "仍带着希望",
        "overwhelmed": "情绪有些压不住",
    },
    "communicative_intent": {
        "inform": "自然地传达信息",
        "reassure": "像是在让对方安心",
        "comfort": "像是在安慰对方",
        "encourage": "像是在鼓励对方",
        "persuade": "带有劝说感",
        "question": "带着询问感",
        "confirm": "像是在确认",
        "warn": "带着提醒或警告感",
        "apologize": "表达真诚歉意",
        "thank": "表达真诚感谢",
        "complain": "带一点抱怨感",
        "tease": "像是在逗对方",
        "confess": "像是在说出藏在心里的话",
        "reject": "明确表达拒绝",
        "request": "带着请求感",
        "explain": "耐心解释",
        "challenge": "带着挑战意味",
        "invite": "自然地邀请对方",
    },
    "voice_texture": {
        "normal": "声音自然",
        "soft": "声音轻柔",
        "deep": "声音低沉",
        "low": "声音偏低",
        "bright": "声音明亮",
        "hoarse": "略带沙哑",
        "breathy": "略带气声",
        "trembling": "声音微微发颤",
        "tearful": "略带哭腔",
        "whispering": "接近低声耳语",
        "powerful": "声音有力量",
        "weak": "声音略显虚弱",
        "tired": "声音带着疲惫感",
        "smiling": "声音里带一点笑意",
    },
    "pace": {
        "very_slow": "语速很慢",
        "slow": "语速较慢",
        "slightly_slow": "语速稍慢",
        "normal": "语速自然",
        "slightly_fast": "语速稍快",
        "fast": "语速较快",
    },
    "pitch": {
        "low": "音调偏低",
        "slightly_low": "音调略低",
        "normal": "音调自然",
        "slightly_high": "音调略高",
        "high": "音调偏高",
    },
    "energy": {
        "very_low": "整体能量很低",
        "low": "整体能量偏低",
        "medium": "整体能量自然",
        "high": "整体能量较高",
        "very_high": "整体能量很高",
    },
}


def get_mapped(category: str, key: str, default: str = "") -> str:
    return MAP.get(category, {}).get(key, default)


def map_list(category: str, values: List[str]) -> List[str]:
    return [
        MAP[category][value]
        for value in values
        if value in MAP.get(category, {})
    ]


def normalize_config(config: Dict[str, Any]) -> Dict[str, Any]:
    config = dict(config)

    emotion = config.get("emotion")
    tone = config.get("social_tone")
    states = list(config.get("mental_state", []))
    textures = list(config.get("voice_texture", []))

    if tone == "intimate" and "powerful" in textures:
        textures.remove("powerful")
        if "soft" not in textures:
            textures.append("soft")

    if emotion in {"sad", "hurt", "disappointed"}:
        if config.get("energy") == "very_high":
            config["energy"] = "medium"

    if emotion == "afraid" and config.get("intensity") in {"strong", "intense"}:
        if "trembling" not in textures:
            textures.append("trembling")

    if emotion == "cold" and config.get("energy") in {"high", "very_high"}:
        config["energy"] = "low"

    if tone == "professional":
        textures = [
            x for x in textures
            if x not in {"tearful", "whispering"}
        ]

    config["mental_state"] = states[:2]
    config["voice_texture"] = textures[:2]

    return config


def build_emotion_phrase(config: Dict[str, Any]) -> str:
    emotion = get_mapped("emotion", config.get("emotion", "neutral"))
    intensity = get_mapped("intensity", config.get("intensity", "moderate"))
    tone = get_mapped("social_tone", config.get("social_tone", "neutral"))

    emotion_phrase = f"{intensity}{emotion}" if intensity else emotion

    if tone == "自然" and emotion == "平静":
        return "用自然平静的语气说"

    return f"用{tone}、{emotion_phrase}的语气说"


def build_state_intent_phrase(config: Dict[str, Any]) -> str:
    states = map_list("mental_state", config.get("mental_state", []))
    intent = get_mapped(
        "communicative_intent",
        config.get("communicative_intent", "inform")
    )
    parts = []
    if states:
        parts.append("，".join(states))
    if intent:
        parts.append(intent)
    return "，".join(parts)


def build_voice_phrase(config: Dict[str, Any]) -> str:
    textures = map_list("voice_texture", config.get("voice_texture", []))

    parts = []
    if textures:
        parts.append("、".join(textures))

    for category, default in [
        ("pace", "normal"),
        ("pitch", "normal"),
        ("energy", "medium"),
    ]:
        value = get_mapped(category, config.get(category, default))
        if value:
            parts.append(value)

    return "，".join(parts)


def build_special_phrase(config: Dict[str, Any]) -> str | None:
    emotion = config.get("emotion")
    states = set(config.get("mental_state", []))
    intent = config.get("communicative_intent")

    if (
        emotion == "sad"
        and "hurt" in states
        and "restrained" in states
        and intent == "reassure"
    ):
        return "用温柔、悲伤但克制的语气说，内心虽然受伤，但仍想让对方安心"

    if (
        emotion == "nervous"
        and "shy" in states
        and intent == "confess"
    ):
        return "用紧张而害羞的语气说，像是在鼓起勇气说出藏在心里的话"

    return None


def build_byteplus_prompt(
    config: Dict[str, Any],
    add_naturalness_constraint: bool = True
) -> str:
    config = normalize_config(config)

    sentences = []

    special = build_special_phrase(config)
    if special:
        sentences.append(special)
    else:
        emotion_phrase = build_emotion_phrase(config)
        if emotion_phrase:
            sentences.append(emotion_phrase)

        state_intent_phrase = build_state_intent_phrase(config)
        if state_intent_phrase:
            sentences.append(state_intent_phrase)

    voice_phrase = build_voice_phrase(config)
    if voice_phrase:
        sentences.append(voice_phrase)

    if add_naturalness_constraint:
        sentences.append("整体表达自然，不要过度夸张")

    return "。".join(x for x in sentences if x) + "。"


if __name__ == "__main__":
    example = {
        "emotion": "sad",
        "intensity": "moderate",
        "social_tone": "gentle",
        "mental_state": ["hurt", "restrained"],
        "communicative_intent": "reassure",
        "voice_texture": ["soft", "trembling"],
        "pace": "slow",
        "pitch": "slightly_low",
        "energy": "low",
    }

    print(build_byteplus_prompt(example))
