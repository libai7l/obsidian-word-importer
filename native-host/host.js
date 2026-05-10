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
// HTTP helper
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

// ═══════════════════════════════════════════════════════════════════════
// Translation APIs — meaning only
// ═══════════════════════════════════════════════════════════════════════

async function queryGoogleTranslate(word) {
  const data = await httpGet(
    `https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=zh-CN&dt=t&q=${encodeURIComponent(word)}`
  );
  try {
    const parsed = JSON.parse(data);
    if (parsed?.[0]?.[0]) return parsed[0][0][0];
  } catch (_) {}
  return null;
}

async function queryYoudao(word) {
  const data = await httpGet(
    `https://dict.youdao.com/suggest?num=5&doctype=json&q=${encodeURIComponent(word)}`
  );
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
// Free Dictionary API — pronunciation + part of speech
// ═══════════════════════════════════════════════════════════════════════

async function queryDictionaryApi(word) {
  const data = await httpGet(
    `https://api.dictionaryapi.dev/api/v2/entries/en/${encodeURIComponent(word)}`
  );
  try {
    const parsed = JSON.parse(data);
    if (!Array.isArray(parsed) || !parsed.length) return null;

    const entry = parsed[0];
    const phonetic = entry.phonetic || entry.phonetics?.find(p => p.text)?.text || '';

    // Collect all parts of speech
    const posSet = new Set();
    for (const m of entry.meanings || []) {
      if (m.partOfSpeech) posSet.add(m.partOfSpeech);
    }
    const pos = posSet.size > 0 ? [...posSet].join('/') + '.' : '';

    return { phonetic, pos };
  } catch (_) {}
  return null;
}

// ═══════════════════════════════════════════════════════════════════════
// Etymology analysis — rule-based prefix/suffix/root
// ═══════════════════════════════════════════════════════════════════════

const PREFIXES = {
  "a": "不/无/加强(abnormal, amoral)",
  "ab": "偏离/离开(abnormal, abuse)",
  "ad": "朝向/加强(adhere, adjust)",
  "anti": "反对/抗(antibody)",
  "auto": "自己/自动(automatic)",
  "bene": "好/善(benefit)",
  "bi": "二/双(bicycle, bilateral)",
  "bio": "生命/生物(biology)",
  "circum": "周围/环绕(circumstance)",
  "co": "共同/一起(cooperate)",
  "col": "共同/一起(collaborate)",
  "com": "共同/一起/完全(combine)",
  "con": "共同/一起/完全(connect)",
  "contra": "反对/相反(contradict)",
  "de": "向下/除去/完全(decline)",
  "dia": "通过/之间(diagram, dialect)",
  "dis": "不/除去/分开(dislike)",
  "e": "出/向外(emerge, emit)",
  "en": "使…/在…中(enforce)",
  "ex": "出/向外/超出(export)",
  "extra": "超出/以外(extraordinary)",
  "fore": "前/预先(forecast)",
  "il": "不/无(illegal)",
  "im": "不/无/进入(import)",
  "in": "不/无/进入(incomplete)",
  "inter": "之间/互相(international)",
  "intra": "内部(intranet)",
  "ir": "不/无(irregular)",
  "macro": "大/宏观(macroscopic)",
  "mal": "坏/错误(malfunction)",
  "micro": "小/微(microscope)",
  "mid": "中间(midnight)",
  "mis": "错误(misunderstand)",
  "mono": "单一(monopoly)",
  "multi": "多(multiple)",
  "non": "不/非(nonsense)",
  "ob": "反对/阻碍(object)",
  "out": "超过/向外(outcome)",
  "over": "过度/超过(overload)",
  "per": "贯穿/完全(perfect)",
  "poly": "多(polygon)",
  "post": "后/之后(postpone)",
  "pre": "前/预先(preview)",
  "pro": "向前/支持(progress)",
  "re": "再次/返回(return)",
  "semi": "半(semifinal)",
  "sub": "下/次/子(submarine)",
  "super": "超/上(superior)",
  "sur": "超/上(surface)",
  "sym": "共同/相同(sympathy)",
  "syn": "共同/相同(synthesis)",
  "tele": "远(television)",
  "trans": "跨越/转变(transfer)",
  "tri": "三(triangle)",
  "ultra": "超/极端(ultrasonic)",
  "un": "不/相反(unable)",
  "under": "下/不足(underline)",
  "uni": "单一(unique)",
};

const SUFFIXES = {
  "able": "可…的(readable)",
  "age": "状态/集合(shortage)",
  "al": "…的(natural)",
  "ance": "状态/性质(importance)",
  "ant": "…的人/…的(assistant)",
  "ary": "…的/场所(necessary)",
  "ate": "使…/…的(create)",
  "ation": "动作/状态(education)",
  "ed": "已…的(interested)",
  "ence": "状态/性质(difference)",
  "ent": "…的/…的人(different)",
  "er": "…的人/比较级(teacher)",
  "est": "最…(biggest)",
  "ful": "充满…的(beautiful)",
  "fy": "使…化(simplify)",
  "ial": "…的(industrial)",
  "ian": "…的人(musician)",
  "ible": "可…的(possible)",
  "ic": "…的(scientific)",
  "ical": "…的(political)",
  "ify": "使…(beautify)",
  "ing": "正在…(running)",
  "ion": "动作/状态(action)",
  "ish": "…的/像…(childish)",
  "ism": "主义/学说(socialism)",
  "ist": "…家/…者(scientist)",
  "ity": "性质/状态(reality)",
  "ive": "有…倾向的(active)",
  "ize": "使…化(modernize)",
  "less": "无…的(hopeless)",
  "logy": "…学/论(biology)",
  "ly": "…地(quickly)",
  "ment": "行为/状态/物(development)",
  "ness": "性质/状态(happiness)",
  "or": "…者/…器(actor)",
  "ory": "…的/场所(factory)",
  "ous": "有…性质的(famous)",
  "ship": "关系/状态(friendship)",
  "sion": "动作/状态(decision)",
  "tion": "动作/状态(attention)",
  "ture": "动作/结果(mixture)",
  "ty": "性质/状态(safety)",
  "ward": "向…方向(forward)",
};

const ROOTS = {
  "act": "行动/做(action, react)",
  "ag": "做/驱动(agent)",
  "am": "爱(amateur)",
  "anim": "生命/精神(animal)",
  "ann": "年(annual)",
  "aud": "听(audience)",
  "bio": "生命(biology)",
  "cap": "头/拿(captain)",
  "ced": "走/让步(precede)",
  "cept": "拿/取(accept)",
  "cid": "切/杀(decide)",
  "circ": "圆/环(circle)",
  "claim": "喊/叫(claim)",
  "clar": "清楚(clear)",
  "clud": "关闭(include)",
  "cogn": "知道(cognitive)",
  "corp": "身体(corporation)",
  "cred": "相信(credit)",
  "cur": "跑/流动(current)",
  "cycl": "圆/环(cycle)",
  "dict": "说(predict)",
  "don": "给予(donate)",
  "duc": "引导(produce)",
  "dur": "持续(durable)",
  "equ": "相等(equal)",
  "fac": "做/制造(factory)",
  "fer": "带来/承受(transfer)",
  "fid": "信任(confident)",
  "fin": "结束/边界(finish)",
  "flect": "弯曲(reflect)",
  "flu": "流动(fluent)",
  "form": "形状(form)",
  "gen": "产生/种族(generate)",
  "geo": "地球/土地(geography)",
  "grad": "步/走(grade)",
  "graph": "写/画(graph)",
  "her": "黏附(adhere)",
  "ject": "投/扔(inject)",
  "jud": "判断(judge)",
  "lect": "选/收集(collect)",
  "leg": "法律/读(legal)",
  "lev": "举起/轻(elevate)",
  "loc": "位置(locate)",
  "log": "说/思想(dialogue)",
  "lumin": "光(illuminate)",
  "man": "手(manual)",
  "mand": "命令(command)",
  "mar": "海(marine)",
  "medi": "中间(medium)",
  "memor": "记忆(memory)",
  "ment": "头脑/心智(mental)",
  "meter": "测量(thermometer)",
  "migr": "迁移(migrate)",
  "min": "小/突出(minimum)",
  "miss": "送/发送(mission)",
  "mob": "移动(mobile)",
  "mot": "移动(motor)",
  "nat": "出生/天生(nature)",
  "neg": "否定(negative)",
  "norm": "规则/标准(normal)",
  "not": "知道/标记(note)",
  "nov": "新(novel)",
  "numer": "数字(number)",
  "oper": "工作(operate)",
  "opt": "选择/最好(option)",
  "ord": "顺序(order)",
  "part": "部分/分开(part)",
  "pass": "通过/感觉(passage)",
  "path": "感觉/疾病(sympathy)",
  "ped": "脚(pedal)",
  "pel": "推动(compel)",
  "pend": "悬挂/支付(depend)",
  "pet": "追求/寻求(compete)",
  "phon": "声音(telephone)",
  "photo": "光(photograph)",
  "plic": "折叠(complicated)",
  "pol": "城市/政治(politics)",
  "pon": "放置(postpone)",
  "port": "携带/门(transport)",
  "pos": "放置(position)",
  "press": "压(compress)",
  "prim": "第一(primary)",
  "psych": "心灵(psychology)",
  "publ": "公共(public)",
  "put": "思考/计算(compute)",
  "quer": "寻求(question)",
  "rect": "直/正确(correct)",
  "rupt": "断裂(interrupt)",
  "scend": "爬升(ascend)",
  "sci": "知道(science)",
  "scrib": "写(describe)",
  "secut": "跟随(consecutive)",
  "sens": "感觉(sense)",
  "sequ": "跟随(sequence)",
  "serv": "保持/服务(observe)",
  "sign": "标记(signal)",
  "simil": "相似(similar)",
  "sist": "站立(consist)",
  "solv": "解开(solve)",
  "spec": "看(inspect)",
  "spir": "呼吸(inspire)",
  "struct": "建造(construct)",
  "sum": "拿/取(assume)",
  "tact": "触碰(contact)",
  "tain": "拿住(contain)",
  "tect": "遮盖(detect)",
  "tempor": "时间(temporary)",
  "tend": "伸展/趋向(tend)",
  "terr": "土地(territory)",
  "test": "证明(testify)",
  "therm": "热(thermal)",
  "tract": "拉/拖(attract)",
  "trib": "给予(tribute)",
  "urb": "城市(urban)",
  "vac": "空(vacuum)",
  "val": "价值/力量(value)",
  "ven": "来(adventure)",
  "ver": "真实(verify)",
  "vert": "转(convert)",
  "vid": "看(video)",
  "viv": "生命/活(vivid)",
  "voc": "声音/呼喊(voice)",
  "volv": "卷/转(involve)",
};

function analyzeWordStructure(word) {
  const parts = [];
  let w = word.toLowerCase();

  // Longest-match prefix
  const sortedPrefixes = Object.keys(PREFIXES).sort((a, b) => b.length - a.length);
  for (const prefix of sortedPrefixes) {
    if (w.startsWith(prefix) && prefix.length >= 2) {
      const remaining = w.slice(prefix.length);
      if (remaining.length >= 2) {
        parts.push(`前缀: ${prefix}(${PREFIXES[prefix]})`);
        w = remaining;
        break;
      }
    }
  }

  // Longest-match suffix
  const sortedSuffixes = Object.keys(SUFFIXES).sort((a, b) => b.length - a.length);
  for (const suffix of sortedSuffixes) {
    if (w.endsWith(suffix) && suffix.length >= 2) {
      const remaining = w.slice(0, -suffix.length);
      if (remaining.length >= 2) {
        parts.push(`后缀: ${suffix}(${SUFFIXES[suffix]})`);
        w = remaining;
        break;
      }
    }
  }

  // Root match within remaining stem
  const sortedRoots = Object.keys(ROOTS).sort((a, b) => b.length - a.length);
  for (const root of sortedRoots) {
    if (w.includes(root) && root.length >= 2) {
      parts.push(`词根: ${root}(${ROOTS[root]})`);
      break;
    }
  }

  return parts.length > 0 ? parts.join(' | ') : '';
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
          if (fs.statSync(full).isDirectory() && fs.existsSync(path.join(full, '.obsidian')))
            candidates.push(full);
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
  // Returns [{word, meaning}] — word is extracted, meaning is the full block including ### header
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
    entries.push({ word, meaning: trimmed });
  }
  return entries;
}

