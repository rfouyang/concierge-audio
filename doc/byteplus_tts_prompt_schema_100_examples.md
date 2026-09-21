# BytePlus TTS Prompt Schema + 100 个常见示例

> 说明：这是一套面向 BytePlus / Seed Speech TTS 2.0 `context_texts` 的工程化控制 schema，并非 BytePlus 官方固定 JSON 枚举。目标是让上游 LLM 输出稳定、有限、可测试的语音控制参数，再映射成自然语言语音指令。

## 1. Field 定义

```json
{
  "emotion": {
    "type": "enum",
    "multi": false,
    "values": [
      "neutral",
      "happy",
      "excited",
      "relieved",
      "sad",
      "disappointed",
      "hurt",
      "angry",
      "annoyed",
      "afraid",
      "nervous",
      "surprised",
      "disgusted",
      "cold"
    ]
  },
  "intensity": {
    "type": "enum",
    "multi": false,
    "values": [
      "subtle",
      "mild",
      "moderate",
      "strong",
      "intense"
    ]
  },
  "social_tone": {
    "type": "enum",
    "multi": false,
    "values": [
      "neutral",
      "gentle",
      "warm",
      "intimate",
      "flirty",
      "cute",
      "comforting",
      "reassuring",
      "teasing",
      "sarcastic",
      "firm",
      "serious",
      "argumentative",
      "distant",
      "professional",
      "casual"
    ]
  },
  "mental_state": {
    "type": "enum[]",
    "multi": true,
    "max_items": 2,
    "values": [
      "calm",
      "hesitant",
      "shy",
      "expectant",
      "uncertain",
      "restrained",
      "hurt",
      "exhausted",
      "desperate",
      "heartbroken",
      "confident",
      "impatient",
      "embarrassed",
      "confused",
      "suspicious",
      "resigned",
      "hopeful",
      "overwhelmed"
    ]
  },
  "communicative_intent": {
    "type": "enum",
    "multi": false,
    "values": [
      "inform",
      "reassure",
      "comfort",
      "encourage",
      "persuade",
      "question",
      "confirm",
      "warn",
      "apologize",
      "thank",
      "complain",
      "tease",
      "confess",
      "reject",
      "request",
      "explain",
      "challenge",
      "invite"
    ]
  },
  "voice_texture": {
    "type": "enum[]",
    "multi": true,
    "max_items": 2,
    "values": [
      "normal",
      "soft",
      "deep",
      "low",
      "bright",
      "hoarse",
      "breathy",
      "trembling",
      "tearful",
      "whispering",
      "powerful",
      "weak",
      "tired",
      "smiling"
    ]
  },
  "pace": {
    "type": "enum",
    "multi": false,
    "values": [
      "very_slow",
      "slow",
      "slightly_slow",
      "normal",
      "slightly_fast",
      "fast"
    ]
  },
  "pitch": {
    "type": "enum",
    "multi": false,
    "values": [
      "low",
      "slightly_low",
      "normal",
      "slightly_high",
      "high"
    ]
  },
  "energy": {
    "type": "enum",
    "multi": false,
    "values": [
      "very_low",
      "low",
      "medium",
      "high",
      "very_high"
    ]
  }
}
```

### 是否支持多个值

| Field | 多选 | 建议数量 | 说明 |
|---|---:|---:|---|
| `emotion` | 否 | 1 | 主情绪 |
| `intensity` | 否 | 1 | 主情绪强度 |
| `social_tone` | 否 | 1 | 面向听者的社交语气 |
| `mental_state` | 是 | 0–2 | 心理子状态 |
| `communicative_intent` | 否 | 1 | 这句话要完成的交流动作 |
| `voice_texture` | 是 | 1–2 | 可听见的声音质感 |
| `pace` | 否 | 1 | 语速/节奏 |
| `pitch` | 否 | 1 | 音调区间 |
| `energy` | 否 | 1 | 整体能量/激活度 |

## 2. 推荐输入格式

```json
{
  "emotion": "sad",
  "intensity": "moderate",
  "social_tone": "gentle",
  "mental_state": [
    "hurt",
    "restrained"
  ],
  "communicative_intent": "reassure",
  "voice_texture": [
    "soft",
    "trembling"
  ],
  "pace": "slow",
  "pitch": "slightly_low",
  "energy": "low"
}
```

## 3. 100 个常见组合

### 001. 平静陈述

**概括：** 平静陈述

```json
{
  "emotion": "neutral",
  "intensity": "subtle",
  "social_tone": "neutral",
  "mental_state": [
    "calm"
  ],
  "communicative_intent": "inform",
  "voice_texture": [
    "normal"
  ],
  "pace": "normal",
  "pitch": "normal",
  "energy": "medium"
}
```

### 002. 专业说明

**概括：** 专业说明

```json
{
  "emotion": "neutral",
  "intensity": "mild",
  "social_tone": "professional",
  "mental_state": [
    "calm",
    "confident"
  ],
  "communicative_intent": "explain",
  "voice_texture": [
    "normal"
  ],
  "pace": "normal",
  "pitch": "normal",
  "energy": "medium"
}
```

### 003. 温柔提醒

**概括：** 温柔提醒

```json
{
  "emotion": "neutral",
  "intensity": "mild",
  "social_tone": "gentle",
  "mental_state": [
    "calm"
  ],
  "communicative_intent": "warn",
  "voice_texture": [
    "soft"
  ],
  "pace": "slightly_slow",
  "pitch": "slightly_low",
  "energy": "low"
}
```

### 004. 耐心安抚

**概括：** 耐心安抚

