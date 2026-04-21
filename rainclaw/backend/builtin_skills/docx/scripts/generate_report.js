#!/usr/bin/env node
/**
 * generate_report.js — JSON-driven DOCX report generator
 *
 * Usage:  node generate_report.js <data.json> <output.docx>
 *
 * Accepts the SAME JSON schema as the PDF generate_report.py so that
 * one data file can produce both PDF and DOCX output.
 *
 * Supported section types:
 *   heading, text, bullets, table, kv, image, callout,
 *   references, page_break
 */

"use strict";

const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
  ShadingType, PageNumber, PageBreak, TableOfContents, LevelFormat,
  ImageRun, ExternalHyperlink, InternalHyperlink, Bookmark,
  FootnoteReferenceRun, TabStopType, TabStopPosition,
} = require("docx");

// ── Colour palette (matches PDF template) ────────────────────────
const NAVY    = "1B3A5C";
const ACCENT  = "2E75B6";
const LIGHT   = "F2F7FB";
const MUTED   = "888888";
const BODY_C  = "333333";
const WHITE   = "FFFFFF";
const REF_C   = "555555";

// ── Line spacing: 1.5x = 360 (in 240ths of a line) ──────────────
const LINE_SPACING = 360;

// ── Page geometry (A4) ───────────────────────────────────────────
const PAGE_W  = 11906;  // A4 width  in DXA
const PAGE_H  = 16838;  // A4 height in DXA
const MARGIN  = 1440;   // 1 inch
const CONTENT_W = PAGE_W - 2 * MARGIN;  // 9026 DXA

// ── Thin border helper ───────────────────────────────────────────
const thinBorder = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const cellBorders = { top: thinBorder, bottom: thinBorder, left: thinBorder, right: thinBorder };
const noBorder = { style: BorderStyle.NONE, size: 0 };
const noBorders = { top: noBorder, bottom: noBorder, left: noBorder, right: noBorder };
const cellPad = { top: 80, bottom: 80, left: 120, right: 120 };

// ── Citation regex ───────────────────────────────────────────────
const CITE_RE = /\[(\d+(?:\s*[,，、]\s*\d+)*)\]/g;

function parseCitations(text) {
  const parts = [];
  let last = 0;
  let m;
  CITE_RE.lastIndex = 0;
  while ((m = CITE_RE.exec(text)) !== null) {
    if (m.index > last) {
      parts.push({ type: "text", value: text.slice(last, m.index) });
    }
    const nums = m[1].split(/\s*[,，、]\s*/);
    parts.push({ type: "cite", nums });
    last = m.index + m[0].length;
  }
  if (last < text.length) {
    parts.push({ type: "text", value: text.slice(last) });
  }
  return parts;
}

function textRunsWithCitations(text, opts = {}) {
  const BOLD_RE = /\*\*(.+?)\*\*/g;

  function expandBoldAndCitations(str, baseOpts) {
    const runs = [];
    let last = 0;
    let bm;
    BOLD_RE.lastIndex = 0;
    while ((bm = BOLD_RE.exec(str)) !== null) {
      if (bm.index > last) {
        runs.push(...citationRuns(str.slice(last, bm.index), baseOpts));
      }
      runs.push(...citationRuns(bm[1], { ...baseOpts, bold: true }));
      last = bm.index + bm[0].length;
    }
    if (last < str.length) {
      runs.push(...citationRuns(str.slice(last), baseOpts));
    }
    return runs;
  }

  function citationRuns(str, baseOpts) {
    const parts = parseCitations(str);
    const runs = [];
    for (const p of parts) {
      if (p.type === "text") {
        runs.push(new TextRun({ text: p.value, ...baseOpts }));
      } else {
        for (let i = 0; i < p.nums.length; i++) {
          const n = p.nums[i].trim();
          runs.push(new TextRun({
            text: `[${n}]`,
            superScript: true,
            color: ACCENT,
            font: baseOpts.font || "Arial",
            size: (baseOpts.size || 22) - 4,
          }));
        }
      }
    }
    return runs;
  }

  return expandBoldAndCitations(text, opts);
}

