"use strict";

const STYLE_OPTIONS = {
  emotion: {
    neutral: "平静", happy: "开心", excited: "兴奋", relieved: "如释重负",
    sad: "悲伤", disappointed: "失望", hurt: "受伤 / 委屈", angry: "生气",
    annoyed: "不耐烦", afraid: "害怕", nervous: "紧张", surprised: "惊讶",
    disgusted: "厌恶", cold: "冷淡",
  },
  intensity: { subtle: "非常克制", mild: "轻微", moderate: "适中", strong: "明显", intense: "强烈" },
  social_tone: {
    neutral: "自然", gentle: "温柔", warm: "温暖亲切", intimate: "亲密",
    flirty: "暧昧", cute: "撒娇感", comforting: "安慰", reassuring: "让人安心",
    teasing: "俏皮调侃", sarcastic: "略带讽刺", firm: "坚定", serious: "认真严肃",
    argumentative: "争辩", distant: "疏离冷淡", professional: "专业", casual: "自然随意",
  },
  mental_state: {
    calm: "平静", hesitant: "犹豫", shy: "害羞", expectant: "期待", uncertain: "不确定",
    restrained: "克制", hurt: "受伤", exhausted: "疲惫", desperate: "绝望",
    heartbroken: "心碎", confident: "自信", impatient: "不耐烦", embarrassed: "尴尬",
    confused: "困惑", suspicious: "怀疑", resigned: "无奈接受", hopeful: "希望",
    overwhelmed: "情绪压不住",
  },
  communicative_intent: {
    inform: "传达信息", reassure: "让对方安心", comfort: "安慰", encourage: "鼓励",
    persuade: "劝说", question: "询问", confirm: "确认", warn: "提醒 / 警告",
    apologize: "道歉", thank: "感谢", complain: "抱怨", tease: "逗对方",
    confess: "告白", reject: "拒绝", request: "请求", explain: "解释",
    challenge: "挑战", invite: "邀请",
  },
  voice_texture: {
    normal: "自然", soft: "轻柔", deep: "低沉", low: "偏低", bright: "明亮",
    hoarse: "沙哑", breathy: "气声", trembling: "发颤", tearful: "哭腔",
    whispering: "耳语", powerful: "有力量", weak: "虚弱", tired: "疲惫", smiling: "笑意",
  },
  pace: { very_slow: "很慢", slow: "较慢", slightly_slow: "稍慢", normal: "自然", slightly_fast: "稍快", fast: "较快" },
  pitch: { low: "偏低", slightly_low: "略低", normal: "自然", slightly_high: "略高", high: "偏高" },
  energy: { very_low: "很低", low: "偏低", medium: "自然", high: "较高", very_high: "很高" },
};

const EMOTION_COLORS = {
  neutral: ["#8b94a7", "rgba(139,148,167,.15)"], happy: ["#e8ad2f", "rgba(232,173,47,.16)"],
  excited: ["#ef7c34", "rgba(239,124,52,.15)"], relieved: ["#4da48b", "rgba(77,164,139,.15)"],
  sad: ["#5a7fbf", "rgba(90,127,191,.16)"], disappointed: ["#7181a8", "rgba(113,129,168,.16)"],
  hurt: ["#8a6fa8", "rgba(138,111,168,.16)"], angry: ["#c84c4c", "rgba(200,76,76,.16)"],
  annoyed: ["#b9674c", "rgba(185,103,76,.16)"], afraid: ["#7a6c9d", "rgba(122,108,157,.16)"],
  nervous: ["#8f72b8", "rgba(143,114,184,.16)"], surprised: ["#f2994a", "rgba(242,153,74,.16)"],
  disgusted: ["#6e8b5e", "rgba(110,139,94,.16)"], cold: ["#547f91", "rgba(84,127,145,.16)"],
};

const DEFAULT_STYLE = {
  emotion: "neutral", intensity: "subtle", social_tone: "neutral", mental_state: ["calm"],
  communicative_intent: "inform", voice_texture: ["normal"], pace: "normal", pitch: "normal", energy: "medium",
};

