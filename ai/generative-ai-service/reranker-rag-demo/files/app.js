const presets = {
  meaning: "What public holidays are listed, and how many annual leave days do Netherlands and Poland employees get?",
  useCases: "If leave is without manager approval it may be unpaid, but what if the absence is illness over two days?",
  adoption: "Who counts as a direct relative, and how much compassionate leave is given for death of a spouse or direct relative?"
};

const RESULT_LIMIT = 12;

const presetLabels = {
  meaning: "Annual days",
  useCases: "Sick certificate",
  adoption: "Compassionate"
};

const ui = {
  documentTitle: "Vision Corp Leave Policy RAG",
  eyebrow: "Retrieval augmented generation",
  title: "Vision Corp Leave Policy RAG",
  queryLabel: "Question",
  vectorMode: "Vector store only",
  rerankMode: "OCI Reranker on",
  toggleSr: "Use OCI Reranker",
  steps: {
    query: "Query",
    vector: "Vector search",
    rerank: "Rerank top-k",
    answer: "Answer"
  },
  answerEyebrow: "Generated response",
  answerTitle: "RAG answer",
  scoreEyebrow: "Ranking effect",
  scoreTitle: "Top passages",
  withoutReranker: "Without reranker - top 12",
  withReranker: "With OCI Reranker - top 12",
  vectorOnly: "Vector store",
  callingOci: "Calling OCI",
  ociReranker: "OCI Reranker",
  ociFailed: "OCI call failed",
  rankingStable: "Ranking stable",
  startServer: "Start server.py",
  retrieved: "retrieved",
  sameRank: "same rank",
  scoreNote:
    "Vector score is cosine similarity from OCI embeddings in FAISS. Reranker score is OCI relevance_score. They are real scores, but different scales.",
  up: (amount) => `up ${amount}`,
  down: (amount) => `down ${amount}`,
  movedUp: (title, amount) => `${title} moved up ${amount}`,
  backendMessage: (message) => `Backend message: ${message}`
};

const queryInput = document.querySelector("#query-input");
const rerankToggle = document.querySelector("#rerank-toggle");
const rankList = document.querySelector("#rank-list");
const answerCopy = document.querySelector("#answer-copy");
const citationRow = document.querySelector("#citation-row");
const answerMode = document.querySelector("#answer-mode");
const liftBadge = document.querySelector("#lift-badge");
const modelPill = document.querySelector("#model-pill");
const modelPillText = document.querySelector("#model-pill-text");
const vectorStack = document.querySelector("#vector-stack");
const rerankStack = document.querySelector("#rerank-stack");
const presetButtons = document.querySelectorAll(".preset-button");
const scoreNote = document.querySelector("#score-note");
const initialParams = new URLSearchParams(window.location.search);
const presetKeys = Object.keys(presets);

let activePreset = presetKeys.includes(initialParams.get("preset"))
  ? initialParams.get("preset")
  : "meaning";
let renderToken = 0;
let renderTimer;
let activeSearchController = null;

function setText(selector, value) {
  document.querySelector(selector).textContent = value;
}

function formatScore(value) {
  const score = Number(value);
  if (!Number.isFinite(score)) {
    return "--";
  }
  return score.toFixed(3);
}

function scoreValue(doc, mode) {
  return mode === "reranker" ? doc.rerankScore : doc.vectorScore;
}

function scoreLabel(mode) {
  return mode === "reranker" ? "relevance" : "cosine";
}

function movementLabel(doc, index, mode) {
  if (mode !== "reranker") {
    return ui.retrieved;
  }

  const movement = doc.vectorRank - (index + 1);
  if (movement > 0) {
    return ui.up(movement);
  }
  if (movement < 0) {
    return ui.down(Math.abs(movement));
  }
  return ui.sameRank;
}

function movementClass(doc, index, mode) {
  if (mode !== "reranker") {
    return "movement";
  }
  const movement = doc.vectorRank - (index + 1);
  return movement < 0 ? "movement down" : "movement";
}