```json
{
  "emotion": "neutral",
  "intensity": "moderate",
  "social_tone": "reassuring",
  "mental_state": [
    "calm"
  ],
  "communicative_intent": "reassure",
  "voice_texture": [
    "soft"
  ],
  "pace": "slow",
  "pitch": "slightly_low",
  "energy": "low"
}
```

### 005. 轻松聊天

**概括：** 轻松聊天

```json
{
  "emotion": "happy",
  "intensity": "mild",
  "social_tone": "casual",
  "mental_state": [
    "calm"
  ],
  "communicative_intent": "inform",
  "voice_texture": [
    "smiling"
  ],
  "pace": "normal",
  "pitch": "normal",
  "energy": "medium"
}
```

### 006. 自然开心

**概括：** 自然开心

```json
{
  "emotion": "happy",
  "intensity": "moderate",
  "social_tone": "warm",
  "mental_state": [
    "hopeful"
  ],
  "communicative_intent": "inform",
  "voice_texture": [
    "bright",
    "smiling"
  ],
  "pace": "normal",
  "pitch": "slightly_high",
  "energy": "high"
}
```

### 007. 开心分享

**概括：** 开心分享

```json
{
  "emotion": "happy",
  "intensity": "moderate",
  "social_tone": "casual",
  "mental_state": [
    "confident"
  ],
  "communicative_intent": "inform",
  "voice_texture": [
    "bright",
    "smiling"
  ],
  "pace": "slightly_fast",
  "pitch": "slightly_high",
  "energy": "high"
}
```

### 008. 开心感谢

**概括：** 开心感谢

```json
{
  "emotion": "happy",
  "intensity": "moderate",
  "social_tone": "warm",
  "mental_state": [
    "calm"
  ],
  "communicative_intent": "thank",
  "voice_texture": [
    "soft",
    "smiling"
  ],
  "pace": "normal",
  "pitch": "normal",
  "energy": "medium"
}
```

### 009. 开心邀请

**概括：** 开心邀请

```json
{
  "emotion": "happy",
  "intensity": "moderate",
  "social_tone": "warm",
  "mental_state": [
    "expectant"
  ],
  "communicative_intent": "invite",
  "voice_texture": [
    "bright",
    "smiling"
  ],
  "pace": "slightly_fast",
  "pitch": "slightly_high",
  "energy": "high"
}
```

### 010. 克制开心

**概括：** 克制开心

```json
{
  "emotion": "happy",
  "intensity": "mild",
  "social_tone": "gentle",
  "mental_state": [
    "restrained"
  ],
  "communicative_intent": "inform",
  "voice_texture": [
    "soft",
    "smiling"
  ],
  "pace": "slightly_slow",
  "pitch": "normal",
  "energy": "medium"
}
```

### 011. 兴奋宣布

**概括：** 兴奋宣布

```json
{
  "emotion": "excited",
  "intensity": "strong",
  "social_tone": "casual",
  "mental_state": [
    "confident"
  ],
  "communicative_intent": "inform",
  "voice_texture": [
    "bright",
    "powerful"
  ],
  "pace": "fast",
  "pitch": "high",
  "energy": "very_high"
}
```

### 012. 惊喜兴奋

**概括：** 惊喜兴奋

```json
{
  "emotion": "excited",
  "intensity": "intense",
  "social_tone": "warm",
  "mental_state": [
    "overwhelmed"
  ],
  "communicative_intent": "inform",
  "voice_texture": [
    "bright",
    "smiling"
  ],
  "pace": "fast",
  "pitch": "high",
  "energy": "very_high"
}
```

### 013. 兴奋邀请

**概括：** 兴奋邀请

```json
{
  "emotion": "excited",
  "intensity": "strong",
  "social_tone": "casual",
  "mental_state": [
    "expectant"
  ],
  "communicative_intent": "invite",
  "voice_texture": [
    "bright"
  ],
  "pace": "slightly_fast",
  "pitch": "slightly_high",
  "energy": "very_high"
}
```

### 014. 兴奋鼓励

**概括：** 兴奋鼓励

```json
{
  "emotion": "excited",
  "intensity": "strong",
  "social_tone": "warm",
  "mental_state": [
    "confident"
  ],
  "communicative_intent": "encourage",
  "voice_texture": [
    "powerful",
    "bright"
  ],
  "pace": "slightly_fast",
  "pitch": "slightly_high",
  "energy": "high"
}
```

### 015. 压低兴奋

**概括：** 压低兴奋

```json
{
  "emotion": "excited",
  "intensity": "moderate",
  "social_tone": "intimate",
  "mental_state": [
    "restrained",
    "expectant"
  ],
  "communicative_intent": "confess",
  "voice_texture": [
    "soft",
    "smiling"
  ],
  "pace": "slightly_fast",
  "pitch": "normal",
  "energy": "medium"
}
```

### 016. 如释重负

**概括：** 如释重负

```json
{
  "emotion": "relieved",
  "intensity": "moderate",
  "social_tone": "warm",
  "mental_state": [
    "calm"
  ],
  "communicative_intent": "inform",
  "voice_texture": [
    "soft"
  ],
  "pace": "slightly_slow",
  "pitch": "slightly_low",
  "energy": "low"
}
```

### 017. 释然感谢

**概括：** 释然感谢

```json
{
  "emotion": "relieved",
  "intensity": "moderate",
  "social_tone": "warm",
  "mental_state": [
    "calm"
  ],
  "communicative_intent": "thank",
  "voice_texture": [
    "soft",
    "smiling"
  ],
  "pace": "slow",
  "pitch": "normal",
  "energy": "low"
}
```

### 018. 安心确认

**概括：** 安心确认

