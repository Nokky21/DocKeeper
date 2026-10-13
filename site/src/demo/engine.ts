// Port en TypeScript del núcleo de DocKeeper para la demo de la web (solo ficheros Python).
//
// La referencia es el motor en Python (dockeeper/huellas.py, bloques.py, motor.py). Este port
// es deliberadamente pequeño: no limpia cadenas multilínea ni reconoce otros lenguajes.
// tests/test_demo.py (motor real) y scripts/check-demo.ts (este port) comprueban que ambos dan
// los mismos veredictos y huellas en los escenarios de scenarios.json.

export type Verdict = "OK" | "MOVED" | "CHANGED";
export type Kind = "definicion" | "ventana";

export interface Block { kind: Kind; start: number; end: number; name?: string; hash: string; n: number }
export interface Entry { anchor: string; symbol?: string; line?: number; kind: Kind; start: number; end: number; hash: string; n: number }
export interface Result { anchor: string; verdict: Verdict; detail: string; block?: Block; next?: Partial<Entry> }

const WINDOW = 3;
const DEF = /^\s*(?:async\s+)?(?:def|class)\s+([A-Za-z_]\w*)/;
const encoder = new TextEncoder();

/** Colapsa espacios y quita los extremos (como `" ".join(linea.split())`). */
export const normalizeLine = (line: string): string => line.split(/\s+/).filter(Boolean).join(" ");

export async function fingerprint(lines: string[]): Promise<{ hash: string; n: number }> {
  const normalized = lines.map(normalizeLine).filter(Boolean);
  const digest = await crypto.subtle.digest("SHA-256", encoder.encode(normalized.join("\n")));
  const hex = Array.from(new Uint8Array(digest), (b) => b.toString(16).padStart(2, "0")).join("");
  return { hash: hex.slice(0, 16), n: normalized.length };
}

/** Líneas de un fichero como las lee el motor: sin la línea vacía final. */
export function toLines(text: string): string[] {
  const lines = text.replace(/\r\n?/g, "\n").split("\n");
  if (lines.length && lines[lines.length - 1] === "") lines.pop();
  return lines;
}

const indentOf = (s: string): number => {
  const expanded = s.replace(/\t/g, "        ");
  return expanded.length - expanded.trimStart().length;
};
// Un comentario de línea completa no cuenta como código (el motor lo blanquea).
const code = (s: string): string => (s.trim().startsWith("#") ? "" : s);

interface Definition { name: string; header: number; start: number; end: number }

function extent(lines: string[], i0: number): number {
  const indent = indentOf(lines[i0]);
  let depth = 0;
  let i = i0;
  for (; i < lines.length; i++) {
    for (const c of code(lines[i])) {
      if ("([{".includes(c)) depth++;
      else if (")]}".includes(c)) depth--;
    }
    if (depth <= 0) break;
  }
  let end = Math.min(i, lines.length - 1);
  for (let j = end + 1; j < lines.length; j++) {
    const t = code(lines[j]);
    if (!t.trim()) continue;
    if (indentOf(t) <= indent) break;
    end = j;
  }
  return end;
}

export function definitions(lines: string[]): Definition[] {
  const defs: Definition[] = [];
  lines.forEach((line, i) => {
    const m = DEF.exec(code(line));
    if (!m) return;
    let start = i;
    while (start > 0 && lines[start - 1].trim().startsWith("@")) start--;
    defs.push({ name: m[1], header: i + 1, start: start + 1, end: extent(lines, i) + 1 });
  });
  return defs;
}

async function block(lines: string[], kind: Kind, start: number, end: number, name?: string): Promise<Block> {
  const { hash, n } = await fingerprint(lines.slice(start - 1, end));
  return { kind, start, end, name, hash, n };
}

/** Bloque de un ancla por línea: la definición más interior que la contiene, o una ventana recortada. */
export async function blockAt(lines: string[], line: number): Promise<Block> {
  if (line < 1 || line > lines.length) return block(lines, "ventana", line, line - 1);
  const inside = definitions(lines).filter((d) => d.start <= line && line <= d.end);
  if (inside.length) {
    const d = inside.reduce((a, b) => (b.end - b.start < a.end - a.start || (b.end - b.start === a.end - a.start && b.start > a.start) ? b : a));
    return block(lines, "definicion", d.start, d.end, d.name);
  }
  let a = Math.max(1, line - WINDOW);
  let b = Math.min(lines.length, line + WINDOW);
  while (a <= b && !lines[a - 1].trim()) a++;
  while (b >= a && !lines[b - 1].trim()) b--;
  return block(lines, "ventana", a, a <= b ? b : a - 1);
}

