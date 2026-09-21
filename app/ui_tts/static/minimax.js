"use strict";

const SOUND_TAGS = [
  "laughs", "chuckle", "coughs", "clear-throat", "groans", "breath",
  "pant", "inhale", "exhale", "gasps", "sniffs", "sighs", "snorts",
  "burps", "lip-smacking", "humming", "hissing", "emm", "sneezes",
];

const EMOTIONS = [
  ["happy", "Happy", "#f6c344"], ["sad", "Sad", "#5a7fbf"],
  ["angry", "Angry", "#c84c4c"], ["fearful", "Fearful", "#7a6c9d"],
  ["disgusted", "Disgusted", "#6e8b5e"], ["surprised", "Surprised", "#f2994a"],
  ["neutral", "Neutral", "#9aa0a6"], ["fluent", "Fluent", "#4fb3bf"],
];

const FALLBACK_VOICES = [
  { voice_id: "English_expressive_narrator", voice_name: "Expressive Narrator", category: "system_voice", description: "English · expressive narration" },
  { voice_id: "English_CalmWoman", voice_name: "Calm Woman", category: "system_voice", description: "English · calm and composed" },
  { voice_id: "English_Trustworth_Man", voice_name: "Trustworthy Man", category: "system_voice", description: "English · steady and reliable" },
  { voice_id: "English_FriendlyPerson", voice_name: "Friendly Guy", category: "system_voice", description: "English · friendly and natural" },
  { voice_id: "English_ConfidentWoman", voice_name: "Confident Woman", category: "system_voice", description: "English · confident and clear" },
  { voice_id: "English_compelling_lady1", voice_name: "Compelling Lady", category: "system_voice", description: "English · formal British announcer" },
  { voice_id: "English_Gentle-voiced_man", voice_name: "Gentle-voiced Man", category: "system_voice", description: "English · warm and reassuring" },
  { voice_id: "English_ManWithDeepVoice", voice_name: "Man With Deep Voice", category: "system_voice", description: "English · deep and authoritative" },
  { voice_id: "English_Lucky_Robot", voice_name: "Lucky Robot", category: "system_voice", description: "English · friendly robot voice" },
  { voice_id: "Chinese (Mandarin)_Reliable_Executive", voice_name: "Reliable Executive", category: "system_voice", description: "普通话 · 稳重可靠" },
  { voice_id: "Chinese (Mandarin)_News_Anchor", voice_name: "News Anchor", category: "system_voice", description: "普通话 · 专业新闻女声" },
  { voice_id: "Chinese (Mandarin)_Radio_Host", voice_name: "Radio Host", category: "system_voice", description: "普通话 · 磁性电台男声" },
  { voice_id: "Chinese (Mandarin)_Male_Announcer", voice_name: "Male Announcer", category: "system_voice", description: "普通话 · 清晰播音男声" },
  { voice_id: "Chinese (Mandarin)_IntellectualGirl", voice_name: "Intellectual Girl", category: "system_voice", description: "普通话 · 知性清晰女声" },
  { voice_id: "Chinese (Mandarin)_Crisp_Girl", voice_name: "Crisp Girl", category: "system_voice", description: "普通话 · 温暖清脆女声" },
  { voice_id: "Chinese (Mandarin)_Gentle_Youth", voice_name: "Gentle Youth", category: "system_voice", description: "普通话 · 温柔青年男声" },
  { voice_id: "Chinese (Mandarin)_Mature_Woman", voice_name: "Mature Woman", category: "system_voice", description: "普通话 · 成熟魅力女声" },
  { voice_id: "Chinese (Mandarin)_HK_Flight_Attendant", voice_name: "HK Flight Attendant", category: "system_voice", description: "普通话 · 亲切服务" },
  { voice_id: "Cantonese_GentleLady", voice_name: "Cantonese Gentle Lady", category: "system_voice", description: "粤语 · 温柔女声" },
  { voice_id: "Japanese_Whisper_Belle", voice_name: "Whisper Belle", category: "system_voice", description: "日本語 · soft female voice" },
];

