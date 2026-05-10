const form = document.getElementById("settings-form");
const statusEl = document.getElementById("status");
const btnTest = document.getElementById("btn-test");

const defaults = {
  vault_path: "",
  target_file: "6英语/论文单词.md",
  dictionary_api: "google",
  debounce_seconds: 60,
  notifications_enabled: true,
};

function showStatus(msg, type) {
  statusEl.textContent = msg;
  statusEl.className = `status ${type}`;
  setTimeout(() => {
    statusEl.className = "status hidden";
  }, 4000);
}

async function loadSettings() {
  return new Promise((resolve) => {
    chrome.storage.sync.get(defaults, (items) => resolve(items));
  });
}

async function saveSettings(settings) {
  return new Promise((resolve) => {
    chrome.storage.sync.set(settings, resolve);
  });
}

function bindForm(settings) {
  document.getElementById("vault-path").value = settings.vault_path || "";
  document.getElementById("target-file").value = settings.target_file;
  document.getElementById("dictionary-api").value = settings.dictionary_api;
  document.getElementById("debounce-seconds").value = settings.debounce_seconds;
  document.getElementById("notifications-enabled").checked = settings.notifications_enabled;
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const settings = {
    vault_path: document.getElementById("vault-path").value.trim(),
    target_file: document.getElementById("target-file").value.trim() || defaults.target_file,
    dictionary_api: document.getElementById("dictionary-api").value,
    debounce_seconds: Math.max(0, parseInt(document.getElementById("debounce-seconds").value) || defaults.debounce_seconds),
    notifications_enabled: document.getElementById("notifications-enabled").checked,
  };

  try {
    await saveSettings(settings);
    showStatus("设置已保存 ✓", "success");
  } catch (err) {
    showStatus(`保存失败: ${err.message}`, "error");
  }
});

btnTest.addEventListener("click", async () => {
  showStatus("正在测试连接...", "info");
  try {
    const response = await chrome.runtime.sendNativeMessage("com.obsidian.wordimporter", {
      action: "test",
    });
    if (response && response.status === "ok") {
      showStatus("Native Host 连接成功 ✓", "success");
    } else {
      showStatus(`连接失败: ${response ? response.message : "无响应"}`, "error");
    }
  } catch (err) {
    showStatus(`连接失败: ${err.message}`, "error");
  }
});

document.addEventListener("DOMContentLoaded", async () => {
  const settings = await loadSettings();
  bindForm(settings);
});
