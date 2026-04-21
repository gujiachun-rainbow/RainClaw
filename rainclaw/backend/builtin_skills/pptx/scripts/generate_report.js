#!/usr/bin/env node
/**
 * generate_report.js — JSON-driven PPTX presentation generator
 *
 * Usage:  node generate_report.js <data.json> [output.pptx]
 *
 * Produces professionally styled 16:9 presentations with:
 *   - Dark cover slide with title, subtitle, author, date
 *   - Auto-generated Table of Contents slide (from section titles)
 *   - Agenda slide with numbered items
 *   - Content slides with varied layouts (text, bullets, two-column, stats, tables, charts)
 *   - Section divider slides
 *   - Quote slides
 *   - Closing slide
 *
 * Supported slide types:
 *   title, agenda, section, content, bullets, two_column, table,
 *   stat, image, chart_bar, chart_pie, chart_line, quote, closing
 */

"use strict";

const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

// ── Theme palettes ───────────────────────────────────────────────
const THEMES = {
  midnight:  { primary: "1E2761", secondary: "CADCFC", accent: "408EC6", bg_dark: "0F1535", text_light: "E8ECF1", text_dark: "1E2761" },
  forest:    { primary: "2C5F2D", secondary: "97BC62", accent: "4A7C59", bg_dark: "1A3A1C", text_light: "E8F0E8", text_dark: "2C5F2D" },
  coral:     { primary: "F96167", secondary: "F9E795", accent: "2F3C7E", bg_dark: "2F3C7E", text_light: "F9E795", text_dark: "2F3C7E" },
  ocean:     { primary: "065A82", secondary: "1C7293", accent: "21295C", bg_dark: "041E2E", text_light: "D0E8F2", text_dark: "065A82" },
  charcoal:  { primary: "36454F", secondary: "F2F2F2", accent: "5A7D8B", bg_dark: "1E2A30", text_light: "E8ECEE", text_dark: "36454F" },
  teal:      { primary: "028090", secondary: "00A896", accent: "02C39A", bg_dark: "013840", text_light: "D0F0EA", text_dark: "028090" },
  berry:     { primary: "6D2E46", secondary: "A26769", accent: "D4A5A5", bg_dark: "3A1525", text_light: "ECE2D0", text_dark: "6D2E46" },
};

const SLIDE_W = 10;
const SLIDE_H = 5.625;
const MARGIN = 0.6;
const CONTENT_W = SLIDE_W - MARGIN * 2;

function getTheme(name) {
  return THEMES[name] || THEMES.midnight;
}

function makeShadow() {
  return { type: "outer", blur: 6, offset: 2, angle: 135, color: "000000", opacity: 0.12 };
}

// ── Slide renderers ──────────────────────────────────────────────

function renderTitleSlide(pres, data, theme) {
  const slide = pres.addSlide();
  slide.background = { color: theme.bg_dark };

  // Left accent bar
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 0.08, h: SLIDE_H,
    fill: { color: theme.accent },
  });

  // Title
  slide.addText(data.title || "Presentation", {
    x: MARGIN + 0.2, y: 1.2, w: CONTENT_W - 0.4, h: 1.6,
    fontSize: 40, fontFace: "Arial", color: "FFFFFF",
    bold: true, align: "left", valign: "bottom",
  });

  // Accent line under title
  slide.addShape(pres.shapes.RECTANGLE, {
    x: MARGIN + 0.2, y: 2.9, w: 2.5, h: 0.04,
    fill: { color: theme.accent },
  });

  // Subtitle
  if (data.subtitle) {
    slide.addText(data.subtitle, {
      x: MARGIN + 0.2, y: 3.1, w: CONTENT_W - 0.4, h: 0.6,
      fontSize: 18, fontFace: "Arial", color: theme.secondary,
      align: "left",
    });
  }

  // Author + Date
  const meta = [data.author, data.date].filter(Boolean).join("  |  ");
  if (meta) {
    slide.addText(meta, {
      x: MARGIN + 0.2, y: 4.6, w: CONTENT_W - 0.4, h: 0.4,
      fontSize: 11, fontFace: "Arial", color: theme.text_light,
      align: "left",
    });
  }

  // Bottom bar
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: SLIDE_H - 0.06, w: SLIDE_W, h: 0.06,
    fill: { color: theme.accent },
  });
}

