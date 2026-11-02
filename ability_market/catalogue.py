"""The Services catalogue - everything Ability Bazaar sells, in one table.

V2.9.0. This is the single source of truth for the /services cards AND for
checkout: the storefront renders from it and /buy/<sku> reads the amount to
charge from it, so a price can never drift between what a buyer is shown and
what they are charged. The amount is NEVER taken from the submitted form.

Fields:
  sku            url segment for /buy/<sku> (paid items only)
  product        order product code, drives fulfillment routing in routes.py
  price_usd      amount charged (0 for free, None for "custom quote")
  price_label    what the card shows
  includes       what the buyer gets - one line per bullet
  turnaround     delivery promise shown on the card
  cta            free | buy | quote
  needs_target_url  the buy form requires the site to work on
  brief_label    label for the optional free-text brief on the buy form
  brief_hint     guidance shown under that label, for work where we need the
                 customer to tell us what to build (the website builds). Left
                 off products where a brief is incidental, like a scan.

Training sponsorships are NOT here: they are a workforce-development
engagement sold on /sponsor (SPONSOR_TIERS in routes.py), deliberately kept
off the services storefront.
"""

FREE = "free"
BUY = "buy"
QUOTE = "quote"

CATALOGUE = [
    {
        "sku": "able-screening",
        "product": None,
        "name": "Basic ABLE Screening",
        "badge": "Free",
        "price_usd": 0,
        "price_label": "Free",
        "summary": ("An automated WCAG 2.2 check of one page by ABLE, our "
                    "Accessibility Barrier Locator Engine."),
        "includes": [
            "Automated WCAG 2.2 check of one page",
            "Counts of critical, serious, moderate and minor issues",
            "Automated only - no human verification and no written report",
            "No sign-up, no card, no strings",
        ],
        "turnaround": "A few minutes, right here on this page",
        "cta": FREE,
        "cta_label": "Run a free screening",
    },
    {
        "sku": "advanced-scan",
        "product": "advanced-accessibility-scan",
        "name": "Advanced Accessibility Scan",
        "badge": "Most popular",
        "price_usd": 199,
        "price_label": "$199",
        "summary": ("An automated WCAG 2.2 scan of up to 200 public pages on "
                    "one website, followed by a focused review by an "
                    "accessibility expert who is blind or has low vision."),
        "includes": [
            "Automated WCAG 2.2 crawl of up to 200 unique public pages on one website",
            "Pages must be reachable without a sign-in; duplicate and unreachable pages are excluded",
            "A blind or low-vision accessibility expert validates and prioritises up to 20 highest-impact distinct automated findings",
            "Focused manual checks on 3 key public pages: home, one form or primary workflow, and one representative content page",
            "Prioritised report with issue locations and practical remediation guidance",
            "Not a comprehensive manual audit or assistive-technology test; deeper testing is available by custom quote",
        ],
        "turnaround": "Report within 3 business days after we receive a reachable site and key-page choices",
        "cta": BUY,
        "cta_label": "Buy - $199",
        "needs_target_url": True,
        "brief_label": "Which 3 key pages should we hand-check? (optional)",
        "brief_hint": (
            "List the homepage, your main public form or workflow, and one "
            "representative content page. If you leave this blank, we will "
            "select three public pages. Authenticated areas require a custom "
            "quote."
        ),
    },
    {
        "sku": "doc-starter",
        "product": "document-remediation-starter",
        "name": "Document Starter",
        "badge": "Up to 30 pages",
        "price_usd": 199,
        "price_label": "$199",
        "summary": ("Accessibility remediation for a small collection of PDF, "
                    "Word or PowerPoint files, with screen-reader validation "
                    "included."),
        "includes": [
            "Up to 30 standard pages in any mix of PDF, Word and PowerPoint files",
            "A complex page - a fillable form, data table, scanned/OCR page, chart or infographic - counts as 2 pages",
            "Remediation tested against relevant WCAG 2.2 success criteria; PDF files are also tested against applicable PDF/UA criteria",
            "Every file is verified with NVDA or JAWS by a blind or low-vision professional before delivery",
            "Accessible remediated files plus a concise delivery note",
            "Excel workbooks and complex fillable forms require a custom quote",
            "Rush service may be available by prior agreement at a 50% surcharge",
        ],
        "turnaround": "Within 5 business days after we receive usable source files",
        "cta": BUY,
        "cta_label": "Buy - $199",
        "needs_target_url": False,
        "brief_label": "Tell us about the documents (optional)",
        "brief_hint": (
            "List the file types, approximate standard and complex-page "
            "counts, and any deadline. After payment, reply to your "
            "confirmation email with the source files. Contact us before "
            "ordering if you need rush service, Excel workbooks or complex "
            "fillable forms."
        ),
    },
    {
        "sku": "doc-standard",
        "product": "document-remediation-standard",
        "name": "Document Standard",
        "badge": "Up to 90 pages",
        "price_usd": 499,
        "price_label": "$499",
        "summary": ("Accessibility remediation for a larger collection of "
                    "PDF, Word or PowerPoint files, with screen-reader "
                    "validation included."),
        "includes": [
            "Up to 90 standard pages in any mix of PDF, Word and PowerPoint files",
            "A complex page - a fillable form, data table, scanned/OCR page, chart or infographic - counts as 2 pages",
            "Remediation tested against relevant WCAG 2.2 success criteria; PDF files are also tested against applicable PDF/UA criteria",
            "Every file is verified with NVDA or JAWS by a blind or low-vision professional before delivery",
            "Accessible remediated files plus a concise delivery note",
            "Excel workbooks and complex fillable forms require a custom quote",
            "Rush service may be available by prior agreement at a 50% surcharge",
        ],
        "turnaround": "Within 7 business days after we receive usable source files",
        "cta": BUY,
        "cta_label": "Buy - $499",
        "needs_target_url": False,
        "brief_label": "Tell us about the documents (optional)",
        "brief_hint": (
            "List the file types, approximate standard and complex-page "
            "counts, and any deadline. After payment, reply to your "
            "confirmation email with the source files. Contact us before "
            "ordering if you need rush service, Excel workbooks or complex "
            "fillable forms."
        ),
    },
    {
        "sku": "doc-pro",
        "product": "document-remediation-pro",
        "name": "Document Pro",
        "badge": "Up to 180 pages",
        "price_usd": 899,
        "price_label": "$899",
        "summary": ("Accessibility remediation for a high-volume collection "
                    "of PDF, Word or PowerPoint files, with screen-reader "
                    "validation included."),
        "includes": [
            "Up to 180 standard pages in any mix of PDF, Word and PowerPoint files",
            "A complex page - a fillable form, data table, scanned/OCR page, chart or infographic - counts as 2 pages",
            "Remediation tested against relevant WCAG 2.2 success criteria; PDF files are also tested against applicable PDF/UA criteria",
            "Every file is verified with NVDA or JAWS by a blind or low-vision professional before delivery",
            "Accessible remediated files plus a concise delivery note",
            "Excel workbooks and complex fillable forms require a custom quote",
            "Rush service may be available by prior agreement at a 50% surcharge",
        ],
        "turnaround": "Within 10 business days after we receive usable source files",
        "cta": BUY,
        "cta_label": "Buy - $899",
        "needs_target_url": False,
        "brief_label": "Tell us about the documents (optional)",
        "brief_hint": (
            "List the file types, approximate standard and complex-page "
            "counts, and any deadline. After payment, reply to your "
            "confirmation email with the source files. Contact us before "
            "ordering if you need rush service, Excel workbooks or complex "
            "fillable forms."
        ),
    },
    {
        "sku": "static-site",
        "product": "website-build-static",
        "name": "Starter Website or App Build",
        "badge": "Launch for $500",
        "price_usd": 500,
        "price_label": "$500",
        "summary": ("Launch a focused website, lightweight web app, "
                    "mobile-friendly app or AI proof of concept with a clear, "
                    "fixed starter scope."),
        "includes": [
            "One website, web app, installable mobile-friendly web app or AI proof of concept",
            "Up to 10 pages or screens and 1 simple user workflow",
            "Initial design and development, plus 2 revision rounds",
            "5 hours of live collaboration and customer support during build and handoff",
            "One year of Ability Bazaar-managed hosting at no additional charge, up to 10,000 visits per month",
            "Accessibility review against WCAG 2.2 AA criteria and source-code handoff",
            "Use an Ability Bazaar address or add a custom domain billed at its actual registration cost",
            "App-store, paid API and other third-party charges are not included",
        ],
        "turnaround": "First working version within 10 business days after complete brief and content",
        "cta": BUY,
        "cta_label": "Start for $500",
        "needs_target_url": False,
        "brief_label": "Tell us about the website or app you want to launch (optional)",
        "brief_hint": (
            "Please provide an initial short description here. Add as "
            "much detail as you like - there is no minimum or maximum, "
            "so include anything you think helps. Once you have paid, "
            "you can reply to your confirmation email to send us "
            "images, documents or design ideas as attachments. We will "
            "review all of it and then contact you for more details "
            "before finalising the design of your website or app."
        ),
    },
    {
        "sku": "dynamic-site",
        "product": "website-build-dynamic",
        "name": "Growth Website or App Build",
        "badge": "Best value",
        "price_usd": 1000,
        "price_label": "$1,000",
        "summary": ("Build a more capable website or working MVP for a web, "
                    "mobile-friendly or AI application with bounded workflows "
                    "and one useful integration."),
        "includes": [
            "One website, web app, installable mobile-friendly web app or AI-enabled MVP",
            "Up to 20 pages or screens and 2 core user workflows",
            "One integration: choose AI API, database or CMS, sign-in, or another third-party API",
            "Initial design and development, plus 3 revision rounds",
            "10 hours of live collaboration and customer support during build and handoff",
            "One year of Ability Bazaar-managed hosting at no additional charge, up to 25,000 visits per month",
            "Accessibility review against WCAG 2.2 AA criteria and source-code handoff",
            "Use an Ability Bazaar address or add a custom domain billed at its actual registration cost",
            "App-store, usage-based AI/API and other third-party charges are not included",
        ],
        "turnaround": "First working MVP within 20 business days after complete brief and content",
        "cta": BUY,
        "cta_label": "Start for $1,000",
        "needs_target_url": False,
        "brief_label": "Tell us what the website or app needs to do (optional)",
        "brief_hint": (
            "Please provide an initial short description here. Add as "
            "much detail as you like - there is no minimum or maximum, "
            "so include anything you think helps. Once you have paid, "
            "you can reply to your confirmation email to send us "
            "images, documents or design ideas as attachments. We will "
            "review all of it and then contact you for more details "
            "before finalising the design of your website or app."
        ),
    },
    {
        "sku": "custom",
        "product": None,
        "name": "Anything larger",
        "badge": "Custom",
        "price_usd": None,
        "price_label": "Custom quote",
        "summary": ("Human-reviewed accessibility scans and other larger "
                    "engagements, scoped and quoted with you by the team who "
                    "will deliver them."),
        "includes": [
            "Human-reviewed scans and manual audits by expert testers with disabilities",
            "VPAT / ACR conformance documentation",
            "Assistive-technology testing",
            "Mobile and AI app builds",
            "Custom hosting and monitoring",
        ],
        "turnaround": "Scoped with you - we reply within 2 business days",
        "cta": QUOTE,
        "cta_label": "Request a quote",
        "quote_about": "Custom human-reviewed accessibility scan or engagement",
    },
]

# sku -> item, for the paid items only (the ones /buy/<sku> can sell).
BUYABLE = {item["sku"]: item for item in CATALOGUE if item["cta"] == BUY}

DOCUMENT_SKUS = ("doc-starter", "doc-standard", "doc-pro")
DOCUMENT_PRODUCTS = tuple(BUYABLE[sku]["product"] for sku in DOCUMENT_SKUS)

# Products whose fulfillment is an ABLE scan of the buyer's site.
SCAN_PRODUCTS = ("ai-scan-expert-verification", "advanced-accessibility-scan")


def get_buyable(sku):
    """Return the catalogue item for a sellable sku, or None."""
    return BUYABLE.get(sku)
