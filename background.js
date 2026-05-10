const CACHE_DB_NAME = "WordImporterCache";
const CACHE_STORE = "words";
const CACHE_TTL_MS = 24 * 60 * 60 * 1000;
const NATIVE_HOST_NAME = "com.obsidian.wordimporter";

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
      if (entry && Date.now() - entry.ts < CACHE_TTL_MS) {
        resolve(entry);
      } else {
        resolve(null);
      }
    };
    req.onerror = () => resolve(null);
  });
}

async function setCache(word, pos, meaning, pronunciation, etymology) {
  const db = await openCache();
  return new Promise((resolve) => {
    const tx = db.transaction(CACHE_STORE, "readwrite");
    const store = tx.objectStore(CACHE_STORE);
    store.put({ word, pos, meaning, pronunciation, etymology, ts: Date.now() });
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
    target_file: "6英语/论文单词.md",
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
  if (pronunciation) {
    return `${word} ${pronunciation}`;
  }
  return word;
}

function buildMessage(pos, meaning, etymology) {
  let msg = `[${pos}] ${meaning}`;
  if (etymology) {
    msg += `\n${etymology}`;
  }
  return msg;
}

async function processWord(word, pageTranslation) {
  const settings = await getSettings();

  if (!settings.vault_path) {
    if (settings.notifications_enabled) {
      showNotification("请先配置 Vault 路径", "点击扩展图标 → 设置 Obsidian Vault 路径");
    }
    return;
  }

  if (isDebounced(word, settings.debounce_seconds)) return;

  const cached = await getCache(word);
  if (cached) {
    if (settings.notifications_enabled) {
      showNotification(
        "📌 已存在: " + buildTitle(word, cached.pronunciation),
        buildMessage(cached.pos, cached.meaning, cached.etymology)
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
      await setCache(word, response.pos, response.meaning,
                     response.pronunciation, response.etymology);
      if (settings.notifications_enabled) {
        showNotification(
          "✅ 已收录: " + buildTitle(word, response.pronunciation),
          buildMessage(response.pos, response.meaning, response.etymology)
        );
      }
    } else if (response.status === "exists") {
      await setCache(word, response.pos, response.meaning,
                     response.pronunciation, response.etymology);
      if (settings.notifications_enabled) {
        showNotification(
          "📌 已存在: " + buildTitle(word, response.pronunciation),
          buildMessage(response.pos, response.meaning, response.etymology)
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
    processWord(msg.word, msg.pageTranslation);
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
// Also create immediately on service worker start
ensureContextMenu();

chrome.contextMenus.onClicked.addListener((info, _tab) => {
  if (info.menuItemId === "add-to-obsidian" && info.selectionText) {
    const word = info.selectionText.trim();
    if (word && /^[a-zA-Z][a-zA-Z\s\-]{1,79}$/.test(word)) {
      processWord(word.toLowerCase());
    }
  }
});