```json
{
  "emotion": "relieved",
  "intensity": "mild",
  "social_tone": "reassuring",
  "mental_state": [
    "calm"
  ],
  "communicative_intent": "confirm",
  "voice_texture": [
    "soft"
  ],
  "pace": "normal",
  "pitch": "normal",
  "energy": "medium"
}
```

### 019. 劫后余生

**概括：** 劫后余生

```json
{
  "emotion": "relieved",
  "intensity": "strong",
  "social_tone": "casual",
  "mental_state": [
    "overwhelmed",
    "calm"
  ],
  "communicative_intent": "inform",
  "voice_texture": [
    "breathy",
    "tired"
  ],
  "pace": "slightly_slow",
  "pitch": "slightly_low",
  "energy": "low"
}
```

### 020. 释怀告别

**概括：** 释怀告别

```json
{
  "emotion": "relieved",
  "intensity": "mild",
  "social_tone": "distant",
  "mental_state": [
    "resigned",
    "calm"
  ],
  "communicative_intent": "inform",
  "voice_texture": [
    "soft"
  ],
  "pace": "slow",
  "pitch": "slightly_low",
  "energy": "low"
}
```

### 021. 轻微难过

**概括：** 轻微难过

```json
{
  "emotion": "sad",
  "intensity": "mild",
  "social_tone": "gentle",
  "mental_state": [
    "restrained"
  ],
  "communicative_intent": "inform",
  "voice_texture": [
    "soft"
  ],
  "pace": "slightly_slow",
  "pitch": "slightly_low",
  "energy": "low"
}
```

### 022. 克制悲伤

**概括：** 克制悲伤

```json
{
  "emotion": "sad",
  "intensity": "moderate",
  "social_tone": "gentle",
  "mental_state": [
    "hurt",
    "restrained"
  ],
  "communicative_intent": "inform",
  "voice_texture": [
    "soft",
    "trembling"
  ],
  "pace": "slow",
  "pitch": "slightly_low",
  "energy": "low"
}
```

### 023. 深度悲伤

**概括：** 深度悲伤

```json
{
  "emotion": "sad",
  "intensity": "strong",
  "social_tone": "serious",
  "mental_state": [
    "heartbroken"
  ],
  "communicative_intent": "inform",
  "voice_texture": [
    "tearful",
    "trembling"
  ],
  "pace": "slow",
  "pitch": "low",
  "energy": "very_low"
}
```

### 024. 悲伤安慰

**概括：** 悲伤安慰

```json
{
  "emotion": "sad",
  "intensity": "moderate",
  "social_tone": "comforting",
  "mental_state": [
    "hurt",
    "restrained"
  ],
  "communicative_intent": "comfort",
  "voice_texture": [
    "soft",
    "tearful"
  ],
  "pace": "slow",
  "pitch": "slightly_low",
  "energy": "low"
}
```

### 025. 悲伤道歉

**概括：** 悲伤道歉

```json
{
  "emotion": "sad",
  "intensity": "moderate",
  "social_tone": "gentle",
  "mental_state": [
    "hurt",
    "hesitant"
  ],
  "communicative_intent": "apologize",
  "voice_texture": [
    "soft",
    "trembling"
  ],
  "pace": "slow",
  "pitch": "slightly_low",
  "energy": "low"
}
```

### 026. 失望陈述

**概括：** 失望陈述

```json
{
  "emotion": "disappointed",
  "intensity": "moderate",
  "social_tone": "serious",
  "mental_state": [
    "resigned"
  ],
  "communicative_intent": "inform",
  "voice_texture": [
    "tired"
  ],
  "pace": "slightly_slow",
  "pitch": "slightly_low",
  "energy": "low"
}
```

### 027. 失望质问

**概括：** 失望质问

```json
{
  "emotion": "disappointed",
  "intensity": "strong",
  "social_tone": "firm",
  "mental_state": [
    "hurt",
    "impatient"
  ],
  "communicative_intent": "question",
  "voice_texture": [
    "low"
  ],
  "pace": "normal",
  "pitch": "slightly_low",
  "energy": "medium"
}
```

### 028. 失望抱怨

**概括：** 失望抱怨

```json
{
  "emotion": "disappointed",
  "intensity": "moderate",
  "social_tone": "casual",
  "mental_state": [
    "hurt"
  ],
  "communicative_intent": "complain",
  "voice_texture": [
    "tired"
  ],
  "pace": "normal",
  "pitch": "slightly_low",
  "energy": "medium"
}
```

### 029. 无奈接受

**概括：** 无奈接受

```json
{
  "emotion": "disappointed",
  "intensity": "mild",
  "social_tone": "distant",
  "mental_state": [
    "resigned"
  ],
  "communicative_intent": "confirm",
  "voice_texture": [
    "soft",
    "tired"
  ],
  "pace": "slow",
  "pitch": "low",
  "energy": "low"
}
```

### 030. 冷静失望

**概括：** 冷静失望

```json
{
  "emotion": "disappointed",
  "intensity": "moderate",
  "social_tone": "distant",
  "mental_state": [
    "restrained"
  ],
  "communicative_intent": "inform",
  "voice_texture": [
    "low"
  ],
  "pace": "normal",
  "pitch": "low",
  "energy": "low"
}
```

### 031. 受伤却克制

**概括：** 受伤却克制

```json
{
  "emotion": "hurt",
  "intensity": "moderate",
  "social_tone": "gentle",
  "mental_state": [
    "hurt",
    "restrained"
  ],
  "communicative_intent": "inform",
  "voice_texture": [
    "soft",
    "trembling"
  ],
  "pace": "slow",
  "pitch": "slightly_low",
  "energy": "low"
}
```

### 032. 委屈抱怨

**概括：** 委屈抱怨