// ── Section renderers ────────────────────────────────────────────

function renderHeading(sec) {
  const level = sec.level || 1;
  const num = sec.number || "";
  const display = num ? `${num} ${sec.text}` : sec.text;
  const hl = level === 1 ? HeadingLevel.HEADING_1
           : level === 2 ? HeadingLevel.HEADING_2
           : HeadingLevel.HEADING_3;
  const result = [];
  if (level === 1) {
    result.push(new Paragraph({
      border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: ACCENT, space: 1 } },
      spacing: { before: 360, after: 80 },
      children: [],
    }));
  }
  result.push(new Paragraph({
    heading: hl,
    children: [new TextRun(display)],
  }));
  return result;
}

const MD_HEADING_RE  = /^(#{1,4})\s+(.*)/;
const MD_BULLET_RE   = /^[-*]\s+(.*)/;
const MD_NUMLIST_RE  = /^\d+[.)]\s+(.*)/;
const MD_TABLE_ROW   = /^\|(.+)\|$/;
const MD_TABLE_SEP   = /^\|[\s:|-]+\|$/;

function renderText(sec) {
  const result = [];
  if (sec.heading) {
    result.push(new Paragraph({
      spacing: { before: 120, after: 60 },
      children: [new TextRun({ text: sec.heading, bold: true, color: NAVY, size: 24, font: "Arial" })],
    }));
  }
  if (!sec.body) return result;

  const body = sec.body.replace(/(\d+\.)\s*\n(?!\n)/g, "$1 ");
  const lines = body.split("\n");
  const pending = [];
  const pendingTable = [];

  function flushParagraph() {
    if (pending.length === 0) return;
    const text = pending.join(" ");
    pending.length = 0;
    result.push(new Paragraph({
      alignment: AlignmentType.JUSTIFIED,
      spacing: { before: 40, after: 80, line: LINE_SPACING },
      children: textRunsWithCitations(text, { font: "Arial", size: 22, color: BODY_C }),
    }));
  }

  function flushTable() {
    if (pendingTable.length === 0) return;
    const dataRows = pendingTable.filter(r => !MD_TABLE_SEP.test(r));
    pendingTable.length = 0;
    if (dataRows.length === 0) return;

    const parseRow = (r) => r.replace(/^\|/, "").replace(/\|$/, "").split("|").map(c => c.trim());
    const headers = parseRow(dataRows[0]);
    const rows = dataRows.slice(1).map(parseRow);

    result.push(...renderTable({ headers, rows }));
  }

  for (const line of lines) {
    const stripped = line.trim();

    if (MD_TABLE_ROW.test(stripped)) {
      flushParagraph();
      pendingTable.push(stripped);
      continue;
    } else if (pendingTable.length) {
      flushTable();
    }

    if (!stripped) {
      flushParagraph();
      continue;
    }

    const hm = MD_HEADING_RE.exec(stripped);
    if (hm) {
      flushParagraph();
      const level = hm[1].length;
      const htext = hm[2];
      const hl = level <= 2 ? HeadingLevel.HEADING_2 : HeadingLevel.HEADING_3;
      result.push(new Paragraph({
        heading: hl,
        children: [new TextRun(htext)],
      }));
      continue;
    }

    let bm = MD_BULLET_RE.exec(stripped);
    if (!bm) bm = MD_NUMLIST_RE.exec(stripped);
    if (bm) {
      flushParagraph();
      result.push(new Paragraph({
        numbering: { reference: "report_bullets", level: 0 },
        spacing: { before: 20, after: 40, line: LINE_SPACING },
        children: textRunsWithCitations(bm[1], { font: "Arial", size: 22, color: BODY_C }),
      }));
      continue;
    }

    pending.push(stripped);
  }

  flushTable();
  flushParagraph();
  return result;
}