// Keep this order stable so existing subcategories retain their colors.
const COLORED_SUBCATEGORIES = [
  "咨询说明", "引导配合", "安抚确认", "闲聊分享", "邀请致谢", "喜讯动员", "开场邀请",
  "心意告白", "释怀告别", "脱险回应", "低落倾诉", "共情安慰", "道歉修复", "质问争辩",
  "不满抱怨", "冷淡回应", "不舍挽留", "催促警告", "拒绝交流", "恐惧不安", "紧急求助",
  "犹豫提问", "惊讶确认", "鼓励打气", "暧昧私语", "撒娇请求", "朋友玩笑", "讽刺反驳",
  "服务致歉", "通知播报", "悬疑恐怖", "温暖叙事", "史诗英雄", "儿童故事", "游戏角色",
  "反派演绎", "知识讲解", "教学互动", "结束致谢", "迎宾接待", "身份介绍", "等待交接",
  "服务收尾", "指令确认", "执行进度", "完成反馈", "异常恢复", "对话衔接", "澄清理解",
  "兴趣探索", "关怀问候", "肯定支持", "放松陪伴", "分步教学", "启发互动", "纠错反馈",
  "展馆导览", "安全提醒", "紧急指引", "纪实解说", "趣味演绎", "清晰慢读", "语言学习",
];

function styleColors(style, presetId) {
  const preset = state.presets.find((item) => item.id === presetId);
  const index = COLORED_SUBCATEGORIES.indexOf(preset?.subcategory);
  if (index >= 0) {
    const hue = (215 + index * 137.508) % 360;
    return [`hsl(${hue} 60% ${index % 2 ? 32 : 40}%)`, `hsl(${hue} 65% 93%)`];
  }
  return EMOTION_COLORS[style.emotion] || EMOTION_COLORS.neutral;
}

const state = {
  selectionRange: null,
  editingSegment: null,
  selectedPresetId: null,
  selectedPresetName: null,
  defaultPresetId: null,
  customized: false,
  presets: [],
  voices: [],
  voiceLanguage: "all",
  selectedVoice: null,
  promptTimer: null,
  audioUrl: null,
  toastTimer: null,
};

const byId = (id) => document.getElementById(id);

document.addEventListener("DOMContentLoaded", () => {
  populateSelect("style-emotion", STYLE_OPTIONS.emotion);
  populateSelect("style-intensity", STYLE_OPTIONS.intensity);
  populateSelect("style-social-tone", STYLE_OPTIONS.social_tone);
  populateSelect("style-intent", STYLE_OPTIONS.communicative_intent);
  populateSelect("style-pace", STYLE_OPTIONS.pace);
  populateSelect("style-pitch", STYLE_OPTIONS.pitch);
  populateSelect("style-energy", STYLE_OPTIONS.energy);
  populateMultiOptions("mental-state-options", STYLE_OPTIONS.mental_state, 2);
  populateMultiOptions("voice-texture-options", STYLE_OPTIONS.voice_texture, 2);
  bindEditor();
  bindStylePanel();
  bindVoiceDialog();
  bindGeneration();
  for (const tab of ["settings", "history"]) {
    byId(`${tab}-tab`).addEventListener("click", () => {
      for (const name of ["settings", "history"]) {
        const selected = name === tab;
        byId(`${name}-tab`).classList.toggle("active", selected);
        byId(`${name}-tab`).setAttribute("aria-selected", String(selected));
        byId(`${name}-content`).hidden = !selected;
      }
      if (tab === "history") window.refreshTtsHistory();
    });
  }
  bindRange("speech-rate", "speech-rate-value");
  bindRange("loudness", "loudness-value");
  loadStyle(DEFAULT_STYLE);
  updateCharacterCount();
  checkHealth();
  loadPresets();
  loadVoices();
});

function populateSelect(id, options) {
  const select = byId(id);
  Object.entries(options).forEach(([value, label]) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = `${label} · ${value}`;
    select.appendChild(option);
  });
}