const state = {
  selectedVoice: FALLBACK_VOICES[0],
  voices: FALLBACK_VOICES,
  voicesLoaded: false,
  currentAudioUrl: null,
  toastTimer: null,
  editorRange: null,
  emotionRange: null,
  voiceTab: "library",
  voiceLanguage: "all",
};

const byId = (id) => document.getElementById(id);

document.addEventListener("DOMContentLoaded", () => {
  populateSoundTags();
  populateEmotions();
  bindRange("speed", "speed-value", (value) => trimDecimal(Number(value)));
  bindRange("pitch", "pitch-value", (value) => String(Math.round(Number(value))));
  bindRange("volume", "volume-value", (value) => trimDecimal(Number(value)));
  bindRange("modifier-pitch", "modifier-pitch-value", signedInteger);
  bindRange("modifier-intensity", "modifier-intensity-value", signedInteger);
  bindRange("modifier-timbre", "modifier-timbre-value", signedInteger);
  bindEditorActions();
  bindSettingsActions();
  bindVoiceDialog();
  bindGeneration();
  applyVoice(FALLBACK_VOICES[0]);
  updateCharacterCount();
  updateModelCompatibility();
  checkHealth();
});

function bindRange(inputId, outputId, formatter) {
  const input = byId(inputId);
  const output = byId(outputId);
  const update = () => {
    const formatted = formatter(input.value);
    output.value = formatted;
    if (output.tagName !== "INPUT") output.textContent = formatted;
  };
  input.addEventListener("input", update);
  if (output.tagName === "INPUT") {
    const syncInput = () => {
      const minimum = Number(output.min);
      const maximum = Number(output.max);
      const value = Math.min(maximum, Math.max(minimum, Number(output.value)));
      if (!Number.isFinite(value)) return update();
      input.value = String(value);
      output.value = formatter(input.value);
    };
    output.addEventListener("input", syncInput);
    output.addEventListener("change", syncInput);
  }
  update();
}

function signedInteger(value) {
  const number = Number(value);
  return number > 0 ? `+${number}` : String(number);
}

function bindEditorActions() {
  const editor = byId("speech-text");
  editor.addEventListener("input", () => {
    const limit = editorLimit();
    const text = editorText();
    if (text.length > limit) {
      setEditorText(text.slice(0, limit));
      showToast(`文本已截断为 ${limit.toLocaleString()} 个字符。`, "error");
    }
    updateCharacterCount();
  });
  editor.addEventListener("keyup", captureEditorSelection);
  editor.addEventListener("mouseup", captureEditorSelection);
  editor.addEventListener("mousedown", (event) => {
    if (event.target.closest(".emotion-badge")) event.preventDefault();
  });
  editor.addEventListener("click", (event) => {
    const removeButton = event.target.closest(".emotion-remove");
    if (removeButton) {
      removeEmotion(removeButton.closest(".emotion-segment"));
      return;
    }
    const badge = event.target.closest(".emotion-badge");
    const segment = badge?.closest(".emotion-segment");
    editor.querySelectorAll(".emotion-segment.editing").forEach((item) => {
      if (item !== segment) item.classList.remove("editing");
    });
    if (segment) segment.classList.toggle("editing");
  });
  document.addEventListener("selectionchange", captureEditorSelection);

  byId("long-text").addEventListener("change", (event) => {
    const limit = event.target.checked ? 200000 : 5000;
    const text = editorText();
    if (text.length > limit) {
      setEditorText(text.slice(0, limit));
      showToast(`文本已截断为 ${limit.toLocaleString()} 个字符。`, "error");
    }
    updateCharacterCount();
  });

  byId("emotion-button").addEventListener("mousedown", (event) => event.preventDefault());
  byId("emotion-button").addEventListener("click", () => {
    byId("emotion-popover").hidden = !byId("emotion-popover").hidden;
  });
  document.addEventListener("click", (event) => {
    if (!event.target.closest(".emotion-tool")) byId("emotion-popover").hidden = true;
    if (!event.target.closest(".emotion-segment")) {
      editor.querySelectorAll(".emotion-segment.editing").forEach((item) => item.classList.remove("editing"));
    }
  });

  document.querySelectorAll("[data-pause]").forEach((button) => {
    button.addEventListener("click", () => insertPause(button.dataset.pause));
  });
  byId("insert-custom-pause").addEventListener("click", () => {
    const rawValue = byId("custom-pause").value;
    const value = Number(rawValue);
    if (!Number.isFinite(value) || value < 0.01 || value > 99.99) {
      showToast("Pause 必须在 0.01 到 99.99 秒之间。", "error");
      return;
    }
    insertPause(trimDecimal(value));
  });

  byId("model").addEventListener("change", updateModelCompatibility);
  byId("text-file").addEventListener("change", async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    const limit = editorLimit();
    const text = await file.text();
    setEditorText(text.slice(0, limit));
    updateCharacterCount();
    if (text.length > limit) showToast(`文本已截断为 ${limit.toLocaleString()} 个字符。`, "error");
    event.target.value = "";
  });
}

