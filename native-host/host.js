#!/usr/bin/env node
'use strict';
const https = require('https');
const fs = require('fs');
const path = require('path');
const os = require('os');

// ═══════════════════════════════════════════════════════════════════════
// Native Messaging protocol
// ═══════════════════════════════════════════════════════════════════════

function readMessage() {
  const buf = readExact(4);
  if (!buf) return null;
  const len = buf.readUInt32LE(0);
  const payload = readExact(len);
  if (!payload) return null;
  return JSON.parse(payload.toString('utf-8'));
}

function readExact(n) {
  const buf = Buffer.alloc(n);
  let offset = 0;
  while (offset < n) {
    const chunk = (() => {
      try { return fs.readSync(0, buf, offset, n - offset, null); }
      catch (_) { return 0; }
    })();
    if (chunk === 0) return null;
    offset += chunk;
  }
  return buf;
}

function sendMessage(data) {
  const payload = Buffer.from(JSON.stringify(data), 'utf-8');
  const header = Buffer.alloc(4);
  header.writeUInt32LE(payload.length, 0);
  fs.writeSync(1, header);
  fs.writeSync(1, payload);
}

// ═══════════════════════════════════════════════════════════════════════
// Translation APIs
// ═══════════════════════════════════════════════════════════════════════

function httpGet(url) {
  return new Promise((resolve) => {
    https.get(url, { timeout: 5000 }, (res) => {
      let data = '';
      res.on('data', c => data += c);
      res.on('end', () => resolve(data));
    }).on('error', () => resolve(null));
  });
}

async function queryGoogleTranslate(word) {
  const url = `https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=zh-CN&dt=t&q=${encodeURIComponent(word)}`;
  const data = await httpGet(url);
  try {
    const parsed = JSON.parse(data);
    if (parsed?.[0]?.[0]) return parsed[0][0][0];
  } catch (_) {}
  return null;
}

async function queryYoudao(word) {
  const url = `https://dict.youdao.com/suggest?num=5&doctype=json&q=${encodeURIComponent(word)}`;
  const data = await httpGet(url);
  try {
    const parsed = JSON.parse(data);
    if (parsed?.data?.entries) {
      for (const e of parsed.data.entries) {
        if (e.explain) return e.explain;
      }
    }
  } catch (_) {}
  return null;
}

// ═══════════════════════════════════════════════════════════════════════
// Obsidian vault file operations
// ═══════════════════════════════════════════════════════════════════════

function detectObsidianVault() {
  const home = os.homedir();
  const candidates = [];

  const vaultNames = ['Obsidian Vault', 'obsidian', 'notes', 'Notes', 'vault'];

  if (os.platform() === 'win32') {
    for (const root of [home, path.join(home, 'Documents'), path.join(home, 'OneDrive', 'Documents'), path.join(home, 'Desktop')]) {
      if (!fs.existsSync(root)) continue;
      for (const name of vaultNames) {
        const p = path.join(root, name);
        if (fs.existsSync(path.join(p, '.obsidian'))) candidates.push(p);
      }
      try {
        for (const entry of fs.readdirSync(root)) {
          const full = path.join(root, entry);
          if (fs.statSync(full).isDirectory() && fs.existsSync(path.join(full, '.obsidian'))) {
            candidates.push(full);
          }
        }
      } catch (_) {}
    }
  } else {
    for (const p of [
      path.join(home, '文档', 'Obsidian Vault'),
      path.join(home, 'Documents', 'Obsidian Vault'),
      path.join(home, 'Obsidian Vault'),
    ]) {
      if (fs.existsSync(path.join(p, '.obsidian'))) candidates.push(p);
    }
  }

  return candidates[0] || null;
}