function renderTocSlide(pres, slides, theme) {
  const tocItems = [];
  for (const s of slides) {
    if (s.type === "section" && s.title) {
      tocItems.push(s.title);
    }
  }
  if (tocItems.length === 0) {
    for (const s of slides) {
      if (s.title && s.type !== "closing" && s.type !== "quote") {
        tocItems.push(s.title);
      }
    }
  }
  if (tocItems.length === 0) return;

  const slide = pres.addSlide();
  slide.background = { color: "FFFFFF" };

  slide.addText("Table of Contents", {
    x: MARGIN, y: 0.3, w: CONTENT_W, h: 0.7,
    fontSize: 28, fontFace: "Arial", color: theme.primary,
    bold: true, align: "left",
  });

  slide.addShape(pres.shapes.RECTANGLE, {
    x: MARGIN, y: 1.0, w: 1.5, h: 0.03,
    fill: { color: theme.accent },
  });

  const startY = 1.3;
  const maxItems = Math.min(tocItems.length, 12);
  const availH = SLIDE_H - startY - 0.5;
  const itemH = Math.min(availH / maxItems, 0.55);

  tocItems.slice(0, maxItems).forEach((item, i) => {
    slide.addShape(pres.shapes.RECTANGLE, {
      x: MARGIN + 0.1, y: startY + i * itemH + itemH / 2 - 0.015,
      w: 0.2, h: 0.03,
      fill: { color: theme.accent },
    });
    slide.addText(String(item), {
      x: MARGIN + 0.5, y: startY + i * itemH,
      w: CONTENT_W - 0.7, h: itemH,
      fontSize: 15, fontFace: "Arial", color: theme.text_dark,
      valign: "middle",
    });
  });

  addFooter(slide, theme, pres);
}

function renderAgendaSlide(pres, sec, theme) {
  const slide = pres.addSlide();
  slide.background = { color: "FFFFFF" };

  const title = sec.title || "Agenda";
  slide.addText(title, {
    x: MARGIN, y: 0.3, w: CONTENT_W, h: 0.7,
    fontSize: 28, fontFace: "Arial", color: theme.primary,
    bold: true, align: "left",
  });

  slide.addShape(pres.shapes.RECTANGLE, {
    x: MARGIN, y: 1.0, w: 1.5, h: 0.03,
    fill: { color: theme.accent },
  });

  const items = sec.items || [];
  const startY = 1.3;
  const itemH = 0.55;

  items.forEach((item, i) => {
    // Number circle
    slide.addShape(pres.shapes.OVAL, {
      x: MARGIN + 0.1, y: startY + i * itemH + 0.05,
      w: 0.35, h: 0.35,
      fill: { color: theme.primary },
    });
    slide.addText(String(i + 1), {
      x: MARGIN + 0.1, y: startY + i * itemH + 0.05,
      w: 0.35, h: 0.35,
      fontSize: 13, fontFace: "Arial", color: "FFFFFF",
      bold: true, align: "center", valign: "middle",
    });
    // Item text
    slide.addText(String(item), {
      x: MARGIN + 0.6, y: startY + i * itemH,
      w: CONTENT_W - 0.8, h: itemH,
      fontSize: 16, fontFace: "Arial", color: theme.text_dark,
      valign: "middle",
    });
  });

  addFooter(slide, theme, pres);
}