function bindSettingsActions() {
  byId("settings-tab").addEventListener("click", () => switchSideTab("settings"));
  byId("history-tab").addEventListener("click", () => switchSideTab("history"));
  byId("open-modifier").addEventListener("click", () => {
    byId("settings-main").hidden = true;
    byId("modifier-main").hidden = false;
  });
  byId("close-modifier").addEventListener("click", closeModifier);
  byId("reset-modifier").addEventListener("click", resetModifier);
  byId("reset-settings").addEventListener("click", resetSettings);
  document.querySelectorAll('input[name="sound-effect"]').forEach((toggle) => {
    toggle.addEventListener("change", () => {
      if (!toggle.checked) return;
      document.querySelectorAll('input[name="sound-effect"]').forEach((other) => {
        if (other !== toggle) other.checked = false;
      });
    });
  });
}

function bindVoiceDialog() {
  byId("voice-card").addEventListener("click", () => {
    byId("voice-dialog").showModal();
    if (!state.voicesLoaded) loadVoices();
  });
  byId("voice-search").addEventListener("input", renderVoices);
  document.querySelectorAll("[data-voice-tab]").forEach((button) => {
    button.addEventListener("click", () => {
      state.voiceTab = button.dataset.voiceTab;
      document.querySelectorAll("[data-voice-tab]").forEach((tab) => tab.classList.toggle("active", tab === button));
      renderVoices();
    });
  });
  document.querySelectorAll("[data-voice-query]").forEach((button) => {
    button.addEventListener("click", () => {
      byId("voice-search").value = button.dataset.voiceQuery;
      state.voiceTab = "library";
      state.voiceLanguage = "all";
      document.querySelectorAll("[data-voice-tab]").forEach((tab) => tab.classList.toggle("active", tab.dataset.voiceTab === "library"));
      document.querySelectorAll("[data-voice-language]").forEach((item) => item.classList.toggle("active", item.dataset.voiceLanguage === "all"));
      renderVoices();
    });
  });
  document.querySelectorAll("[data-voice-language]").forEach((button) => {
    button.addEventListener("click", () => {
      state.voiceLanguage = button.dataset.voiceLanguage;
      document.querySelectorAll("[data-voice-language]").forEach((item) => item.classList.toggle("active", item === button));
      renderVoices();
    });
  });
  byId("use-manual-voice").addEventListener("click", () => {
    const voiceId = byId("manual-voice-id").value.trim();
    if (!voiceId) {
      showToast("请输入 Voice ID。", "error");
      return;
    }
    applyVoice({ voice_id: voiceId, voice_name: voiceId, category: "manual", description: "Manual Voice ID" });
    byId("voice-dialog").close();
  });
}