function populateMultiOptions(containerId, options, maxItems) {
  const container = byId(containerId);
  Object.entries(options).forEach(([value, label]) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "option-chip";
    button.dataset.value = value;
    button.textContent = label;
    button.addEventListener("click", () => {
      if (!button.classList.contains("selected") && container.querySelectorAll(".selected").length >= maxItems) {
        showToast(`最多选择 ${maxItems} 个选项。`, "error");
        return;
      }
      button.classList.toggle("selected");
      state.customized = true;
      renderPresets();
      schedulePromptPreview();
    });
    container.appendChild(button);
  });
}

function bindRange(inputId, outputId) {
  const input = byId(inputId);
  const output = byId(outputId);
  const update = () => { output.value = input.value; };
  input.addEventListener("input", update);
  output.addEventListener("input", () => {
    if (output.value === "" || !Number.isFinite(output.valueAsNumber)) return;
    input.value = String(Math.min(Number(input.max), Math.max(Number(input.min), Math.round(output.valueAsNumber))));
    update();
  });
  output.addEventListener("change", update);
  update();
}

function bindEditor() {
  const editor = byId("speech-text");
  editor.addEventListener("input", updateCharacterCount);
  editor.addEventListener("paste", (event) => {
    event.preventDefault();
    const text = event.clipboardData?.getData("text/plain") || "";
    document.execCommand("insertText", false, text.slice(0, Math.max(0, 10000 - editorText().length)));
  });
  document.addEventListener("selectionchange", captureSelection);
  editor.addEventListener("click", (event) => {
    const badge = event.target.closest(".style-badge");
    if (!badge) return;
    event.preventDefault();
    const segment = badge.closest(".style-segment");
    if (segment) openExistingStyle(segment);
  });
}

function captureSelection() {
  const selection = window.getSelection();
  if (!selection?.rangeCount) return;
  const range = selection.getRangeAt(0);
  if (!validEditorRange(range)) return;
  const hasText = !range.collapsed && range.toString().trim().length > 0;
  if (hasText) state.selectionRange = range.cloneRange();
  byId("emotion-button").disabled = !hasText;
}

function validEditorRange(range) {
  const editor = byId("speech-text");
  return Boolean(range && (editor.contains(range.commonAncestorContainer) || range.commonAncestorContainer === editor));
}

function bindStylePanel() {
  const button = byId("emotion-button");
  button.addEventListener("mousedown", (event) => event.preventDefault());
  button.addEventListener("click", () => openNewStyle());
  byId("close-emotion-panel").addEventListener("click", closeStylePanel);
  byId("cancel-style").addEventListener("click", closeStylePanel);
  byId("apply-style").addEventListener("click", applyStyle);
  byId("remove-style").addEventListener("click", removeEditingStyle);
  byId("preset-search").addEventListener("input", renderPresets);
  byId("preset-category").addEventListener("change", () => { renderSubcategories(); renderPresets(); });
  byId("preset-subcategory").addEventListener("change", renderPresets);
  ["style-emotion", "style-intensity", "style-social-tone", "style-intent", "style-pace", "style-pitch", "style-energy"].forEach((id) => {
    byId(id).addEventListener("change", () => {
      state.customized = true;
      renderPresets();
      schedulePromptPreview();
    });
  });
  document.addEventListener("click", (event) => {
    if (byId("emotion-panel").hidden) return;
    if (event.target.closest("#emotion-panel") || event.target.closest("#emotion-button") || event.target.closest(".style-badge")) return;
    closeStylePanel();
  });
}

function openNewStyle() {
  if (!validEditorRange(state.selectionRange) || state.selectionRange.collapsed) return;
  const preset = state.presets.find(p => p.id === state.defaultPresetId);
  if (!preset) { showToast("预设正在加载，请稍后重试。", "error"); return; }
  byId("preset-search").value = "";
  loadStyle(preset.style, preset.name, preset.id);
  byId("advanced-style").open = false;
  state.editingSegment = null;
  byId("selection-preview").textContent = `“${state.selectionRange.toString().trim().slice(0, 90)}”`;
  byId("remove-style").hidden = true;
  byId("apply-style").textContent = "应用到选中文字";
  byId("emotion-panel").hidden = false;
  schedulePromptPreview();
}

