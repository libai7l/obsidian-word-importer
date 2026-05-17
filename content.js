(function () {
  const MAX_INPUT_CHARS = 800;
  let lastCopiedText = "";
  let lastCopyTime = 0;

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
    if (t.length < 2 || t.length > MAX_INPUT_CHARS) return false;
    if (!/[a-zA-Z]/.test(t)) return false;
    if (/[^\x20-\x7E]/.test(t)) return false;
    return /^[a-zA-Z0-9"'(]/.test(t);
  }

  // ── Extract translation from Immersive Translate full-page bilingual mode ──
  function extractImmersiveTranslate() {
    // Immersive Translate uses these classes in all modes
    const classPatterns = [
      "[class*='immersive-translate-target-inner']",
      "[class*='immersive-translate-target']",
      "[class*='immersive-translate']",
    ];

    let targets = [];
    for (const sel of classPatterns) {
      try {
        targets = document.querySelectorAll(sel);
        if (targets.length > 0) break;
      } catch (_) {}
    }

    if (targets.length === 0) {
      // Last resort: any element with Chinese text near the selection
      return findNearbyChinese();
    }

    // Find the paragraph containing the selection
    const selection = document.getSelection();
    let anchorEl = null;
    if (selection && selection.rangeCount > 0) {
      anchorEl = selection.getRangeAt(0).startContainer;
      if (anchorEl && anchorEl.nodeType === 3) anchorEl = anchorEl.parentElement;
    }

    // Walk up to find the containing block element
    let englishBlock = anchorEl;
    while (englishBlock && !isBlockElement(englishBlock)) {
      englishBlock = englishBlock.parentElement;
    }

    if (englishBlock) {
      // Look for the NEXT sibling block containing Chinese translation
      let sibling = englishBlock.nextElementSibling;
      for (let i = 0; i < 5 && sibling; i++) {
        const fonts = sibling.querySelectorAll("[class*='immersive-translate-target-inner'], [class*='immersive-translate-target']");
        for (const f of fonts) {
          const text = f.textContent.trim();
          if (isValidTranslation(text)) return text;
        }
        // Also check if the sibling ITSELF contains Chinese (e.g., a <p> with Chinese text)
        if (hasChinese(sibling.textContent) && sibling.textContent.trim().length < 1000 && isValidTranslation(sibling.textContent.trim())) {
          return sibling.textContent.trim();
        }
        sibling = sibling.nextElementSibling;
      }
    }

    // Fallback: first valid Chinese text from any Immersive Translate element
    for (const el of targets) {
      const text = el.textContent.trim();
      if (isValidTranslation(text)) return text;
    }

    // Last resort
    return findNearbyChinese();
  }

  // Scan for any Chinese text block near the selection
  function findNearbyChinese() {
    const selection = document.getSelection();
    if (!selection || selection.rangeCount === 0) return null;
    let node = selection.getRangeAt(0).startContainer;
    if (node && node.nodeType === 3) node = node.parentElement;

    // Skip navigation, header, footer, sidebar elements
    const skipTags = /^(NAV|HEADER|FOOTER|ASIDE|MENU|BUTTON|INPUT|SELECT|TEXTAREA|LABEL)$/;

    let parent = node;
    const seen = new Set();
    for (let i = 0; i < 5 && parent; i++) {
      if (seen.has(parent)) break;
      seen.add(parent);
      const all = Array.from(parent.querySelectorAll("p, div, span, font, li")).slice(0, 300);
      for (const el of all) {
        if (skipTags.test(el.tagName) || el.closest("nav, header, footer, aside, [role='navigation'], [role='banner']")) continue;
        const text = el.textContent.trim();
        if (isValidTranslation(text)) return text;
      }
      parent = parent.parentElement;
    }

    // Bounded broad scan: skip UI areas
    const all = Array.from(document.querySelectorAll("p, div, span, font")).slice(0, 1000);
    for (const el of all) {
      if (skipTags.test(el.tagName) || el.closest("nav, header, footer, aside, [role='navigation'], [role='banner']")) continue;
      const text = el.textContent.trim();
      if (isValidTranslation(text)) return text;
    }
    return null;
  }

  function isBlockElement(el) {
    if (!el || !el.tagName) return false;
    return /^(P|DIV|LI|TD|BLOCKQUOTE|SECTION|ARTICLE|H[1-6]|MAIN|ASIDE)$/.test(el.tagName);
  }

  function hasChinese(text) {
    return /[一-鿿]/.test(text);
  }

  // UI keywords that are NOT valid translations
  const UI_NOISE_WORDS = [
    '主题', '设置', '登录', '注册', '关于', '搜索', '首页', '返回', '更多',
    '评论', '评论区', '发表评论', '回复', '分享', '点赞', '收藏', '下载', '上传',
    '提交', '取消', '确定', '保存', '编辑', '删除', '新建', '打开', '关闭',
    '菜单', '导航', '个人', '退出', '语言', '帮助', '用户', '密码', '账号',
    '邮箱', '手机', '验证码', '重置', '作者', '时间', '日期', '上一页', '下一页',
    '注释', '说明', '注意', '提示', '备注', '翻译',
  ];

  const UI_NOISE = new RegExp(`^(${UI_NOISE_WORDS.join('|')})\\s*[:：]?$`);
  const UI_NOISE_PREFIX = new RegExp(`^(${UI_NOISE_WORDS.join('|')})\\s*[:：]\\s*`, 'u');

  // Garbage patterns: cookie banners, privacy notices, navigation UI, etc.
  const GARBAGE_PATTERNS = [
    /Cookie/i,
    /隐私政策/,
    /接受.*cookie/i,
    /cookie.*偏好/i,
    /个性化.*广告/,
    /有针对性的广告/,
    /定制.*广告/,
    /新窗(口|中)打开/,
    /打开外部网站/,
    /本网站.*cookie/i,
    /我们使用.*cookie/i,
    /使用cookie/i,
    /数据保护/,
    /数据安全/,
    /同意并继续/,
    /点击.*接受/,
    /条款.*条件/,
    /服务条款/,
    /隐私.*条款/,
    /隐私.*设置/,
    /了解更多/,
    /阅读更多/,
    /查看详情/,
    /广告投放/,
    /广告商/,
    /第三方.*广告/,
    /行为.*广告/,
    /个性化.*内容/,
    /网站功能/,
    /基本功能/,
    /社交.*插件/,
    /分析.*个性化/,
    /数据处理/,
    /数据收集/,
    /跟踪.*技术/,
  ];

  function isValidTranslation(text) {
    const t = text.trim();
    const compact = t.replace(/[\s:：,，.。;；!！?？]+$/g, "");
    // Must contain real Chinese content, while allowing short word translations.
    const cnChars = t.replace(/[\s\d\w\p{P}]/gu, "");
    if (cnChars.length < 2) return false;
    // Must not be a UI keyword
    if (UI_NOISE.test(t) || UI_NOISE.test(compact)) return false;
    // Must not start with a UI keyword prefix (e.g., "评论：实验性的")
    if (UI_NOISE_PREFIX.test(t)) return false;
    // Must contain at least some actual semantic content (not just single char repeated)
    if (new Set(cnChars).size < 2) return false;
    // Reject garbage (cookie banners, privacy notices, etc.)
    for (const pattern of GARBAGE_PATTERNS) {
      if (pattern.test(t)) return false;
    }
    // Reject text with too many URLs or domain references
    const urlCount = (t.match(/https?:\/\/|www\.|\.com|\.cn|\.org/g) || []).length;
    if (urlCount >= 1 && cnChars.length < 30) return false;
    // Reject text that looks like a footer/nav with multiple short fragments
    const shortFragments = t.split(/\s+/).filter(s => s.length > 1 && s.length < 5);
    if (shortFragments.length > 5 && cnChars.length < 20) return false;
    // Reject text where a single regex keyword dominates
    const garbageWords = /(接受|拒绝|订阅|关注|分享到|转发|收藏|点赞|举报|反馈)/g;
    const garbageCount = (t.match(garbageWords) || []).length;
    if (garbageCount >= 3 && cnChars.length < 30) return false;
    return true;
  }

  // ── Copy event handler ──
  function onCopy(e) {
    const selection = document.getSelection();
    let text = (selection && selection.toString().trim()) || "";

    if (!text) {
      const clipboardData = e.clipboardData;
      if (clipboardData) {
        text = clipboardData.getData("text/plain").trim();
      }
    }

    if (!isValidInput(text)) return;

    const word = normalizeInput(text);

    const now = Date.now();
    if (word === lastCopiedText && now - lastCopyTime < 1000) return;
    lastCopiedText = word;
    lastCopyTime = now;

    // Primary translation source: Immersive Translate on the page
    const pageTranslation = extractImmersiveTranslate();

    chrome.runtime.sendMessage({
      type: "WORD_COPIED",
      word: word,
      pageTranslation: pageTranslation,
    }).catch(() => {});
  }

  function onContextMenu() {
    lastCopiedText = document.getSelection().toString().trim();
  }

  document.addEventListener("copy", onCopy, true);
  document.addEventListener("contextmenu", onContextMenu, true);

  chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
    if (msg.type === "GET_SELECTED_TEXT") {
      const text = document.getSelection().toString().trim();
      sendResponse({ text: isValidInput(text) ? normalizeInput(text) : "" });
    }
  });
})();