```json
{
  "emotion": "hurt",
  "intensity": "moderate",
  "social_tone": "casual",
  "mental_state": [
    "hurt"
  ],
  "communicative_intent": "complain",
  "voice_texture": [
    "tearful"
  ],
  "pace": "normal",
  "pitch": "normal",
  "energy": "medium"
}
```

### 033. 受伤质问

**概括：** 受伤质问

```json
{
  "emotion": "hurt",
  "intensity": "strong",
  "social_tone": "firm",
  "mental_state": [
    "hurt",
    "overwhelmed"
  ],
  "communicative_intent": "question",
  "voice_texture": [
    "trembling"
  ],
  "pace": "normal",
  "pitch": "slightly_high",
  "energy": "high"
}
```

### 034. 受伤挽留

**概括：** 受伤挽留

```json
{
  "emotion": "hurt",
  "intensity": "strong",
  "social_tone": "intimate",
  "mental_state": [
    "heartbroken",
    "hopeful"
  ],
  "communicative_intent": "request",
  "voice_texture": [
    "tearful",
    "soft"
  ],
  "pace": "slow",
  "pitch": "slightly_low",
  "energy": "low"
}
```

### 035. 受伤安慰别人

**概括：** 受伤安慰别人

```json
{
  "emotion": "hurt",
  "intensity": "moderate",
  "social_tone": "reassuring",
  "mental_state": [
    "hurt",
    "restrained"
  ],
  "communicative_intent": "reassure",
  "voice_texture": [
    "soft",
    "trembling"
  ],
  "pace": "slow",
  "pitch": "slightly_low",
  "energy": "low"
}
```

### 036. 轻微生气

**概括：** 轻微生气

```json
{
  "emotion": "angry",
  "intensity": "mild",
  "social_tone": "firm",
  "mental_state": [
    "restrained"
  ],
  "communicative_intent": "warn",
  "voice_texture": [
    "low"
  ],
  "pace": "normal",
  "pitch": "slightly_low",
  "energy": "medium"
}
```

### 037. 明显生气

**概括：** 明显生气

```json
{
  "emotion": "angry",
  "intensity": "strong",
  "social_tone": "argumentative",
  "mental_state": [
    "impatient"
  ],
  "communicative_intent": "challenge",
  "voice_texture": [
    "powerful"
  ],
  "pace": "slightly_fast",
  "pitch": "slightly_high",
  "energy": "high"
}
```

### 038. 愤怒质问

**概括：** 愤怒质问

```json
{
  "emotion": "angry",
  "intensity": "strong",
  "social_tone": "argumentative",
  "mental_state": [
    "impatient",
    "hurt"
  ],
  "communicative_intent": "question",
  "voice_texture": [
    "powerful"
  ],
  "pace": "fast",
  "pitch": "high",
  "energy": "very_high"
}
```

### 039. 强硬警告

**概括：** 强硬警告

```json
{
  "emotion": "angry",
  "intensity": "moderate",
  "social_tone": "firm",
  "mental_state": [
    "confident",
    "restrained"
  ],
  "communicative_intent": "warn",
  "voice_texture": [
    "deep",
    "powerful"
  ],
  "pace": "normal",
  "pitch": "low",
  "energy": "high"
}
```

### 040. 压抑愤怒

**概括：** 压抑愤怒

```json
{
  "emotion": "angry",
  "intensity": "strong",
  "social_tone": "distant",
  "mental_state": [
    "restrained",
    "hurt"
  ],
  "communicative_intent": "inform",
  "voice_texture": [
    "low",
    "trembling"
  ],
  "pace": "slow",
  "pitch": "low",
  "energy": "medium"
}
```

### 041. 轻度不耐烦

**概括：** 轻度不耐烦

```json
{
  "emotion": "annoyed",
  "intensity": "mild",
  "social_tone": "casual",
  "mental_state": [
    "impatient"
  ],
  "communicative_intent": "complain",
  "voice_texture": [
    "normal"
  ],
  "pace": "slightly_fast",
  "pitch": "normal",
  "energy": "medium"
}
```

### 042. 不耐烦催促

**概括：** 不耐烦催促

```json
{
  "emotion": "annoyed",
  "intensity": "moderate",
  "social_tone": "firm",
  "mental_state": [
    "impatient"
  ],
  "communicative_intent": "request",
  "voice_texture": [
    "low"
  ],
  "pace": "slightly_fast",
  "pitch": "slightly_low",
  "energy": "medium"
}
```

### 043. 烦躁拒绝

**概括：** 烦躁拒绝

```json
{
  "emotion": "annoyed",
  "intensity": "moderate",
  "social_tone": "distant",
  "mental_state": [
    "impatient"
  ],
  "communicative_intent": "reject",
  "voice_texture": [
    "low"
  ],
  "pace": "normal",
  "pitch": "slightly_low",
  "energy": "medium"
}
```

### 044. 轻微恐惧

**概括：** 轻微恐惧

```json
{
  "emotion": "afraid",
  "intensity": "mild",
  "social_tone": "serious",
  "mental_state": [
    "uncertain"
  ],
  "communicative_intent": "inform",
  "voice_texture": [
    "soft",
    "breathy"
  ],
  "pace": "slightly_slow",
  "pitch": "slightly_high",
  "energy": "low"
}
```

### 045. 明显害怕

**概括：** 明显害怕

```json
{
  "emotion": "afraid",
  "intensity": "strong",
  "social_tone": "serious",
  "mental_state": [
    "overwhelmed"
  ],
  "communicative_intent": "warn",
  "voice_texture": [
    "trembling",
    "breathy"
  ],
  "pace": "slightly_fast",
  "pitch": "high",
  "energy": "high"
}
```

### 046. 恐惧求助

**概括：** 恐惧求助