function renderBullets(sec, bulletRef) {
  const result = [];
  if (sec.heading) {
    result.push(new Paragraph({
      spacing: { before: 120, after: 60 },
      children: [new TextRun({ text: sec.heading, bold: true, color: NAVY, size: 24, font: "Arial" })],
    }));
  }
  for (const item of (sec.items || [])) {
    result.push(new Paragraph({
      numbering: { reference: bulletRef, level: 0 },
      spacing: { before: 20, after: 40, line: LINE_SPACING },
      children: textRunsWithCitations(String(item), { font: "Arial", size: 22, color: BODY_C }),
    }));
  }
  return result;
}

function renderTable(sec) {
  const result = [];
  if (sec.heading) {
    result.push(new Paragraph({
      spacing: { before: 160, after: 80 },
      children: [new TextRun({ text: sec.heading, bold: true, color: NAVY, size: 22, font: "Arial" })],
    }));
  }

  const headers = sec.headers || [];
  const rows = sec.rows || [];
  const colCount = headers.length || (rows[0] || []).length || 1;
  const colW = Math.floor(CONTENT_W / colCount);
  const colWidths = Array(colCount).fill(colW);
  // Adjust last column to absorb rounding
  colWidths[colCount - 1] = CONTENT_W - colW * (colCount - 1);

  const tableRows = [];

  // Header row
  if (headers.length) {
    tableRows.push(new TableRow({
      tableHeader: true,
      children: headers.map((h, i) => new TableCell({
        borders: cellBorders,
        width: { size: colWidths[i], type: WidthType.DXA },
        shading: { fill: NAVY, type: ShadingType.CLEAR },
        margins: cellPad,
        children: [new Paragraph({
          children: [new TextRun({ text: String(h), bold: true, color: WHITE, font: "Arial", size: 20 })],
        })],
      })),
    }));
  }

  // Data rows
  rows.forEach((row, ri) => {
    const isAlt = ri % 2 === 1;
    tableRows.push(new TableRow({
      children: row.map((cell, ci) => new TableCell({
        borders: cellBorders,
        width: { size: colWidths[ci] || colW, type: WidthType.DXA },
        shading: isAlt ? { fill: LIGHT, type: ShadingType.CLEAR } : undefined,
        margins: cellPad,
        children: [new Paragraph({
          children: [new TextRun({ text: String(cell), font: "Arial", size: 20, color: BODY_C })],
        })],
      })),
    }));
  });

  if (tableRows.length) {
    result.push(new Table({
      width: { size: CONTENT_W, type: WidthType.DXA },
      columnWidths: colWidths,
      rows: tableRows,
    }));
  }

  if (sec.caption) {
    result.push(new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 40, after: 120 },
      children: [new TextRun({ text: sec.caption, italics: true, color: MUTED, size: 18, font: "Arial" })],
    }));
  }

  return result;
}

function renderKv(sec) {
  const result = [];
  if (sec.heading) {
    result.push(new Paragraph({
      spacing: { before: 120, after: 60 },
      children: [new TextRun({ text: sec.heading, bold: true, color: NAVY, size: 24, font: "Arial" })],
    }));
  }

  const items = sec.items || [];
  const keyW = Math.floor(CONTENT_W * 0.35);
  const valW = CONTENT_W - keyW;

  const tableRows = items.map((item, i) => {
    const isAlt = i % 2 === 0;
    return new TableRow({
      children: [
        new TableCell({
          borders: noBorders,
          width: { size: keyW, type: WidthType.DXA },
          shading: isAlt ? { fill: LIGHT, type: ShadingType.CLEAR } : undefined,
          margins: cellPad,
          children: [new Paragraph({
            children: [new TextRun({ text: String(item[0] || ""), bold: true, color: NAVY, font: "Arial", size: 20 })],
          })],
        }),
        new TableCell({
          borders: noBorders,
          width: { size: valW, type: WidthType.DXA },
          shading: isAlt ? { fill: LIGHT, type: ShadingType.CLEAR } : undefined,
          margins: cellPad,
          children: [new Paragraph({
            children: [new TextRun({ text: String(item[1] || ""), font: "Arial", size: 20, color: BODY_C })],
          })],
        }),
      ],
    });
  });

  if (tableRows.length) {
    result.push(new Table({
      width: { size: CONTENT_W, type: WidthType.DXA },
      columnWidths: [keyW, valW],
      rows: tableRows,
    }));
  }
  return result;
}

