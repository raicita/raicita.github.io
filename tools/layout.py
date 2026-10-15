#!/usr/bin/env python3
"""Refreshes the shared parts of every page: <head>, header, footer and legal tables of contents.

Each page keeps its own content inside <main>. The shared parts sit between marker comments and are rewritten
from the templates below, so a change here (a new footer link, a new page) reaches every page in one run:

    <!-- @head --> ... <!-- /@head -->      title, description, canonical, hreflang, Open Graph, icons, CSS
    <!-- @header --> ... <!-- /@header -->  skip link, logo, navigation, language switch
    <!-- @footer --> ... <!-- /@footer -->  legal links, contact, company
    <!-- @toc --> ... <!-- /@toc -->        contents list built from the page's <h2 id="..."> headings

Also writes sitemap.xml. Standard library only:  python3 tools/layout.py
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Where the site is served. Change this (and add a CNAME file) once the domain is decided.
SITE = "https://raicita.github.io"
# From packages/shared/src/brand.ts (BRAND). Keep in step with the app.
BRAND = {
    "name": "Raicita",
    "nameZh": "根芽",
    "domain": "raicita.app",
    "supportEmail": "support@raicita.app",
    "company": "Raicita Ltd",
    "country": "United Kingdom",
}
# The web app. Unconfirmed: deploy/env.example only has a placeholder WEB_DOMAIN.
APP_URL = "https://app.raicita.app"
UPDATED = "2026-10-15"

LANGS = ("en", "zh")

# slug: (title en, title zh, description en, description zh)
PAGES: dict[str, tuple[str, str, str, str]] = {
    "": (
        "Raicita · Someone who gets you",
        "根芽 Raicita · 懂你的人，一直都在",
        "Raicita is an AI companion app for adults (18+). Chat, send voice messages and call characters who remember you. Every character is AI, and the app always says so.",
        "根芽（Raicita）是面向成年人（18 岁以上）的 AI 陪伴应用。和记得你的角色聊天、发语音、打电话。所有角色都是 AI，应用会一直明确告诉你。",
    ),
    "terms": (
        "Terms of Service · Raicita",
        "用户协议 · 根芽",
        "The terms for using Raicita: 18+ only, AI characters, coins and subscriptions, your content, and your rights.",
        "使用根芽的条款：仅限 18 岁以上、AI 角色、金币与订阅、你的内容和你的权利。",
    ),
    "privacy": (
        "Privacy Policy · Raicita",
        "隐私政策 · 根芽",
        "What Raicita collects, why, who processes it (including AI providers), how long we keep it and how to use your rights.",
        "根芽收集哪些数据、为什么收集、由谁处理（包括 AI 服务商）、保存多久，以及如何行使你的权利。",
    ),
    "guidelines": (
        "Community Guidelines · Raicita",
        "社区准则 · 根芽",
        "What is and isn't allowed in chats, user-created characters and comments on Raicita, how to report, and what happens next.",
        "根芽聊天、自建角色和评论中允许与不允许的内容、如何举报，以及之后会发生什么。",
    ),
    "coins": (
        "Coins & Payments · Raicita",
        "金币与付款 · 根芽",
        "How coins, coin packs and monthly coin subscriptions work on Raicita: prices, payment methods, validity, receipts and refunds.",
        "根芽的金币、金币包和包月金币订阅如何运作：价格、付款方式、有效期、收据和退款。",
    ),
    "safety": (
        "AI & Safety · Raicita",
        "AI 与安全 · 根芽",
        "Raicita characters are AI. How we remind you, how safety checks and crisis support work, and how to report a problem.",
        "根芽的角色都是 AI。我们如何提醒你、安全检测和危机支持如何运作，以及如何举报问题。",
    ),
    "cookies": (
        "Cookie Notice · Raicita",
        "Cookie 说明 · 根芽",
        "Raicita uses no tracking cookies. Only essential storage for signing in and remembering your settings.",
        "根芽不使用任何追踪 Cookie，只使用登录和记住设置所必需的本地存储。",
    ),
    "accessibility": (
        "Accessibility · Raicita",
        "无障碍说明 · 根芽",
        "How accessible Raicita is today, the problems we know about, and how to tell us what doesn't work for you.",
        "根芽目前的无障碍情况、已知问题，以及如何告诉我们哪里不好用。",
    ),
    "imprint": (
        "Imprint & Contact · Raicita",
        "公司信息与联系方式 · 根芽",
        "Company details for Raicita Ltd and how to contact us.",
        "Raicita Ltd 的公司信息和联系方式。",
    ),
}
LEGAL = ["terms", "privacy", "guidelines", "coins", "safety", "cookies", "accessibility", "imprint"]

T = {
    "en": {
        "skip": "Skip to content",
        "home": "Home",
        "features": "Features",
        "coins": "Coins",
        "safety": "Safety",
        "privacy": "Privacy",
        "open_app": "Open the app",
        "menu": "Menu",
        "lang_label": "中文",
        "lang_aria": "阅读中文版",
        "tagline": "Someone who gets you",
        "legal": "Legal",
        "help": "Help & contact",
        "app": "Get the app",
        "web_app": "Web app",
        "android": "Android app",
        "support": "Support",
        "foot_about": "An AI companion app for adults. Every character is AI, not a person, and is not a substitute for professional help.",
        "adults": "For adults 18+ only.",
        "crisis": 'In crisis? In the UK call Samaritans on <a href="tel:116123">116 123</a>. In the US call or text <a href="tel:988">988</a>. Elsewhere, see <a href="https://findahelpline.com">findahelpline.com</a>.',
        "toc": "Contents",
        "nav_labels": {
            "terms": "Terms of Service",
            "privacy": "Privacy Policy",
            "guidelines": "Community Guidelines",
            "coins": "Coins & Payments",
            "safety": "AI & Safety",
            "cookies": "Cookie Notice",
            "accessibility": "Accessibility",
            "imprint": "Imprint & Contact",
        },
    },
    "zh": {
        "skip": "跳到正文",
        "home": "首页",
        "features": "功能",
        "coins": "金币",
        "safety": "安全",
        "privacy": "隐私",
        "open_app": "打开应用",
        "menu": "菜单",
        "lang_label": "English",
        "lang_aria": "Read in English",
        "tagline": "懂你的人，一直都在",
        "legal": "法律信息",
        "help": "帮助与联系",
        "app": "获取应用",
        "web_app": "网页版",
        "android": "安卓 App",
        "support": "客服邮箱",
        "foot_about": "面向成年人的 AI 陪伴应用。所有角色都是 AI，不是真人，也不能替代专业帮助。",
        "adults": "仅限 18 岁以上成年人使用。",
        "crisis": '需要紧急帮助？英国请拨打 Samaritans <a href="tel:116123">116 123</a>；美国请拨打或发短信到 <a href="tel:988">988</a>；其他地区请访问 <a href="https://findahelpline.com">findahelpline.com</a>。',
        "toc": "目录",
        "nav_labels": {
            "terms": "用户协议",
            "privacy": "隐私政策",
            "guidelines": "社区准则",
            "coins": "金币与付款",
            "safety": "AI 与安全",
            "cookies": "Cookie 说明",
            "accessibility": "无障碍说明",
            "imprint": "公司信息与联系",
        },
    },
}


def rel_path(slug: str, lang: str) -> str:
    """Site path of a page, e.g. /terms/ or /zh/terms/."""
    base = "/zh/" if lang == "zh" else "/"
    return base + (f"{slug}/" if slug else "")


def file_of(slug: str, lang: str) -> Path:
    parts = (["zh"] if lang == "zh" else []) + ([slug] if slug else [])
    return ROOT.joinpath(*parts, "index.html")


def depth_prefix(slug: str, lang: str) -> str:
    """Relative prefix from a page back to the site root, so the site also works from a sub-path or a file:// copy."""
    depth = (1 if lang == "zh" else 0) + (1 if slug else 0)
    return "../" * depth or "./"