function bindGeneration() {
  byId("generate-button").addEventListener("click", generateSpeech);
}

function populateSoundTags() {
  const grid = byId("sound-tag-grid");
  SOUND_TAGS.forEach((tag) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = `(${tag})`;
    button.addEventListener("click", () => insertAtCursor(`(${tag})`));
    grid.appendChild(button);
  });
}

function populateEmotions() {
  const grid = byId("emotion-grid");
  EMOTIONS.forEach(([value, label, color]) => {
    const button = document.createElement("button");
    button.type = "button";
    button.dataset.emotion = value;
    button.style.setProperty("--emotion-color", color);
    button.textContent = label;
    button.addEventListener("mousedown", (event) => event.preventDefault());
    button.addEventListener("click", () => applyEmotion(value, label));
    grid.appendChild(button);
  });
}

function insertAtCursor(text) {
  const editor = byId("speech-text");
  const limit = editorLimit();
  if (editorText().length + text.length > limit) {
    showToast(`当前文本上限为 ${limit.toLocaleString()} 个字符。`, "error");
    return;
  }
  const range = validEditorRange(state.editorRange) ? state.editorRange.cloneRange() : document.createRange();
  if (!validEditorRange(state.editorRange)) range.selectNodeContents(editor), range.collapse(false);
  range.deleteContents();
  const node = document.createTextNode(text);
  range.insertNode(node);
  range.setStartAfter(node);
  range.collapse(true);
  const selection = window.getSelection();
  selection.removeAllRanges();
  selection.addRange(range);
  state.editorRange = range.cloneRange();
  editor.focus();
  updateCharacterCount();
}

function insertPause(seconds) {
  insertAtCursor(`<#${seconds}#>`);
}

function updateCharacterCount() {
  const length = editorText().length;
  const limit = editorLimit();
  byId("character-count").textContent = `${length.toLocaleString()} / ${limit.toLocaleString()}`;
  byId("long-text-warning").hidden = !byId("long-text").checked;
}

function updateModelCompatibility() {
  const model = byId("model").value;
  const supportsSoundTags = model.startsWith("speech-2.8-");
  byId("sound-tag-button").disabled = !supportsSoundTags;
  byId("sound-tag-button").title = supportsSoundTags ? "插入 Sound Tag" : "Sound Tag 仅支持 speech-2.8";
}

function captureEditorSelection() {
  const selection = window.getSelection();
  if (!selection || !selection.rangeCount) return;
  const range = selection.getRangeAt(0);
  if (!validEditorRange(range)) return;
  state.editorRange = range.cloneRange();
  const hasText = !range.collapsed && range.toString().trim().length > 0;
  if (hasText) state.emotionRange = range.cloneRange();
  byId("emotion-button").disabled = !hasText;
  if (!hasText) byId("emotion-popover").hidden = true;
}

function validEditorRange(range) {
  if (!range) return false;
  const editor = byId("speech-text");
  return editor.contains(range.commonAncestorContainer) || range.commonAncestorContainer === editor;
}