function readEntries(filepath) {
  // Returns [{word, meaning}] objects
  if (!fs.existsSync(filepath)) return [];
  const content = fs.readFileSync(filepath, 'utf-8');
  const entries = [];
  const parts = content.split(/\n(?=### )/);
  for (const part of parts) {
    const trimmed = part.trim();
    if (!trimmed.startsWith('### ')) continue;
    const nl = trimmed.indexOf('\n');
    const header = nl > 0 ? trimmed.substring(4, nl).trim() : trimmed.substring(4).trim();
    const word = header.split(/[\s/]/)[0].toLowerCase();
    const meaning = nl > 0 ? trimmed.substring(nl + 1).trim() : '';
    entries.push({ word, meaning });
  }
  return entries;
}

function writeToObsidian(vaultPath, targetFile, word, meaning) {
  const targetDir = path.dirname(path.join(vaultPath, targetFile));
  fs.mkdirSync(targetDir, { recursive: true });

  const baseName = path.basename(targetFile, '.md');
  const ext = '.md';

  // Find active file (< 100 entries, rotate if full)
  let filePath = path.join(vaultPath, targetFile);
  let entries = readEntries(filePath);

  if (entries.length >= 100) {
    let n = 1;
    while (true) {
      const numPath = path.join(vaultPath, `${baseName}${n}${ext}`);
      if (fs.existsSync(numPath)) {
        entries = readEntries(numPath);
        if (entries.length < 100) { filePath = numPath; break; }
      } else {
        filePath = numPath; entries = []; break;
      }
      n++;
    }
  }

  // Check duplicate
  if (entries.some(e => e.word === word.toLowerCase())) {
    return { status: 'exists', word, meaning };
  }

  // Append and sort
  entries.push({ word: word.toLowerCase(), meaning });
  entries.sort((a, b) => a.word.localeCompare(b.word));

  // Write file
  const lines = ['# 论文词汇表\n'];
  for (const e of entries) {
    lines.push(`### ${e.word}\n${e.meaning}\n`);
  }
  fs.writeFileSync(filePath, lines.join('\n'), 'utf-8');

  const fullPath = path.join(vaultPath, targetFile);
  const writtenTo = filePath === fullPath ? targetFile : path.relative(vaultPath, filePath);

  return { status: 'ok', word, meaning, file: writtenTo };
}

// ═══════════════════════════════════════════════════════════════════════
// Message handler
// ═══════════════════════════════════════════════════════════════════════

function isValidWord(text) {
  return /^[a-zA-Z][a-zA-Z\s\-]{1,79}$/.test(text.trim());
}

async function handleMessage(msg) {
  const action = msg.action;

  if (action === 'test') {
    const vault = detectObsidianVault();
    let message = 'Native host v3.0 (Node.js + Google/Youdao) is running';
    if (vault) message += `\n检测到 Vault: ${vault}`;
    return { status: 'ok', message };
  }

  const word = (msg.word || '').trim().toLowerCase();
  if (!isValidWord(word)) {
    return { status: 'error', message: '请输入有效的英文单词或词组' };
  }

  const settings = msg.settings || {};
  let vaultPath = settings.vault_path || '';

  // Auto-detect vault if not configured
  if (!vaultPath || !fs.existsSync(vaultPath)) {
    const detected = detectObsidianVault();
    if (detected) {
      vaultPath = detected;
    } else {
      return { status: 'error', message: '未找到 Obsidian Vault，请在插件中手动配置路径' };
    }
  }

  const targetFile = settings.target_file || '论文单词.md';
  const apiChoice = settings.dictionary_api || 'google';

  // Step 1: Use page translation (from Immersive Translate)
  let meaning = (msg.pageTranslation || '').trim();

  // Step 2: Try API
  if (!meaning) {
    if (apiChoice === 'youdao') {
      meaning = await queryYoudao(word);
      if (!meaning) meaning = await queryGoogleTranslate(word);
    } else {
      meaning = await queryGoogleTranslate(word);
      if (!meaning) meaning = await queryYoudao(word);
    }
  }

  // Step 3: Nothing worked
  if (!meaning) {
    return { status: 'error', message: '翻译失败，请检查网络后重试' };
  }

  return writeToObsidian(vaultPath, targetFile, word, meaning);
}

// ═══════════════════════════════════════════════════════════════════════
// Main loop
// ═══════════════════════════════════════════════════════════════════════

async function main() {
  while (true) {
    try {
      const msg = readMessage();
      if (!msg) break;
      const response = await handleMessage(msg);
      sendMessage(response);
    } catch (e) {
      if (e.code === 'EOF' || e.code === 'EPIPE') break;
      try { sendMessage({ status: 'error', message: e.message }); }
      catch (_) { break; }
    }
  }
}

main();