function renderSectionSlide(pres, sec, theme) {
  const slide = pres.addSlide();
  slide.background = { color: theme.bg_dark };

  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 0.08, h: SLIDE_H,
    fill: { color: theme.accent },
  });

  slide.addText(sec.title || "", {
    x: MARGIN + 0.3, y: 1.8, w: CONTENT_W - 0.6, h: 1.2,
    fontSize: 34, fontFace: "Arial", color: "FFFFFF",
    bold: true, align: "left", valign: "middle",
  });

  slide.addShape(pres.shapes.RECTANGLE, {
    x: MARGIN + 0.3, y: 3.1, w: 2, h: 0.04,
    fill: { color: theme.accent },
  });

  if (sec.subtitle) {
    slide.addText(sec.subtitle, {
      x: MARGIN + 0.3, y: 3.3, w: CONTENT_W - 0.6, h: 0.6,
      fontSize: 16, fontFace: "Arial", color: theme.secondary,
      align: "left",
    });
  }
}

function renderContentSlide(pres, sec, theme) {
  const slide = pres.addSlide();
  slide.background = { color: "FFFFFF" };
  addSlideTitle(slide, sec.title, theme, pres);

  const layout = sec.layout || "text";
  const bodyY = 1.3;
  const bodyH = SLIDE_H - bodyY - 0.6;

  if (layout === "text-image" && sec.image && fs.existsSync(sec.image)) {
    // Left text, right image
    const textW = CONTENT_W * 0.55;
    const imgW = CONTENT_W * 0.4;

    if (sec.body) {
      slide.addText(sec.body, {
        x: MARGIN, y: bodyY, w: textW, h: bodyH,
        fontSize: 13, fontFace: "Arial", color: "444444",
        valign: "top", lineSpacingMultiple: 1.4,
      });
    }

    slide.addImage({
      path: sec.image,
      x: MARGIN + textW + CONTENT_W * 0.05, y: bodyY,
      w: imgW, h: bodyH,
      sizing: { type: "contain", w: imgW, h: bodyH },
    });
  } else {
    if (sec.body) {
      slide.addText(sec.body, {
        x: MARGIN, y: bodyY, w: CONTENT_W, h: bodyH,
        fontSize: 14, fontFace: "Arial", color: "444444",
        valign: "top", lineSpacingMultiple: 1.4,
      });
    }
  }

  addFooter(slide, theme, pres);
}

function renderBulletsSlide(pres, sec, theme) {
  const slide = pres.addSlide();
  slide.background = { color: "FFFFFF" };
  addSlideTitle(slide, sec.title, theme, pres);

  if (sec.subtitle) {
    slide.addText(sec.subtitle, {
      x: MARGIN, y: 1.1, w: CONTENT_W, h: 0.35,
      fontSize: 13, fontFace: "Arial", color: "888888",
    });
  }

  const items = sec.items || [];
  const startY = sec.subtitle ? 1.5 : 1.3;
  const availH = SLIDE_H - startY - 0.5;
  const itemH = Math.min(availH / Math.max(items.length, 1), 0.65);

  items.forEach((item, i) => {
    // Accent dot
    slide.addShape(pres.shapes.OVAL, {
      x: MARGIN + 0.1, y: startY + i * itemH + itemH / 2 - 0.04,
      w: 0.08, h: 0.08,
      fill: { color: theme.accent },
    });
    slide.addText(String(item), {
      x: MARGIN + 0.35, y: startY + i * itemH,
      w: CONTENT_W - 0.5, h: itemH,
      fontSize: 14, fontFace: "Arial", color: "444444",
      valign: "middle", lineSpacingMultiple: 1.2,
    });
  });

  addFooter(slide, theme, pres);
}

