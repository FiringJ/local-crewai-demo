import fs from "node:fs/promises";
import path from "node:path";
import { Presentation, PresentationFile } from "/Users/firingj/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/.pnpm/@oai+artifact-tool@file+local-deps+-oai-artifact-tool-oai-artifact_tool-2.8.13.tgz/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs";

const ROOT = "/Users/firingj/Projects/local_crewai_demo";
const OUT = path.join(ROOT, "outputs/opc-demo");
const PACK = path.join(ROOT, "outputs/xiaohuanxiong-screenshot-pack");
const FINAL = path.join(OUT, "ppt/opc-xiaohuanxiong-workflow-submission.pptx");
const PREVIEW = path.join(OUT, "ppt/xiaohuanxiong-preview");
const LAYOUT = path.join(OUT, "ppt/xiaohuanxiong-layout");
const QA = path.join(OUT, "qa");
const SCREEN = path.join(OUT, "screenshots");
const review = JSON.parse(await fs.readFile(path.join(OUT, "review-response.json"), "utf8"));
const stats = review.analytics.compliance_summary;
const passRate = review.analytics.pass_rate;
const highRiskCount = review.analytics.risk_distribution["高风险"] ?? 0;

await fs.mkdir(PREVIEW, { recursive: true });
await fs.mkdir(LAYOUT, { recursive: true });
await fs.mkdir(QA, { recursive: true });

const W = 1280;
const H = 720;
// Swiss IKB theme (guizang-ppt-skill · Style B)
const C = {
  ink: "#0A0A0A",
  muted: "#737373",
  faint: "#F0F0EE",
  paper: "#FAFAF8",
  white: "#FFFFFF",
  line: "#D4D4D2",
  accent: "#002FA7",
  accentSoft: "#E8EDF8",
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
    fontFace: "Helvetica",
    fontSize: 20,
    color: C.ink,
    ...style,
  };
  return t;
}

function footer(slide, n) {
  shape(slide, {
    geometry: "line",
    position: { left: 72, top: 660, width: 1136, height: 0 },
    fill: "none",
    line: { style: "solid", fill: C.line, width: 1 },
  });
  text(slide, "办公小浣熊 · 企业合同初审持续运营工作流", { left: 72, top: 674, width: 560, height: 20 }, {
    fontSize: 11,
    color: C.muted,
  });
  text(slide, String(n).padStart(2, "0"), { left: 1160, top: 674, width: 48, height: 20 }, {
    fontSize: 11,
    bold: true,
    color: C.muted,
    alignment: "right",
  });
}

function title(slide, eyebrow, headline, sub = "") {
  shape(slide, {
    geometry: "line",
    position: { left: 72, top: 34, width: 64, height: 0 },
    fill: "none",
    line: { style: "solid", fill: C.accent, width: 2 },
  });
  text(slide, eyebrow, { left: 72, top: 44, width: 760, height: 24 }, {
    fontSize: 12,
    bold: true,
    color: C.muted,
  });
  text(slide, headline, { left: 72, top: 78, width: 880, height: 90 }, {
    fontSize: 36,
    bold: false,
    color: C.ink,
  });
  if (sub) {
    text(slide, sub, { left: 74, top: 160, width: 820, height: 56 }, {
      fontSize: 18,
      color: C.muted,
    });
  }
}

function metric(slide, x, y, w, h, value, label, accent = false) {
  shape(slide, {
    geometry: "rect",
    position: { left: x, top: y, width: w, height: h },
    fill: accent ? C.accent : C.faint,
    line: { style: "solid", fill: accent ? C.accent : C.line, width: 1 },
  });
  text(slide, value, { left: x + 18, top: y + 20, width: w - 36, height: 48 }, {
    fontSize: value.length > 7 ? 22 : value.length > 4 ? 32 : 39,
    bold: false,
    color: accent ? C.white : C.ink,
  });
  text(slide, label, { left: x + 18, top: y + 76, width: w - 36, height: 28 }, {
    fontSize: 14,
    color: accent ? C.white : C.muted,
  });
}

