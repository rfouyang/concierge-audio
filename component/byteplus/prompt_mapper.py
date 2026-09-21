"""Convert structured BytePlus style controls into one natural-language prompt."""

from __future__ import annotations

from dataclasses import replace
from component.byteplus.presets import list_presets

from component.byteplus.models import ByteplusStyleConfig
from component.common.models import ValidationError


MAP: dict[str, dict[str, str]] = {
    "emotion": {
        "neutral": "平静", "happy": "开心", "excited": "兴奋",
        "relieved": "如释重负", "sad": "悲伤", "disappointed": "失望",
        "hurt": "受伤、委屈", "angry": "生气", "annoyed": "不耐烦",
        "afraid": "害怕", "nervous": "紧张", "surprised": "惊讶",
        "disgusted": "厌恶", "cold": "冷淡",
    },
    "intensity": {
        "subtle": "非常克制的", "mild": "轻微的", "moderate": "",
        "strong": "明显的", "intense": "强烈的",
    },
    "social_tone": {
        "neutral": "自然", "gentle": "温柔", "warm": "温暖亲切",
        "intimate": "亲密", "flirty": "暧昧", "cute": "带一点撒娇感",
        "comforting": "安慰人的", "reassuring": "让人安心的",
        "teasing": "俏皮调侃", "sarcastic": "略带讽刺", "firm": "坚定",
        "serious": "认真严肃", "argumentative": "像在争辩",
        "distant": "疏离冷淡", "professional": "专业", "casual": "自然随意",
    },
    "mental_state": {
        "calm": "内心平静", "hesitant": "有些犹豫", "shy": "带一点害羞",
        "expectant": "带着期待", "uncertain": "有些不确定",
        "restrained": "努力克制情绪", "hurt": "内心受伤",
        "exhausted": "显得疲惫", "desperate": "带着绝望感",
        "heartbroken": "有明显心碎感", "confident": "显得自信",
        "impatient": "明显不耐烦", "embarrassed": "略显尴尬",
        "confused": "有些困惑", "suspicious": "带着怀疑",
        "resigned": "像是已经无奈接受", "hopeful": "仍带着希望",
        "overwhelmed": "情绪有些压不住",
    },
    "communicative_intent": {
        "inform": "自然地传达信息", "reassure": "像是在让对方安心",
        "comfort": "像是在安慰对方", "encourage": "像是在鼓励对方",
        "persuade": "带有劝说感", "question": "带着询问感",
        "confirm": "像是在确认", "warn": "带着提醒或警告感",
        "apologize": "表达真诚歉意", "thank": "表达真诚感谢",
        "complain": "带一点抱怨感", "tease": "像是在逗对方",
        "confess": "像是在说出藏在心里的话", "reject": "明确表达拒绝",
        "request": "带着请求感", "explain": "耐心解释",
        "challenge": "带着挑战意味", "invite": "自然地邀请对方",
    },
    "voice_texture": {
        "normal": "声音自然", "soft": "声音轻柔", "deep": "声音低沉",
        "low": "声音偏低", "bright": "声音明亮", "hoarse": "略带沙哑",
        "breathy": "略带气声", "trembling": "声音微微发颤",
        "tearful": "略带哭腔", "whispering": "用低声耳语发声，带清晰气声而非普通音量说话",
        "powerful": "声音有力量", "weak": "声音略显虚弱",
        "tired": "声音带着疲惫感", "smiling": "声音里带一点笑意",
    },
    "pace": {
        "very_slow": "语速很慢", "slow": "语速较慢",
        "slightly_slow": "语速稍慢", "normal": "语速自然",
        "slightly_fast": "语速稍快", "fast": "语速较快",
    },
    "pitch": {
        "low": "音调偏低", "slightly_low": "音调略低", "normal": "音调自然",
        "slightly_high": "音调略高", "high": "音调偏高",
    },
    "energy": {
        "very_low": "整体能量很低", "low": "整体能量偏低",
        "medium": "整体能量自然", "high": "整体能量较高",
        "very_high": "整体能量很高",
    },
}