function renderImage(sec) {
  const result = [];
  const imgPath = sec.path;
  if (!imgPath || !fs.existsSync(imgPath)) {
    result.push(new Paragraph({
      children: [new TextRun({ text: `[Image not found: ${imgPath || "no path"}]`, italics: true, color: MUTED })],
    }));
    return result;
  }

  const imgData = fs.readFileSync(imgPath);
  const ext = path.extname(imgPath).toLowerCase().replace(".", "");
  const type = ext === "jpg" ? "jpeg" : ext;

  // Default width 450pt ≈ 6 inches, auto-scale height
  const widthPx = sec.width ? Math.round(sec.width * 2.835) : 450;
  const heightPx = sec.height ? Math.round(sec.height * 2.835) : Math.round(widthPx * 0.6);

  result.push(new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 120, after: 40 },
    children: [new ImageRun({
      type,
      data: imgData,
      transformation: { width: widthPx, height: heightPx },
      altText: { title: sec.caption || "Image", description: sec.caption || "Image", name: path.basename(imgPath) },
    })],
  }));

  if (sec.caption) {
    result.push(new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 40, after: 120 },
      children: [new TextRun({ text: sec.caption, italics: true, color: MUTED, size: 18, font: "Arial" })],
    }));
  }
  return result;
}

function renderCallout(sec) {
  const result = [];
  const rows = [];

  const content = [];
  if (sec.title) {
    content.push(new Paragraph({
      children: [new TextRun({ text: sec.title, bold: true, color: NAVY, font: "Arial", size: 22 })],
    }));
  }
  if (sec.body) {
    content.push(new Paragraph({
      spacing: { before: 40, line: LINE_SPACING },
      children: textRunsWithCitations(sec.body, { font: "Arial", size: 20, color: BODY_C }),
    }));
  }

  const accentBar = new TableCell({
    borders: noBorders,
    width: { size: 80, type: WidthType.DXA },
    shading: { fill: ACCENT, type: ShadingType.CLEAR },
    children: [new Paragraph({ children: [] })],
  });

  rows.push(new TableRow({
    children: [
      accentBar,
      new TableCell({
        borders: noBorders,
        width: { size: CONTENT_W - 80, type: WidthType.DXA },
        shading: { fill: LIGHT, type: ShadingType.CLEAR },
        margins: { top: 120, bottom: 120, left: 200, right: 200 },
        children: content,
      }),
    ],
  }));

  result.push(new Paragraph({ spacing: { before: 120 }, children: [] }));
  result.push(new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: [80, CONTENT_W - 80],
    rows,
  }));
  result.push(new Paragraph({ spacing: { after: 120 }, children: [] }));
  return result;
}

function renderReferences(sec) {
  const result = [];
  const items = sec.items || [];
  const showHeading = sec.show_heading || (sec.heading != null);

  if (showHeading) {
    const h = sec.heading || "References";
    result.push(new Paragraph({
      border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: ACCENT, space: 1 } },
      spacing: { before: 360, after: 80 },
      children: [],
    }));
    result.push(new Paragraph({
      heading: HeadingLevel.HEADING_1,
      children: [new TextRun(h)],
    }));
  }

  items.forEach((ref, i) => {
    let refStr = typeof ref === "object" && ref !== null
      ? (ref.text || ref.content || JSON.stringify(ref))
      : String(ref);
    refStr = refStr.replace(/^\[\d+\]\s*/, "");
    result.push(new Paragraph({
      spacing: { before: 20, after: 60, line: LINE_SPACING },
      indent: { left: 480, hanging: 480 },
      children: [
        new TextRun({ text: `[${i + 1}]  `, bold: true, color: NAVY, font: "Arial", size: 18 }),
        new TextRun({ text: refStr, font: "Arial", size: 18, color: REF_C }),
      ],
    }));
  });

  return result;
}