def href(target_slug: str, lang: str, here_slug: str, here_lang: str, anchor: str = "") -> str:
    """Relative link from one page to another (same language stays inside its folder)."""
    if lang == here_lang:
        up = "../" if here_slug else ""
        path = f"{target_slug}/" if target_slug else ""
        return (up + path or "./") + anchor
    root = depth_prefix(here_slug, here_lang)
    path = ("zh/" if lang == "zh" else "") + (f"{target_slug}/" if target_slug else "")
    return (root + path if path else root) + anchor


ICON_MENU = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg>'
ICON_GLOBE = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/></svg>'


def head(slug: str, lang: str) -> str:
    te, tz, de, dz = PAGES[slug]
    title, desc = (te, de) if lang == "en" else (tz, dz)
    root = depth_prefix(slug, lang)
    url = SITE + rel_path(slug, lang)
    alt_en = SITE + rel_path(slug, "en")
    alt_zh = SITE + rel_path(slug, "zh")
    og_locale = "en_GB" if lang == "en" else "zh_CN"
    og_alt = "zh_CN" if lang == "en" else "en_GB"
    e = html.escape
    return f"""
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta name="theme-color" content="#fbf6f2" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#121016" media="(prefers-color-scheme: dark)">
<meta name="referrer" content="strict-origin-when-cross-origin">
<link rel="canonical" href="{url}">
<link rel="alternate" hreflang="en" href="{alt_en}">
<link rel="alternate" hreflang="zh-Hans" href="{alt_zh}">
<link rel="alternate" hreflang="x-default" href="{alt_en}">
<link rel="icon" href="{root}favicon.svg" type="image/svg+xml">
<link rel="icon" href="{root}favicon.ico" sizes="32x32">
<link rel="apple-touch-icon" href="{root}assets/img/apple-touch-icon.png">
<link rel="preload" href="{root}assets/fonts/figtree-latin-wght-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{root}assets/css/site.css">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{BRAND['name']}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:locale" content="{og_locale}">
<meta property="og:locale:alternate" content="{og_alt}">
<meta property="og:image" content="{SITE}/assets/img/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{BRAND['name']}: AI companions for adults. Every character is AI.">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(title)}">
<meta name="twitter:description" content="{e(desc)}">
<meta name="twitter:image" content="{SITE}/assets/img/og.png">
"""