function tag(slide, label, x, y, accent = false, width = 118) {
  shape(slide, {
    geometry: "rect",
    position: { left: x, top: y, width, height: 28 },
    fill: accent ? C.accent : C.faint,
    line: { style: "solid", fill: accent ? C.accent : C.line, width: 1 },
  });
  text(slide, label, { left: x, top: y + 6, width, height: 16 }, {
    fontSize: 11,
    bold: true,
    color: accent ? C.white : C.ink,
    alignment: "center",
  });
}

function bullet(slide, items, x, y, w, gap = 42) {
  items.forEach((item, i) => {
    shape(slide, {
      geometry: "rect",
      position: { left: x, top: y + i * gap + 8, width: 8, height: 8 },
      fill: item.accent ? C.accent : C.ink,
    });
    text(slide, item.text, { left: x + 24, top: y + i * gap, width: w - 24, height: item.height || 36 }, {
      fontSize: item.size || 18,
      bold: item.bold || false,
      color: item.muted ? C.muted : C.ink,
    });
  });
}

async function addImage(slide, file, pos, alt, base = ROOT, fit = "cover") {
  const blob = await fs.readFile(path.join(base, file));
  slide.images.add({
    blob,
    contentType: "image/png",
    alt,
    fit,
    position: pos,
    geometry: "rect",
  });
}

function stepNode(slide, x, y, w, label, cap, accent = false) {
  shape(slide, {
    geometry: "rect",
    position: { left: x, top: y, width: w, height: 86 },
    fill: accent ? C.accent : C.faint,
    line: { style: "solid", fill: accent ? C.accent : C.line, width: 1 },
  });
  text(slide, cap, { left: x + 14, top: y + 12, width: w - 28, height: 20 }, {
    fontSize: 11,
    bold: true,
    color: accent ? C.white : C.muted,
  });
  text(slide, label, { left: x + 14, top: y + 38, width: w - 28, height: 36 }, {
    fontSize: 15,
    bold: false,
    color: accent ? C.white : C.ink,
  });
}

// 1 · Cover split (IKB left + paper right)
{
  const s = p.slides.add();
  s.background.fill = C.paper;
  shape(s, { geometry: "rect", position: { left: 0, top: 0, width: 520, height: H }, fill: C.accent });
  text(s, "小浣熊挑战赛 · 赛道二", { left: 72, top: 48, width: 400, height: 24 }, { fontSize: 12, bold: true, color: C.white });
  text(s, "让合同初审从\n人工盯单变成\n自动值守", { left: 72, top: 120, width: 420, height: 220 }, { fontSize: 44, bold: false, color: C.white });
  text(s, "面向采购和法务的日常合同初审：每天自动拉取待审合同，先查风险、再按清单核对、最后生成审核意见和周报。", { left: 74, top: 360, width: 420, height: 100 }, { fontSize: 17, color: C.white });
  metric(s, 72, 500, 130, 100, "约92%", "4h→3min", true);
  metric(s, 214, 500, 110, 100, `${stats.total}项`, "法规对齐检查", true);
  metric(s, 336, 500, 130, 100, `${passRate}%`, "样本通过率", true);
  shape(s, { geometry: "line", position: { left: 560, top: 82, width: 640, height: 0 }, fill: "none", line: { style: "solid", fill: C.line, width: 1 } });
  await addImage(s, "outputs/opc-demo/ppt/assets/cover-raccoon-task-running-crop.png", { left: 560, top: 100, width: 640, height: 280 }, "小浣熊定时任务运行中局部截图", ROOT, "contain");
  text(s, "小浣熊桌面端真实任务", { left: 560, top: 400, width: 400, height: 28 }, { fontSize: 22, bold: false, color: C.ink });
  tag(s, "运行中", 1040, 398, true, 88);
  text(s, "每日合同初审流水线已创建，并可手动触发到运行中。", { left: 560, top: 448, width: 560, height: 42 }, { fontSize: 16, color: C.muted });
  text(s, "证据：桌面端任务页 + 运行录屏", { left: 560, top: 510, width: 500, height: 24 }, { fontSize: 15, bold: true, color: C.accent });
  footer(s, 1);
}