function applyEmotion(value, label) {
  const range = state.emotionRange;
  if (!validEditorRange(range) || range.collapsed) return;
  const boundaryInsideEmotion = (node, offset, isStart) => {
    const element = node.nodeType === Node.ELEMENT_NODE ? node : node.parentElement;
    if (!element?.closest(".emotion-segment")) return false;
    if (node.nodeType !== Node.TEXT_NODE) return true;
    if (isStart && offset >= (node.nodeValue || "").length) return false;
    if (!isStart && offset === 0) return false;
    return true;
  };
  const selectedContent = range.cloneContents();
  const containsSelectedEmotionText = [...selectedContent.querySelectorAll(".emotion-segment")]
    .some((segment) => segment.querySelector(".emotion-content")?.textContent);
  const intersectsEmotion = Boolean(
    boundaryInsideEmotion(range.startContainer, range.startOffset, true)
    || boundaryInsideEmotion(range.endContainer, range.endOffset, false)
    || containsSelectedEmotionText
  );
  if (intersectsEmotion) {
    showToast("当前区域已经添加了 Emotion。", "error");
    return;
  }
  const wrapper = document.createElement("span");
  wrapper.className = "emotion-segment";
  wrapper.dataset.emotion = value;
  const badge = document.createElement("span");
  badge.className = "emotion-badge";
  badge.contentEditable = "false";
  const badgeLabel = document.createElement("span");
  badgeLabel.className = "emotion-badge-label";
  badgeLabel.textContent = label;
  const removeButton = document.createElement("button");
  removeButton.type = "button";
  removeButton.className = "emotion-remove";
  removeButton.tabIndex = -1;
  removeButton.setAttribute("aria-label", `移除 ${label} Emotion`);
  removeButton.innerHTML = '<span class="emotion-divider" aria-hidden="true"></span><span aria-hidden="true">×</span>';
  badge.append(badgeLabel, removeButton);
  const content = document.createElement("span");
  content.className = "emotion-content";
  content.appendChild(range.extractContents());
  wrapper.append(badge, content);
  range.insertNode(wrapper);
  range.selectNodeContents(content);
  const selection = window.getSelection();
  selection.removeAllRanges();
  selection.addRange(range);
  state.editorRange = range.cloneRange();
  state.emotionRange = null;
  byId("emotion-popover").hidden = true;
  byId("emotion-button").disabled = true;
  updateCharacterCount();
}

function removeEmotion(segment) {
  if (!segment) return;
  const content = [...segment.children].find((child) => child.classList.contains("emotion-content"));
  if (!content) return;
  const fragment = document.createDocumentFragment();
  let lastNode = null;
  while (content.firstChild) {
    lastNode = content.firstChild;
    fragment.appendChild(lastNode);
  }
  segment.replaceWith(fragment);
  if (lastNode) {
    const range = document.createRange();
    range.setStartAfter(lastNode);
    range.collapse(true);
    const selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(range);
    state.editorRange = range.cloneRange();
  }
  state.emotionRange = null;
  byId("emotion-button").disabled = true;
  byId("speech-text").focus();
  updateCharacterCount();
}

function editorText() {
  return editorSegments().map((segment) => segment.text).join("");
}

function editorSegments() {
  const segments = [];
  const appendText = (text, emotion) => {
    const cleanText = text.replace(/\u200b/g, "");
    if (!cleanText) return;
    const previous = segments.at(-1);
    if (previous && previous.emotion === emotion) previous.text += cleanText;
    else segments.push({ text: cleanText, emotion });
  };
  const appendNode = (node, emotion = null) => {
    if (node.nodeType === Node.TEXT_NODE) {
      appendText(node.nodeValue || "", emotion);
      return;
    }
    if (node.nodeType !== Node.ELEMENT_NODE || node.classList.contains("emotion-badge")) return;
    if (node.tagName === "BR") {
      appendText("\n", emotion);
      return;
    }
    if (node.classList.contains("emotion-segment")) {
      const segmentEmotion = node.dataset.emotion || null;
      const content = [...node.children].find((child) => child.classList.contains("emotion-content"));
      if (content) content.childNodes.forEach((child) => appendNode(child, segmentEmotion));
      return;
    }
    node.childNodes.forEach((child) => appendNode(child, emotion));
    if (["DIV", "P"].includes(node.tagName) && !segments.at(-1)?.text.endsWith("\n")) appendText("\n", emotion);
  };
  byId("speech-text").childNodes.forEach((node) => appendNode(node));
  const last = segments.at(-1);
  if (last?.text.endsWith("\n")) last.text = last.text.slice(0, -1);
  return segments.filter((segment) => segment.text);
}

function setEditorText(text) {
  const editor = byId("speech-text");
  editor.textContent = text;
  state.editorRange = null;
  state.emotionRange = null;
  byId("emotion-button").disabled = true;
}