export async function blocksForSymbol(lines: string[], symbol: string): Promise<Block[]> {
  const found = definitions(lines).filter((d) => d.name === symbol);
  return Promise.all(found.map((d) => block(lines, "definicion", d.start, d.end, d.name)));
}

/** Tramos donde `n` líneas con contenido seguidas tienen la huella buscada. */
async function search(lines: string[], hash: string, n: number): Promise<Array<[number, number]>> {
  if (n <= 0) return [];
  const idx = lines.map((l, i) => [i + 1, normalizeLine(l)] as const).filter(([, t]) => t);
  const spans: Array<[number, number]> = [];
  for (let i = 0; i + n <= idx.length; i++) {
    const window = idx.slice(i, i + n);
    if ((await fingerprint(window.map(([, t]) => t))).hash === hash) spans.push([window[0][0], window[n - 1][0]]);
  }
  return spans;
}

function parse(anchor: string): { symbol?: string; line?: number } {
  const hashAt = anchor.indexOf("#");
  if (hashAt >= 0) return { symbol: anchor.slice(hashAt + 1) };
  return { line: Number(anchor.slice(anchor.lastIndexOf(":") + 1)) };
}

/** `dockeeper scan` para un ancla: calcula su bloque y lo sella. */
export async function seal(lines: string[], anchor: string): Promise<Entry | null> {
  const { symbol, line } = parse(anchor);
  const b = symbol ? (await blocksForSymbol(lines, symbol))[0] : await blockAt(lines, line!);
  if (!b || b.n === 0) return null;
  return { anchor, symbol, line, kind: b.kind, start: b.start, end: b.end, hash: b.hash, n: b.n };
}

/** `dockeeper check` para un ancla sellada. */
export async function verify(lines: string[], e: Entry): Promise<Result> {
  if (e.symbol) {
    const candidates = await blocksForSymbol(lines, e.symbol);
    for (const b of candidates) {
      if (b.hash !== e.hash) continue;
      if (b.start === e.start && b.end === e.end) return { anchor: e.anchor, verdict: "OK", detail: "Same block, same place.", block: b };
      return { anchor: e.anchor, verdict: "MOVED", detail: `${e.symbol} moved from lines ${e.start}–${e.end} to ${b.start}–${b.end}.`, block: b, next: { start: b.start, end: b.end } };
    }
    if (!candidates.length) return { anchor: e.anchor, verdict: "CHANGED", detail: `${e.symbol} no longer exists in the file.` };
    const b = candidates[0];
    return { anchor: e.anchor, verdict: "CHANGED", detail: `The content of ${e.symbol} changed (lines ${b.start}–${b.end}).`, block: b };
  }
  const b = e.kind === "ventana" ? await block(lines, "ventana", e.start, Math.min(e.end, lines.length)) : await blockAt(lines, e.line!);
  if (b.hash === e.hash && b.n === e.n) {
    if (b.start === e.start && b.end === e.end) return { anchor: e.anchor, verdict: "OK", detail: "Same block, same place.", block: b };
    return { anchor: e.anchor, verdict: "MOVED", detail: `The block moved from lines ${e.start}–${e.end} to ${b.start}–${b.end}.`, block: b, next: { start: b.start, end: b.end, line: e.line! + b.start - e.start } };
  }
  const spans = await search(lines, e.hash, e.n);
  if (spans.length) {
    const [start, end] = spans.reduce((a, s) => (Math.abs(s[0] - e.start) < Math.abs(a[0] - e.start) ? s : a));
    const line = Math.min(Math.max(start + (e.line! - e.start), start), end);
    return { anchor: e.anchor, verdict: "MOVED", detail: `The block moved from lines ${e.start}–${e.end} to ${start}–${end}.`, block: { kind: e.kind, start, end, hash: e.hash, n: e.n }, next: { start, end, line } };
  }
  return { anchor: e.anchor, verdict: "CHANGED", detail: `The block at lines ${e.start}–${e.end} changed.`, block: b.n ? b : undefined };
}

/** `dockeeper fix`: aplica las posiciones nuevas de los MOVED. */
export const relocate = (e: Entry, r: Result): Entry => (r.verdict === "MOVED" && r.next ? { ...e, ...r.next } : e);

/** `dockeeper fix --aceptar`: resella un CHANGED revisado (si su símbolo o su línea siguen existiendo). */
export async function accept(lines: string[], e: Entry): Promise<Entry> {
  const b = e.symbol ? (await blocksForSymbol(lines, e.symbol))[0] : await blockAt(lines, e.line!);
  if (!b || b.n === 0) return e;
  return { ...e, kind: b.kind, start: b.start, end: b.end, hash: b.hash, n: b.n };
}
