# Concierge Audio 当前状态

更新时间：2026-09-21

## 最新变更：BytePlus 场景预设面板

- 语气修复：朋友鼓励、亲密低语、不耐烦催促加入场景指令，耳语改为明确发声要求；去掉全局「不要过度夸张」约束。
- 新生成 BytePlus 历史 JSON 的 synthesis_details 保留实际分段、prompt、音色、语速、音量及 request ID，不记录密钥；旧记录无法补回。
- 对照工具：`uv run python -X utf8 -m tests.byteplus.compare_emotions` 默认仅预览；加 `--generate` 合成 4 个同文本同音色对照并保存到 History。说明见 `doc/byteplus_emotion_cases.md`。
- 本次验证：15 项 BytePlus 单元测试通过；实际调用 4 次生成无语气/朋友鼓励/亲密低语/不耐烦催促对照，均成功。听感需人工试听确认，不能以请求成功或时长差异代替情绪验收。
- 实测发现另一份旧 app/main.py 进程占用 5000，首次 4 次请求落入旧服务；已重启本项目服务，再调用 4 次。合计 8 次付费合成，旧文件保留。有效新对照 ID：基线 dd6331dae7ea4170bd2dae36f4235cc4、鼓励 6825c2f90245447193bd382104e9569e、低语 876d5cf88e8c4278882615876507d08e、催促 43331a98ab6b4dedab789c0b15c273d9。均验证 16 kHz/mono/16-bit，且 JSON 有实际 prompt。
- 正文语气标签与预设按钮按二级分类稳定配色（63 类），正文使用对应浅底色；同一二级分类同色，无场景的旧标签仍按 emotion 配色。
- Emotion 面板按一级分类 → 二级分类 → preset 选择，共 150 个预设（原有 100 + 新增 50）。
- 新选中文字默认使用「接待服务 → 身份介绍 → 自我介绍」；编辑已有标签时恢复原有分类及参数。
- 高级设置默认收起，每次打开面板都保持收起；手动修改后标记为自定义。
- `config/byteplus_config.py` 保存分类、默认 ID、新增预设和场景 prompt；`config/byteplus_presets.json` 保存原有预设参数，原 component 数据文件已迁移。
- `preset_id` 随 style 保存，后端将配置中的场景提示与九维参数合成为 context prompt，不混入朗读文本。
- 浏览器已验证默认选择、分类联动、预设应用、自定义保存及重新打开回显；没有调用付费合成接口。
- 验证：BytePlus 专项 14 项测试通过，覆盖全部 150 个预设、默认路径、无效 ID 拒绝、场景提示与朗读文本分离；浏览器无 console error。

## 目标与不变量

项目提供接近官方 Studio 交互的 Flask + DaisyUI TTS 界面，当前包含 MiniMax 和
BytePlus 两个 Provider，用于生成可在 Unitree G1 上播放的语音。

所有返回给浏览器的音频必须通过服务端校验：

- WAV
- 16 kHz
- 单声道
- 16-bit PCM

浏览器不能提交或覆盖采样率、声道和最终输出格式。

## 程序入口与架构

唯一程序入口：

```powershell
uv run python -m app.main
```

没有 `run.py`。依赖由 `uv` 管理，Python 版本固定为 3.12，依赖声明在
`pyproject.toml`，锁文件为 `uv.lock`。依赖方向保持为：

```text
app -> component -> util
```

当前主要结构：

```text
app/
  main.py
  context.py
  api_tts/
    service.py
    routes/api_minimax.py
    routes/api_byteplus.py
  ui_tts/
    minimax/ui_minimax.py
    byteplus/ui_byteplus.py
    templates/
    static/
component/
  common/models.py
  minimax/models.py
  minimax/tts_service.py
  byteplus/models.py
  byteplus/tts_service.py
  byteplus/prompt_mapper.py
  byteplus/presets.py
  byteplus/voices.py
util/
  minimax_tts_helper.py
  byteplus_tts_helper.py
  wav_helper.py
config/
  system_config.py
  minimax_config.py
  byteplus_config.py
  settings.py
tests/
  minimax/
  byteplus/
  common/
```

`app/api_tts/service.py` 是 API Blueprint 的统一入口。规范化路径为
`/api/minimax/*` 和 `/api/byteplus/*`；原 `/api/tts`、`/api/voices` 等 MiniMax
路由作为兼容别名保留。

## MiniMax 状态

MiniMax 页面位于 `/`，现有功能保持不变：

