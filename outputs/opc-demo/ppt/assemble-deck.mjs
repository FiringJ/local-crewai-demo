#!/usr/bin/env node
/**
 * Assemble guizang Swiss template + deck extensions + slide content → index.html
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const templatePath = "/Users/firingj/.cursor/skills/guizang-ppt-skill/assets/template-swiss.html";
const slidesPath = path.join(__dirname, "xiaohuanxiong-slides.html");
const extensionsPath = path.join(__dirname, "deck-extensions.css");
const outPath = path.join(__dirname, "index.html");
const motionSrc = "/Users/firingj/.cursor/skills/guizang-ppt-skill/assets/motion.min.js";
const motionDst = path.join(__dirname, "assets/motion.min.js");

const DECK_TITLE = "办公小浣熊 · 企业合同审查持续运营工作流 · 复赛";

let html = fs.readFileSync(templatePath, "utf8");
const slidesRaw = fs.readFileSync(slidesPath, "utf8");
const extensions = fs.existsSync(extensionsPath)
  ? fs.readFileSync(extensionsPath, "utf8")
  : "";

function extractSlides(raw) {
  const startMarker = "<!-- SLIDES_CONTENT -->";
  const endMarker = "<!-- /SLIDES_CONTENT -->";
  const start = raw.indexOf(startMarker);
  const end = raw.indexOf(endMarker);
  if (start !== -1 && end !== -1 && end > start) {
    return raw.slice(start + startMarker.length, end).trim();
  }
  return raw.trim();
}

const slides = extractSlides(slidesRaw);

html = html.replace("[必填] 替换为 PPT 标题 · Deck Title", DECK_TITLE);

if (extensions.trim()) {
  html = html.replace("</style>", `${extensions}\n</style>`);
}

const start = html.indexOf("<!-- SLIDES_HERE");
const end = html.indexOf("\n</div>\n\n<div id=\"nav\">");
if (start === -1 || end === -1) {
  throw new Error("Could not locate SLIDES_HERE insertion point in template");
}

html = html.slice(0, start) + "<!-- SLIDES_HERE -->\n" + slides + html.slice(end);

fs.mkdirSync(path.dirname(motionDst), { recursive: true });
fs.copyFileSync(motionSrc, motionDst);
fs.writeFileSync(outPath, html);

const slideCount = (slides.match(/<section\b/g) || []).length;
console.log(`Wrote ${outPath} (${slideCount} slides)`);
