# raicita.github.io

The public website for **Raicita** (根芽): the home page and the legal pages, in English and Simplified Chinese.

It is a plain static site: HTML, one CSS file and self-hosted fonts. There is no build step, no JavaScript, no
cookies, no analytics and no request to any other site, so the cookie and privacy statements on it stay true.
Keep it that way: don't add trackers, embeds, CDN links or Google Fonts.

> **Legal pages are drafts.** Everything under `terms/`, `privacy/`, `guidelines/`, `coins/`, `safety/`,
> `cookies/`, `accessibility/` and `imprint/` (and the `zh/` copies) was written from the product's code and docs
> and still needs a lawyer's sign-off. Each file starts with an HTML comment saying so. Before going live, fill in
> every placeholder (search for `[` inside `class="ph"`):
>
> - `[Registered address – to be added]`
> - `[Company number – to be added]`
> - `[VAT number – to be added]`
> - `[Director name(s) – to be added]`
> - `[ICO registration number – to be added]`
> - `[EU representative name and address – to be added]`
>
> The English text is authoritative; each Chinese legal page says so in one line. Change both languages together.

## Layout

| Path | What |
| --- | --- |
| `index.html`, `zh/index.html` | Home page (English at `/`, Chinese at `/zh/`): highlights, features, characters, packages and prices, safety, FAQ |
| `terms/` `privacy/` `guidelines/` `coins/` `safety/` `cookies/` `accessibility/` `imprint/` | Legal pages, one `index.html` each; the same set under `zh/` |
| `404.html` | Not-found page (GitHub Pages serves it for any missing path; it uses root-absolute links) |
| `assets/css/site.css` | The only stylesheet. Colours, fonts and shapes follow the app (`apps/web/app/globals.css`); light and dark follow the visitor's system setting |
| `assets/fonts/` | Fraunces 600/700 and Figtree (variable), Latin subset, with their OFL licences. Chinese text uses system fonts |
| `assets/img/` | App icon (`icon.svg`, from `apps/web/app/icon.svg`), `apple-touch-icon.png`, Open Graph image `og.png` |
| `assets/screens/` | App screenshots (mock data only), WebP at 540 px wide |
| `favicon.svg`, `favicon.ico` | Browser icons |
| `robots.txt`, `sitemap.xml` | Search engines (`sitemap.xml` is generated, see below) |
| `.nojekyll` | Tells GitHub Pages to serve the files as they are |
| `tools/` | Helper scripts, not part of the site (see below) |

## Editing

Each page has its own content inside `<main>`. Edit it directly. The parts every page shares sit between marker
comments and are rewritten by `tools/layout.py`:

| Marker | Contents |
| --- | --- |
| `<!-- @head -->` | title, description, canonical and `hreflang` links, Open Graph and Twitter tags, icons, CSS |
| `<!-- @header -->` | skip link, logo, navigation, language switch, "Open the app" button |
| `<!-- @footer -->` | legal links, support email, company line |
| `<!-- @toc -->` | the contents list of a legal page, built from its `<h2 id="...">` headings |

So:

- **To change text on a page**, edit that page's `<main>`, and the same page in the other language.
- **To change a title, description, a nav or footer link, or add a page**, edit `tools/layout.py` (`PAGES`, `T`,
  `LEGAL`), then run it. Anything you type between the markers by hand is overwritten.
- **Legal pages**: give every section an `<h2 id="...">`; the contents list updates itself. Update the
  "Last updated" line (and `UPDATED` in `tools/layout.py` for the sitemap). When the app needs users to accept new
  terms, publish a new terms version in the admin as well.

After any change:

```bash
python3 tools/layout.py     # refresh shared parts and sitemap.xml
python3 tools/check.py      # HTML validity, headings, alt text, ids, internal links and anchors, no external loads
```

`check.py` uses only the standard library, plus `html5lib` (`pip install html5lib`) for strict HTML parsing.
It exits non-zero on any problem.

### Facts that come from the app

The site repeats a few things from the app repository. Keep them in step when the app changes:

- Name, Chinese name, domain, support email, company: `packages/shared/src/brand.ts` (copied into `BRAND` in `tools/layout.py`).
- Official characters on the home page: `OFFICIAL_CHARACTERS` in `packages/shared/src/catalog.ts`.
- Helplines on the AI & Safety page: `packages/shared/src/helplines.ts`.
- AI providers in the Privacy Policy: the providers the app's consent screen lists (`GET /v1/ai/providers`).
- Coin validity and reminder (6 months, reminder after 5): `DEFAULT_COIN_EXPIRY` in `packages/shared/src/coins.ts`.
- Packages and prices on the home page: `COIN_PACKS` and `SUBSCRIPTION_PLANS` in `packages/shared/src/catalog.ts` (GBP;
  EUR and USD are the defaults from `packages/shared/src/currency.ts`), coin costs from `COIN_ACTIONS` in
  `packages/shared/src/content.ts`. These are the built-in defaults; if prices are changed in the admin (计费配置),
  update the "Packages and prices" section in both languages.
- Inactive-account deletion (24 months + 30 days): `packages/shared/src/retention.ts`.
- Accessibility statement: `apps/web/app/accessibility/page.tsx`.

### Links to the app

The web app is linked as `https://app.raicita.app` and the Android download as `https://app.raicita.app/download`
(the app's own download page, which always points at the latest signed APK). The web domain isn't confirmed yet
(`deploy/env.example` only has a placeholder). If it changes, update `APP_URL` in `tools/layout.py`, run it, and
search the pages for `app.raicita.app`.

## Domain

The site is served at `https://raicita.thymoria.com` (the `CNAME` file). Canonical, `hreflang`, Open Graph,
`robots.txt` and the sitemap use that address (`SITE` in `tools/layout.py` and `tools/check.py`). Page-to-page links
are relative, so they work on any domain. To move it: change `CNAME`, both `SITE` values and `robots.txt`, then run
`tools/layout.py`.

## Tools

`tools/` is published along with the site (GitHub Pages serves the whole branch) but nothing links to it and
`robots.txt` keeps it out of search engines. Nothing in it runs in the browser.

| Script | What |
| --- | --- |
| `tools/layout.py` | Rewrites shared parts of every page and `sitemap.xml` |
| `tools/check.py` | Validity, accessibility basics and link checker |
| `tools/screenshot.cjs` | Review screenshots with Playwright: serve the site (`python3 -m http.server 8765`), then `NODE_PATH=$(npm root -g) node tools/screenshot.cjs http://localhost:8765 ./shots dark` |
| `tools/og.html`, `tools/render_images.cjs` | Source of `assets/img/og.png` and the PNG icons. `NODE_PATH=$(npm root -g) node tools/render_images.cjs`, then build `favicon.ico` from the 16/32/48 px PNGs (for example with Pillow) |

## Screenshots

Screenshots in `assets/screens/` come from the app's test runs with mock data and no personal data. If you replace
them, use mock accounts only, export at 540 px wide as WebP, and write alt text that describes what the screen shows.