- Speech 2.8、2.6、02、01 模型
- 账户音色加载、搜索、语言筛选和手动 Voice ID
- Speed、Pitch、Volume、全局 Emotion
- 八种不同颜色的分段 Emotion 标签
- 点击现有标签重新编辑或移除；移除后原文本保留
- Pause 0.25、0.5、1.0、1.5 秒以及 0.01–99.99 秒自定义值
- Speech 2.8 的 19 个 Sound Tag
- Voice Modifier 与 `spacious_echo`、`auditorium_echo`、`lofi_telephone`、
  `robotic` 四种效果
- Long Text 异步创建、轮询、试听和下载

公开 `POST /v1/t2a_v2` 不解释 MiniMax Studio 私有网关使用的
`{happy}...{/happy}` 标记，而会把标签名称朗读出来。当前实现因此始终提交纯文本：

```json
{
  "text": "你好，很高兴见到你。可是我现在要离开了。",
  "segments": [
    {"text": "你好，很高兴见到你。", "emotion": "happy"},
    {"text": "可是我现在要离开了。", "emotion": "sad"}
  ]
}
```

后端校验所有 segment 拼接后与 `text` 完全一致，再逐段用相应
`voice_setting.emotion` 请求并在 PCM 层拼接。UI 的 `neutral` 映射为 API 的
`calm`。分段 Emotion 当前不支持 Long Text。

MiniMax 服务端固定参数：

```json
{
  "sample_rate": 16000,
  "format": "wav",
  "channel": 1
}
```

### 已保留的真实 MiniMax 验证

2026-09-19 已验证：

- Happy + Pause：16 kHz、Mono、16-bit，1.899 s
- Sound Tag + Robotic Modifier：16 kHz、Mono、16-bit，2.043 s
- Speech 2.8 + Fluent：16 kHz、Mono、16-bit，0.801 s
- 中文 Happy + Sad 结构化分段：两次纯文本请求、PCM 拼接，4.50 s
- Async direct text 与浏览器轮询：TAR 中提取 WAV 后校验通过

证据保存在本机 `debug/minimax_live/` 与 `debug/minimax_async_live/`，目录已由
`.gitignore` 忽略。

## BytePlus 状态

BytePlus 页面位于 `/byteplus`。页面与 MiniMax 使用同一套 Studio 主体结构，顶部
Provider 导航负责切换。
BytePlus 历史与 MiniMax 一样放在右侧 Settings / History 标签页，带历史数量，
使用相同历史卡片提供时长、原文、播放、下载和删除；不再放在页面底部。

右侧 Speech Rate 与 Loudness 已统一采用 MiniMax 的标题、数值输入框和 DaisyUI
滑杆布局；支持双向同步，范围为 -50 到 100，0 为正常值。浏览器已验证数值修改和布局。

### Emotion / Voice Direction 交互

选择文本后打开 Voice Direction panel。可配置 9 类字段：

1. `emotion`
2. `intensity`
3. `social_tone`
4. `mental_state`（多选）
5. `communicative_intent`
6. `voice_texture`（多选）
7. `pace`
8. `pitch`
9. `energy`

`doc/byteplus_tts_prompt_schema_100_examples.md` 中的 100 个典型组合已经转成 UI
预设，支持搜索、一键载入与继续微调。`component/byteplus/prompt_mapper.py` 根据用户
提供的 Python 规则将配置转成自然语言风格 prompt。浏览器会调用
`POST /api/byteplus/prompt-preview` 显示服务端实际映射结果。

应用风格后，编辑器保存结构化 `segments`。风格标签只显示在 DOM 与 JSON 中，不会写入
可朗读文本。点击标签可重开 panel；Remove 只移除风格，保留原文字。

### 音色

已从官方 TTS 2.0 音色表整理出 151 个 Voice ID：

- 中文：23
- 英文：54
- 其余语言：74

UI 支持搜索、语言筛选、性别/类别信息显示和手动 Voice ID。真实账号最终可用范围仍取决
于 BytePlus 账号区域、套餐与音色权限；后端会把无权限错误翻译成明确提示。

### BytePlus 请求格式

当前调用：

```text
POST https://voice.ap-southeast-1.bytepluses.com/api/v3/tts/unidirectional
X-Api-Key: <BYTEPLUS_API_KEY>
X-Api-Resource-Id: seed-tts-2.0
X-Api-Request-Id: <UUID>
Content-Type: application/json
```

核心请求结构：

```json
{
  "user": {"uid": "concierge-audio"},
  "req_params": {
    "text": "你好，很高兴见到你。",
    "speaker": "zh_female_vv_uranus_bigtts",
    "audio_params": {
      "format": "pcm",
      "sample_rate": 16000,
      "speech_rate": 0,
      "loudness_rate": 0
    },
    "additions": "{\"context_texts\":[\"用开心、友好的语气说。\"]}"
  }
}
```