def validate_style(style: ByteplusStyleConfig) -> None:
    if style.preset_id and not any(p["id"] == style.preset_id for p in list_presets()):
        raise ValidationError("未知 BytePlus 预设。")
    for field in (
        "emotion", "intensity", "social_tone", "communicative_intent",
        "pace", "pitch", "energy",
    ):
        value = getattr(style, field)
        if value not in MAP[field]:
            raise ValidationError(f"不支持 BytePlus 风格参数 {field}={value}。")
    if len(style.mental_state) > 2:
        raise ValidationError("mental_state 最多选择两个值。")
    if len(style.voice_texture) > 2:
        raise ValidationError("voice_texture 最多选择两个值。")
    for value in style.mental_state:
        if value not in MAP["mental_state"]:
            raise ValidationError(f"不支持 mental_state={value}。")
    for value in style.voice_texture:
        if value not in MAP["voice_texture"]:
            raise ValidationError(f"不支持 voice_texture={value}。")


def normalize_style(style: ByteplusStyleConfig) -> ByteplusStyleConfig:
    validate_style(style)
    textures = list(style.voice_texture)
    energy = style.energy
    if style.social_tone == "intimate" and "powerful" in textures:
        textures.remove("powerful")
        if "soft" not in textures:
            textures.append("soft")
    if style.emotion in {"sad", "hurt", "disappointed"} and energy == "very_high":
        energy = "medium"
    if style.emotion == "afraid" and style.intensity in {"strong", "intense"}:
        if "trembling" not in textures:
            textures.append("trembling")
    if style.emotion == "cold" and energy in {"high", "very_high"}:
        energy = "low"
    if style.social_tone == "professional":
        textures = [value for value in textures if value not in {"tearful", "whispering"}]
    return replace(style, voice_texture=tuple(textures[:2]), energy=energy)


def build_byteplus_prompt(
    style: ByteplusStyleConfig,
    *,
    add_naturalness_constraint: bool = True,
) -> str:
    style = normalize_style(style)
    special = _build_special_phrase(style)
    sentences: list[str] = []
    if special:
        sentences.append(special)
    else:
        emotion = MAP["emotion"][style.emotion]
        intensity = MAP["intensity"][style.intensity]
        tone = MAP["social_tone"][style.social_tone]
        if tone == "自然" and emotion == "平静":
            sentences.append("用自然平静的语气说")
        else:
            sentences.append(f"用{tone}、{intensity}{emotion}的语气说")
        states = [MAP["mental_state"][value] for value in style.mental_state]
        intent = MAP["communicative_intent"][style.communicative_intent]
        sentences.append("，".join([*states, intent]))
    voice_parts = [MAP["voice_texture"][value] for value in style.voice_texture]
    voice_parts.extend(
        [MAP["pace"][style.pace], MAP["pitch"][style.pitch], MAP["energy"][style.energy]]
    )
    sentences.append("，".join(voice_parts))
    if add_naturalness_constraint:
        sentences.append("保持吐字清晰，同时充分表现上述语气和发声方式")
    prompt = "。".join(value for value in sentences if value) + "。"
    if style.preset_id:
        preset = next(p for p in list_presets() if p["id"] == style.preset_id)
        prompt += preset["scene_prompt"]
    return prompt


def _build_special_phrase(style: ByteplusStyleConfig) -> str | None:
    states = set(style.mental_state)
    if (
        style.emotion == "sad"
        and {"hurt", "restrained"}.issubset(states)
        and style.communicative_intent == "reassure"
    ):
        return "用温柔、悲伤但克制的语气说，内心虽然受伤，但仍想让对方安心"
    if (
        style.emotion == "nervous"
        and "shy" in states
        and style.communicative_intent == "confess"
    ):
        return "用紧张而害羞的语气说，像是在鼓起勇气说出藏在心里的话"
    return None