// 2
{
  const s = p.slides.add();
  s.background.fill = C.paper;
  title(s, "真实业务场景", "采购合同多、风险细、人工审得慢也容易漏", "这个作品不是闲聊工具，而是解决企业合同初审每天都会遇到的重复工作。");
  const rows = [
    ["每天都有新合同", "采购、技术服务、外包、软件实施等合同从邮件、审批系统、共享盘进入待审队列。"],
    ["人工审查跨度大", "法务看条款，财务核金额和税率，业务确认付款节点，单份通常要 4 小时左右。"],
    ["风险藏在细节里", "30% 异常税率、0.03% 付款比例、缺少标的、不可抗力条款不完整，都可能在签署后变成损失。"],
    ["管理层还要周报", "每周还要统计问题趋势、高频风险、重点供应商，手工整理约 2 小时。"],
  ];
  rows.forEach((row, i) => {
    const y = 220 + i * 88;
    shape(s, { geometry: "rect", position: { left: 92, top: y, width: 1050, height: 64 }, fill: C.faint, line: { style: "solid", fill: C.line, width: 1 } });
    text(s, String(i + 1).padStart(2, "0"), { left: 108, top: y + 18, width: 40, height: 26 }, { fontSize: 20, bold: false, color: i === 0 ? C.accent : C.muted });
    text(s, row[0], { left: 158, top: y + 18, width: 210, height: 26 }, { fontSize: 22, bold: false, color: C.ink });
    text(s, row[1], { left: 390, top: y + 16, width: 720, height: 30 }, { fontSize: 17, color: C.muted });
  });
  footer(s, 2);
}

// 3
{
  const s = p.slides.add();
  s.background.fill = C.paper;
  title(s, "完整工作流", "每天自动初审，每周自动复盘", "小浣熊把一次性问答变成连续运转的合同处理流程。");
  const nodes = [
    ["早上九点", "自动拉取待审合同"],
    ["逐份处理", "读合同并抽取字段"],
    ["查对方公司", "查询公开风险线索"],
    ["查内部资料", "读取红线和历史案例"],
    ["规则参考", "26 项维度初筛信号"],
    ["终局报告", "大模型复核+归档"],
  ];
  nodes.forEach((n, i) => {
    const x = 72 + i * 190;
    stepNode(s, x, 250, 154, n[1], n[0], i === 0 || i === 5);
    if (i < nodes.length - 1) {
      shape(s, { geometry: "line", position: { left: x + 154, top: 293, width: 36, height: 0 }, fill: "none", line: { style: "solid", fill: C.line, width: 2 } });
    }
  });
  shape(s, { geometry: "rect", position: { left: 112, top: 428, width: 1038, height: 124 }, fill: C.accentSoft, line: { style: "solid", fill: C.accent, width: 1 } });
  text(s, "每周五下午：小浣熊把一周审核结果汇总成趋势、风险排行和整改建议，再生成采购委员会可看的周报。", { left: 152, top: 454, width: 960, height: 32 }, { fontSize: 20, bold: false, color: C.ink });
  text(s, "沉淀方式：对方公司画像、风险案例、法务红线都会进入知识库，下次遇到同类合同可以直接复用。", { left: 152, top: 500, width: 960, height: 30 }, { fontSize: 17, color: C.muted });
  footer(s, 3);
}

// 4
{
  const s = p.slides.add();
  s.background.fill = C.paper;
  title(s, "小浣熊做什么", "六项能力各司其职，不是只问一次就结束", "题目要求体现工具能力组合，本作品把这些能力放进同一条合同初审主线。");
  const caps = [
    ["01", "定时任务", "每天拉合同，每周做复盘"],
    ["02", "联网检索", "查询对方公司公开风险"],
    ["03", "知识库", "存放红线、案例和公司画像"],
    ["04", "数据分析", "统计通过率和高频问题"],
    ["05", "演示文稿", "自动整理周报给委员会"],
    ["06", "对话协作", "把步骤串起来并给出意见"],
  ];
  caps.forEach((cap, i) => {
    const x = 96 + (i % 3) * 370;
    const y = 230 + Math.floor(i / 3) * 150;
    const accent = i === 5;
    shape(s, { geometry: "rect", position: { left: x, top: y, width: 300, height: 104 }, fill: accent ? C.accent : C.faint, line: { style: "solid", fill: accent ? C.accent : C.line, width: 1 } });
    text(s, cap[0], { left: x + 20, top: y + 16, width: 40, height: 20 }, { fontSize: 11, bold: true, color: accent ? C.white : C.muted });
    text(s, cap[1], { left: x + 24, top: y + 38, width: 250, height: 28 }, { fontSize: 22, bold: false, color: accent ? C.white : C.ink });
    text(s, cap[2], { left: x + 24, top: y + 72, width: 250, height: 28 }, { fontSize: 15, color: accent ? C.white : C.muted });
  });
  text(s, "价值在于组合：拉取、查询、沉淀、统计、汇报形成闭环，法务只处理异常和最终判断。", { left: 118, top: 558, width: 1000, height: 30 }, { fontSize: 19, bold: false, color: C.ink });
  footer(s, 4);
}