`additions` 是 JSON 编码后的字符串，`context_texts` 是其中的数组。当前仅写入一个
prompt，因为 TTS 2.0 只使用第一个 context。风格 prompt 与 `text` 分离，不会被朗读。

官方流式响应会连续返回 JSON 对象：`code=0` 携带 Base64 PCM，
`code=20000000` 表示结束。适配器支持 JSON 对象和 UTF-8 字符跨网络 chunk 分割。
由于流式 WAV 可能产生多个 header，项目请求 16 kHz PCM，再由 `WavHelper.from_pcm()`
封装为一个标准 WAV。

有多个不同风格片段时，后端逐段请求 BytePlus，验证并拼接 WAV；相邻且配置相同的片段会
先合并以减少请求次数。当前最多 50 段。

### BytePlus API

```text
GET  /api/byteplus/health
GET  /api/byteplus/voices
GET  /api/byteplus/presets
POST /api/byteplus/prompt-preview
POST /api/byteplus/tts
```

截至本次记录，BytePlus 请求构造、碎片化流解析、prompt 映射、100 个 preset、151 个
voice、分段拼接和 Flask API 均已通过 mock 测试。浏览器实测已覆盖：打开 panel、加载
预设、更新 prompt、应用/重开/移除标签、原文保留、151 个音色加载、中文 23 个与英文
54 个筛选；控制台没有 warning/error。实测期间还修复了 preset 重绘后 click 冒泡导致
panel 意外关闭的问题。

2026-09-20 实际生成发现：上游会发送 `code=0, data=null, sentence={...}` 的句子
元数据，旧解析器误判为缺失音频并返回 502。已修复为跳过该元数据，保留最终完成和音频
校验，并把真实响应形态加入回归测试。真实带风格中文 smoke 已通过：3.814 秒、16 kHz、
Mono、16-bit WAV。证据：`debug/byteplus_live/20260920-000909/result.json` 与
`styled_chinese.wav`。显式脚本为 `tests/byteplus/live_byteplus_smoke.py`。

## 配置

项目根目录 `.env` 或 `app/.env` 可包含：

```dotenv
MINIMAX_API_KEY=...
BYTEPLUS_API_KEY=...
BYTEPLUS_TTS_RESOURCE_ID=seed-tts-2.0
BYTEPLUS_TTS_USER_ID=concierge-audio
```

配置代码按系统、MiniMax、BytePlus 分开，最后由 `config/settings.py` 组合。API Key
不会返回浏览器，也不会写入报告。

## 测试与验证

普通测试：

```powershell
uv run python -m unittest discover -s tests -v
```

当前结果：60 项全部通过。另已通过 `uv sync --locked`、Python `compileall`、
`node --check`（MiniMax 与 BytePlus JavaScript）以及本地浏览器交互检查。

真实测试必须显式执行，会消耗对应 credit：

```powershell
uv run python -m tests.minimax.live_minimax_smoke
uv run python -m tests.minimax.live_minimax_async_smoke
uv run python -m tests.byteplus.live_byteplus_smoke
```

MiniMax async 脚本可附带已有 Task ID，只做查询与验证：

```powershell
uv run python -m tests.minimax.live_minimax_async_smoke <task_id>
```

## 已知限制

- MiniMax 同步文本上限为 9,999 字符；Long Text 使用异步接口。
- MiniMax Long Text 暂不支持分段 Emotion。
- MiniMax 或 BytePlus 分段风格都会产生多次上游请求，额度、延迟和失败概率随实际片段数
  增加。
- BytePlus 音色目录是静态官方快照，账号能否使用某音色仍由服务端权限决定。
- BytePlus 已完成真实账号 credit smoke test，尚未完成 Unitree G1 实机播放验证。
- History 已持久化在 `output/tts/minimax/` 与 `output/tts/byteplus/`，每条包含 WAV 和
  JSON 元数据（原文、音色、时长、时间）。两页读取服务器历史，支持播放、下载和确认删除。
  MiniMax 异步任务保存原文并按任务去重。历史、下载和删除均按 Provider 隔离。
  已通过临时目录测试验证应用重建后恢复、下载字节一致、删除文件、异步去重和非法路径拒绝。
- 当前为 Flask 开发服务器，尚未配置生产 WSGI。

## 下一步

1. 后续变更按需运行 BytePlus live smoke，保留 `debug/byteplus_live/` 证据。
2. 在 Unitree G1 实际播放 MiniMax 与 BytePlus 生成的 16 kHz WAV，并保留设备日志。