function openExistingStyle(segment) {
  state.editingSegment = segment;
  state.selectionRange = null;
  let style;
  try { style = JSON.parse(segment.dataset.style || "{}"); } catch { style = DEFAULT_STYLE; }
  loadStyle(style, segment.dataset.label || null, segment.dataset.presetId || null);
  state.customized = segment.dataset.customized === "true";
  byId("advanced-style").open = false;
  renderPresets();
  byId("selection-preview").textContent = `“${segment.querySelector(".style-content")?.textContent?.trim().slice(0, 90) || ""}”`;
  byId("remove-style").hidden = false;
  byId("apply-style").textContent = "保存设置";
  byId("emotion-panel").hidden = false;
  schedulePromptPreview();
}

function closeStylePanel() {
  byId("emotion-panel").hidden = true;
  state.editingSegment = null;
}

async function loadPresets() {
  try {
    const response = await fetch("/api/byteplus/presets", { headers: { Accept: "application/json" } });
    if (!response.ok) throw new Error("无法读取 Preset");
    const data = await response.json();
    state.presets = data.presets || [];
    state.defaultPresetId = data.default_preset_id;
    byId("preset-count").textContent = `${state.presets.length} Presets`;
    byId("preset-category").replaceChildren(...[...new Set(state.presets.map(p => p.category))].map(name => new Option(name, name)));
    renderSubcategories();
    renderPresets();
  } catch (error) {
    showToast(error.message, "error");
  }
}

function renderSubcategories() {
  const names = [...new Set(state.presets.filter(p => p.category === byId("preset-category").value).map(p => p.subcategory))];
  byId("preset-subcategory").replaceChildren(...names.map(name => new Option(name, name)));
}

function renderPresets() {
  const query = byId("preset-search").value.trim().toLowerCase();
  const presets = state.presets.filter(preset => preset.category === byId("preset-category").value && preset.subcategory === byId("preset-subcategory").value && `${preset.id} ${preset.name}`.toLowerCase().includes(query));
  byId("preset-status").textContent = state.selectedPresetName ? `当前：${state.selectedPresetName}${state.customized ? " · 已自定义" : ""}` : "请选择预设";
  const container = byId("preset-grid");
  container.replaceChildren();
  presets.forEach((preset) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `preset-chip${state.selectedPresetId === preset.id ? " active" : ""}`;
    button.textContent = preset.name;
    const [color, soft] = styleColors(preset.style, preset.id);
    button.style.setProperty("--preset-color", color);
    button.style.setProperty("--preset-soft", soft);
    button.addEventListener("click", (event) => {
      // loadStyle re-renders the preset buttons. Stop this click before its
      // detached target reaches the document-level outside-click handler.
      event.stopPropagation();
      loadStyle(preset.style, preset.name, preset.id);
    });
    container.appendChild(button);
  });
  if (!presets.length) {
    const empty = document.createElement("span");
    empty.className = "selection-preview";
    empty.textContent = "没有匹配的组合";
    container.appendChild(empty);
  }
}

function loadStyle(style, label = null, presetId = null) {
  const normalized = { ...DEFAULT_STYLE, ...style };
  byId("style-emotion").value = normalized.emotion;
  byId("style-intensity").value = normalized.intensity;
  byId("style-social-tone").value = normalized.social_tone;
  byId("style-intent").value = normalized.communicative_intent;
  byId("style-pace").value = normalized.pace;
  byId("style-pitch").value = normalized.pitch;
  byId("style-energy").value = normalized.energy;
  setMultiSelection("mental-state-options", normalized.mental_state || []);
  setMultiSelection("voice-texture-options", normalized.voice_texture || []);
  state.selectedPresetId = presetId;
  state.selectedPresetName = label;
  state.customized = false;
  const preset = state.presets.find(p => p.id === presetId);
  if (preset) {
    state.selectedPresetName = preset.name;
    byId("preset-category").value = preset.category;
    renderSubcategories();
    byId("preset-subcategory").value = preset.subcategory;
    byId("preset-search").value = "";
  }
  renderPresets();
  schedulePromptPreview();
}

function setMultiSelection(containerId, values) {
  byId(containerId).querySelectorAll(".option-chip").forEach((button) => {
    button.classList.toggle("selected", values.includes(button.dataset.value));
  });
}

