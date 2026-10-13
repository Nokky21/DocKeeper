// Comprueba que el port de la demo (src/demo/engine.ts) da los veredictos y huellas de
// scenarios.json, los mismos que tests/test_demo.py exige al motor real en Python.
// Uso: node scripts/check-demo.ts (Node 22.18+ ejecuta TypeScript sin compilar).

import data from "../src/demo/scenarios.json" with { type: "json" };
import { accept, relocate, seal, toLines, verify, type Entry } from "../src/demo/engine.ts";

const fallos: string[] = [];
const original = toLines(data.original.join("\n") + "\n");

async function check(lines: string[], entries: Entry[]) {
  const results = await Promise.all(entries.map((e) => verify(lines, e)));
  return { results, verdicts: Object.fromEntries(results.map((r) => [r.anchor, r.verdict])) };
}

function compare(id: string, step: string, got: Record<string, string>, want: Record<string, string>) {
  if (JSON.stringify(got) !== JSON.stringify(want)) fallos.push(`${id} (${step}): ${JSON.stringify(got)} ≠ ${JSON.stringify(want)}`);
}

for (const escenario of data.scenarios) {
  let entries = (await Promise.all(data.claims.map((c) => seal(original, c.anchor)))) as Entry[];
  compare(escenario.id, "seal", Object.fromEntries(entries.map((e) => [e.anchor, e.hash])), data.sealed);
  const lines = toLines((escenario.code ?? data.original).join("\n") + "\n");
  const { results, verdicts } = await check(lines, entries);
  compare(escenario.id, "check", verdicts, escenario.expected);
  if ("afterFix" in escenario && escenario.afterFix) {
    entries = entries.map((e, i) => relocate(e, results[i]));
    compare(escenario.id, "fix", (await check(lines, entries)).verdicts, escenario.afterFix);
  }
  if ("afterAccept" in escenario && escenario.afterAccept) {
    entries = await Promise.all(entries.map((e, i) => (results[i].verdict === "CHANGED" ? accept(lines, e) : e)));
    compare(escenario.id, "fix --aceptar", (await check(lines, entries)).verdicts, escenario.afterAccept);
  }
}

if (fallos.length) {
  console.error("La demo no coincide con el motor:\n" + fallos.join("\n"));
  process.exit(1);
}
console.log(`demo OK: ${data.scenarios.length} escenarios coinciden con el motor`);