```json
{
  "emotion": "afraid",
  "intensity": "strong",
  "social_tone": "gentle",
  "mental_state": [
    "desperate",
    "overwhelmed"
  ],
  "communicative_intent": "request",
  "voice_texture": [
    "trembling",
    "tearful"
  ],
  "pace": "fast",
  "pitch": "high",
  "energy": "high"
}
```

### 047. 惊恐警告

**概括：** 惊恐警告

```json
{
  "emotion": "afraid",
  "intensity": "intense",
  "social_tone": "firm",
  "mental_state": [
    "desperate"
  ],
  "communicative_intent": "warn",
  "voice_texture": [
    "trembling",
    "powerful"
  ],
  "pace": "fast",
  "pitch": "high",
  "energy": "very_high"
}
```

### 048. 紧张发言

**概括：** 紧张发言

```json
{
  "emotion": "nervous",
  "intensity": "moderate",
  "social_tone": "serious",
  "mental_state": [
    "hesitant",
    "uncertain"
  ],
  "communicative_intent": "inform",
  "voice_texture": [
    "trembling"
  ],
  "pace": "slightly_fast",
  "pitch": "slightly_high",
  "energy": "medium"
}
```

### 049. 紧张提问

**概括：** 紧张提问

```json
{
  "emotion": "nervous",
  "intensity": "moderate",
  "social_tone": "gentle",
  "mental_state": [
    "hesitant",
    "uncertain"
  ],
  "communicative_intent": "question",
  "voice_texture": [
    "soft",
    "trembling"
  ],
  "pace": "slightly_slow",
  "pitch": "slightly_high",
  "energy": "low"
}
```

### 050. 紧张确认

**概括：** 紧张确认

```json
{
  "emotion": "nervous",
  "intensity": "mild",
  "social_tone": "reassuring",
  "mental_state": [
    "uncertain"
  ],
  "communicative_intent": "confirm",
  "voice_texture": [
    "soft"
  ],
  "pace": "normal",
  "pitch": "slightly_high",
  "energy": "medium"
}
```

### 051. 紧张告白

**概括：** 紧张告白

```json
{
  "emotion": "nervous",
  "intensity": "strong",
  "social_tone": "intimate",
  "mental_state": [
    "shy",
    "hesitant"
  ],
  "communicative_intent": "confess",
  "voice_texture": [
    "soft",
    "trembling"
  ],
  "pace": "slightly_slow",
  "pitch": "slightly_high",
  "energy": "medium"
}
```

### 052. 惊讶反应

**概括：** 惊讶反应

```json
{
  "emotion": "surprised",
  "intensity": "moderate",
  "social_tone": "casual",
  "mental_state": [
    "confused"
  ],
  "communicative_intent": "question",
  "voice_texture": [
    "bright"
  ],
  "pace": "slightly_fast",
  "pitch": "high",
  "energy": "high"
}
```

### 053. 惊喜确认

**概括：** 惊喜确认

```json
{
  "emotion": "surprised",
  "intensity": "strong",
  "social_tone": "warm",
  "mental_state": [
    "expectant"
  ],
  "communicative_intent": "confirm",
  "voice_texture": [
    "bright",
    "smiling"
  ],
  "pace": "slightly_fast",
  "pitch": "high",
  "energy": "high"
}
```

### 054. 难以置信

**概括：** 难以置信

```json
{
  "emotion": "surprised",
  "intensity": "strong",
  "social_tone": "serious",
  "mental_state": [
    "confused",
    "overwhelmed"
  ],
  "communicative_intent": "question",
  "voice_texture": [
    "trembling"
  ],
  "pace": "slightly_slow",
  "pitch": "high",
  "energy": "high"
}
```

### 055. 厌恶拒绝

**概括：** 厌恶拒绝

```json
{
  "emotion": "disgusted",
  "intensity": "moderate",
  "social_tone": "distant",
  "mental_state": [
    "restrained"
  ],
  "communicative_intent": "reject",
  "voice_texture": [
    "low"
  ],
  "pace": "normal",
  "pitch": "slightly_low",
  "energy": "medium"
}
```

### 056. 厌烦抱怨

**概括：** 厌烦抱怨

```json
{
  "emotion": "disgusted",
  "intensity": "mild",
  "social_tone": "sarcastic",
  "mental_state": [
    "impatient"
  ],
  "communicative_intent": "complain",
  "voice_texture": [
    "low"
  ],
  "pace": "normal",
  "pitch": "normal",
  "energy": "medium"
}
```

### 057. 冷漠陈述

**概括：** 冷漠陈述

```json
{
  "emotion": "cold",
  "intensity": "moderate",
  "social_tone": "distant",
  "mental_state": [
    "restrained"
  ],
  "communicative_intent": "inform",
  "voice_texture": [
    "low"
  ],
  "pace": "normal",
  "pitch": "low",
  "energy": "low"
}
```

### 058. 冷淡拒绝

**概括：** 冷淡拒绝

```json
{
  "emotion": "cold",
  "intensity": "moderate",
  "social_tone": "distant",
  "mental_state": [
    "calm"
  ],
  "communicative_intent": "reject",
  "voice_texture": [
    "low"
  ],
  "pace": "slightly_slow",
  "pitch": "low",
  "energy": "low"
}
```

### 059. 冷静警告

**概括：** 冷静警告

```json
{
  "emotion": "cold",
  "intensity": "moderate",
  "social_tone": "firm",
  "mental_state": [
    "confident",
    "restrained"
  ],
  "communicative_intent": "warn",
  "voice_texture": [
    "deep",
    "low"
  ],
  "pace": "slow",
  "pitch": "low",
  "energy": "medium"
}
```

### 060. 温柔安慰