function selectedMulti(containerId) {
  return [...byId(containerId).querySelectorAll(".option-chip.selected")].map((button) => button.dataset.value);
}

function currentStyle() {
  return {
    preset_id: state.selectedPresetId,
    emotion: byId("style-emotion").value,
    intensity: byId("style-intensity").value,
    social_tone: byId("style-social-tone").value,
    mental_state: selectedMulti("mental-state-options"),
    communicative_intent: byId("style-intent").value,
    voice_texture: selectedMulti("voice-texture-options"),
    pace: byId("style-pace").value,
    pitch: byId("style-pitch").value,
    energy: byId("style-energy").value,
  };
}

function schedulePromptPreview() {
  clearTimeout(state.promptTimer);
  state.promptTimer = setTimeout(refreshPromptPreview, 120);
}

async function refreshPromptPreview() {
  byId("prompt-loading").hidden = false;
  try {
    const response = await fetch("/api/byteplus/prompt-preview", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ style: currentStyle() }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Prompt 生成失败");
    byId("prompt-preview").textContent = data.prompt;
  } catch (error) {
    byId("prompt-preview").textContent = error.message;
  } finally {
    byId("prompt-loading").hidden = true;
  }
}

function applyStyle() {
  const style = currentStyle();
  const label = (state.selectedPresetName || `${STYLE_OPTIONS.emotion[style.emotion]} · ${STYLE_OPTIONS.social_tone[style.social_tone]}`) + (state.customized ? " · 自定义" : "");
  if (state.editingSegment) {
    updateSegmentStyle(state.editingSegment, style, label, state.selectedPresetId);
    closeStylePanel();
    updateCharacterCount();
    return;
  }
  const range = state.selectionRange;
  if (!validEditorRange(range) || range.collapsed) return;
  const boundaryInsideStyle = (node, offset, isStart) => {
    const element = node.nodeType === Node.ELEMENT_NODE ? node : node.parentElement;
    if (!element?.closest(".style-segment")) return false;
    if (node.nodeType !== Node.TEXT_NODE) return true;
    if (isStart && offset >= (node.nodeValue || "").length) return false;
    if (!isStart && offset === 0) return false;
    return true;
  };
  const selectedContent = range.cloneContents();
  const containsStyledText = [...selectedContent.querySelectorAll(".style-segment")]
    .some((segment) => segment.querySelector(".style-content")?.textContent);
  if (containsStyledText || boundaryInsideStyle(range.startContainer, range.startOffset, true) || boundaryInsideStyle(range.endContainer, range.endOffset, false)) {
    showToast("当前区域已经包含 Voice Direction，请先编辑或移除原设置。", "error");
    return;
  }
  const wrapper = document.createElement("span");
  wrapper.className = "style-segment";
  const badge = document.createElement("span");
  badge.className = "style-badge";
  badge.contentEditable = "false";
  const content = document.createElement("span");
  content.className = "style-content";
  content.appendChild(range.extractContents());
  wrapper.append(badge, content);
  updateSegmentStyle(wrapper, style, label, state.selectedPresetId);
  range.insertNode(wrapper);
  range.selectNodeContents(content);
  const selection = window.getSelection();
  selection.removeAllRanges();
  selection.addRange(range);
  state.selectionRange = null;
  byId("emotion-button").disabled = true;
  closeStylePanel();
  updateCharacterCount();
}

function updateSegmentStyle(segment, style, label, presetId) {
  segment.dataset.customized = String(state.customized);
  segment.dataset.style = JSON.stringify(style);
  segment.dataset.label = label;
  if (presetId) segment.dataset.presetId = presetId; else delete segment.dataset.presetId;
  const [color, soft] = styleColors(style, presetId);
  segment.style.setProperty("--style-color", color);
  segment.style.setProperty("--style-soft", soft);
  segment.querySelector(".style-badge").textContent = label;
}

