const CACHE_DB_NAME = "WordImporterCache";
const CACHE_STORE = "words";
const CACHE_TTL_MS = 24 * 60 * 60 * 1000;
const NATIVE_HOST_NAME = "com.obsidian.wordimporter";
const MAX_NOTIFICATION_TITLE = 80;

function normalizeInput(text) {
  let t = String(text || "")
    .replace(/[\u2018\u2019]/g, "'")
    .replace(/[\u201C\u201D]/g, "\"")
    .replace(/[\u2013\u2014]/g, "-")
    .replace(/\u2026/g, "...")
    .replace(/[\u200B\u200C\u200D\uFEFF\u00AD]/g, "")
    .replace(/\s+/g, " ")
    .trim();
  t = t.replace(/^["']+|["']+$/g, "").trim();
  if (/^[a-zA-Z][a-zA-Z'-]{1,79}[.,;:!?]+$/.test(t)) {
    t = t.replace(/[.,;:!?]+$/, "");
  }
  return t;
}

function isValidInput(text) {
  const t = normalizeInput(text);
  if (t.length < 2 || t.length > 800) return false;
  if (!/[a-zA-Z]/.test(t)) return false;
  if (/[^\x20-\x7E]/.test(t)) return false;
  return /^[a-zA-Z0-9"'(]/.test(t);
}

function openCache() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(CACHE_DB_NAME, 1);
    req.onupgradeneeded = (e) => {
      const db = e.target.result;
      if (!db.objectStoreNames.contains(CACHE_STORE)) {
        db.createObjectStore(CACHE_STORE, { keyPath: "word" });
      }
    };
    req.onsuccess = (e) => resolve(e.target.result);
    req.onerror = () => reject(req.error);
  });
}

async function getCache(word) {
  const db = await openCache();
  return new Promise((resolve) => {
    const tx = db.transaction(CACHE_STORE, "readonly");
    const store = tx.objectStore(CACHE_STORE);
    const req = store.get(word);
    req.onsuccess = () => {
      const entry = req.result;
      if (entry && Date.now() - entry.ts < CACHE_TTL_MS) resolve(entry);
      else resolve(null);
    };
    req.onerror = () => resolve(null);
  });
}

async function setCache(word, pronunciation, pos, meaning, etymology) {
  const db = await openCache();
  return new Promise((resolve) => {
    const tx = db.transaction(CACHE_STORE, "readwrite");
    const store = tx.objectStore(CACHE_STORE);
    store.put({ word, pronunciation, pos, meaning, etymology, ts: Date.now() });
    tx.oncomplete = () => resolve();
  });
}

const debounceMap = new Map();

function isDebounced(word, seconds) {
  const last = debounceMap.get(word);
  if (last && Date.now() - last < seconds * 1000) return true;
  debounceMap.set(word, Date.now());
  return false;
}

async function getSettings() {
  const defaults = {
    vault_path: "",
    target_file: "论文单词.md",
    dictionary_api: "google",
    notifications_enabled: true,
    debounce_seconds: 60,
  };
  return new Promise((resolve) => {
    chrome.storage.sync.get(defaults, (items) => resolve(items));
  });
}

function showNotification(title, message) {
  chrome.notifications.create({
    type: "basic",
    iconUrl: "icons/icon128.png",
    title,
    message,
    priority: 1,
    requireInteraction: false,
  }, (id) => {
    setTimeout(() => chrome.notifications.clear(id), 3000);
  });
}

function buildTitle(word, pronunciation) {
  const title = pronunciation ? `${word} ${pronunciation}` : word;
  return title.length > MAX_NOTIFICATION_TITLE ? `${title.slice(0, MAX_NOTIFICATION_TITLE - 1)}…` : title;
}

function buildMessage(pos, meaning) {
  return pos ? `[${pos}] ${meaning}` : meaning;
}

async function processWord(word, pageTranslation) {
  const settings = await getSettings();
  const cacheKey = word.toLowerCase();

  if (isDebounced(cacheKey, settings.debounce_seconds)) return;

  const cached = await getCache(cacheKey);
  if (cached) {
    if (settings.notifications_enabled) {
      showNotification(
        "\u{1F4CC} 已存在: " + buildTitle(word, cached.pronunciation),
        buildMessage(cached.pos, cached.meaning)
      );
    }
    return;
  }

  try {
    const response = await chrome.runtime.sendNativeMessage(NATIVE_HOST_NAME, {
      word,
      settings,
      pageTranslation: pageTranslation || null,
    });

    if (!response) {
      throw new Error("Native host 无响应");
    }

    if (response.status === "ok") {
      await setCache(cacheKey, response.pronunciation, response.pos,
                     response.meaning, response.etymology);
      if (settings.notifications_enabled) {
        const suffix = response.file ? `\n写入: ${response.file}` : "";
        showNotification(
          "✅ 已收录: " + buildTitle(word, response.pronunciation),
          buildMessage(response.pos, response.meaning) + suffix
        );
      }
    } else if (response.status === "exists") {
      await setCache(cacheKey, response.pronunciation, response.pos,
                     response.meaning, response.etymology);
      if (settings.notifications_enabled) {
        showNotification(
          "\u{1F4CC} 已存在: " + buildTitle(word, response.pronunciation),
          buildMessage(response.pos, response.meaning)
        );
      }
    } else if (response.status === "error") {
      if (settings.notifications_enabled) {
        showNotification("❌ 收录失败: " + word, response.message);
      }
    }
  } catch (err) {
    if (settings.notifications_enabled) {
      showNotification("❌ 收录失败: " + word, err.message);
    }
  }
}

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg.type === "WORD_COPIED" && msg.word) {
    processWord(msg.word, msg.pageTranslation)
      .then(() => sendResponse({ status: "ok" }))
      .catch((err) => sendResponse({ status: "error", message: err.message }));
    return true;
  }
  if (msg.type === "GET_SETTINGS") {
    getSettings().then(sendResponse);
    return true;
  }
});

function ensureContextMenu() {
  chrome.contextMenus.removeAll(() => {
    chrome.contextMenus.create({
      id: "add-to-obsidian",
      title: "添加到 Obsidian 词库",
      contexts: ["selection"],
    });
  });
}

chrome.runtime.onInstalled.addListener(ensureContextMenu);
chrome.runtime.onStartup.addListener(ensureContextMenu);
ensureContextMenu();

chrome.contextMenus.onClicked.addListener((info, _tab) => {
  if (info.menuItemId === "add-to-obsidian" && info.selectionText) {
    const word = normalizeInput(info.selectionText);
    if (isValidInput(word)) {
      processWord(word);
    }
  }
});
