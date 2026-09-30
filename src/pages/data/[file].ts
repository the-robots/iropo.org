import type { APIRoute, GetStaticPaths } from "astro";
import fs from "node:fs";
import path from "node:path";
import { DATA_DIR, openDataFiles, readOpenData } from "../../lib/data";

/** Published JSON datasets (in addition to every CSV in data/processed/open-data). */
const JSON_FILES = ["national.json", "states.json", "sources.json", "official-registries.json", "meta.json"];

export const getStaticPaths = (() => [
  ...openDataFiles().map((f) => ({ params: { file: f.name } })),
  ...JSON_FILES.map((name) => ({ params: { file: name } })),
]) satisfies GetStaticPaths;

export const GET: APIRoute = ({ params }) => {
  const file = params.file!;
  if (file.endsWith(".csv")) {
    return new Response(readOpenData(file), { headers: { "Content-Type": "text/csv; charset=utf-8" } });
  }
  const body = fs.readFileSync(path.join(DATA_DIR, file), "utf8");
  return new Response(body, { headers: { "Content-Type": "application/json; charset=utf-8" } });
};