function removeEditingStyle() {
  const segment = state.editingSegment;
  if (!segment) return;
  const content = segment.querySelector(".style-content");
  const fragment = document.createDocumentFragment();
  while (content?.firstChild) fragment.appendChild(content.firstChild);
  segment.replaceWith(fragment);
  closeStylePanel();
  updateCharacterCount();
  byId("speech-text").focus();
}

function editorSegments() {
  const segments = [];
  const appendText = (text, style) => {
    const clean = text.replace(/\u200b/g, "");
    if (!clean) return;
    const key = style ? JSON.stringify(style) : "";
    const last = segments.at(-1);
    if (last && (last.style ? JSON.stringify(last.style) : "") === key) last.text += clean;
    else segments.push({ text: clean, style });
  };
  const visit = (node, inheritedStyle = null) => {
    if (node.nodeType === Node.TEXT_NODE) return appendText(node.nodeValue || "", inheritedStyle);
    if (node.nodeType !== Node.ELEMENT_NODE) return;
    if (node.tagName === "BR") return appendText("\n", inheritedStyle);
    if (node.classList.contains("style-segment")) {
      let style = null;
      try { style = JSON.parse(node.dataset.style || "null"); } catch { style = null; }
      node.querySelector(".style-content")?.childNodes.forEach((child) => visit(child, style));
      return;
    }
    node.childNodes.forEach((child) => visit(child, inheritedStyle));
    if (["DIV", "P"].includes(node.tagName) && segments.length && !segments.at(-1).text.endsWith("\n")) appendText("\n", inheritedStyle);
  };
  byId("speech-text").childNodes.forEach((node) => visit(node));
  if (segments.length && segments.at(-1).text.endsWith("\n")) segments.at(-1).text = segments.at(-1).text.slice(0, -1);
  return segments.filter((segment) => segment.text);
}

function editorText() { return editorSegments().map((segment) => segment.text).join(""); }

function updateCharacterCount() {
  const count = editorText().length;
  byId("character-count").textContent = `${count.toLocaleString()} / 10,000`;
  byId("character-count").classList.toggle("limit-warning", count > 9500);
}

async function checkHealth() {
  const status = byId("service-status");
  try {
    const response = await fetch("/api/byteplus/health", { headers: { Accept: "application/json" } });
    const data = await response.json();
    status.className = `status-pill ${response.ok ? "status-ready" : "status-error"}`;
    status.querySelector("span:last-child").textContent = response.ok ? "BytePlus Ready" : "需要 API Key";
    if (!data.audio || data.audio.sample_rate !== 16000) throw new Error("音频配置不是 16 kHz");
  } catch (error) {
    status.className = "status-pill status-error";
    status.querySelector("span:last-child").textContent = "服务不可用";
  }
}

function bindVoiceDialog() {
  byId("voice-card").addEventListener("click", () => byId("voice-dialog").showModal());
  byId("voice-search").addEventListener("input", renderVoices);
  document.querySelectorAll("[data-language]").forEach((button) => {
    button.addEventListener("click", () => {
      state.voiceLanguage = button.dataset.language;
      document.querySelectorAll("[data-language]").forEach((item) => item.classList.toggle("active", item === button));
      renderVoices();
    });
  });
  byId("use-manual-voice").addEventListener("click", () => {
    const voiceId = byId("manual-voice-id").value.trim();
    if (!voiceId) return showToast("请输入 Voice ID。", "error");
    selectVoice({ voice_id: voiceId, voice_name: voiceId, language: "Manual", gender: "Unknown", category: "Manual" });
  });
}

async function loadVoices() {
  try {
    const response = await fetch("/api/byteplus/voices", { headers: { Accept: "application/json" } });
    if (!response.ok) throw new Error("无法读取 BytePlus 音色");
    state.voices = (await response.json()).voices || [];
    const preferred = state.voices.find((voice) => voice.voice_id === "zh_female_vv_uranus_bigtts") || state.voices[0];
    if (preferred) selectVoice(preferred, false);
    renderVoices();
  } catch (error) {
    showToast(error.message, "error");
  }
}

