const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

const STORAGE = {
  theme: "fieldnotes-theme",
  fontSize: "fieldnotes-reader-size",
  readChapters: "fieldnotes-read-chapters",
  lastChapter: "fieldnotes-last-chapter",
  progress: "fieldnotes-book-progress"
};

const state = {
  book: null,
  chapterCache: new Map(),
  currentId: null,
  readChapters: new Set(),
  progress: 0,
  readerSize: 18,
  scrollQueued: false,
  searchTimer: null
};

function safeStorageGet(key) {
  try { return localStorage.getItem(key); } catch { return null; }
}

function safeStorageSet(key, value) {
  try { localStorage.setItem(key, value); } catch { /* Private browsing may disable storage. */ }
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function renderInline(text) {
  const code = [];
  let value = String(text).replace(/`([^`]+)`/g, (_match, snippet) => {
    const token = `\u0000${code.length}\u0000`;
    code.push(escapeHtml(snippet));
    return token;
  });
  value = escapeHtml(value)
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*([^*]+)\*/g, "<em>$1</em>")
    .replace(/\u0000(\d+)\u0000/g, (_match, index) => `<code>${code[Number(index)]}</code>`);
  return value;
}

function isTableDivider(line) {
  return /^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)+\|?\s*$/.test(line);
}

function tableCells(line) {
  return line.trim().replace(/^\|/, "").replace(/\|$/, "").split("|").map(cell => cell.trim());
}

function startsBlock(lines, index) {
  const line = lines[index] ?? "";
  return /^#{1,4}\s/.test(line)
    || /^>\s?/.test(line)
    || /^\s*[-*+]\s+/.test(line)
    || /^\s*\d+\.\s+/.test(line)
    || /^\s*```/.test(line)
    || /^\s*---+\s*$/.test(line)
    || (line.trim().startsWith("|") && isTableDivider(lines[index + 1] ?? ""));
}