function renderTwoColumnSlide(pres, sec, theme) {
  const slide = pres.addSlide();
  slide.background = { color: "FFFFFF" };
  addSlideTitle(slide, sec.title, theme, pres);

  const colW = (CONTENT_W - 0.4) / 2;
  const colY = 1.3;
  const colH = SLIDE_H - colY - 0.5;

  [sec.left, sec.right].forEach((col, ci) => {
    if (!col) return;
    const x = MARGIN + ci * (colW + 0.4);

    // Card background
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y: colY, w: colW, h: colH,
      fill: { color: ci === 0 ? "F8F9FA" : "F0F4F8" },
      shadow: makeShadow(),
    });

    // Column heading
    if (col.heading) {
      slide.addText(col.heading, {
        x: x + 0.2, y: colY + 0.15, w: colW - 0.4, h: 0.4,
        fontSize: 15, fontFace: "Arial", color: theme.primary,
        bold: true,
      });
    }

    const contentY = colY + (col.heading ? 0.6 : 0.2);
    const contentH = colH - (col.heading ? 0.8 : 0.4);

    if (col.body) {
      slide.addText(col.body, {
        x: x + 0.2, y: contentY, w: colW - 0.4, h: contentH,
        fontSize: 12, fontFace: "Arial", color: "555555",
        valign: "top", lineSpacingMultiple: 1.3,
      });
    } else if (col.items) {
      const bulletText = col.items.map(item => ({
        text: String(item),
        options: { bullet: true, breakLine: true, fontSize: 12, color: "555555" },
      }));
      slide.addText(bulletText, {
        x: x + 0.2, y: contentY, w: colW - 0.4, h: contentH,
        fontFace: "Arial", valign: "top",
      });
    }
  });

  addFooter(slide, theme, pres);
}

function renderTableSlide(pres, sec, theme) {
  const slide = pres.addSlide();
  slide.background = { color: "FFFFFF" };
  addSlideTitle(slide, sec.title, theme, pres);

  const headers = sec.headers || [];
  const rows = sec.rows || [];
  const nCols = headers.length || (rows[0] || []).length || 1;
  const colW = CONTENT_W / nCols;

  const tableData = [];

  if (headers.length) {
    tableData.push(headers.map(h => ({
      text: String(h),
      options: { bold: true, color: "FFFFFF", fontSize: 11, fontFace: "Arial", align: "center" },
    })));
  }

  rows.forEach(row => {
    tableData.push(row.map(cell => ({
      text: String(cell),
      options: { fontSize: 10, fontFace: "Arial", color: "444444" },
    })));
  });

  if (tableData.length) {
    slide.addTable(tableData, {
      x: MARGIN, y: 1.4, w: CONTENT_W,
      colW: Array(nCols).fill(colW),
      border: { pt: 0.5, color: "CCCCCC" },
      rowH: 0.35,
      autoPage: false,
    });

    // Style header row
    if (headers.length && tableData.length > 0) {
      slide.addShape(pres.shapes.RECTANGLE, {
        x: MARGIN, y: 1.4, w: CONTENT_W, h: 0.35,
        fill: { color: theme.primary },
      });
      // Re-add header text on top of the shape
      headers.forEach((h, i) => {
        slide.addText(String(h), {
          x: MARGIN + i * colW, y: 1.4, w: colW, h: 0.35,
          fontSize: 11, fontFace: "Arial", color: "FFFFFF",
          bold: true, align: "center", valign: "middle",
        });
      });
    }
  }

  if (sec.caption) {
    slide.addText(sec.caption, {
      x: MARGIN, y: SLIDE_H - 0.7, w: CONTENT_W, h: 0.3,
      fontSize: 9, fontFace: "Arial", color: "999999",
      italic: true, align: "center",
    });
  }

  addFooter(slide, theme, pres);
}

function renderStatSlide(pres, sec, theme) {
  const slide = pres.addSlide();
  slide.background = { color: "FFFFFF" };
  addSlideTitle(slide, sec.title, theme, pres);

  const stats = sec.stats || [];
  const n = Math.min(stats.length, 4);
  if (n === 0) return;

  const cardW = (CONTENT_W - (n - 1) * 0.3) / n;
  const cardH = 2.2;
  const cardY = 1.6;

  stats.slice(0, 4).forEach((stat, i) => {
    const x = MARGIN + i * (cardW + 0.3);

    slide.addShape(pres.shapes.RECTANGLE, {
      x, y: cardY, w: cardW, h: cardH,
      fill: { color: "F8F9FA" },
      shadow: makeShadow(),
    });

    // Top accent bar on card
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y: cardY, w: cardW, h: 0.04,
      fill: { color: theme.accent },
    });

    // Big number
    slide.addText(String(stat.value || ""), {
      x, y: cardY + 0.3, w: cardW, h: 1.0,
      fontSize: 36, fontFace: "Arial", color: theme.primary,
      bold: true, align: "center", valign: "middle",
    });

    // Label
    slide.addText(String(stat.label || ""), {
      x: x + 0.1, y: cardY + 1.3, w: cardW - 0.2, h: 0.7,
      fontSize: 11, fontFace: "Arial", color: "777777",
      align: "center", valign: "top",
    });
  });

  addFooter(slide, theme, pres);
}