function editorLimit() {
  return byId("long-text").checked ? 200000 : 5000;
}

function switchSideTab(tab) {
  const isSettings = tab === "settings";
  byId("settings-tab").classList.toggle("active", isSettings);
  byId("history-tab").classList.toggle("active", !isSettings);
  byId("settings-content").hidden = !isSettings;
  byId("history-content").hidden = isSettings;
  if (isSettings) closeModifier();
}

function closeModifier() {
  byId("settings-main").hidden = false;
  byId("modifier-main").hidden = true;
}

function resetModifier() {
  ["modifier-pitch", "modifier-intensity", "modifier-timbre"].forEach((id) => {
    const element = byId(id);
    element.value = 0;
    element.dispatchEvent(new Event("input"));
  });
  document.querySelectorAll('input[name="sound-effect"]').forEach((toggle) => { toggle.checked = false; });
}

function resetSettings() {
  byId("speed").value = 1;
  byId("pitch").value = 0;
  byId("volume").value = 1;
  ["speed", "pitch", "volume"].forEach((id) => byId(id).dispatchEvent(new Event("input")));
  byId("text-normalization").checked = false;
  resetModifier();
  showToast("设置已恢复默认值。", "success");
}

async function checkHealth() {
  const pill = byId("service-status");
  try {
    const response = await fetch("/api/minimax/health", { headers: { Accept: "application/json" } });
    const data = await response.json();
    pill.className = `status-pill ${data.minimax_configured ? "status-ready" : "status-error"}`;
    pill.querySelector("span:last-child").textContent = data.minimax_configured ? "MiniMax Ready" : "API Key 未配置";
  } catch (_) {
    pill.className = "status-pill status-error";
    pill.querySelector("span:last-child").textContent = "服务不可用";
  }
}

async function loadVoices() {
  byId("voice-loading").hidden = false;
  byId("voice-list").hidden = true;
  byId("voice-notice").hidden = true;
  try {
    const response = await fetch("/api/minimax/voices", { headers: { Accept: "application/json" } });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "无法读取音色列表");
    state.voices = data.voices.length ? data.voices : FALLBACK_VOICES;
  } catch (error) {
    state.voices = FALLBACK_VOICES;
    byId("voice-notice").textContent = `${error.message} 当前显示内置常用音色，也可以手动输入 Voice ID。`;
    byId("voice-notice").hidden = false;
  } finally {
    state.voicesLoaded = true;
    byId("voice-loading").hidden = true;
    byId("voice-list").hidden = false;
    renderVoices();
  }
}

function renderVoices() {
  const query = byId("voice-search").value.trim().toLowerCase();
  const queryTokens = query.split(/\s+/).filter(Boolean);
  const filtered = state.voices.filter((voice) => {
    if (state.voiceTab === "collected") return false;
    if (state.voiceTab === "voice_cloning" && !["voice_cloning", "voice_generation"].includes(voice.category)) return false;
    if (state.voiceTab === "library" && !["system_voice"].includes(voice.category)) return false;
    if (state.voiceLanguage !== "all" && inferLanguage(voice.voice_id, voice.description) !== state.voiceLanguage) return false;
    const haystack = `${voice.voice_name} ${voice.voice_id} ${voice.description || ""}`.toLowerCase();
    return queryTokens.every((token) => haystack.includes(token));
  });
  byId("voice-result-count").textContent = `${filtered.length.toLocaleString()} voices`;
  const list = byId("voice-list");
  list.replaceChildren();
  if (!filtered.length) {
    const empty = document.createElement("div");
    empty.className = "voice-notice";
    empty.textContent = state.voiceTab === "collected" ? "No collected voices yet." : "没有找到匹配的音色。";
    list.appendChild(empty);
    return;
  }
  filtered.forEach((voice) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `voice-option${voice.voice_id === state.selectedVoice.voice_id ? " selected" : ""}`;
    const initials = voiceInitials(voice);
    button.innerHTML = `
      <span class="voice-avatar">${escapeHtml(initials)}</span>
      <span><strong>${escapeHtml(voice.voice_name)}</strong><small>${escapeHtml(voice.voice_id)}</small></span>
      <span class="voice-category">${escapeHtml(inferLanguage(voice.voice_id, voice.description))}</span>`;
    button.addEventListener("click", () => {
      applyVoice(voice);
      byId("voice-dialog").close();
    });
    list.appendChild(button);
  });
}

