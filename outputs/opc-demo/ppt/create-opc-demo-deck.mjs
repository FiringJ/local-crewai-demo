import fs from "node:fs/promises";
import path from "node:path";
import { Presentation, PresentationFile } from "/Users/firingj/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/.pnpm/@oai+artifact-tool@file+local-deps+-oai-artifact-tool-oai-artifact_tool-2.8.11.tgz/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs";

const ROOT = "/Users/firingj/Projects/local_crewai_demo";
const OUT = path.join(ROOT, "outputs/opc-demo");
const FINAL = path.join(OUT, "ppt/opc-contract-audit-demo.pptx");
const PREVIEW = path.join(OUT, "ppt/preview");
const LAYOUT = path.join(OUT, "ppt/layout");
const QA = path.join(OUT, "qa");
const SCREEN = path.join(OUT, "screenshots");
const review = JSON.parse(await fs.readFile(path.join(OUT, "review-response.json"), "utf8"));

await fs.mkdir(PREVIEW, { recursive: true });
await fs.mkdir(LAYOUT, { recursive: true });
await fs.mkdir(QA, { recursive: true });

const W = 1280;
const H = 720;
const C = {
  ink: "#172033",
  muted: "#5E687A",
  paper: "#F7F8F6",
  white: "#FFFFFF",
  line: "#D8DDE2",
  red: "#C9463A",
  amber: "#B57A30",
  green: "#2D7D5A",
  blue: "#2F6F9F",
  navy: "#16283F",
};

const p = Presentation.create({ slideSize: { width: W, height: H } });

function shape(slide, cfg) {
  return slide.shapes.add({
    line: { style: "solid", fill: "none", width: 0 },
    ...cfg,
  });
}

function text(slide, value, pos, style = {}) {
  const t = shape(slide, {
    geometry: "textbox",
    position: pos,
    fill: "none",
  });
  t.text = value;
  t.text.style = {
    fontSize: 22,
    color: C.ink,
    fontFace: "Aptos",
    ...style,
  };
  return t;
}

function title(slide, kicker, headline, sub = "") {
  text(slide, kicker, { left: 72, top: 42, width: 620, height: 26 }, {
    fontSize: 12,
    bold: true,
    color: C.blue,
  });
  text(slide, headline, { left: 72, top: 76, width: 820, height: 86 }, {
    fontSize: 36,
    bold: true,
    color: C.ink,
  });
  if (sub) text(slide, sub, { left: 72, top: 148, width: 820, height: 54 }, {
    fontSize: 18,
    color: C.muted,
  });
}

function footer(slide, n) {
  shape(slide, {
    geometry: "line",
    position: { left: 72, top: 664, width: 1136, height: 0 },
    fill: "none",
    line: { style: "solid", fill: C.line, width: 1 },
  });
  text(slide, "办公小浣熊 · 企业合同初审持续运营工作流", { left: 72, top: 674, width: 520, height: 18 }, {
    fontSize: 10,
    color: C.muted,
  });
  text(slide, String(n).padStart(2, "0"), { left: 1160, top: 674, width: 48, height: 18 }, {
    fontSize: 10,
    bold: true,
    color: C.muted,
    alignment: "right",
  });
}

function card(slide, x, y, w, h, label, value, color = C.navy) {
  shape(slide, {
    geometry: "roundRect",
    position: { left: x, top: y, width: w, height: h },
    fill: C.white,
    line: { style: "solid", fill: C.line, width: 1 },
    borderRadius: 8,
  });
  text(slide, value, { left: x + 22, top: y + 24, width: w - 44, height: 50 }, {
    fontSize: 42,
    bold: true,
    color,
  });
  text(slide, label, { left: x + 22, top: y + 82, width: w - 44, height: 30 }, {
    fontSize: 16,
    color: C.muted,
  });
}

function bullet(slide, items, x, y, w, gap = 42) {
  items.forEach((item, i) => {
    shape(slide, {
      geometry: "ellipse",
      position: { left: x, top: y + i * gap + 7, width: 9, height: 9 },
      fill: item.color || C.blue,
    });
    text(slide, item.text, { left: x + 22, top: y + i * gap, width: w - 22, height: 36 }, {
      fontSize: item.size || 19,
      color: item.muted ? C.muted : C.ink,
      bold: item.bold || false,
    });
  });
}