**概括：** 温柔安慰

```json
{
  "emotion": "neutral",
  "intensity": "moderate",
  "social_tone": "comforting",
  "mental_state": [
    "calm"
  ],
  "communicative_intent": "comfort",
  "voice_texture": [
    "soft"
  ],
  "pace": "slow",
  "pitch": "slightly_low",
  "energy": "low"
}
```

### 061. 温柔鼓励

**概括：** 温柔鼓励

```json
{
  "emotion": "happy",
  "intensity": "mild",
  "social_tone": "warm",
  "mental_state": [
    "hopeful"
  ],
  "communicative_intent": "encourage",
  "voice_texture": [
    "soft",
    "smiling"
  ],
  "pace": "slightly_slow",
  "pitch": "normal",
  "energy": "medium"
}
```

### 062. 温柔道歉

**概括：** 温柔道歉

```json
{
  "emotion": "sad",
  "intensity": "mild",
  "social_tone": "gentle",
  "mental_state": [
    "hesitant"
  ],
  "communicative_intent": "apologize",
  "voice_texture": [
    "soft"
  ],
  "pace": "slow",
  "pitch": "slightly_low",
  "energy": "low"
}
```

### 063. 温柔请求

**概括：** 温柔请求

```json
{
  "emotion": "neutral",
  "intensity": "mild",
  "social_tone": "gentle",
  "mental_state": [
    "hesitant"
  ],
  "communicative_intent": "request",
  "voice_texture": [
    "soft"
  ],
  "pace": "slightly_slow",
  "pitch": "normal",
  "energy": "low"
}
```

### 064. 亲密低语

**概括：** 亲密低语

```json
{
  "emotion": "happy",
  "intensity": "mild",
  "social_tone": "intimate",
  "mental_state": [
    "calm"
  ],
  "communicative_intent": "inform",
  "voice_texture": [
    "whispering",
    "soft"
  ],
  "pace": "slow",
  "pitch": "slightly_low",
  "energy": "very_low"
}
```

### 065. 暧昧试探

**概括：** 暧昧试探

```json
{
  "emotion": "happy",
  "intensity": "moderate",
  "social_tone": "flirty",
  "mental_state": [
    "shy",
    "expectant"
  ],
  "communicative_intent": "question",
  "voice_texture": [
    "soft",
    "breathy"
  ],
  "pace": "slightly_slow",
  "pitch": "normal",
  "energy": "low"
}
```

### 066. 暧昧调侃

**概括：** 暧昧调侃

```json
{
  "emotion": "happy",
  "intensity": "moderate",
  "social_tone": "flirty",
  "mental_state": [
    "confident"
  ],
  "communicative_intent": "tease",
  "voice_texture": [
    "smiling",
    "breathy"
  ],
  "pace": "normal",
  "pitch": "slightly_high",
  "energy": "medium"
}
```

### 067. 害羞告白

**概括：** 害羞告白

```json
{
  "emotion": "happy",
  "intensity": "moderate",
  "social_tone": "intimate",
  "mental_state": [
    "shy",
    "hesitant"
  ],
  "communicative_intent": "confess",
  "voice_texture": [
    "soft",
    "trembling"
  ],
  "pace": "slow",
  "pitch": "slightly_high",
  "energy": "low"
}
```

### 068. 撒娇请求

**概括：** 撒娇请求

```json
{
  "emotion": "happy",
  "intensity": "moderate",
  "social_tone": "cute",
  "mental_state": [
    "expectant"
  ],
  "communicative_intent": "request",
  "voice_texture": [
    "soft",
    "smiling"
  ],
  "pace": "slightly_slow",
  "pitch": "slightly_high",
  "energy": "medium"
}
```

### 069. 撒娇抱怨

**概括：** 撒娇抱怨

```json
{
  "emotion": "annoyed",
  "intensity": "mild",
  "social_tone": "cute",
  "mental_state": [
    "hurt"
  ],
  "communicative_intent": "complain",
  "voice_texture": [
    "soft"
  ],
  "pace": "normal",
  "pitch": "slightly_high",
  "energy": "medium"
}
```

### 070. 俏皮调侃

**概括：** 俏皮调侃

```json
{
  "emotion": "happy",
  "intensity": "moderate",
  "social_tone": "teasing",
  "mental_state": [
    "confident"
  ],
  "communicative_intent": "tease",
  "voice_texture": [
    "smiling",
    "bright"
  ],
  "pace": "slightly_fast",
  "pitch": "slightly_high",
  "energy": "high"
}
```

### 071. 轻微讽刺

**概括：** 轻微讽刺

```json
{
  "emotion": "annoyed",
  "intensity": "mild",
  "social_tone": "sarcastic",
  "mental_state": [
    "confident"
  ],
  "communicative_intent": "challenge",
  "voice_texture": [
    "low"
  ],
  "pace": "slightly_slow",
  "pitch": "normal",
  "energy": "medium"
}
```

### 072. 强烈讽刺

**概括：** 强烈讽刺

```json
{
  "emotion": "angry",
  "intensity": "moderate",
  "social_tone": "sarcastic",
  "mental_state": [
    "impatient"
  ],
  "communicative_intent": "challenge",
  "voice_texture": [
    "low"
  ],
  "pace": "normal",
  "pitch": "slightly_low",
  "energy": "medium"
}
```

### 073. 专业客服

**概括：** 专业客服

```json
{
  "emotion": "neutral",
  "intensity": "mild",
  "social_tone": "professional",
  "mental_state": [
    "calm",
    "confident"
  ],
  "communicative_intent": "inform",
  "voice_texture": [
    "normal"
  ],
  "pace": "normal",
  "pitch": "normal",
  "energy": "medium"
}
```

