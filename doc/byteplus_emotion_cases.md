# BytePlus 语气对比测试

先重启服务：`uv run python -m app.main`。旧标签保留旧参数，刷新页面并重新选择预设。

## 一键生成四份对照

先预览请求（不花费额度）：

```powershell
uv run python -X utf8 -m tests.byteplus.compare_emotions
```

实际生成（4 次付费合成）：

```powershell
uv run python -X utf8 -m tests.byteplus.compare_emotions --generate
```

固定 Vivi 音色、语速 0、音量 0、同一句中文，仅改变语气。
四份 WAV 自动出现在 BytePlus History，并保存到 output/tts/byteplus。
同名 JSON 中的 synthesis_details 保存实际分段、语气提示及 request ID，不保存密钥。

## 手动复现

每次仅使用下面这一句，全文选择后应用预设；基线不加标签。

> 来，靠近一点。看着我，我们再试一次，现在就开始。

| 用例 | 分类路径 | 重点听什么 |
| --- | --- | --- |
| 无语气基线 | 不加标签 | 普通叙述 |
| 朋友鼓励 | 情感陪伴 → 鼓励打气 | 明亮、支持感、鼓励词重音 |
| 亲密低语 | 亲密互动 → 暧昧私语 | 耳语气声、轻柔、慢速，不能仅音量变小 |
| 不耐烦催促 | 冲突沟通 → 催促警告 | 急促、行动词重音、干脆句尾 |

保持播放器音量一致。建议每种重复 2 次；若仅响度变化，没有发声和节奏差异，则不能算语气控制通过。
生成成功及单元测试通过不代表主观听感达标。

英文对照可用 --text "Come closer. Look at me. Let's try again. Start now."，
并用 --voice-id 指定界面中可用的英文音色 ID；不要在同组对照中同时改变音色和语气。