function renderPageBreak() {
  return [new Paragraph({ children: [new PageBreak()] })];
}

// ── Cover page builder ───────────────────────────────────────────

function buildCoverSection(data) {
  const children = [];

  // Top spacer
  children.push(new Paragraph({ spacing: { before: 2400 }, children: [] }));

  // Title
  children.push(new Paragraph({
    spacing: { after: 200 },
    children: [new TextRun({
      text: data.title || "Report",
      bold: true, font: "Arial", size: 52, color: NAVY,
    })],
  }));

  // Subtitle
  if (data.subtitle) {
    children.push(new Paragraph({
      spacing: { after: 200 },
      children: [new TextRun({
        text: data.subtitle,
        font: "Arial", size: 28, color: ACCENT, italics: true,
      })],
    }));
  }

  // Accent line
  children.push(new Paragraph({
    border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: ACCENT, space: 1 } },
    spacing: { after: 300 },
    children: [new TextRun({ text: "                              ", size: 2 })],
  }));

  // Cover metadata table
  if (data.cover_meta && data.cover_meta.length) {
    const keyW = Math.floor(CONTENT_W * 0.3);
    const valW = CONTENT_W - keyW;
    const metaRows = data.cover_meta.map((item, i) => {
      if (!item || item.length < 2) return null;
      const isAlt = i % 2 === 0;
      return new TableRow({
        children: [
          new TableCell({
            borders: noBorders,
            width: { size: keyW, type: WidthType.DXA },
            shading: isAlt ? { fill: LIGHT, type: ShadingType.CLEAR } : undefined,
            margins: cellPad,
            children: [new Paragraph({
              children: [new TextRun({ text: String(item[0]), bold: true, color: NAVY, font: "Arial", size: 20 })],
            })],
          }),
          new TableCell({
            borders: noBorders,
            width: { size: valW, type: WidthType.DXA },
            shading: isAlt ? { fill: LIGHT, type: ShadingType.CLEAR } : undefined,
            margins: cellPad,
            children: [new Paragraph({
              children: [new TextRun({ text: String(item[1]), font: "Arial", size: 20, color: BODY_C })],
            })],
          }),
        ],
      });
    }).filter(Boolean);

    if (metaRows.length) {
      children.push(new Table({
        width: { size: CONTENT_W, type: WidthType.DXA },
        columnWidths: [keyW, valW],
        rows: metaRows,
      }));
    }
  }

  // Disclaimer at bottom
  if (data.disclaimer) {
    children.push(new Paragraph({ spacing: { before: 2000 }, children: [] }));
    children.push(new Paragraph({
      children: [new TextRun({
        text: data.disclaimer,
        italics: true, font: "Arial", size: 16, color: MUTED,
      })],
    }));
  }

  // Bottom accent bar via border
  children.push(new Paragraph({
    spacing: { before: 200 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 12, color: NAVY, space: 1 } },
    children: [],
  }));

  return {
    properties: {
      page: {
        size: { width: PAGE_W, height: PAGE_H },
        margin: { top: MARGIN, right: MARGIN, bottom: MARGIN, left: MARGIN },
      },
    },
    children,
  };
}

// ── Main content section builder ─────────────────────────────────