function applyVoice(voice) {
  state.selectedVoice = voice;
  const language = inferLanguage(voice.voice_id, voice.description);
  const initials = voiceInitials(voice);
  byId("voice-name").textContent = voice.voice_name;
  byId("voice-language").textContent = `${language} · ${categoryLabel(voice.category)}`;
  byId("voice-avatar").textContent = initials;
  byId("modifier-avatar").textContent = initials;
  byId("modifier-voice-name").textContent = voice.voice_name;
}

async function generateSpeech() {
  const displayText = editorText();
  const segments = editorSegments();
  const hasSegmentEmotions = segments.some((segment) => segment.emotion);
  const longTextMode = byId("long-text").checked;
  if (!displayText.trim()) {
    showToast("请输入需要合成的文本。", "error");
    byId("speech-text").focus();
    return;
  }

  if (!longTextMode && displayText.length > 9999) {
    showToast("同步生成最多提交 9,999 字符；请启用 Long text。", "error");
    return;
  }

  if (longTextMode && hasSegmentEmotions) {
    showToast("Long Text 暂不支持分段 Emotion；请关闭 Long Text 后生成。", "error");
    return;
  }

  const payload = {
    text: displayText,
    segments: hasSegmentEmotions ? segments : null,
    model: byId("model").value,
    voice_id: state.selectedVoice.voice_id,
    language_boost: byId("language").value,
    speed: Number(byId("speed").value),
    volume: Number(byId("volume").value),
    pitch: Number(byId("pitch").value),
    emotion: null,
    text_normalization: byId("text-normalization").checked,
    modifier_pitch: Number(byId("modifier-pitch").value),
    modifier_intensity: Number(byId("modifier-intensity").value),
    modifier_timbre: Number(byId("modifier-timbre").value),
    sound_effect: document.querySelector('input[name="sound-effect"]:checked')?.value || null,
  };

  setGenerating(true);
  try {
    const response = longTextMode
      ? await generateLongText(payload)
      : await postSynthesis("/api/minimax/tts", payload);
    await consumeAudioResponse(response, payload, displayText);
    showToast("已生成 G1 可播放的 16 kHz WAV。", "success");
  } catch (error) {
    showToast(error.message || "语音生成失败。", "error");
  } finally {
    setGenerating(false);
  }
}

async function postSynthesis(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "audio/wav, application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) await throwResponseError(response);
  return response;
}

async function generateLongText(payload) {
  const creationResponse = await fetch("/api/minimax/tts/async", {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(payload),
  });
  if (!creationResponse.ok) await throwResponseError(creationResponse);
  const task = await creationResponse.json();
  if (!task.task_id) throw new Error("长文本任务没有返回 Task ID。");

  setGenerating(true, "Processing…");
  showToast(`长文本任务 ${task.task_id} 已提交，正在等待 MiniMax 完成。`, "success");
  for (let attempt = 0; attempt < 300; attempt += 1) {
    await delay(2000);
    const response = await fetch(`/api/minimax/tts/async/${encodeURIComponent(task.task_id)}`, {
      headers: { Accept: "audio/wav, application/json" },
    });
    if (response.status === 202) continue;
    if (!response.ok) await throwResponseError(response);
    return response;
  }
  throw new Error("长文本任务等待超过 10 分钟，请稍后重试。");
}