def header(slug: str, lang: str) -> str:
    t = T[lang]
    root = depth_prefix(slug, lang)
    other = "zh" if lang == "en" else "en"
    home = href("", lang, slug, lang)
    cur = lambda s: ' aria-current="page"' if s == slug else ""  # noqa: E731
    links = [
        (href("", lang, slug, lang, "#features"), t["features"], None),
        (href("coins", lang, slug, lang), t["coins"], "coins"),
        (href("safety", lang, slug, lang), t["safety"], "safety"),
        (href("privacy", lang, slug, lang), t["privacy"], "privacy"),
    ]
    nav = "\n    ".join(f'<a href="{h}"{cur(s)}>{x}</a>' for h, x, s in links)
    menu = "\n        ".join(f'<a href="{h}">{x}</a>' for h, x, _ in links)
    other_lang_attr = "zh-Hans" if other == "zh" else "en"
    return f"""
<a class="skip" href="#main">{t['skip']}</a>
<header class="site-head">
  <div class="wrap">
    <a class="brand" href="{home}" aria-label="{BRAND['name']} · {t['home']}">
      <img src="{root}assets/img/icon.svg" alt="" width="34" height="34">
      <b>{BRAND['name'] if lang == 'en' else BRAND['nameZh']}</b><small lang="{'zh-Hans' if lang == 'en' else 'en'}">{BRAND['nameZh'] if lang == 'en' else BRAND['name']}</small>
    </a>
    <nav class="nav" aria-label="{t['menu']}">
    {nav}
    </nav>
    <div class="head-actions">
      <a class="lang" href="{href(slug, other, slug, lang)}" hreflang="{other_lang_attr}" lang="{other_lang_attr}" aria-label="{t['lang_aria']}">{ICON_GLOBE}{t['lang_label']}</a>
      <a class="btn pri sm" href="{APP_URL}">{t['open_app']}</a>
      <details class="menu">
        <summary aria-label="{t['menu']}">{ICON_MENU}</summary>
        <div class="menu-panel">
        {menu}
        <a href="{APP_URL}">{t['open_app']}</a>
        </div>
      </details>
    </div>
  </div>
</header>
"""


