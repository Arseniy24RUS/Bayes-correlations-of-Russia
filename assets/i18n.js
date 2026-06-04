(function () {
  const SUPPORTED = ['en', 'ru'];
  const DEFAULT_LANG = 'en';
  const state = {
    lang: DEFAULT_LANG,
    dictionaries: {},
    observer: null,
    applying: false,
  };

  function deviceLanguage() {
    const saved = localStorage.getItem('lang');
    if (SUPPORTED.includes(saved)) return saved;
    const langs = navigator.languages && navigator.languages.length ? navigator.languages : [navigator.language || ''];
    return langs.some((lang) => String(lang).toLowerCase().startsWith('ru')) ? 'ru' : 'en';
  }

  function lookup(obj, path) {
    return String(path).split('.').reduce((acc, key) => (acc && acc[key] !== undefined ? acc[key] : undefined), obj);
  }

  function interpolate(text, vars) {
    if (!vars) return text;
    return String(text).replace(/\{\{\s*([\w.-]+)\s*\}\}/g, (_, key) => (vars[key] ?? ''));
  }

  function currentDict() {
    return state.dictionaries[state.lang] || {};
  }

  function t(key, fallback, vars) {
    const dict = currentDict();
    const value = lookup(dict, key);
    if (value !== undefined) return interpolate(value, vars);
    if (fallback !== undefined) {
      const mapped = translateText(fallback);
      return interpolate(mapped, vars);
    }
    return key;
  }

  function translateText(raw) {
    if (raw === null || raw === undefined) return raw;
    const dict = currentDict();
    const source = String(raw);
    const trimmed = source.trim();
    if (!trimmed) return raw;
    const value =
      (dict.text && dict.text[trimmed]) ||
      (dict.regions && dict.regions[trimmed]) ||
      (dict.organs && dict.organs[trimmed]) ||
      trimmed;
    return source.replace(trimmed, value);
  }

  function translateNode(node) {
    if (!node.nodeValue || !node.nodeValue.trim()) return;
    if (node.__i18nOriginal === undefined) node.__i18nOriginal = node.nodeValue;
    node.nodeValue = state.lang === 'ru' ? node.__i18nOriginal : translateText(node.__i18nOriginal);
  }

  function translateAttr(el, attr) {
    if (!el.hasAttribute(attr)) return;
    const store = `i18nOriginal${attr}`;
    if (el[store] === undefined) el[store] = el.getAttribute(attr);
    el.setAttribute(attr, state.lang === 'ru' ? el[store] : translateText(el[store]));
  }

  function apply(root) {
    if (state.applying) return;
    state.applying = true;
    const target = root || document.body;
    target.querySelectorAll?.('[data-i18n], [data-i18n-html]').forEach((el) => {
      const textKey = el.getAttribute('data-i18n');
      const htmlKey = el.getAttribute('data-i18n-html');
      if (textKey) {
        if (el.__i18nOriginalText === undefined) el.__i18nOriginalText = el.textContent;
        el.textContent = t(textKey, el.__i18nOriginalText);
      }
      if (htmlKey) {
        if (el.__i18nOriginalHtml === undefined) el.__i18nOriginalHtml = el.innerHTML;
        el.innerHTML = t(htmlKey, el.__i18nOriginalHtml);
      }
    });
    const walker = document.createTreeWalker(target, NodeFilter.SHOW_TEXT, {
      acceptNode(node) {
        const parent = node.parentElement;
        if (!parent) return NodeFilter.FILTER_REJECT;
        if (parent.closest('[data-i18n], [data-i18n-html]')) return NodeFilter.FILTER_REJECT;
        if (['SCRIPT', 'STYLE', 'NOSCRIPT', 'CODE'].includes(parent.tagName)) return NodeFilter.FILTER_REJECT;
        return NodeFilter.FILTER_ACCEPT;
      },
    });
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach(translateNode);
    target.querySelectorAll?.('[placeholder], [aria-label], [title], img[alt]').forEach((el) => {
      ['placeholder', 'aria-label', 'title', 'alt'].forEach((attr) => translateAttr(el, attr));
    });
    updateToggle();
    state.applying = false;
  }

  function updateToggle() {
    const button = document.querySelector('[data-testid="language-toggle"]');
    if (!button) return;
    const next = state.lang === 'ru' ? 'EN' : 'RU';
    button.textContent = next;
    button.setAttribute('aria-label', state.lang === 'ru' ? 'Switch to English' : 'Переключить на русский');
    button.setAttribute('title', state.lang === 'ru' ? 'Switch to English' : 'Переключить на русский');
  }

  function ensureToggle() {
    if (document.querySelector('[data-testid="language-toggle"]')) return;
    const style = document.createElement('style');
    style.textContent = `
      .language-toggle {
        position: fixed;
        top: 14px;
        right: 14px;
        z-index: 1000;
        width: auto !important;
        max-width: 48px;
        min-width: 44px;
        min-height: 34px;
        border-radius: 999px;
        border: 1px solid rgba(11, 99, 229, .35);
        background: #ffffff;
        color: #0b63e5;
        box-shadow: 0 4px 16px rgba(0,0,0,.12);
        font-weight: 700;
        letter-spacing: 0;
        padding: 6px 11px;
      }
      .language-toggle:hover { background: #edf4ff; }
      @media (max-width: 640px) {
        .language-toggle { top: 8px; right: 8px; width: auto !important; max-width: 44px; min-width: 40px; min-height: 32px; padding: 5px 9px; }
        .header-title { padding-right: 54px; }
      }
    `;
    document.head.appendChild(style);
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'language-toggle';
    button.dataset.testid = 'language-toggle';
    button.addEventListener('click', () => toggleLanguage());
    document.body.appendChild(button);
    updateToggle();
  }

  async function loadDictionary(lang) {
    if (state.dictionaries[lang]) return state.dictionaries[lang];
    const response = await fetch(`locales/${lang}.json`);
    if (!response.ok) throw new Error(`Unable to load ${lang}.json`);
    state.dictionaries[lang] = await response.json();
    return state.dictionaries[lang];
  }

  async function setLanguage(lang) {
    state.lang = SUPPORTED.includes(lang) ? lang : DEFAULT_LANG;
    localStorage.setItem('lang', state.lang);
    await loadDictionary(state.lang);
    document.documentElement.lang = state.lang;
    const meta = currentDict().meta || {};
    if (meta.title) document.title = meta.title;
    const description = document.querySelector('meta[name="description"]');
    if (description && meta.description) description.setAttribute('content', meta.description);
    ensureToggle();
    apply(document.body);
    window.dispatchEvent(new CustomEvent('i18n:change', { detail: { lang: state.lang } }));
  }

  function getLanguage() {
    return state.lang;
  }

  function toggleLanguage() {
    return setLanguage(state.lang === 'ru' ? 'en' : 'ru');
  }

  const ready = Promise.all([loadDictionary('ru'), loadDictionary('en')])
    .then(() => setLanguage(deviceLanguage()))
    .then(() => {
      state.observer = new MutationObserver((mutations) => {
        if (state.applying) return;
        for (const mutation of mutations) {
          mutation.addedNodes.forEach((node) => {
            if (node.nodeType === Node.TEXT_NODE) translateNode(node);
            if (node.nodeType === Node.ELEMENT_NODE) apply(node);
          });
        }
      });
      state.observer.observe(document.body, { childList: true, subtree: true });
    })
    .catch((error) => console.error('i18n initialization failed', error));

  window.AppI18n = { t, getLanguage, setLanguage, toggleLanguage, apply, ready, translateText };
})();