async function screenshot(slide, file, pos, alt) {
  const blob = await fs.readFile(path.join(SCREEN, file));
  slide.images.add({
    blob,
    contentType: "image/png",
    alt,
    fit: "cover",
    position: pos,
    geometry: "roundRect",
    borderRadius: 8,
  });
}

function workflowNode(slide, i, label, x, y, w = 132) {
  shape(slide, {
    geometry: "roundRect",
    position: { left: x, top: y, width: w, height: 74 },
    fill: i === 6 ? "#FFF2E8" : C.white,
    line: { style: "solid", fill: i === 6 ? C.amber : C.line, width: 1.2 },
    borderRadius: 8,
  });
  text(slide, String(i).padStart(2, "0"), { left: x + 12, top: y + 10, width: 32, height: 20 }, {
    fontSize: 12,
    bold: true,
    color: i === 6 ? C.amber : C.blue,
  });
  text(slide, label, { left: x + 12, top: y + 32, width: w - 24, height: 36 }, {
    fontSize: 15,
    bold: true,
    color: C.ink,
  });
}

// 1
{
  const s = p.slides.add();
  s.background.fill = C.paper;
  text(s, "OPC 高手创造赛演示包", { left: 72, top: 48, width: 360, height: 26 }, { fontSize: 13, bold: true, color: C.blue });
  text(s, "办公小浣熊把合同初审跑成持续运营流水线", { left: 72, top: 118, width: 740, height: 140 }, { fontSize: 50, bold: true, color: C.ink });
  text(s, "不是单点审阅工具：每日拉取、逐份初审、主体尽调、知识库沉淀、周报 PPT 自动生成。", { left: 74, top: 286, width: 660, height: 78 }, { fontSize: 22, color: C.muted });
  card(s, 72, 430, 220, 130, "单份审核耗时", "4h→3m", C.red);
  card(s, 320, 430, 170, 130, "规则证据", "22", C.navy);
  card(s, 518, 430, 220, 130, "样本合规率", `${review.analytics.pass_rate}%`, C.amber);
  await screenshot(s, "01-home.png", { left: 820, top: 88, width: 388, height: 470 }, "Demo home screen");
  footer(s, 1);
}

// 2
{
  const s = p.slides.add();
  s.background.fill = C.paper;
  title(s, "CREWAI 定位", "CrewAI 是审核引擎节点里的编排层，不是作品主角", "作品主角是小浣熊网页端的持续运营能力；CrewAI 只负责把结构化证据交给 Agent 生成报告与汇报。");
  const rows = [
    ["做什么", "读取本地 22 条规则证据、知识库上下文、合同正文，顺序执行审核报告和汇报大纲任务。"],
    ["不做什么", "不负责定时任务、网页端联网尽调、知识库存取截图、PPT 网页端生成。"],
    ["为什么需要", "把确定性校验和语言生成分开：规则避免算错金额，Agent 负责解释风险和生成可读交付物。"],
  ];
  rows.forEach((r, i) => {
    shape(s, { geometry: "roundRect", position: { left: 86, top: 228 + i * 112, width: 1080, height: 86 }, fill: C.white, line: { style: "solid", fill: C.line, width: 1 }, borderRadius: 8 });
    text(s, r[0], { left: 116, top: 250 + i * 112, width: 140, height: 28 }, { fontSize: 22, bold: true, color: i === 1 ? C.red : C.blue });
    text(s, r[1], { left: 274, top: 246 + i * 112, width: 830, height: 42 }, { fontSize: 19, color: C.ink });
  });
  footer(s, 2);
}

// 3
{
  const s = p.slides.add();
  s.background.fill = C.paper;
  title(s, "工作流骨架", "每日流水线处理合同；每周流水线维护红线并输出周报", "规则引擎只作为第 6 步证据层，喂给小浣熊做语义复核和汇报。");
  const labels = ["定时任务", "Agent 编排", "文档处理", "联网尽调", "知识库复核", "规则证据", "报告/归档"];
  labels.forEach((l, i) => workflowNode(s, i + 1, l, 72 + i * 166, 250));
  for (let i = 0; i < labels.length - 1; i++) {
    shape(s, { geometry: "line", position: { left: 204 + i * 166, top: 287, width: 32, height: 0 }, fill: "none", line: { style: "solid", fill: C.blue, width: 2 } });
  }
  shape(s, { geometry: "roundRect", position: { left: 188, top: 430, width: 900, height: 94 }, fill: "#EFF6F8", line: { style: "solid", fill: "#BED7DF", width: 1 }, borderRadius: 8 });
  text(s, "每周五 17:00：法规/税率巡检 → 知识库红线补丁 → 周度数据分析 → 合同初审周报 PPT → 推送采购委员会", { left: 230, top: 462, width: 820, height: 36 }, { fontSize: 21, bold: true, color: C.navy });
  footer(s, 3);
}