function renderImageSlide(pres, sec, theme) {
  const slide = pres.addSlide();
  slide.background = { color: "FFFFFF" };
  addSlideTitle(slide, sec.title, theme, pres);

  const imgPath = sec.image;
  if (imgPath && fs.existsSync(imgPath)) {
    const imgY = 1.3;
    const imgH = SLIDE_H - imgY - 0.8;
    slide.addImage({
      path: imgPath,
      x: MARGIN + 0.5, y: imgY,
      w: CONTENT_W - 1.0, h: imgH,
      sizing: { type: "contain", w: CONTENT_W - 1.0, h: imgH },
    });
  }

  if (sec.caption) {
    slide.addText(sec.caption, {
      x: MARGIN, y: SLIDE_H - 0.7, w: CONTENT_W, h: 0.3,
      fontSize: 10, fontFace: "Arial", color: "999999",
      italic: true, align: "center",
    });
  }

  addFooter(slide, theme, pres);
}

function renderChartBarSlide(pres, sec, theme) {
  const slide = pres.addSlide();
  slide.background = { color: "FFFFFF" };
  addSlideTitle(slide, sec.title, theme, pres);

  const cats = sec.categories || [];
  const series = sec.series || [];
  if (!cats.length || !series.length) return;

  const chartColors = [theme.primary, theme.accent, theme.secondary, "E8A838", "E05555", "8B5CF6"];

  const chartData = series.map((s, i) => ({
    name: s.name || `Series ${i + 1}`,
    labels: cats,
    values: s.values || [],
  }));

  slide.addChart(pres.charts.BAR, chartData, {
    x: MARGIN + 0.3, y: 1.4, w: CONTENT_W - 0.6, h: 3.5,
    barDir: "col",
    showTitle: false,
    showValue: true,
    dataLabelPosition: "outEnd",
    dataLabelColor: "555555",
    dataLabelFontSize: 8,
    chartColors: chartColors.slice(0, series.length),
    catAxisLabelColor: "666666",
    valAxisLabelColor: "666666",
    catAxisLabelFontSize: 9,
    valAxisLabelFontSize: 8,
    valGridLine: { color: "E8E8E8", size: 0.5 },
    catGridLine: { style: "none" },
    showLegend: series.length > 1,
    legendPos: "b",
    legendFontSize: 9,
  });

  addFooter(slide, theme, pres);
}

function renderChartPieSlide(pres, sec, theme) {
  const slide = pres.addSlide();
  slide.background = { color: "FFFFFF" };
  addSlideTitle(slide, sec.title, theme, pres);

  const labels = sec.labels || [];
  const values = sec.values || [];
  if (!labels.length || !values.length) return;

  const chartColors = [theme.primary, theme.accent, theme.secondary, "E8A838", "E05555", "8B5CF6", "38A169", "D69E2E"];

  const chartData = [{
    name: sec.title || "Distribution",
    labels,
    values,
  }];

  slide.addChart(pres.charts.PIE, chartData, {
    x: MARGIN + 0.5, y: 1.3, w: CONTENT_W - 1.0, h: 3.6,
    showTitle: false,
    showValue: false,
    showPercent: true,
    showLegend: true,
    legendPos: "r",
    legendFontSize: 10,
    dataLabelColor: "FFFFFF",
    dataLabelFontSize: 10,
    chartColors: chartColors.slice(0, labels.length),
  });

  addFooter(slide, theme, pres);
}