def footer(slug: str, lang: str) -> str:
    t = T[lang]
    root = depth_prefix(slug, lang)
    legal = "\n          ".join(
        f'<li><a href="{href(s, lang, slug, lang)}">{html.escape(t["nav_labels"][s])}</a></li>' for s in LEGAL
    )
    name = BRAND["name"] if lang == "en" else f"{BRAND['nameZh']}（{BRAND['name']}）"
    return f"""
<footer class="site-foot">
  <div class="wrap">
    <div class="foot-grid">
      <div>
        <a class="brand" href="{href('', lang, slug, lang)}"><img src="{root}assets/img/icon.svg" alt="" width="34" height="34"><b>{name}</b></a>
        <p>{t['foot_about']}</p>
        <p><strong>{t['adults']}</strong></p>
        <p>{t['crisis']}</p>
      </div>
      <nav aria-labelledby="foot-legal-{lang}">
        <h2 id="foot-legal-{lang}">{t['legal']}</h2>
        <ul>
          {legal}
        </ul>
      </nav>
      <div>
        <h2>{html.escape(t['help'])}</h2>
        <ul>
          <li>{t['support']}{'：' if lang == 'zh' else ': '}<a href="mailto:{BRAND['supportEmail']}">{BRAND['supportEmail']}</a></li>
          <li><a href="{APP_URL}">{t['web_app']}</a></li>
          <li><a href="{APP_URL}/download">{t['android']}</a></li>
          <li><a href="{href(slug, 'zh' if lang == 'en' else 'en', slug, lang)}" hreflang="{'zh-Hans' if lang == 'en' else 'en'}" lang="{'zh-Hans' if lang == 'en' else 'en'}">{t['lang_label']}</a></li>
        </ul>
      </div>
    </div>
    <div class="foot-base">
      <p>© 2026 {BRAND['company']} · {BRAND['country'] if lang == 'en' else '英国'}</p>
      <p>{BRAND['domain']}</p>
    </div>
  </div>
</footer>
"""


H2 = re.compile(r'<h2 id="([^"]+)"[^>]*>(.*?)</h2>', re.S)
TAGS = re.compile(r"<[^>]+>")


def toc(page_html: str, lang: str) -> str:
    main = page_html.split('<main', 1)[-1].split('</main>', 1)[0]
    items = []
    for hid, inner in H2.findall(main):
        if hid.startswith("toc"):
            continue
        label = TAGS.sub("", inner).strip()
        items.append(f'<li><a href="#{hid}">{label}</a></li>')
    if not items:
        return ""
    lis = "\n    ".join(items)
    return f"""
  <h2 id="toc-title">{T[lang]['toc']}</h2>
  <ol>
    {lis}
  </ol>
"""


def replace_block(text: str, name: str, body: str, path: Path) -> str:
    pat = re.compile(rf"(<!-- @{name} -->)(.*?)(<!-- /@{name} -->)", re.S)
    if not pat.search(text):
        if name in ("head", "header", "footer"):
            sys.exit(f"{path}: missing <!-- @{name} --> markers")
        return text
    return pat.sub(lambda m: m.group(1) + body + m.group(3), text, count=1)


def sitemap() -> str:
    rows = []
    for slug in PAGES:
        for lang in LANGS:
            alts = "".join(
                f'\n    <xhtml:link rel="alternate" hreflang="{"zh-Hans" if l == "zh" else "en"}" href="{SITE}{rel_path(slug, l)}"/>'
                for l in LANGS
            )
            rows.append(
                f"  <url>\n    <loc>{SITE}{rel_path(slug, lang)}</loc>\n    <lastmod>{UPDATED}</lastmod>{alts}\n  </url>"
            )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
        + "\n".join(rows)
        + "\n</urlset>\n"
    )


def main() -> None:
    changed = 0
    for slug in PAGES:
        for lang in LANGS:
            path = file_of(slug, lang)
            if not path.exists():
                print(f"layout: warning: missing page {path.relative_to(ROOT)}", file=sys.stderr)
                continue
            text = path.read_text(encoding="utf-8")
            new = replace_block(text, "head", head(slug, lang), path)
            new = replace_block(new, "header", header(slug, lang), path)
            new = replace_block(new, "footer", footer(slug, lang), path)
            new = replace_block(new, "toc", toc(new, lang), path)
            if new != text:
                path.write_text(new, encoding="utf-8")
                changed += 1
    (ROOT / "sitemap.xml").write_text(sitemap(), encoding="utf-8")
    print(f"layout: {changed} page(s) updated, sitemap.xml written")


if __name__ == "__main__":
    main()