### 074. 客服安抚

**概括：** 客服安抚

```json
{
  "emotion": "neutral",
  "intensity": "moderate",
  "social_tone": "reassuring",
  "mental_state": [
    "calm"
  ],
  "communicative_intent": "reassure",
  "voice_texture": [
    "soft"
  ],
  "pace": "slightly_slow",
  "pitch": "normal",
  "energy": "medium"
}
```

### 075. 客服道歉

**概括：** 客服道歉

```json
{
  "emotion": "sad",
  "intensity": "mild",
  "social_tone": "professional",
  "mental_state": [
    "calm"
  ],
  "communicative_intent": "apologize",
  "voice_texture": [
    "soft"
  ],
  "pace": "slightly_slow",
  "pitch": "normal",
  "energy": "low"
}
```

### 076. 客服解释

**概括：** 客服解释

```json
{
  "emotion": "neutral",
  "intensity": "mild",
  "social_tone": "professional",
  "mental_state": [
    "calm"
  ],
  "communicative_intent": "explain",
  "voice_texture": [
    "normal"
  ],
  "pace": "normal",
  "pitch": "normal",
  "energy": "medium"
}
```

### 077. 正式播报

**概括：** 正式播报

```json
{
  "emotion": "neutral",
  "intensity": "mild",
  "social_tone": "serious",
  "mental_state": [
    "confident"
  ],
  "communicative_intent": "inform",
  "voice_texture": [
    "deep"
  ],
  "pace": "normal",
  "pitch": "slightly_low",
  "energy": "medium"
}
```

### 078. 新闻紧急播报

**概括：** 新闻紧急播报

```json
{
  "emotion": "neutral",
  "intensity": "strong",
  "social_tone": "serious",
  "mental_state": [
    "confident"
  ],
  "communicative_intent": "warn",
  "voice_texture": [
    "powerful"
  ],
  "pace": "slightly_fast",
  "pitch": "normal",
  "energy": "high"
}
```

### 079. 悬疑旁白

**概括：** 悬疑旁白

```json
{
  "emotion": "afraid",
  "intensity": "mild",
  "social_tone": "serious",
  "mental_state": [
    "suspicious"
  ],
  "communicative_intent": "inform",
  "voice_texture": [
    "low",
    "breathy"
  ],
  "pace": "slow",
  "pitch": "low",
  "energy": "low"
}
```

### 080. 恐怖旁白

**概括：** 恐怖旁白

```json
{
  "emotion": "afraid",
  "intensity": "strong",
  "social_tone": "serious",
  "mental_state": [
    "overwhelmed"
  ],
  "communicative_intent": "inform",
  "voice_texture": [
    "whispering",
    "trembling"
  ],
  "pace": "very_slow",
  "pitch": "low",
  "energy": "very_low"
}
```

### 081. 温暖旁白

**概括：** 温暖旁白

```json
{
  "emotion": "happy",
  "intensity": "mild",
  "social_tone": "warm",
  "mental_state": [
    "calm"
  ],
  "communicative_intent": "inform",
  "voice_texture": [
    "soft"
  ],
  "pace": "slow",
  "pitch": "normal",
  "energy": "low"
}
```

### 082. 史诗旁白

**概括：** 史诗旁白

```json
{
  "emotion": "neutral",
  "intensity": "strong",
  "social_tone": "serious",
  "mental_state": [
    "confident"
  ],
  "communicative_intent": "inform",
  "voice_texture": [
    "deep",
    "powerful"
  ],
  "pace": "slow",
  "pitch": "low",
  "energy": "high"
}
```

### 083. 深夜电台

**概括：** 深夜电台

```json
{
  "emotion": "neutral",
  "intensity": "mild",
  "social_tone": "intimate",
  "mental_state": [
    "calm"
  ],
  "communicative_intent": "inform",
  "voice_texture": [
    "soft",
    "breathy"
  ],
  "pace": "slow",
  "pitch": "slightly_low",
  "energy": "very_low"
}
```

### 084. 睡前故事

**概括：** 睡前故事

```json
{
  "emotion": "happy",
  "intensity": "mild",
  "social_tone": "gentle",
  "mental_state": [
    "calm"
  ],
  "communicative_intent": "inform",
  "voice_texture": [
    "soft"
  ],
  "pace": "very_slow",
  "pitch": "slightly_low",
  "energy": "very_low"
}
```

### 085. 儿童故事兴奋

**概括：** 儿童故事兴奋

```json
{
  "emotion": "excited",
  "intensity": "strong",
  "social_tone": "cute",
  "mental_state": [
    "expectant"
  ],
  "communicative_intent": "inform",
  "voice_texture": [
    "bright"
  ],
  "pace": "slightly_fast",
  "pitch": "high",
  "energy": "high"
}
```

### 086. 游戏NPC欢迎

**概括：** 游戏NPC欢迎

```json
{
  "emotion": "happy",
  "intensity": "moderate",
  "social_tone": "warm",
  "mental_state": [
    "confident"
  ],
  "communicative_intent": "invite",
  "voice_texture": [
    "bright"
  ],
  "pace": "normal",
  "pitch": "normal",
  "energy": "high"
}
```

### 087. 游戏NPC警告

**概括：** 游戏NPC警告

```json
{
  "emotion": "angry",
  "intensity": "moderate",
  "social_tone": "firm",
  "mental_state": [
    "confident"
  ],
  "communicative_intent": "warn",
  "voice_texture": [
    "deep",
    "powerful"
  ],
  "pace": "normal",
  "pitch": "low",
  "energy": "high"
}
```

### 088. 反派威胁

**概括：** 反派威胁