// 5
{
  const s = p.slides.add();
  s.background.fill = C.paper;
  title(s, "我的技术实现", "规则参考层 + 大模型决策层，不是纯硬编码检索", "先把合同变成可复核的维度信号，再交给小浣熊结合 @知识库 产出终局审核报告。");
  const cols = [
    ["LAYER 01", "读合同\n抽取甲乙方、金额、税率、日期、付款比例", C.faint, C.ink],
    ["LAYER 02", "规则参考层\n26 项初筛（6 组·对接《民法典》等上位法）", C.accent, C.white],
    ["LAYER 03", "大模型决策\n@知识库 + 全文复核 → 终局报告与周报", C.ink, C.white],
  ];
  cols.forEach((c, i) => {
    const x = 96 + i * 370;
    shape(s, { geometry: "rect", position: { left: x, top: 238, width: 300, height: 246 }, fill: c[2], line: { style: "solid", fill: c[2], width: 0 } });
    text(s, c[0], { left: x + 24, top: 264, width: 250, height: 30 }, { fontSize: 12, bold: true, color: c[3] });
    text(s, c[1], { left: x + 24, top: 318, width: 250, height: 128 }, { fontSize: 20, color: c[3] });
    if (i < 2) shape(s, { geometry: "line", position: { left: x + 300, top: 362, width: 70, height: 0 }, fill: "none", line: { style: "solid", fill: C.line, width: 2 } });
  });
  text(s, "引擎输出是初筛参考，非终局结论；语义类风险由大模型结合合同原文修正误报。", { left: 118, top: 550, width: 1000, height: 32 }, { fontSize: 19, bold: false, color: C.ink });
  footer(s, 5);
}

// 6
{
  const s = p.slides.add();
  s.background.fill = C.paper;
  title(s, "样本合同验证", `128 万元合同检出 ${highRiskCount} 项高风险`, "数字来自脱敏样本 `review-response.json`（规则参考层）；终局报告由小浣熊 @知识库 复核产出。");
  metric(s, 72, 220, 168, 118, String(stats.passed), "检查通过", false);
  metric(s, 264, 220, 168, 118, String(stats.failed), "未通过", true);
  metric(s, 456, 220, 168, 118, String(stats.needs_review), "需人工看", false);
  bullet(s, [
    { text: "异常税率：识别到 30%（R09），须改为法定档位。", accent: true, bold: true },
    { text: "付款比例：识别到 0.03%，合计不等于 100%（R10）。", accent: true, bold: true },
    { text: "争议解决：仲裁与诉讼并存（R23），签署前必须择一。", accent: true, bold: true },
  ], 80, 386, 610, 48);
  await addImage(s, "outputs/opc-demo/screenshots/03-analytics.png", { left: 760, top: 214, width: 420, height: 330 }, "本地审核台数据分析截图", ROOT, "contain");
  text(s, "可复查材料：样本合同、审核截图、规则统计结果均已放入提交材料包。", { left: 76, top: 584, width: 860, height: 28 }, { fontSize: 17, bold: false, color: C.accent });
  footer(s, 6);
}

