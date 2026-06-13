const els = {
  contractFile: document.querySelector("#contractFile"),
  contractText: document.querySelector("#contractText"),
  reviewMode: document.querySelector("#reviewMode"),
  provider: document.querySelector("#provider"),
  model: document.querySelector("#model"),
  baseUrl: document.querySelector("#baseUrl"),
  apiKey: document.querySelector("#apiKey"),
  runButton: document.querySelector("#runButton"),
  status: document.querySelector("#status"),
  statusText: document.querySelector(".status__text"),
  report: document.querySelector("#report"),
  json: document.querySelector("#json"),
  rules: document.querySelector("#rules"),
  logs: document.querySelector("#logs"),
  tabs: document.querySelectorAll(".tab"),
  views: document.querySelectorAll(".view"),
  dropzone: document.querySelector("#dropzone"),
  fileName: document.querySelector("#fileName"),
  charCount: document.querySelector("#charCount"),
};

let providers = {};

function setStatus(text, mode = "") {
  if (els.statusText) {
    els.statusText.textContent = text;
  } else {
    els.status.textContent = text;
  }
  els.status.className = `status ${mode}`.trim();
}

function setActiveView(name) {
  els.tabs.forEach((tab) => {
    const isActive = tab.dataset.view === name;
    tab.classList.toggle("active", isActive);
    tab.setAttribute("aria-selected", String(isActive));
  });
  els.views.forEach((view) => view.classList.toggle("active", view.id === name));
}

function updateCharCount() {
  const count = els.contractText.value.length;
  els.charCount.textContent = `${count.toLocaleString("zh-CN")} 字`;
}

function updateFileDisplay() {
  const file = els.contractFile.files[0];
  if (file) {
    els.dropzone.classList.add("has-file");
    els.fileName.hidden = false;
    els.fileName.textContent = file.name;
  } else {
    els.dropzone.classList.remove("has-file");
    els.fileName.hidden = true;
    els.fileName.textContent = "";
  }
}

function fillProvider(providerKey) {
  const provider = providers[providerKey];
  if (!provider) return;
  els.model.value = provider.model || "";
  els.baseUrl.value = provider.base_url || "";
  els.apiKey.placeholder = provider.api_key_placeholder
    ? `默认：${provider.api_key_placeholder}`
    : "仅本次运行使用";
}

function buildFormData() {
  const formData = new FormData();
  const file = els.contractFile.files[0];
  if (file) {
    formData.append("contract", file, file.name);
  }
  formData.append("contractText", els.contractText.value);
  formData.append("fileName", file ? file.name : "pasted_contract.txt");
  formData.append("reviewMode", els.reviewMode.value);
  formData.append("provider", els.provider.value);
  formData.append("model", els.model.value);
  formData.append("baseUrl", els.baseUrl.value);
  formData.append("apiKey", els.apiKey.value);
  return formData;
}

async function loadConfig() {
  const response = await fetch("/api/config");
  const config = await response.json();
  providers = config.providers;

  els.provider.innerHTML = Object.entries(providers)
    .map(([key, value]) => `<option value="${key}">${value.label}</option>`)
    .join("");

  els.reviewMode.innerHTML = Object.entries(config.reviewModes)
    .map(([key, label]) => `<option value="${key}">${label}</option>`)
    .join("");

  els.provider.value = config.defaults.provider;
  els.reviewMode.value = config.defaults.reviewMode;
  fillProvider(els.provider.value);
  els.rules.textContent = JSON.stringify(config.rules, null, 2);
  initCustomSelects();
}

async function runReview() {
  if (!els.contractFile.files[0] && !els.contractText.value.trim()) {
    setStatus("缺少合同", "error");
    els.report.textContent = "请上传合同文件，或粘贴合同正文。";
    setActiveView("report");
    return;
  }

  els.runButton.disabled = true;
  els.report.textContent = "正在审核...";
  els.json.textContent = "";
  els.logs.textContent = "";
  setStatus("审核中", "busy");
  setActiveView("report");

  try {
    const response = await fetch("/api/review", {
      method: "POST",
      body: buildFormData(),
    });
    const data = await response.json();

    if (!data.ok) {
      setStatus("失败", "error");
      els.report.textContent = data.error || "审核失败。";
      els.logs.textContent = data.traceback || data.logs || "";
      return;
    }

    setStatus(data.mode === "rules_fallback" ? "已回退" : "完成");
    els.report.textContent = data.report || "";
    els.json.textContent = data.auditJson || "";
    els.logs.textContent = data.logs || "";
  } catch (error) {
    setStatus("失败", "error");
    els.report.textContent = error.message;
  } finally {
    els.runButton.disabled = false;
  }
}

els.provider.addEventListener("change", () => fillProvider(els.provider.value));
els.runButton.addEventListener("click", runReview);
els.tabs.forEach((tab) => tab.addEventListener("click", () => setActiveView(tab.dataset.view)));
els.contractFile.addEventListener("change", updateFileDisplay);
els.contractText.addEventListener("input", updateCharCount);

els.dropzone.addEventListener("dragover", (event) => {
  event.preventDefault();
  els.dropzone.classList.add("is-dragover");
});

els.dropzone.addEventListener("dragleave", () => {
  els.dropzone.classList.remove("is-dragover");
});

els.dropzone.addEventListener("drop", (event) => {
  event.preventDefault();
  els.dropzone.classList.remove("is-dragover");
  const file = event.dataTransfer?.files?.[0];
  if (!file) return;
  const transfer = new DataTransfer();
  transfer.items.add(file);
  els.contractFile.files = transfer.files;
  updateFileDisplay();
});

updateCharCount();

loadConfig().catch((error) => {
  setStatus("失败", "error");
  els.report.textContent = error.message;
});