// 4
{
  const s = p.slides.add();
  s.background.fill = C.paper;
  title(s, "提交成熟度判断", "可以提交，但要把“网页端真实能力证据”补齐", "当前仓库已具备主文档、Prompt、Demo 和运行材料；评审分主要来自小浣熊网页端截图。");
  card(s, 72, 232, 260, 142, "当前状态", "可提交骨架", C.green);
  card(s, 374, 232, 260, 142, "本地 Demo", "已跑通", C.blue);
  card(s, 676, 232, 260, 142, "缺口", "网页端截图", C.amber);
  bullet(s, [
    { text: "必须补拍：定时任务创建、联网检索开关和来源、@知识库读取、知识库写入、数据分析图表、PPT 生成、多轮调优。", color: C.red },
    { text: "本地 Demo 可证明：合同解析、22 条结构化证据、数据洞察、报告和大纲生成。", color: C.green },
    { text: "讲述口径：小浣熊是运营主线，CrewAI/规则引擎是可体验审核节点。", color: C.blue },
  ], 78, 440, 1030, 52);
  footer(s, 4);
}

// 5
{
  const s = p.slides.add();
  s.background.fill = C.paper;
  title(s, "如何运转起来", "评委 3 分钟内可以复现本地审核引擎节点", "完整工作流在小浣熊网页端按截图清单复现，本地节点用于证明单份合同的链路输出。");
  const cmds = [
    "uv run crew_gui --no-open",
    "打开 http://127.0.0.1:7860",
    "上传 knowledge/realistic_software_service_contract.txt",
    "选择“仅规则引擎（离线演示）”或配置 SenseNova Key 后跑全链路",
    "查看：审核报告 / 数据洞察 / 工作流 / 汇报大纲 / JSON / 规则",
  ];
  cmds.forEach((c, i) => {
    shape(s, { geometry: "roundRect", position: { left: 92, top: 220 + i * 72, width: 1030, height: 48 }, fill: i === 0 ? "#172033" : C.white, line: { style: "solid", fill: C.line, width: 1 }, borderRadius: 8 });
    text(s, `${i + 1}. ${c}`, { left: 116, top: 233 + i * 72, width: 980, height: 24 }, { fontSize: 20, bold: i === 0, color: i === 0 ? C.white : C.ink });
  });
  footer(s, 5);
}

// 6
{
  const s = p.slides.add();
  s.background.fill = C.paper;
  title(s, "本地演示结果", "样本合同检出 3 项高风险，输出报告、数据洞察和大纲", "这张证明审核引擎节点不是静态文档，而是能接受合同输入并产生结构化交付物。");
  card(s, 72, 214, 170, 126, "通过", String(review.analytics.compliance_summary.passed), C.green);
  card(s, 268, 214, 170, 126, "不通过", String(review.analytics.compliance_summary.failed), C.red);
  card(s, 464, 214, 170, 126, "需复核", String(review.analytics.compliance_summary.needs_review), C.amber);
  bullet(s, [
    { text: `高风险项：${review.analytics.high_risk_items.map((x) => x.rule).join("、")}`, bold: true, color: C.red },
    { text: "报告包含总体结论、关键字段、三组规则表格和可复制修改建议。", color: C.blue },
    { text: "数据洞察 Tab 输出合规率、风险分布、效率对比，供周报链路继续使用。", color: C.green },
  ], 80, 390, 610, 48);
  await screenshot(s, "03-analytics.png", { left: 760, top: 206, width: 420, height: 330 }, "Analytics tab screenshot");
  footer(s, 6);
}

