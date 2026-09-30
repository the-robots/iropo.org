import type { APIRoute, GetStaticPaths } from "astro";
import { agenciesFor, states } from "../../../lib/data";

export const getStaticPaths = (() => states.map((s) => ({ params: { state: s.abbr } }))) satisfies GetStaticPaths;

export const GET: APIRoute = ({ params }) =>
  new Response(JSON.stringify(agenciesFor(params.state!)), {
    headers: { "Content-Type": "application/json; charset=utf-8" },
  });
