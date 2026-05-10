(function () {
  let lastCopiedText = "";
  let lastCopyTime = 0;

  function isValidInput(text) {
    // Strip trailing punctuation that might get included in selection
    const t = text.replace(/[.,;:!?。，；：！？、""'']+$/, "").trim();
    return /^[a-zA-Z][a-zA-Z\s\-]{1,79}$/.test(t) && t.length >= 2;
  }

  // ── Extract translation from Immersive Translate full-page bilingual mode ──
  function extractImmersiveTranslate() {
    // Immersive Translate uses these classes in all modes
    const classPatterns = [
      "font.immersive-translate-target-inner",
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
        const fonts = sibling.querySelectorAll("font.immersive-translate-target-inner, [class*='immersive-translate-target']");
        for (const f of fonts) {
          const text = f.textContent.trim();
          if (hasChinese(text)) return text;
        }
        // Also check if the sibling ITSELF contains Chinese (e.g., a <p> with Chinese text)
        if (hasChinese(sibling.textContent) && sibling.textContent.trim().length < 1000) {
          return sibling.textContent.trim();
        }
        sibling = sibling.nextElementSibling;
      }
    }

    // Fallback: first Chinese text from any Immersive Translate element
    for (const el of targets) {
      const text = el.textContent.trim();
      if (hasChinese(text)) return text;
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

    let parent = node;
    for (let i = 0; i < 8 && parent; i++) {
      const all = parent.querySelectorAll("p, div, span, font, li");
      for (const el of all) {
        const text = el.textContent.trim();
        if (text.length > 3 && text.length < 500 && hasChinese(text)) {
          return text;
        }
      }
      parent = parent.parentElement;
    }

    // Broad scan: first Chinese text on the page
    const all = document.querySelectorAll("p, div, span, font");
    for (const el of all) {
      const text = el.textContent.trim();
      if (text.length > 3 && text.length < 500 && hasChinese(text)) {
        return text;
      }
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

    // Clean trailing punctuation for the word sent to host
    const word = text.replace(/[.,;:!?。，；：！？、""'']+$/, "").trim().toLowerCase();

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
      sendResponse({ text: isValidInput(text) ? text.toLowerCase() : "" });
    }
  });
})();
