# DNS Setup for iropo.org

This document explains the correct DNS configuration required for
`iropo.org` to resolve to the GitHub Pages deployment and describes
the misconfiguration that currently prevents the domain from resolving.

---

## Current problem

The domain is registered with Dynadot and is using two custom (vanity)
nameservers:

| Nameserver | Glue-record IPs |
|---|---|
| `creep.iropo.org` | 185.199.108.153, 185.199.109.153 |
| `conrad.iropo.org` | 185.199.110.153, 185.199.111.153 |

Those IP addresses are GitHub Pages **web-server** addresses. GitHub
Pages servers only speak HTTP/HTTPS — they do **not** run DNS server
software on port 53. When any DNS resolver asks
`creep.iropo.org` or `conrad.iropo.org` for records about `iropo.org`,
it reaches a GitHub Pages web server that never responds to DNS queries,
so the lookup fails with `SERVFAIL` and the domain is unreachable.

---

## How to fix it

The fix requires two changes in the Dynadot control panel.

### Step 1 — Switch to Dynadot's default nameservers

1. Log in to [Dynadot](https://www.dynadot.com).
2. Go to **Manage → Domains → iropo.org → Name Servers**.
3. Remove `creep.iropo.org` and `conrad.iropo.org`.
4. Set the nameservers to Dynadot's default servers, for example:

   ```
   ns1.dynadot.com
   ns2.dynadot.com
   ```

   (The exact hostnames are shown in the Dynadot panel under "Default
   Name Servers".)

### Step 2 — Add DNS records for GitHub Pages

Once the nameservers are switched to Dynadot (or any standard DNS
provider), add the following records in the DNS zone for `iropo.org`:

**A records** (apex / root domain):

| Type | Host | Value |
|------|------|-------|
| A | @ | 185.199.108.153 |
| A | @ | 185.199.109.153 |
| A | @ | 185.199.110.153 |
| A | @ | 185.199.111.153 |

**CNAME record** (www subdomain):

| Type | Host | Value |
|------|------|-------|
| CNAME | www | the-robots.github.io |

These are the [official GitHub Pages IP addresses](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site).

### Step 3 — Verify

DNS propagation can take up to 24–48 hours. To check progress:

```bash
# Should return the four GitHub Pages A records
nslookup iropo.org

# Should return the CNAME pointing to the-robots.github.io
nslookup www.iropo.org
```

GitHub also provides a DNS check in **Settings → Pages** for the
repository. Once the records are visible, GitHub will provision an
HTTPS certificate automatically.

---

## Why the CNAME file matters

The `CNAME` file at the root of this repository contains the custom
domain (`iropo.org`). GitHub Pages reads this file during each build to
configure the custom-domain mapping. Without it, the Pages deployment
would only be reachable at `the-robots.github.io/iropo.org`.

The file must not be deleted, and its contents must match the domain
configured in **Settings → Pages → Custom domain**.

---

## References

- [GitHub Docs — Managing a custom domain for GitHub Pages](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site)
- [GitHub Docs — Troubleshooting custom domains](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/troubleshooting-custom-domains-and-github-pages)
- [GitHub Pages IP addresses](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site#configuring-an-apex-domain)