function renderCitations(results) {
  citationRow.innerHTML = "";
  results.slice(0, 3).forEach((doc) => {
    const citation = document.createElement("span");
    citation.className = "citation";
    citation.textContent = doc.source;
    citationRow.append(citation);
  });
}

function renderRankList(results, mode) {
  rankList.innerHTML = "";

  results.forEach((doc, index) => {
    const card = document.createElement("article");
    card.className = `rank-card${index === 0 ? " is-top" : ""}`;
    card.innerHTML = `
      <div class="rank-number">${index + 1}</div>
      <div>
        <p class="doc-title">${doc.title}</p>
        <p class="doc-copy">${doc.text}</p>
        <div class="tag-row">${doc.tags.map((tag) => `<span class="tag">${tag}</span>`).join("")}</div>
      </div>
      <div class="score-meter">
        <span class="score-value">${formatScore(scoreValue(doc, mode))}</span>
        <span class="score-kind">${scoreLabel(mode)}</span>
        <span class="${movementClass(doc, index, mode)}">${movementLabel(doc, index, mode)}</span>
      </div>
    `;
    rankList.append(card);
  });
}

function renderMiniStack(target, results, mode) {
  target.innerHTML = "";

  if (!results.length) {
    const item = document.createElement("div");
    item.className = "mini-empty";
    item.textContent = "Turn on OCI Reranker to compare the reordered candidates.";
    target.append(item);
    return;
  }

  results.slice(0, RESULT_LIMIT).forEach((doc, index) => {
    const item = document.createElement("div");
    item.className = "mini-item";
    item.innerHTML = `
      <div class="mini-rank">${index + 1}</div>
      <div>
        <strong>${doc.title}</strong>
        <span>${formatScore(scoreValue(doc, mode))} ${scoreLabel(mode)}</span>
      </div>
    `;
    target.append(item);
  });
}

function renderLoading(isReranking) {
  document.body.classList.toggle("rerank-active", isReranking);
  answerMode.textContent = isReranking ? ui.callingOci : ui.vectorOnly;
  liftBadge.textContent = isReranking ? "Embedding search + rerank" : "Embedding search";
  answerCopy.textContent = isReranking
    ? "Running vector search with OCI embeddings, then sending the retrieved candidates to OCI Reranker..."
    : "Running vector search with OCI embeddings in the backend FAISS index...";
  citationRow.innerHTML = "";
  rankList.innerHTML = "";
  vectorStack.innerHTML = "";
  rerankStack.innerHTML = "";
  scoreNote.textContent = ui.scoreNote;
}

function renderError(error) {
  document.body.classList.remove("rerank-active");
  answerMode.textContent = ui.ociFailed;
  liftBadge.textContent = "No fallback score";
  answerCopy.textContent = ui.backendMessage(error.message || "Search failed.");
  citationRow.innerHTML = "";
  rankList.innerHTML = "";
  vectorStack.innerHTML = "";
  rerankStack.innerHTML = "";
}

function renderView(data) {
  const isReranking = data.answerMode === "reranker";
  const activeResults = isReranking ? data.rerankedResults : data.vectorResults;
  const promotedDoc = data.rerankedResults?.[0];

  document.body.classList.toggle("rerank-active", isReranking);
  answerMode.textContent = isReranking ? ui.ociReranker : ui.vectorOnly;

  if (isReranking && promotedDoc) {
    const lift = promotedDoc.vectorRank - promotedDoc.rerankRank;
    liftBadge.textContent = lift > 0 ? ui.movedUp(promotedDoc.title, lift) : ui.rankingStable;
  } else {
    liftBadge.textContent = `${data.vector.engine} - ${data.vector.metric}`;
  }

  answerCopy.textContent = data.answer;
  scoreNote.textContent = ui.scoreNote;

  renderCitations(activeResults);
  renderRankList(activeResults, isReranking ? "reranker" : "vector");
  renderMiniStack(vectorStack, data.vectorResults || [], "vector");
  renderMiniStack(rerankStack, data.rerankedResults || [], "reranker");
}