// 7
{
  const s = p.slides.add();
  s.background.fill = C.paper;
  title(s, "截图证据", "Demo 已产出可放进提交材料的本地运行截图", "这些截图证明本地审核节点可运行；小浣熊网页端能力截图仍需按清单补拍。");
  await screenshot(s, "02-report.png", { left: 72, top: 206, width: 340, height: 300 }, "Report tab screenshot");
  await screenshot(s, "04-workflow.png", { left: 470, top: 206, width: 340, height: 300 }, "Workflow tab screenshot");
  await screenshot(s, "05-briefing.png", { left: 868, top: 206, width: 340, height: 300 }, "Briefing tab screenshot");
  text(s, "输出文件：outputs/opc-demo/screenshots/01-home.png ... 07-rules.png；录屏：outputs/opc-demo/video/local-demo-flow.webm", { left: 76, top: 552, width: 1050, height: 38 }, { fontSize: 18, color: C.muted });
  footer(s, 7);
}

// 8
{
  const s = p.slides.add();
  s.background.fill = C.paper;
  title(s, "提交前最后一公里", "把网页端真实过程补齐，作品形态就清楚了", "建议提交 PPT 中用 5 张小浣熊网页端截图 + 本地 Demo 录屏二维码/链接组合。");
  const checklist = [
    "S1 定时任务：每日 09:00 / 周五 17:00 调度界面",
    "S4 联网检索：开启联网 + 乙方尽调结果 + 来源链接",
    "S5/S6 知识库：@知识库读取红线 + 写入主体画像/案例库",
    "S7 数据分析：周趋势、Top5 风险、主体分布图表",
    "S9/S10 PPT 生成与多轮调优：第 1 轮 vs 第 2 轮对比",
  ];
  bullet(s, checklist.map((text, i) => ({ text, color: [C.blue, C.red, C.green, C.amber, C.navy][i] })), 108, 220, 1020, 58);
  shape(s, { geometry: "roundRect", position: { left: 106, top: 560, width: 970, height: 58 }, fill: "#FFF7E8", line: { style: "solid", fill: "#E7C78F", width: 1 }, borderRadius: 8 });
  text(s, "一句话讲法：小浣熊负责持续运营闭环，CrewAI/规则引擎负责其中可体验、可复现的单份审核节点。", { left: 132, top: 578, width: 910, height: 24 }, { fontSize: 20, bold: true, color: C.ink });
  footer(s, 8);
}

for (const [i, slide] of p.slides.items.entries()) {
  const stem = `slide-${String(i + 1).padStart(2, "0")}`;
  const png = await p.export({ slide, format: "png", scale: 1 });
  await fs.writeFile(path.join(PREVIEW, `${stem}.png`), new Uint8Array(await png.arrayBuffer()));
  const layout = await slide.export({ format: "layout" });
  await fs.writeFile(path.join(LAYOUT, `${stem}.layout.json`), await layout.text());
}

const montage = await p.export({ format: "webp", montage: true, scale: 1 });
await fs.writeFile(path.join(OUT, "ppt/opc-demo-montage.webp"), new Uint8Array(await montage.arrayBuffer()));

const pptx = await PresentationFile.exportPptx(p);
await pptx.save(FINAL);

await fs.writeFile(path.join(OUT, "ppt/source-notes.txt"), [
  "Source notes",
  "- User-provided repository documents: README.md, docs/OPC_SUBMISSION.md, docs/SCREENSHOT_CHECKLIST.md, prompts/xiaohuanxiong_core_prompts.md.",
  "- Local demo screenshots captured from http://127.0.0.1:7862 using Playwright CLI on 2026-06-20.",
  "- Review metrics from outputs/opc-demo/review-response.json generated by POST /api/review rules_only with knowledge/realistic_software_service_contract.txt.",
  "- CrewAI version checked locally: 1.14.3; PyPI latest checked online: 1.14.7.",
  "- External source checked: CrewAI official docs pages for changelog, LLMs, and LLM connections.",
].join("\n"));

await fs.writeFile(path.join(OUT, "ppt/slide-plan.txt"), [
  "Mode: create",
  "Slide size: 1280x720",
  "Palette: paper #F7F8F6, ink #172033, blue #2F6F9F, red #C9463A, amber #B57A30, green #2D7D5A.",
  "Fonts: Aptos / Aptos Display fallback.",
  "Slides: 1 title, 2 CrewAI role, 3 workflow, 4 submit readiness, 5 run steps, 6 demo result, 7 evidence, 8 final checklist.",
].join("\n"));

console.log(FINAL);
