import type { APIRoute } from "astro";
import { LATEST_TABLE_YEAR, agenciesFor, states } from "../../lib/data";
import { agencyAnchor, agencyTotal } from "../../lib/stats";

/** Compact nationwide index used by the client-side agency search on /agencies/. */
export const GET: APIRoute = () => {
  const rows = states.flatMap((state) =>
    agenciesFor(state.abbr).agencies.map((a) => [
      a.ori ?? "",
      a.name,
      state.abbr,
      a.county ?? "",
      a.type,
      a.animal_cruelty?.[String(LATEST_TABLE_YEAR)] ?? null,
      a.animal_cruelty ? agencyTotal(a) : null,
      a.ori ? 0 : agencyAnchor(a),
    ]),
  );
  const payload = {
    year: LATEST_TABLE_YEAR,
    fields: ["ori", "name", "state", "county", "type", "latest", "total", "anchor"],
    states: Object.fromEntries(states.map((s) => [s.abbr, [s.name, s.slug]])),
    rows,
  };
  return new Response(JSON.stringify(payload), { headers: { "Content-Type": "application/json; charset=utf-8" } });
};
