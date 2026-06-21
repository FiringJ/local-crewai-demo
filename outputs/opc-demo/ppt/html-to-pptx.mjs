#!/usr/bin/env node
/**
 * Export guizang HTML deck to PPTX (full-slide screenshots).
 * Usage: node html-to-pptx.mjs
 */
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";
import { Presentation, PresentationFile } from "/Users/firingj/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/.pnpm/@oai+artifact-tool@file+local-deps+-oai-artifact-tool-oai-artifact_tool-2.8.13.tgz/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "../../..");
const HTML = path.join(__dirname, "index.html");
const OUT_PPTX = path.join(__dirname, "opc-xiaohuanxiong-workflow-submission.pptx");
const SHOT_DIR = path.join(__dirname, "html-export-shots");
const PREVIEW = path.join(__dirname, "xiaohuanxiong-preview");

const W = 1280;
const H = 720;

await fs.mkdir(SHOT_DIR, { recursive: true });
await fs.mkdir(PREVIEW, { recursive: true });

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 2 });
await page.goto(`file://${HTML}`, { waitUntil: "networkidle" });
await page.waitForTimeout(800);

// Static mode: stop WebGL/animations for stable export
await page.evaluate(() => window.__setLowPowerMode(true, { silent: true }));
await page.evaluate(() => {
  for (const id of ["hint", "nav"]) {
    const el = document.getElementById(id);
    if (el) el.style.display = "none";
  }
});
await page.waitForTimeout(400);

const total = await page.evaluate(() => document.querySelectorAll("#deck .slide").length);
const shots = [];

for (let i = 0; i < total; i += 1) {
  await page.evaluate((n) => {
    const deck = document.getElementById("deck");
    const slides = deck.querySelectorAll(".slide");
    deck.style.transform = `translateX(${-n * 100}vw)`;
    document.querySelectorAll("#nav .dot").forEach((d, idx) => d.classList.toggle("active", idx === n));
    const el = slides[n];
    const isDark = el.classList.contains("dark") || el.classList.contains("accent");
    document.body.classList.toggle("dark-bg", isDark);
    window.__currentSlideIndex = n;
    if (window.__playSlide) window.__playSlide(n);
  }, i);
  await page.waitForTimeout(1200);
  const shotPath = path.join(SHOT_DIR, `slide-${String(i + 1).padStart(2, "0")}.png`);
  await page.screenshot({ path: shotPath, fullPage: false });
  await fs.copyFile(shotPath, path.join(PREVIEW, `slide-${String(i + 1).padStart(2, "0")}.png`));
  shots.push(shotPath);
  console.log(`Captured ${i + 1}/${total}`);
}

await browser.close();

const p = Presentation.create({ slideSize: { width: W, height: H } });

for (const shotPath of shots) {
  const slide = p.slides.add();
  slide.background.fill = "#FAFAF8";
  const blob = await fs.readFile(shotPath);
  slide.images.add({
    blob,
    contentType: "image/png",
    alt: path.basename(shotPath),
    fit: "cover",
    position: { left: 0, top: 0, width: W, height: H },
    geometry: "rect",
  });
}

const pptx = await PresentationFile.exportPptx(p);
await pptx.save(OUT_PPTX);
console.log(OUT_PPTX);