function renderVoices() {
  const queryTokens = byId("voice-search").value.trim().toLowerCase().split(/\s+/).filter(Boolean);
  const voices = state.voices.filter((voice) => {
    if (state.voiceLanguage !== "all" && voice.language !== state.voiceLanguage) return false;
    const haystack = `${voice.voice_name} ${voice.voice_id} ${voice.language} ${voice.gender}`.toLowerCase();
    return queryTokens.every((token) => haystack.includes(token));
  });
  byId("voice-result-count").textContent = `${voices.length} voices`;
  const list = byId("voice-list");
  list.replaceChildren();
  voices.forEach((voice) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `voice-option${state.selectedVoice?.voice_id === voice.voice_id ? " selected" : ""}`;
    const avatar = document.createElement("span");
    avatar.className = "voice-avatar byteplus-avatar";
    avatar.textContent = `${voice.language?.slice(0, 1) || "B"}${voice.gender === "Female" ? "F" : voice.gender === "Male" ? "M" : "P"}`;
    const copy = document.createElement("span");
    const name = document.createElement("strong");
    name.textContent = voice.voice_name;
    const detail = document.createElement("small");
    detail.textContent = `${voice.language} · ${voice.gender} · ${voice.voice_id}`;
    copy.append(name, detail);
    const arrow = document.createElement("span");
    arrow.textContent = "›";
    button.append(avatar, copy, arrow);
    button.addEventListener("click", () => selectVoice(voice));
    list.appendChild(button);
  });
}

function selectVoice(voice, closeDialog = true) {
  state.selectedVoice = voice;
  byId("voice-name").textContent = voice.voice_name;
  byId("voice-language").textContent = `${voice.language} · ${voice.gender} · Official TTS 2.0`;
  byId("voice-avatar").textContent = voice.language === "Chinese" ? "中" : voice.language === "English" ? "EN" : "BP";
  renderVoices();
  if (closeDialog && byId("voice-dialog").open) byId("voice-dialog").close();
}

function bindGeneration() { byId("generate-button").addEventListener("click", generateSpeech); }

async function generateSpeech() {
  const text = editorText();
  if (!text.trim()) return showToast("请输入需要合成的文本。", "error");
  if (text.length > 10000) return showToast("BytePlus 文本不能超过 10,000 个字符。", "error");
  if (!state.selectedVoice) return showToast("请选择 BytePlus 音色。", "error");
  const segments = editorSegments();
  const payload = {
    text,
    voice_id: state.selectedVoice.voice_id,
    speech_rate: Number(byId("speech-rate").value),
    loudness_rate: Number(byId("loudness").value),
  };
  if (segments.some((segment) => segment.style)) payload.segments = segments;
  const button = byId("generate-button");
  button.disabled = true;
  button.querySelector("span:last-child").textContent = "Generating…";
  try {
    const response = await fetch("/api/byteplus/tts", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "audio/wav, application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(data.error || `BytePlus 请求失败：${response.status}`);
    }
    const blob = await response.blob();
    if (state.audioUrl) URL.revokeObjectURL(state.audioUrl);
    state.audioUrl = URL.createObjectURL(blob);
    byId("audio-player").src = state.audioUrl;
    byId("download-link").href = state.audioUrl;
    const durationMs = Number(response.headers.get("X-Audio-Duration-Ms") || 0);
    const segmentsUsed = payload.segments?.filter((segment) => segment.text.trim()).length || 1;
    byId("result-meta").textContent = `16 kHz · Mono · ${(durationMs / 1000).toFixed(2)} s · ${segmentsUsed} segment${segmentsUsed > 1 ? "s" : ""}`;
    byId("result-panel").hidden = false;
    showToast("BytePlus 语音生成完成。", "success");
    window.refreshTtsHistory();
  } catch (error) {
    showToast(error.message || "生成失败。", "error");
  } finally {
    button.disabled = false;
    button.querySelector("span:last-child").textContent = "Generate Speech";
  }
}

function showToast(message, type = "error") {
  const container = byId("toast");
  clearTimeout(state.toastTimer);
  container.replaceChildren();
  const alert = document.createElement("div");
  alert.className = `alert alert-${type}`;
  alert.textContent = message;
  container.appendChild(alert);
  state.toastTimer = setTimeout(() => container.replaceChildren(), 4200);
}
