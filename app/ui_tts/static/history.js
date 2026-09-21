"use strict";

window.refreshTtsHistory = async function () {
  const list = document.getElementById("history-list");
  if (!list) return;
  const provider = list.dataset.provider;
  try {
    const response = await fetch(`/api/${provider}/history`, {cache: "no-store"});
    if (!response.ok) throw new Error("历史记录加载失败，请刷新重试。");
    const {history} = await response.json();
    list.replaceChildren();
    document.getElementById("empty-history").hidden = history.length > 0;
    const count = document.getElementById("history-count");
    if (count) count.textContent = history.length;
    for (const item of history) {
      const article = document.createElement("article");
      article.className = "history-item saved-audio";
      const title = document.createElement("strong");
      title.textContent = `${Number(item.duration_seconds).toFixed(2)} s · ${new Date(item.created_at).toLocaleString()}`;
      const text = document.createElement("p");
      text.textContent = item.text || "原始文本未记录";
      const audio = document.createElement("audio");
      audio.controls = true;
      audio.preload = "none";
      const base = `/api/${provider}/history/${item.id}`;
      audio.src = `${base}/audio`;
      const actions = document.createElement("div");
      actions.className = "saved-audio-actions";
      const download = document.createElement("a");
      download.className = "btn btn-sm";
      download.textContent = "下载 WAV";
      download.href = `${base}/audio?download=1`;
      const remove = document.createElement("button");
      remove.type = "button";
      remove.className = "btn btn-sm btn-ghost";
      remove.textContent = "删除";
      remove.addEventListener("click", async () => {
        if (!window.confirm("删除这条历史记录及其 WAV 文件？删除后无法恢复。")) return;
        remove.disabled = true;
        try {
          const result = await fetch(base, {method: "DELETE"});
          if (!result.ok) throw new Error("删除失败，请重试。");
          audio.pause();
          await window.refreshTtsHistory();
        } catch (error) {
          window.alert(error.message);
          remove.disabled = false;
        }
      });
      actions.append(download, remove);
      article.append(title, text, audio, actions);
      list.append(article);
    }
  } catch (error) {
    list.textContent = error.message;
  }
};
document.addEventListener("DOMContentLoaded", window.refreshTtsHistory);
