# Concierge Audio Studio

面向 Unitree G1 的 Flask + DaisyUI Text-to-Speech Studio，当前同时支持
MiniMax 与 BytePlus Seed Speech。所有成功返回的音频都会在服务端统一为并校验为
**16 kHz、单声道、16-bit PCM WAV**。

开发状态、请求映射、真实服务证据和已知限制见
[`doc/current_state.md`](doc/current_state.md)。

## 功能

### MiniMax

- 保留 MiniMax Studio 风格的编辑器、音色、模型、语言、Speed、Pitch、Volume
- 选中文字添加八种不同颜色的 Emotion 标签；点击标签可编辑或移除，文本不丢失
- Pause、Speech 2.8 Sound Tag、Voice Modifier 与四种 Sound Effect
- 分段 Emotion 由后端拆成干净文本请求，标签名称不会被朗读
- Long Text 异步创建、轮询、试听和下载

### BytePlus

- 与 MiniMax 页面一致的 Studio 主体结构，通过顶部导航切换 Provider
- Emotion 弹层包含 9 类控制：情绪、强度、社交语气、心理状态、沟通意图、
  声音质感、语速、音高和能量
- 150 个典型风格预设，按一级场景、二级场景选择；高级设置默认收起，可展开微调
- 选中文字应用风格；点击已有标签重新编辑，或移除标签并保留原文
- 风格配置由服务端转换为 BytePlus `context_texts` 自然语言 prompt，绝不会写入
  `text` 或被朗读
- 内置当前官方 TTS 2.0 音色目录 151 个，其中中文 23 个、英文 54 个；支持搜索、
  语言筛选和手动 Voice ID
- BytePlus 流式 PCM 响应由服务端封装成标准 WAV，再执行 G1 音频校验

## 安装与启动

项目使用 `uv` 管理 Python 3.12、虚拟环境和锁定依赖：

```powershell
cd C:\Users\rfouy\workspace\services\concierge-audio
uv sync --locked
Copy-Item .env.example .env
uv run python -m app.main
```

打开 <http://127.0.0.1:5000>。程序入口只有 `app.main`，没有 `run.py`。

在 `.env` 中按需填写：

```dotenv
MINIMAX_API_KEY=...
BYTEPLUS_API_KEY=...
```

Key 只在 Flask 服务端读取，不会发送给浏览器。其余 endpoint、超时、Resource ID
等配置见 [`.env.example`](.env.example)。

## API

生成的 WAV 和文本信息保存在 `output/tts/minimax/`、`output/tts/byteplus/`。
页面历史列表可播放、查看文本和时长、下载及删除；刷新页面或重启服务后仍然保留。
删除会同时移除 WAV 及其元数据。更新前仅存在浏览器临时 URL 的音频无法自动恢复。

规范化路由：

```text
GET  /api/minimax/health
GET  /api/minimax/voices
POST /api/minimax/tts
POST /api/minimax/tts/async
GET  /api/minimax/tts/async/<task_id>

GET  /api/byteplus/health
GET  /api/byteplus/voices
GET  /api/byteplus/presets
POST /api/byteplus/prompt-preview
POST /api/byteplus/tts
```

旧 MiniMax `/api/tts`、`/api/voices` 等路由继续保留，避免破坏现有调用方。
浏览器不能覆盖采样率、格式或声道；这些参数由服务端固定。

## 测试

普通测试不会调用外部服务或消耗额度：

```powershell
uv run python -m unittest discover -s tests -v
```

真实服务测试必须显式运行：

```powershell
uv run python -m tests.minimax.live_minimax_smoke
uv run python -m tests.minimax.live_minimax_async_smoke
uv run python -m tests.byteplus.live_byteplus_smoke
```

它们会消耗对应服务的 credit，并把脱敏 JSON 与 16 kHz WAV 保存到 `debug/`。

## 代码结构

```text
app/
  main.py                       Flask 入口与组合根
  api_tts/
    service.py                  API Blueprint 入口
    routes/
      api_minimax.py
      api_byteplus.py
  ui_tts/
    minimax/ui_minimax.py
    byteplus/ui_byteplus.py
    templates/                  共用模板目录
    static/                     共用静态资源目录
component/
  common/                       Provider 无关模型
  minimax/                      MiniMax 业务流程
  byteplus/                     BytePlus 业务流程、prompt 映射、预设与音色
util/
  minimax_tts_helper.py         MiniMax HTTP 适配
  byteplus_tts_helper.py        BytePlus HTTP/流解析
  wav_helper.py                 PCM 封装、WAV 校验与拼接
config/
  system_config.py
  minimax_config.py
  byteplus_config.py
  settings.py                   配置组合入口
tests/
  minimax/
  byteplus/
  common/
```

依赖方向保持为 `app -> component -> util`。