async function consumeAudioResponse(response, payload, displayText) {
  const blob = await response.blob();
  const audioUrl = URL.createObjectURL(blob);
  state.currentAudioUrl = audioUrl;

  const durationMs = Number(response.headers.get("X-Audio-Duration-Ms") || 0);
  const sampleRate = response.headers.get("X-Audio-Sample-Rate") || "16000";
  const channels = response.headers.get("X-Audio-Channels") || "1";
  const traceId = response.headers.get("X-Minimax-Trace-Id") || "";
  const filename = parseFilename(response.headers.get("Content-Disposition")) || "concierge_16k.wav";
  showResult({ audioUrl, durationMs, sampleRate, channels, traceId, filename, blob, payload, displayText });
}

async function throwResponseError(response) {
  const data = await response.json().catch(() => ({}));
  const suffix = data.trace_id ? `（Trace: ${data.trace_id}）` : "";
  throw new Error(`${data.error || "语音生成失败。"}${suffix}`);
}

function delay(milliseconds) {
  return new Promise((resolve) => window.setTimeout(resolve, milliseconds));
}

function showResult(result) {
  byId("audio-player").src = result.audioUrl;
  byId("download-button").href = result.audioUrl;
  byId("download-button").download = result.filename;
  const seconds = result.durationMs ? `${(result.durationMs / 1000).toFixed(2)} s` : "duration pending";
  const channelLabel = Number(result.channels) === 1 ? "Mono" : `${result.channels} channels`;
  byId("result-meta").textContent = `${Number(result.sampleRate).toLocaleString()} Hz · ${channelLabel} · WAV · ${formatBytes(result.blob.size)} · ${seconds}`;
  byId("result-panel").hidden = false;
  byId("result-panel").scrollIntoView({ behavior: "smooth", block: "nearest" });

  window.refreshTtsHistory();
}

function setGenerating(isGenerating, activeLabel = "Generating…") {
  const button = byId("generate-button");
  button.disabled = isGenerating;
  button.querySelector(".generate-label").textContent = isGenerating ? activeLabel : "Generate";
  button.querySelector(".generate-spark").hidden = isGenerating;
  button.querySelector(".generate-spinner").hidden = !isGenerating;
}

function showToast(message, type) {
  const toast = byId("toast");
  const alert = byId("toast-alert");
  byId("toast-message").textContent = message;
  alert.className = `alert ${type === "error" ? "alert-error" : "alert-success"}`;
  toast.hidden = false;
  clearTimeout(state.toastTimer);
  state.toastTimer = setTimeout(() => { toast.hidden = true; }, type === "error" ? 6000 : 3200);
}

function trimDecimal(value) {
  return value.toFixed(2).replace(/0+$/, "").replace(/\.$/, "");
}

function parseFilename(contentDisposition) {
  if (!contentDisposition) return null;
  const match = contentDisposition.match(/filename="([^"]+)"/i);
  return match ? match[1] : null;
}

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function inferLanguage(voiceId, description = "") {
  const value = `${voiceId} ${description}`.toLowerCase();
  if (value.includes("cantonese")) return "Cantonese";
  if (value.includes("japanese")) return "Japanese";
  if (value.includes("korean")) return "Korean";
  if (value.includes("malay")) return "Malay";
  if (value.includes("english")) return "English";
  if (value.includes("chinese") || value.includes("mandarin") || /[\u4e00-\u9fff]/.test(description)) return "Chinese";
  return "Custom";
}

function voiceInitials(voice) {
  const language = inferLanguage(voice.voice_id, voice.description);
  return { English: "EN", Chinese: "ZH", Cantonese: "YUE", Japanese: "JA", Korean: "KO", Malay: "MS" }[language] || "AI";
}

function categoryLabel(category) {
  return { system_voice: "System Voice", voice_cloning: "Cloned Voice", voice_generation: "Generated Voice", manual: "Manual Voice ID" }[category] || "Voice";
}

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[character]));
}