function renderChartLineSlide(pres, sec, theme) {
  const slide = pres.addSlide();
  slide.background = { color: "FFFFFF" };
  addSlideTitle(slide, sec.title, theme, pres);

  const xLabels = sec.x_labels || [];
  const series = sec.series || [];
  if (!xLabels.length || !series.length) return;

  const chartColors = [theme.primary, theme.accent, "38A169", "E8A838", "E05555", "8B5CF6"];

  const chartData = series.map((s, i) => ({
    name: s.name || `Series ${i + 1}`,
    labels: xLabels,
    values: s.values || [],
  }));

  slide.addChart(pres.charts.LINE, chartData, {
    x: MARGIN + 0.3, y: 1.4, w: CONTENT_W - 0.6, h: 3.5,
    showTitle: false,
    showValue: false,
    lineDataSymbol: "circle",
    lineDataSymbolSize: 6,
    chartColors: chartColors.slice(0, series.length),
    catAxisLabelColor: "666666",
    valAxisLabelColor: "666666",
    catAxisLabelFontSize: 9,
    valAxisLabelFontSize: 8,
    valGridLine: { color: "E8E8E8", size: 0.5 },
    catGridLine: { style: "none" },
    showLegend: series.length > 1,
    legendPos: "b",
    legendFontSize: 9,
  });

  addFooter(slide, theme, pres);
}

function renderQuoteSlide(pres, sec, theme) {
  const slide = pres.addSlide();
  slide.background = { color: theme.bg_dark };

  // Large quote mark
  slide.addText("\u201C", {
    x: MARGIN, y: 0.8, w: 1, h: 1.2,
    fontSize: 80, fontFace: "Georgia", color: theme.accent,
    bold: true,
  });

  // Quote text
  slide.addText(sec.text || "", {
    x: MARGIN + 0.5, y: 1.6, w: CONTENT_W - 1, h: 2.2,
    fontSize: 20, fontFace: "Georgia", color: "FFFFFF",
    italic: true, align: "left", valign: "middle",
    lineSpacingMultiple: 1.5,
  });

  // Attribution
  const attr = [sec.author, sec.title].filter(Boolean).join(", ");
  if (attr) {
    slide.addText(`— ${attr}`, {
      x: MARGIN + 0.5, y: 4.0, w: CONTENT_W - 1, h: 0.4,
      fontSize: 13, fontFace: "Arial", color: theme.secondary,
      align: "right",
    });
  }

  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: SLIDE_H - 0.06, w: SLIDE_W, h: 0.06,
    fill: { color: theme.accent },
  });
}

function renderClosingSlide(pres, sec, theme) {
  const slide = pres.addSlide();
  slide.background = { color: theme.bg_dark };

  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 0.08, h: SLIDE_H,
    fill: { color: theme.accent },
  });

  slide.addText(sec.title || "Thank You", {
    x: MARGIN + 0.3, y: 1.5, w: CONTENT_W - 0.6, h: 1.2,
    fontSize: 38, fontFace: "Arial", color: "FFFFFF",
    bold: true, align: "center", valign: "middle",
  });

  slide.addShape(pres.shapes.RECTANGLE, {
    x: SLIDE_W / 2 - 1.2, y: 2.8, w: 2.4, h: 0.04,
    fill: { color: theme.accent },
  });

  if (sec.subtitle) {
    slide.addText(sec.subtitle, {
      x: MARGIN + 0.3, y: 3.0, w: CONTENT_W - 0.6, h: 0.6,
      fontSize: 16, fontFace: "Arial", color: theme.secondary,
      align: "center",
    });
  }

  if (sec.contact) {
    slide.addText(sec.contact, {
      x: MARGIN + 0.3, y: 3.8, w: CONTENT_W - 0.6, h: 0.5,
      fontSize: 12, fontFace: "Arial", color: theme.text_light,
      align: "center",
    });
  }

  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: SLIDE_H - 0.06, w: SLIDE_W, h: 0.06,
    fill: { color: theme.accent },
  });
}