function buildContentSection(data) {
  const bulletRef = "report_bullets";

  const children = [];

  // TOC — Word field-based Table of Contents
  if (data.toc !== false) {
    children.push(new TableOfContents("目录", {
      hyperlink: true,
      headingStyleRange: "1-3",
    }));
    children.push(new Paragraph({ children: [new PageBreak()] }));
  }

  const sections = data.sections || [];
  for (const sec of sections) {
    const type = sec.type;
    let flowables = [];

    switch (type) {
      case "heading":     flowables = renderHeading(sec); break;
      case "text":        flowables = renderText(sec); break;
      case "bullets":     flowables = renderBullets(sec, bulletRef); break;
      case "table":       flowables = renderTable(sec); break;
      case "kv":          flowables = renderKv(sec); break;
      case "image":       flowables = renderImage(sec); break;
      case "callout":     flowables = renderCallout(sec); break;
      case "references":  flowables = renderReferences(sec); break;
      case "page_break":  flowables = renderPageBreak(); break;
      case "cover":
      case "toc":
        break;
      default:
        flowables = [new Paragraph({
          children: [new TextRun({ text: `[Unknown section type: ${type}]`, color: "FF0000" })],
        })];
    }
    children.push(...flowables);
  }

  const shortTitle = data.short_title || data.title || "";
  const reportType = data.report_type || "";

  return {
    properties: {
      page: {
        size: { width: PAGE_W, height: PAGE_H },
        margin: { top: MARGIN, right: MARGIN, bottom: MARGIN, left: MARGIN },
      },
    },
    headers: {
      default: new Header({
        children: [new Paragraph({
          border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: ACCENT, space: 4 } },
          tabStops: [{ type: TabStopType.RIGHT, position: TabStopPosition.MAX }],
          children: [
            new TextRun({ text: shortTitle, font: "Arial", size: 16, color: MUTED }),
            new TextRun({ text: `\t${reportType}`, font: "Arial", size: 16, color: MUTED }),
          ],
        })],
      }),
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          border: { top: { style: BorderStyle.SINGLE, size: 2, color: "CCCCCC", space: 4 } },
          children: [
            new TextRun({ text: "-- ", font: "Arial", size: 18, color: MUTED }),
            new TextRun({ children: [PageNumber.CURRENT], font: "Arial", size: 18, color: MUTED }),
            new TextRun({ text: " --", font: "Arial", size: 18, color: MUTED }),
          ],
        })],
      }),
    },
    children,
  };
}

// ── Main ─────────────────────────────────────────────────────────

async function main() {
  const args = process.argv.slice(2);
  if (args.length < 2) {
    console.error("Usage: node generate_report.js <data.json> <output.docx>");
    process.exit(1);
  }

  const [jsonPath, outputPath] = args;

  if (!fs.existsSync(jsonPath)) {
    console.error(`Error: ${jsonPath} not found`);
    process.exit(1);
  }

  const data = JSON.parse(fs.readFileSync(jsonPath, "utf-8"));

  const doc = new Document({
    styles: {
      default: {
        document: { run: { font: "Arial", size: 22 } },
      },
      paragraphStyles: [
        {
          id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal",
          quickFormat: true,
          run: { size: 32, bold: true, font: "Arial", color: NAVY },
          paragraph: { spacing: { before: 240, after: 160 }, outlineLevel: 0 },
        },
        {
          id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal",
          quickFormat: true,
          run: { size: 26, bold: true, font: "Arial", color: ACCENT },
          paragraph: { spacing: { before: 200, after: 120 }, outlineLevel: 1 },
        },
        {
          id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal",
          quickFormat: true,
          run: { size: 24, bold: true, font: "Arial", color: NAVY },
          paragraph: { spacing: { before: 160, after: 80 }, outlineLevel: 2 },
        },
      ],
    },
    numbering: {
      config: [
        {
          reference: "report_bullets",
          levels: [{
            level: 0, format: LevelFormat.BULLET, text: "\u2022",
            alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 720, hanging: 360 } } },
          }],
        },
        {
          reference: "report_numbers",
          levels: [{
            level: 0, format: LevelFormat.DECIMAL, text: "%1.",
            alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 720, hanging: 360 } } },
          }],
        },
      ],
    },
    sections: [
      buildCoverSection(data),
      buildContentSection(data),
    ],
  });

  const buffer = await Packer.toBuffer(doc);
  fs.writeFileSync(outputPath, buffer);

  const sectionCount = (data.sections || []).length;
  const hasToc = data.toc !== false;
  console.log(`Report generated: ${outputPath}`);
  console.log(`  Title    : ${data.title || "(none)"}`);
  console.log(`  Sections : ${sectionCount}`);
  console.log(`  TOC      : ${hasToc ? "yes" : "no"}`);
  console.log(`  Size     : ${buffer.length} bytes`);
}

main().catch(err => {
  console.error("Error:", err.message);
  process.exit(1);
});
