export const SITE = {
  name: "IROPO",
  longName: "International Registry of Pet Offenders",
  url: "https://iropo.org",
  description:
    "IROPO turns official crime data and public records into one verifiable source of truth on animal cruelty in the United States and beyond.",
  repo: "https://github.com/the-robots/iropo.org",
};

export const REPO_FILE = (path: string) => `${SITE.repo}/blob/main/${encodeURI(path)}`;
export const REPO_TREE = (path: string) => `${SITE.repo}/tree/main/${encodeURI(path)}`;
/** Link to one of the issue forms in .github/ISSUE_TEMPLATE. */
export const ISSUE_FORM = (form: "data-source" | "correction" | "volunteer") =>
  `${SITE.repo}/issues/new?template=${form}.yml`;
export const NEW_ISSUE = (title = "") =>
  `${SITE.repo}/issues/new${title ? `?${new URLSearchParams({ title })}` : ""}`;

export const NAV = [
  { href: "/data/", label: "Data" },
  { href: "/states/", label: "States" },
  { href: "/agencies/", label: "Agencies" },
  { href: "/registry/", label: "Registry" },
  { href: "/sources/", label: "Sources" },
  { href: "/about/", label: "About" },
  { href: "/contact/", label: "Contact" },
];