// 7
{
  const s = p.slides.add();
  s.background.fill = C.paper;
  title(s, "真实运行证据", "小浣熊定时任务已经创建并手动跑过", "不是只写方案：桌面端可以看到任务、运行入口、运行中状态和完成后的摘要。");
  await addImage(s, "outputs/xiaohuanxiong-screenshot-pack/12-desktop-task-run/01-schedule-task-ready.png", { left: 72, top: 230, width: 360, height: 250 }, "定时任务待执行列表");
  await addImage(s, "outputs/xiaohuanxiong-screenshot-pack/12-desktop-task-run/02-task-menu-run-option.png", { left: 460, top: 230, width: 360, height: 250 }, "定时任务立刻运行菜单");
  await addImage(s, "outputs/xiaohuanxiong-screenshot-pack/12-desktop-task-run/03-task-running-manual-trigger.png", { left: 848, top: 230, width: 360, height: 250 }, "定时任务运行中");
  text(s, "任务已创建", { left: 78, top: 504, width: 150, height: 26 }, { fontSize: 18, bold: false, color: C.ink });
  text(s, "可立刻运行", { left: 466, top: 504, width: 150, height: 26 }, { fontSize: 18, bold: false, color: C.ink });
  text(s, "运行中", { left: 854, top: 504, width: 150, height: 26 }, { fontSize: 18, bold: false, color: C.accent });
  text(s, "录屏：桌面端小浣熊任务从菜单触发到运行中，文件已放入材料包。", { left: 76, top: 570, width: 1050, height: 26 }, { fontSize: 17, color: C.muted });
  footer(s, 7);
}

// 8
{
  const s = p.slides.add();
  s.background.fill = C.paper;
  title(s, "价值用数字说话", "省时间、少漏项、能沉淀、可汇报", "每个数字都对应现有截图、样本结果或明确估算口径。");
  const values = [
    ["92%", "单份合同预计节省时间", "人工约4小时，流程约3分钟", true],
    ["26项", "法规对齐检查清单", "6 组：效力·标的·价款·违约·担保·文本", false],
    [`${highRiskCount}项`, "样本高风险", "税率·付款·争议解决等", false],
    ["2小时→10分钟", "周报整理时间", "按周报整理估算", false],
  ];
  values.forEach((v, i) => {
    const x = 90 + (i % 2) * 540;
    const y = 230 + Math.floor(i / 2) * 150;
    const longValue = v[0].length > 5;
    const valueWidth = longValue ? 210 : 150;
    const bodyLeft = longValue ? x + 250 : x + 190;
    const bodyWidth = longValue ? 180 : 230;
    shape(s, { geometry: "rect", position: { left: x, top: y, width: 460, height: 110 }, fill: v[3] ? C.accent : C.faint, line: { style: "solid", fill: v[3] ? C.accent : C.line, width: 1 } });
    text(s, v[0], { left: x + 24, top: y + 28, width: valueWidth, height: 40 }, { fontSize: longValue ? 27 : 38, bold: false, color: v[3] ? C.white : C.ink });
    text(s, v[1], { left: bodyLeft, top: y + 24, width: bodyWidth, height: 24 }, { fontSize: 20, bold: false, color: v[3] ? C.white : C.ink });
    text(s, v[2], { left: bodyLeft, top: y + 58, width: bodyWidth, height: 28 }, { fontSize: 15, color: v[3] ? C.white : C.muted });
  });
  text(s, `样本统计：通过 ${stats.passed} 项、未通过 ${stats.failed} 项、需复核 ${stats.needs_review} 项，合规通过率 ${passRate}%。`, { left: 112, top: 558, width: 980, height: 30 }, { fontSize: 18, bold: false, color: C.ink });
  footer(s, 8);
}

// 9
{
  const s = p.slides.add();
  s.background.fill = C.paper;
  title(s, "提交材料怎么证明作品", "评委可以从截图、录屏和本地审核台三处验证", "材料不是孤立文档，而是能串成“创建任务—运行—出结果—做周报”的证据链。");
  const script = [
    ["1", "看小浣熊任务", "证明每天九点的合同初审任务已经存在。"],
    ["2", "看运行录屏", "证明任务可手动触发，并出现运行中状态。"],
    ["3", "看样本审核结果", "证明 26 项维度初筛 + 大模型终局报告能发现具体风险。"],
    ["4", "看知识库和周报截图", "证明结果能沉淀，并可整理成管理层周报。"],
  ];
  script.forEach((row, i) => {
    const y = 220 + i * 88;
    shape(s, { geometry: "rect", position: { left: 92, top: y + 7, width: 46, height: 46 }, fill: i === 3 ? C.accent : C.faint, line: { style: "solid", fill: i === 3 ? C.accent : C.line, width: 1 } });
    text(s, row[0], { left: 92, top: y + 21, width: 46, height: 20 }, { fontSize: 18, bold: false, color: i === 3 ? C.white : C.ink, alignment: "center" });
    text(s, row[1], { left: 166, top: y, width: 300, height: 30 }, { fontSize: 22, bold: false, color: C.ink });
    text(s, row[2], { left: 490, top: y + 4, width: 630, height: 34 }, { fontSize: 17, color: C.muted });
  });
  shape(s, { geometry: "rect", position: { left: 116, top: 588, width: 990, height: 48 }, fill: C.accentSoft, line: { style: "solid", fill: C.accent, width: 1 } });
  text(s, "提交时建议把演示文稿、录屏、截图包和作品简介放在同一个公开材料链接中。", { left: 142, top: 602, width: 940, height: 22 }, { fontSize: 16, bold: false, color: C.ink });
  footer(s, 9);
}