```json
{
  "emotion": "cold",
  "intensity": "strong",
  "social_tone": "distant",
  "mental_state": [
    "confident"
  ],
  "communicative_intent": "warn",
  "voice_texture": [
    "deep",
    "low"
  ],
  "pace": "slow",
  "pitch": "low",
  "energy": "medium"
}
```

### 089. 反派嘲讽

**概括：** 反派嘲讽

```json
{
  "emotion": "happy",
  "intensity": "mild",
  "social_tone": "sarcastic",
  "mental_state": [
    "confident"
  ],
  "communicative_intent": "challenge",
  "voice_texture": [
    "low",
    "smiling"
  ],
  "pace": "slightly_slow",
  "pitch": "slightly_low",
  "energy": "medium"
}
```

### 090. 英雄鼓舞

**概括：** 英雄鼓舞

```json
{
  "emotion": "excited",
  "intensity": "strong",
  "social_tone": "firm",
  "mental_state": [
    "confident",
    "hopeful"
  ],
  "communicative_intent": "encourage",
  "voice_texture": [
    "powerful"
  ],
  "pace": "slightly_fast",
  "pitch": "normal",
  "energy": "very_high"
}
```

### 091. 老师讲解

**概括：** 老师讲解

```json
{
  "emotion": "neutral",
  "intensity": "mild",
  "social_tone": "professional",
  "mental_state": [
    "calm",
    "confident"
  ],
  "communicative_intent": "explain",
  "voice_texture": [
    "normal"
  ],
  "pace": "slightly_slow",
  "pitch": "normal",
  "energy": "medium"
}
```

### 092. 老师鼓励

**概括：** 老师鼓励

```json
{
  "emotion": "happy",
  "intensity": "mild",
  "social_tone": "warm",
  "mental_state": [
    "hopeful"
  ],
  "communicative_intent": "encourage",
  "voice_texture": [
    "soft",
    "smiling"
  ],
  "pace": "normal",
  "pitch": "normal",
  "energy": "medium"
}
```

### 093. 老师提醒

**概括：** 老师提醒

```json
{
  "emotion": "neutral",
  "intensity": "moderate",
  "social_tone": "firm",
  "mental_state": [
    "calm"
  ],
  "communicative_intent": "warn",
  "voice_texture": [
    "normal"
  ],
  "pace": "normal",
  "pitch": "slightly_low",
  "energy": "medium"
}
```

### 094. 主持人开场

**概括：** 主持人开场

```json
{
  "emotion": "excited",
  "intensity": "moderate",
  "social_tone": "professional",
  "mental_state": [
    "confident"
  ],
  "communicative_intent": "invite",
  "voice_texture": [
    "bright",
    "powerful"
  ],
  "pace": "slightly_fast",
  "pitch": "slightly_high",
  "energy": "high"
}
```

### 095. 主持人收尾

**概括：** 主持人收尾

```json
{
  "emotion": "happy",
  "intensity": "moderate",
  "social_tone": "warm",
  "mental_state": [
    "calm"
  ],
  "communicative_intent": "thank",
  "voice_texture": [
    "smiling"
  ],
  "pace": "normal",
  "pitch": "normal",
  "energy": "medium"
}
```

### 096. 朋友安慰

**概括：** 朋友安慰

```json
{
  "emotion": "sad",
  "intensity": "mild",
  "social_tone": "comforting",
  "mental_state": [
    "calm"
  ],
  "communicative_intent": "comfort",
  "voice_texture": [
    "soft"
  ],
  "pace": "slow",
  "pitch": "slightly_low",
  "energy": "low"
}
```

### 097. 朋友吐槽

**概括：** 朋友吐槽

```json
{
  "emotion": "annoyed",
  "intensity": "mild",
  "social_tone": "casual",
  "mental_state": [
    "impatient"
  ],
  "communicative_intent": "complain",
  "voice_texture": [
    "normal"
  ],
  "pace": "slightly_fast",
  "pitch": "normal",
  "energy": "medium"
}
```

### 098. 朋友鼓励

**概括：** 朋友鼓励

```json
{
  "emotion": "happy",
  "intensity": "moderate",
  "social_tone": "casual",
  "mental_state": [
    "confident",
    "hopeful"
  ],
  "communicative_intent": "encourage",
  "voice_texture": [
    "bright"
  ],
  "pace": "normal",
  "pitch": "normal",
  "energy": "high"
}
```

### 099. 朋友调侃

**概括：** 朋友调侃

```json
{
  "emotion": "happy",
  "intensity": "moderate",
  "social_tone": "teasing",
  "mental_state": [
    "confident"
  ],
  "communicative_intent": "tease",
  "voice_texture": [
    "smiling"
  ],
  "pace": "slightly_fast",
  "pitch": "slightly_high",
  "energy": "high"
}
```

### 100. 认真道歉

**概括：** 认真道歉

```json
{
  "emotion": "sad",
  "intensity": "moderate",
  "social_tone": "serious",
  "mental_state": [
    "hurt",
    "restrained"
  ],
  "communicative_intent": "apologize",
  "voice_texture": [
    "soft"
  ],
  "pace": "slow",
  "pitch": "slightly_low",
  "energy": "low"
}
```

## 4. 映射成 BytePlus `context_texts` 的建议

把 JSON 先转换成 1–3 句自然语言 voice direction，不建议机械逐字段朗读。

例如：

```text
用温柔而克制的悲伤语气说，带着受伤但仍想安慰对方的感觉；声音轻柔、略微发颤，语速较慢、音调略低，整体能量偏低。
```

建议优先级：`emotion/intensity` → `social_tone` → `mental_state/intent` → `voice_texture` → `pace/pitch/energy`。发生冲突时，优先保证语义与社交意图，其次才是声学参数。