function buildEntryBlock(word, pronunciation, pos, meaning, etymology) {
  const lines = [];
  if (pronunciation) {
    lines.push(`### ${word} ${pronunciation}`);
  } else {
    lines.push(`### ${word}`);
  }
  const tag = pos ? `[${pos}] ${meaning}` : meaning;
  lines.push(tag);
  if (etymology) {
    lines.push(`← *${etymology}*`);
  }
  return lines.join('\n');
}

function writeToObsidian(vaultPath, targetFile, word, pronunciation, pos, meaning, etymology) {
  const targetDir = path.dirname(path.join(vaultPath, targetFile));
  fs.mkdirSync(targetDir, { recursive: true });

  const baseName = path.basename(targetFile, '.md');
  const ext = '.md';

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

  if (entries.some(e => e.word === word.toLowerCase())) {
    return { status: 'exists', word, pronunciation, pos, meaning, etymology };
  }

  const block = buildEntryBlock(word, pronunciation, pos, meaning, etymology);
  entries.push({ word: word.toLowerCase(), meaning: block });
  entries.sort((a, b) => a.word.localeCompare(b.word));

  const lines = ['# 论文词汇表\n'];
  for (const e of entries) {
    lines.push(`${e.meaning}\n`);
  }
  fs.writeFileSync(filePath, lines.join('\n'), 'utf-8');

  const fullPath = path.join(vaultPath, targetFile);
  const writtenTo = filePath === fullPath ? targetFile : path.relative(vaultPath, filePath);

  return { status: 'ok', word, pronunciation, pos, meaning, etymology, file: writtenTo };
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
    let message = 'Native host v3.0 (Node.js) is running';
    if (vault) message += `\n检测到 Vault: ${vault}`;
    return { status: 'ok', message };
  }

  const word = (msg.word || '').trim().toLowerCase();
  if (!isValidWord(word)) {
    return { status: 'error', message: '请输入有效的英文单词或词组' };
  }

  const settings = msg.settings || {};
  let vaultPath = settings.vault_path || '';

  if (!vaultPath || !fs.existsSync(vaultPath)) {
    const detected = detectObsidianVault();
    if (detected) vaultPath = detected;
    else return { status: 'error', message: '未找到 Obsidian Vault，请在插件中手动配置路径' };
  }

  const targetFile = settings.target_file || '论文单词.md';
  const apiChoice = settings.dictionary_api || 'google';

  // Step 1: Translation (page → Google → Youdao)
  let meaning = (msg.pageTranslation || '').trim();
  if (!meaning) {
    if (apiChoice === 'youdao') {
      meaning = await queryYoudao(word);
      if (!meaning) meaning = await queryGoogleTranslate(word);
    } else {
      meaning = await queryGoogleTranslate(word);
      if (!meaning) meaning = await queryYoudao(word);
    }
  }
  if (!meaning) {
    return { status: 'error', message: '翻译失败，请检查网络后重试' };
  }

  // Step 2: Pronunciation + POS (Free Dictionary API)
  let pronunciation = '', pos = '';
  const dict = await queryDictionaryApi(word);
  if (dict) {
    pronunciation = dict.phonetic;
    pos = dict.pos;
  }

  // Step 3: Etymology (rule-based morpheme analysis)
  const etymology = analyzeWordStructure(word);

  return writeToObsidian(vaultPath, targetFile, word, pronunciation, pos, meaning, etymology);
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