// ── Helpers ──────────────────────────────────────────────────────

function addSlideTitle(slide, title, theme, presRef) {
  if (!title) return;
  slide.addText(title, {
    x: MARGIN, y: 0.25, w: CONTENT_W, h: 0.65,
    fontSize: 24, fontFace: "Arial", color: theme.primary,
    bold: true, align: "left", valign: "bottom",
  });
  slide.addShape(presRef.shapes.RECTANGLE, {
    x: MARGIN, y: 0.95, w: 1.5, h: 0.025,
    fill: { color: theme.accent },
  });
}

function addFooter(slide, theme, presRef) {
  slide.addShape(presRef.shapes.RECTANGLE, {
    x: 0, y: SLIDE_H - 0.04, w: SLIDE_W, h: 0.04,
    fill: { color: theme.primary },
  });
}

// ── Dispatch ─────────────────────────────────────────────────────

let pres;

const RENDERERS = {
  agenda:     (sec, theme) => renderAgendaSlide(pres, sec, theme),
  section:    (sec, theme) => renderSectionSlide(pres, sec, theme),
  content:    (sec, theme) => renderContentSlide(pres, sec, theme),
  bullets:    (sec, theme) => renderBulletsSlide(pres, sec, theme),
  two_column: (sec, theme) => renderTwoColumnSlide(pres, sec, theme),
  table:      (sec, theme) => renderTableSlide(pres, sec, theme),
  stat:       (sec, theme) => renderStatSlide(pres, sec, theme),
  image:      (sec, theme) => renderImageSlide(pres, sec, theme),
  chart_bar:  (sec, theme) => renderChartBarSlide(pres, sec, theme),
  chart_pie:  (sec, theme) => renderChartPieSlide(pres, sec, theme),
  chart_line: (sec, theme) => renderChartLineSlide(pres, sec, theme),
  quote:      (sec, theme) => renderQuoteSlide(pres, sec, theme),
  closing:    (sec, theme) => renderClosingSlide(pres, sec, theme),
};

// ── Main ─────────────────────────────────────────────────────────

async function main() {
  const args = process.argv.slice(2);
  if (args.length < 1) {
    console.error("Usage: node generate_report.js <data.json> [output.pptx]");
    process.exit(1);
  }

  const jsonPath = args[0];
  const outputPath = args[1] || "presentation.pptx";

  if (!fs.existsSync(jsonPath)) {
    console.error(`Error: ${jsonPath} not found`);
    process.exit(1);
  }

  const data = JSON.parse(fs.readFileSync(jsonPath, "utf-8"));
  const theme = getTheme(data.theme);

  pres = new pptxgen();
  pres.layout = "LAYOUT_16x9";
  pres.author = data.author || "ScienceClaw";
  pres.title = data.title || "Presentation";

  // Title slide (always first)
  renderTitleSlide(pres, data, theme);

  // TOC slide (second slide, auto-generated unless toc: false)
  const slides = data.slides || [];
  if (data.toc !== false) {
    renderTocSlide(pres, slides, theme);
  }

  // Content slides
  for (const sec of slides) {
    const renderer = RENDERERS[sec.type];
    if (renderer) {
      renderer(sec, theme);
    } else {
      console.warn(`Unknown slide type: ${sec.type}, skipping`);
    }
  }

  await pres.writeFile({ fileName: outputPath });

  const hasToc = data.toc !== false;
  const slideCount = slides.length + 1 + (hasToc ? 1 : 0);
  console.log(`Presentation generated: ${outputPath}`);
  console.log(`  Title  : ${data.title || "(none)"}`);
  console.log(`  Theme  : ${data.theme || "midnight"}`);
  console.log(`  TOC    : ${hasToc ? "yes" : "no"}`);
  console.log(`  Slides : ${slideCount}`);
}

main().catch(err => {
  console.error("Error:", err.message || err);
  process.exit(1);
});