// 10
{
  const s = p.slides.add();
  s.background.fill = C.paper;
  title(s, "为什么切合赛题", "不是单点问答，而是围绕真实工作搭建完整流程", "赛道二提交表需要作品名、作品简介、产品介绍演示文稿和可访问材料；本作品围绕这些内容组织。");
  tag(s, "真实场景", 118, 232, false, 128);
  tag(s, "完整流程", 278, 232, false, 128);
  tag(s, "可量化", 438, 232, false, 116);
  tag(s, "可验证", 586, 232, true, 116);
  bullet(s, [
    { text: "真实场景：企业采购合同每天进入待审队列，法务和财务需要快速判断能否签署。", bold: true },
    { text: "完整流程：定时拉取、联网尽调、@知识库、规则参考初筛、大模型终局报告、沉淀周报。" },
    { text: "作品价值：单份从 4 小时降到约 3 分钟，周报从约 2 小时降到约 10 分钟。" },
    { text: "如实说明：当前网页端对方公司风险查询保留了无可用联网工具的降级截图，不包装成已完成工商查询。", accent: true },
  ], 128, 318, 980, 52);
  text(s, "一句话收束：办公小浣熊负责把合同初审持续跑起来，人只需要复核异常、确认修改和决定是否签署。", { left: 118, top: 588, width: 1000, height: 36 }, { fontSize: 20, bold: false, color: C.ink });
  footer(s, 10);
}

for (const [i, slide] of p.slides.items.entries()) {
  const stem = `slide-${String(i + 1).padStart(2, "0")}`;
  const png = await p.export({ slide, format: "png", scale: 1 });
  await fs.writeFile(path.join(PREVIEW, `${stem}.png`), new Uint8Array(await png.arrayBuffer()));
  const layout = await slide.export({ format: "layout" });
  await fs.writeFile(path.join(LAYOUT, `${stem}.layout.json`), await layout.text());
}

const montage = await p.export({ format: "webp", montage: true, scale: 1 });
await fs.writeFile(path.join(OUT, "ppt/xiaohuanxiong-workflow-montage.webp"), new Uint8Array(await montage.arrayBuffer()));

const pptx = await PresentationFile.exportPptx(p);
await pptx.save(FINAL);

await fs.writeFile(path.join(OUT, "ppt/xiaohuanxiong-source-notes.txt"), [
  "材料来源说明",
  "- 提交说明：docs/OPC_SUBMISSION.md。",
  "- 规则证据图示：docs/CREWAI_RULE_EVIDENCE_FLOW.md。",
  "- 小浣熊桌面端截图：2026-06-20 从本机应用真实截取。",
  "- 小浣熊任务运行录屏：outputs/xiaohuanxiong-screenshot-pack/12-desktop-task-run/desktop-raccoon-task-run-verified.mov。",
  "- 本地审核台截图和样本统计：来自 outputs/opc-demo/ 目录下的样本合同运行结果。",
  "- 如实说明：当前对方公司风险查询保留了无可用联网工具时的降级截图，未包装成已完成工商查询。",
].join("\n"));

await fs.writeFile(path.join(OUT, "ppt/xiaohuanxiong-slide-plan.txt"), [
  "制作方式：guizang-ppt-skill 瑞士风 HTML + artifact-tool 同步 PPTX。",
  "页面尺寸：1280x720 · 主题：克莱因蓝 IKB。",
  "叙事顺序：真实场景 -> 小浣熊运行证据 -> 完整工作流 -> 规则清单定位 -> 样本审核结果 -> 证据链 -> 提交判断。",
  "页数：10。",
].join("\n"));

console.log(FINAL);