function renderMarkdown(markdown, { hideFirstHeading = false } = {}) {
  const lines = String(markdown).replace(/\r/g, "").split("\n");
  if (hideFirstHeading) {
    const first = lines.findIndex(line => line.trim());
    if (first >= 0 && /^#\s+/.test(lines[first])) lines.splice(first, 1);
  }

  const html = [];
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    if (!line.trim()) { i += 1; continue; }

    const heading = line.match(/^(#{1,4})\s+(.+?)\s*#*\s*$/);
    if (heading) {
      const level = Math.min(heading[1].length, 4);
      html.push(`<h${level}>${renderInline(heading[2])}</h${level}>`);
      i += 1;
      continue;
    }

    if (/^\s*```/.test(line)) {
      const codeLines = [];
      i += 1;
      while (i < lines.length && !/^\s*```/.test(lines[i])) codeLines.push(lines[i++]);
      if (i < lines.length) i += 1;
      html.push(`<pre><code>${escapeHtml(codeLines.join("\n"))}</code></pre>`);
      continue;
    }

    if (/^\s*---+\s*$/.test(line)) {
      html.push("<hr>");
      i += 1;
      continue;
    }

    if (line.trim().startsWith("|") && isTableDivider(lines[i + 1] ?? "")) {
      const headers = tableCells(line);
      i += 2;
      const rows = [];
      while (i < lines.length && lines[i].trim().startsWith("|")) rows.push(tableCells(lines[i++]));
      const head = headers.map(cell => `<th scope="col">${renderInline(cell)}</th>`).join("");
      const body = rows.map(row => `<tr>${headers.map((_cell, index) => `<td>${renderInline(row[index] ?? "")}</td>`).join("")}</tr>`).join("");
      html.push(`<div class="table-scroll"><table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>`);
      continue;
    }

    if (/^>\s?/.test(line)) {
      const quote = [];
      while (i < lines.length && /^>\s?/.test(lines[i])) quote.push(lines[i++].replace(/^>\s?/, ""));
      const quoteHtml = quote.map(part => `<p>${renderInline(part)}</p>`).join("");
      html.push(`<blockquote>${quoteHtml}</blockquote>`);
      continue;
    }

    const unordered = line.match(/^\s*[-*+]\s+(.+)/);
    const ordered = line.match(/^\s*\d+\.\s+(.+)/);
    if (unordered || ordered) {
      const isOrdered = Boolean(ordered);
      const items = [];
      while (i < lines.length) {
        const match = lines[i].match(isOrdered ? /^\s*\d+\.\s+(.+)/ : /^\s*[-*+]\s+(.+)/);
        if (!match) break;
        items.push(`<li>${renderInline(match[1])}</li>`);
        i += 1;
      }
      const tag = isOrdered ? "ol" : "ul";
      html.push(`<${tag}>${items.join("")}</${tag}>`);
      continue;
    }

    const paragraph = [line.trim()];
    i += 1;
    while (i < lines.length && lines[i].trim() && !startsBlock(lines, i)) paragraph.push(lines[i++].trim());
    html.push(`<p>${renderInline(paragraph.join(" "))}</p>`);
  }
  return html.join("\n");
}

function currentChapterIndex(id = state.currentId) {
  if (!state.book || !id) return -1;
  return state.book.chapters.findIndex(chapter => chapter.id === id);
}

async function getChapter(chapter) {
  if (state.chapterCache.has(chapter.id)) return state.chapterCache.get(chapter.id);
  const response = await fetch(`book/chapters/${encodeURIComponent(chapter.id)}.md`);
  if (!response.ok) throw new Error(`Could not load “${chapter.title}”.`);
  const text = await response.text();
  state.chapterCache.set(chapter.id, text);
  return text;
}

function chapterDisplayNumber(index) {
  const last = state.book.chapters.length - 1;
  if (index === 0) return "00";
  if (index === last) return "↗";
  return String(index).padStart(2, "0");
}

function renderChapterList() {
  const list = $("#chapterList");
  list.replaceChildren();
  state.book.chapters.forEach((chapter, index) => {
    const item = document.createElement("li");
    const button = document.createElement("button");
    button.type = "button";
    button.className = "chapter-link";
    button.dataset.chapterId = chapter.id;
    button.setAttribute("aria-label", `Open ${chapter.title}`);

    const number = document.createElement("span");
    number.className = "chapter-no";
    number.textContent = chapterDisplayNumber(index);
    const title = document.createElement("span");
    title.className = "chapter-label";
    title.textContent = chapter.title;
    const readDot = document.createElement("span");
    readDot.className = "read-dot";
    readDot.setAttribute("aria-hidden", "true");

    button.append(number, title, readDot);
    button.addEventListener("click", () => loadChapter(chapter.id));
    item.append(button);
    list.append(item);
  });
  $("#chapterCount").textContent = String(state.book.chapters.length).padStart(2, "0");
  updateNavigationState();
}

function updateNavigationState() {
  $$(".chapter-link").forEach(button => {
    const isActive = button.dataset.chapterId === state.currentId;
    button.classList.toggle("is-active", isActive);
    button.classList.toggle("is-read", state.readChapters.has(button.dataset.chapterId));
    if (isActive) button.setAttribute("aria-current", "page");
    else button.removeAttribute("aria-current");
  });
  const homeActive = !state.currentId;
  $("#homeNav").classList.toggle("is-active", homeActive);
  if (homeActive) $("#homeNav").setAttribute("aria-current", "page");
  else $("#homeNav").removeAttribute("aria-current");
}

function updateProgress() {
  if (!state.book) return;
  const percent = Math.round(state.progress);
  $("#progressPercent").textContent = `${percent}%`;
  $("#progressFill").style.width = `${percent}%`;
  $("#progressTrack").setAttribute("aria-valuenow", String(percent));
}

function measureProgress() {
  if (!state.currentId || !state.book) return;
  const index = currentChapterIndex();
  const reader = $("#reader");
  const articleHeight = reader.scrollHeight;
  const scrollWithin = window.innerHeight - reader.getBoundingClientRect().top;
  const denominator = Math.max(1, articleHeight);
  const fraction = Math.max(0, Math.min(1, scrollWithin / denominator));
  const measured = ((index + fraction) / state.book.chapters.length) * 100;
  state.progress = Math.max(state.progress, Math.min(100, measured));
  safeStorageSet(STORAGE.progress, String(state.progress));
  updateProgress();
}

function scheduleProgressMeasure() {
  if (state.scrollQueued) return;
  state.scrollQueued = true;
  window.requestAnimationFrame(() => {
    state.scrollQueued = false;
    measureProgress();
  });
}

function setLocation(hash, replace = false) {
  const nextUrl = `${window.location.pathname}${window.location.search}${hash ? `#${hash}` : ""}`;
  if (replace) window.history.replaceState({}, "", nextUrl);
  else window.history.pushState({}, "", nextUrl);
}

function closeMobileMenu() {
  document.body.classList.remove("sidebar-is-open");
  $("#menuToggle").setAttribute("aria-expanded", "false");
  $("#menuToggle").setAttribute("aria-label", "Open table of contents");
}

function renderPagination(index) {
  const nav = $("#chapterPagination");
  nav.replaceChildren();
  const chapters = state.book.chapters;
  const previous = chapters[index - 1];
  const next = chapters[index + 1];

  for (const item of [previous, next]) {
    if (!item) {
      const empty = document.createElement("div");
      empty.className = "page-turn empty";
      empty.setAttribute("aria-hidden", "true");
      nav.append(empty);
      continue;
    }
    const button = document.createElement("button");
    button.type = "button";
    button.className = `page-turn${item === next ? " next" : ""}`;
    const label = document.createElement("span");
    label.className = "page-turn-label";
    label.textContent = item === next ? "Next section →" : "← Previous section";
    const title = document.createElement("span");
    title.className = "page-turn-title";
    title.textContent = item.title;
    button.append(label, title);
    button.addEventListener("click", () => loadChapter(item.id));
    nav.append(button);
  }
}

async function loadChapter(id, { updateHistory = true, shouldScroll = true } = {}) {
  const chapter = state.book?.chapters.find(item => item.id === id);
  if (!chapter) return;
  const index = currentChapterIndex(id);
  state.currentId = id;
  $("#landing").hidden = true;
  $("#reader").hidden = false;
  $("#currentLocation").textContent = chapter.title;
  $("#chapterKicker").textContent = chapter.kicker;
  $("#chapterTitle").textContent = chapter.title;
  $("#chapterSummary").textContent = chapter.summary;
  $("#chapterIndex").textContent = index === 0
    ? "OPENING NOTE"
    : index === state.book.chapters.length - 1
      ? "WORKED DESIGN"
      : `CHAPTER ${String(index).padStart(2, "0")} · 08`;
  $("#articleBody").innerHTML = '<p class="chapter-loading">Opening this chapter…</p>';
  renderPagination(index);
  updateNavigationState();
  document.title = `${chapter.title} — ${state.book.title}`;
  safeStorageSet(STORAGE.lastChapter, id);
  state.readChapters.add(id);
  safeStorageSet(STORAGE.readChapters, JSON.stringify([...state.readChapters]));
  updateNavigationState();
  closeMobileMenu();
  if (updateHistory) setLocation(id);
  if (shouldScroll) window.scrollTo({ top: 0, behavior: "smooth" });

  try {
    const markdown = await getChapter(chapter);
    if (state.currentId !== id) return;
    $("#articleBody").innerHTML = renderMarkdown(markdown, { hideFirstHeading: true });
    scheduleProgressMeasure();
  } catch (error) {
    if (state.currentId !== id) return;
    $("#articleBody").innerHTML = `<p class="chapter-error">${escapeHtml(error.message)} Please refresh and try again.</p>`;
  }
}

function showHome({ updateHistory = true, shouldScroll = true } = {}) {
  state.currentId = null;
  $("#reader").hidden = true;
  $("#landing").hidden = false;
  $("#currentLocation").textContent = "The book";
  document.title = `${state.book.title} — ${state.book.author}`;
  updateNavigationState();
  closeMobileMenu();
  if (updateHistory) setLocation("");
  if (shouldScroll) window.scrollTo({ top: 0, behavior: "smooth" });
}

function setupTheme() {
  const saved = safeStorageGet(STORAGE.theme);
  const theme = saved === "dark" ? "dark" : "light";
  document.documentElement.dataset.theme = theme;
  updateThemeButton();
}

function updateThemeButton() {
  const dark = document.documentElement.dataset.theme === "dark";
  const button = $("#themeToggle");
  button.setAttribute("aria-label", dark ? "Switch to light theme" : "Switch to dark theme");
  button.title = dark ? "Switch to light theme" : "Switch to dark theme";
}

function setupReaderSize() {
  const saved = Number(safeStorageGet(STORAGE.fontSize));
  state.readerSize = Number.isFinite(saved) && saved >= 16 && saved <= 24 ? saved : 18;
  document.documentElement.style.setProperty("--reader-size", `${state.readerSize}px`);
}

function updateReaderSize(delta) {
  state.readerSize = Math.max(16, Math.min(24, state.readerSize + delta));
  document.documentElement.style.setProperty("--reader-size", `${state.readerSize}px`);
  safeStorageSet(STORAGE.fontSize, String(state.readerSize));
}

function cleanMarkdown(text) {
  return text
    .replace(/^#{1,4}\s+/gm, "")
    .replace(/^>\s?/gm, "")
    .replace(/^\s*[-*+]\s+/gm, "")
    .replace(/^\s*\d+\.\s+/gm, "")
    .replace(/\*\*(.*?)\*\*/g, "$1")
    .replace(/\*([^*]+)\*/g, "$1")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/\|/g, " ")
    .replace(/---+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function buildExcerpt(text, query) {
  const lower = text.toLocaleLowerCase();
  const matchAt = lower.indexOf(query.toLocaleLowerCase());
  if (matchAt < 0) return text.slice(0, 150);
  const start = Math.max(0, matchAt - 64);
  const end = Math.min(text.length, matchAt + query.length + 88);
  return `${start > 0 ? "…" : ""}${text.slice(start, end)}${end < text.length ? "…" : ""}`;
}

async function runSearch(query) {
  const results = $("#searchResults");
  const meta = $("#searchMeta");
  results.replaceChildren();
  const term = query.trim();
  if (!term) {
    meta.textContent = "Search the full text of the book.";
    return;
  }
  meta.textContent = "Searching all sections…";
  try {
    const documents = await Promise.all(state.book.chapters.map(async chapter => ({
      chapter,
      text: cleanMarkdown(await getChapter(chapter))
    })));
    const matches = documents.filter(document => document.text.toLocaleLowerCase().includes(term.toLocaleLowerCase()));
    meta.textContent = matches.length ? `${matches.length} section${matches.length === 1 ? "" : "s"} found` : "No matches found. Try another phrase.";
    for (const match of matches.slice(0, 12)) {
      const button = document.createElement("button");
      button.className = "search-result";
      button.type = "button";
      button.setAttribute("role", "listitem");
      const title = document.createElement("span");
      title.className = "search-result-title";
      title.textContent = match.chapter.title;
      const excerpt = document.createElement("span");
      excerpt.className = "search-result-excerpt";
      excerpt.textContent = buildExcerpt(match.text, term);
      button.append(title, excerpt);
      button.addEventListener("click", () => {
        $("#searchPanel").hidden = true;
        $("#searchToggle").setAttribute("aria-expanded", "false");
        loadChapter(match.chapter.id);
      });
      results.append(button);
    }
  } catch {
    meta.textContent = "The book text could not be searched. Please try again.";
  }
}

function openSearch() {
  const panel = $("#searchPanel");
  panel.hidden = false;
  $("#searchToggle").setAttribute("aria-expanded", "true");
  window.setTimeout(() => $("#searchInput").focus(), 0);
}

function closeSearch() {
  $("#searchPanel").hidden = true;
  $("#searchToggle").setAttribute("aria-expanded", "false");
  $("#searchToggle").focus();
}

function setupControls() {
  $("#homeNav").addEventListener("click", () => showHome());
  $("#brandHome").addEventListener("click", event => {
    event.preventDefault();
    showHome();
  });

  $("#startReading").addEventListener("click", () => {
    const last = safeStorageGet(STORAGE.lastChapter);
    const target = state.book.chapters.some(chapter => chapter.id === last) ? last : state.book.chapters[0].id;
    loadChapter(target);
  });

  $("#searchToggle").addEventListener("click", () => {
    if ($( "#searchPanel").hidden) openSearch();
    else closeSearch();
  });
  $("#searchInput").addEventListener("input", event => {
    window.clearTimeout(state.searchTimer);
    const value = event.target.value;
    state.searchTimer = window.setTimeout(() => runSearch(value), 160);
  });
  $("#fontDown").addEventListener("click", () => updateReaderSize(-1));
  $("#fontUp").addEventListener("click", () => updateReaderSize(1));
  $("#themeToggle").addEventListener("click", () => {
    const theme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = theme;
    safeStorageSet(STORAGE.theme, theme);
    updateThemeButton();
  });
  $("#printBook").addEventListener("click", () => window.print());
  $("#menuToggle").addEventListener("click", () => {
    const open = document.body.classList.toggle("sidebar-is-open");
    $("#menuToggle").setAttribute("aria-expanded", String(open));
    $("#menuToggle").setAttribute("aria-label", open ? "Close table of contents" : "Open table of contents");
  });
  $("#sidebarBackdrop").addEventListener("click", closeMobileMenu);

  document.addEventListener("keydown", event => {
    const activeTag = document.activeElement?.tagName;
    const typing = activeTag === "INPUT" || activeTag === "TEXTAREA" || document.activeElement?.isContentEditable;
    if (event.key === "/" && !typing) {
      event.preventDefault();
      openSearch();
    } else if (event.key === "Escape") {
      if (!$("#searchPanel").hidden) closeSearch();
      else if (document.body.classList.contains("sidebar-is-open")) closeMobileMenu();
    }
  });

  window.addEventListener("scroll", scheduleProgressMeasure, { passive: true });
  window.addEventListener("resize", scheduleProgressMeasure);
  window.addEventListener("popstate", () => {
    const id = decodeURIComponent(window.location.hash.slice(1));
    if (state.book?.chapters.some(chapter => chapter.id === id)) loadChapter(id, { updateHistory: false, shouldScroll: false });
    else showHome({ updateHistory: false, shouldScroll: false });
  });
}

async function init() {
  setupTheme();
  setupReaderSize();
  try {
    const response = await fetch("book.json");
    if (!response.ok) throw new Error("Book contents could not be loaded.");
    state.book = await response.json();
    const savedRead = safeStorageGet(STORAGE.readChapters);
    try {
      const parsed = savedRead ? JSON.parse(savedRead) : [];
      if (Array.isArray(parsed)) state.readChapters = new Set(parsed);
    } catch { state.readChapters = new Set(); }
    const savedProgress = Number(safeStorageGet(STORAGE.progress));
    state.progress = Number.isFinite(savedProgress) ? Math.max(0, Math.min(100, savedProgress)) : 0;
    updateProgress();
    renderChapterList();
    setupControls();

    const hash = decodeURIComponent(window.location.hash.slice(1));
    if (state.book.chapters.some(chapter => chapter.id === hash)) {
      loadChapter(hash, { updateHistory: false, shouldScroll: false });
    } else {
      showHome({ updateHistory: false, shouldScroll: false });
      const last = safeStorageGet(STORAGE.lastChapter);
      if (state.book.chapters.some(chapter => chapter.id === last)) {
        $("#startReading").innerHTML = 'Continue reading <span aria-hidden="true">→</span>';
      }
    }
  } catch (error) {
    $("#currentLocation").textContent = "Unavailable";
    $("#articleBody").innerHTML = `<p class="chapter-error">${escapeHtml(error.message)} Make sure you open this book from its web reader.</p>`;
    $("#chapterList").innerHTML = '<li class="chapter-error">Book contents unavailable.</li>';
  }
}

init();