async function requestSearch(query, useReranker, signal) {
  const response = await fetch("/api/search", {
    method: "POST",
    signal,
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      query,
      useReranker,
      topK: RESULT_LIMIT
    })
  });
  const data = await response.json();
  if (!response.ok || !data.ok) {
    throw new Error(data.message || "Search request failed.");
  }
  return data;
}

async function fetchOciStatus() {
  try {
    const response = await fetch("/api/status");
    const data = await response.json();
    if (!response.ok || !data.ok) {
      throw new Error(data.message || "OCI backend is not ready.");
    }
    modelPillText.textContent = `${data.embeddingModel} + ${data.rerankModel}`;
  } catch (error) {
    modelPillText.textContent = ui.startServer;
  }
}

async function render() {
  const token = ++renderToken;
  const query = queryInput.value.trim() || presets.meaning;
  const isReranking = rerankToggle.checked;

  if (activeSearchController) {
    activeSearchController.abort();
  }

  const controller = new AbortController();
  activeSearchController = controller;
  renderLoading(isReranking);

  try {
    const data = await requestSearch(query, isReranking, controller.signal);
    if (token !== renderToken) {
      return;
    }
    activeSearchController = null;
    renderView(data);
  } catch (error) {
    if (error.name === "AbortError" || token !== renderToken) {
      return;
    }
    activeSearchController = null;
    renderError(error);
  }
}

function scheduleRender() {
  window.clearTimeout(renderTimer);
  renderTimer = window.setTimeout(render, 350);
}

function initializeText() {
  document.documentElement.lang = "en";
  document.documentElement.dir = "ltr";
  document.title = ui.documentTitle;
  setText("#page-eyebrow", ui.eyebrow);
  setText("#page-title", ui.title);
  setText("#query-label", ui.queryLabel);
  setText("#vector-mode-label", ui.vectorMode);
  setText("#rerank-mode-label", ui.rerankMode);
  setText("#toggle-sr", ui.toggleSr);
  setText("#step-query", ui.steps.query);
  setText("#step-vector", ui.steps.vector);
  setText("#step-rerank", ui.steps.rerank);
  setText("#step-answer", ui.steps.answer);
  setText("#answer-eyebrow", ui.answerEyebrow);
  setText("#answer-title", ui.answerTitle);
  setText("#score-eyebrow", ui.scoreEyebrow);
  setText("#score-title", ui.scoreTitle);
  setText("#vector-mini-title", ui.withoutReranker);
  setText("#rerank-mini-title", ui.withReranker);

  modelPill.setAttribute("aria-label", "Selected OCI models");
  document.querySelector("#control-strip").setAttribute("aria-label", "Demo controls");
  document.querySelector("#preset-row").setAttribute("aria-label", "Example questions");
  document.querySelector("#pipeline").setAttribute("aria-label", "RAG pipeline");
  citationRow.setAttribute("aria-label", "Cited passages");
  document.querySelector(".compare-grid").setAttribute("aria-label", "Side by side comparison");

  presetButtons.forEach((button) => {
    button.textContent = presetLabels[button.dataset.preset];
    button.classList.toggle("is-active", button.dataset.preset === activePreset);
  });

  queryInput.value = presets[activePreset];
  scoreNote.textContent = ui.scoreNote;
}

queryInput.addEventListener("input", () => {
  activePreset = null;
  presetButtons.forEach((item) => item.classList.remove("is-active"));
  scheduleRender();
});

rerankToggle.addEventListener("change", render);

presetButtons.forEach((button) => {
  button.addEventListener("click", () => {
    activePreset = button.dataset.preset;
    presetButtons.forEach((item) => item.classList.remove("is-active"));
    button.classList.add("is-active");
    queryInput.value = presets[activePreset];
    render();
  });
});

rerankToggle.checked = initialParams.get("rerank") !== "0";
initializeText();
fetchOciStatus();
render();
