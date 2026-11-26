// Entry program for news-image-20261126 (Node 22, standard library only).
//
// The entry image is the entry.png file shipped beside this program. This
// program copies it, byte for byte, to the grader's output directory, so
// both runs of the program write identical bytes.
//
// The output directory is /output in the grader. Outside the grader,
// MAKEFUN_OUTPUT_DIR stands in for it:
//   mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts

import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const source = join(here, "entry.png");
const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? "/output";
const target = join(outDir, "entry.png");

if (!existsSync(source)) {
  console.error(`entry image missing: ${source}`);
  process.exit(1);
}

mkdirSync(outDir, { recursive: true });
const bytes = readFileSync(source);
writeFileSync(target, bytes);
console.log(`wrote ${target} (${bytes.length} bytes)`);
