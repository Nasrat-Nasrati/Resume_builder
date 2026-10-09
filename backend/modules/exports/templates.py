"""Versioned, controlled HTML/CSS templates for CV previews and exports."""
from html import escape

THEMES = {
    "blue-teal": {"ink": "#17324d", "accent": "#087e8b", "muted": "#5d6b7b"},
    "green": {"ink": "#244b3a", "accent": "#39765a", "muted": "#596b61"},
    "maroon": {"ink": "#4b2634", "accent": "#8a4055", "muted": "#6e5a60"},
}
DEFAULT_DESIGN = {"theme": "blue-teal", "font": "sans", "layout": "classic"}
DESIGN_OPTIONS = {
    "public-service-v1": {"themes": tuple(THEMES), "fonts": ("sans", "serif"), "layouts": ("classic",)},
    "professional-v1": {"themes": tuple(THEMES), "fonts": ("sans", "serif"), "layouts": ("classic", "sidebar")},
    "ats-v1": {"themes": ("blue-teal",), "fonts": ("sans", "serif"), "layouts": ("single-column",)},
}

TEMPLATE_CATALOG = {
    "public-service-v1": {
        "version": 1, "name": "Public service", "access_level": "free", "free": True,
        "supported_languages": ("en", "fa", "ps"), "layout_options": ("classic",), "theme_options": tuple(THEMES), "font_options": ("sans", "serif"),
        "description": "A clear formal layout for public service and official applications.",
        "sections": ("personal", "experience", "education", "languages", "skills", "projects", "awards", "publications", "references"),
        "colors": {"ink": "#17324d", "teal": "#087e8b", "muted": "#5d6b7b"},
    },
    "professional-v1": {
        "version": 1, "name": "Professional", "access_level": "premium", "free": False,
        "supported_languages": ("en", "fa", "ps"), "layout_options": ("classic", "sidebar"), "theme_options": tuple(THEMES), "font_options": ("sans", "serif"),
        "description": "A restrained private-sector layout with a strong name and section hierarchy.",
        "sections": ("personal", "experience", "education", "languages", "skills", "projects", "awards", "publications", "references"),
        "colors": {"ink": "#17324d", "teal": "#087e8b", "muted": "#5d6b7b"},
    },
    "ats-v1": {
        "version": 1, "name": "ATS oriented", "access_level": "premium", "free": False,
        "supported_languages": ("en", "fa", "ps"), "layout_options": ("single-column",), "theme_options": ("blue-teal",), "font_options": ("sans", "serif"),
        "description": "A text-first single-column layout. Applicant tracking results vary by employer and system.",
        "sections": ("personal", "experience", "education", "languages", "skills", "projects", "awards", "publications", "references"),
        "colors": {"ink": "#202020", "teal": "#444444", "muted": "#555555"},
    },
}

LABELS = {
    "en": {"profile": "Profile", "experience": "Experience", "education": "Education", "languages": "Languages", "skills": "Skills", "projects": "Projects", "awards": "Awards", "publications": "Publications", "references": "References"},
    "fa": {"profile": "درباره من", "experience": "تجربه کاری", "education": "تحصیلات", "languages": "زبان‌ها", "skills": "مهارت‌ها", "projects": "پروژه‌ها", "awards": "افتخارات", "publications": "انتشارات", "references": "معرف‌ها"},
    "ps": {"profile": "زما په اړه", "experience": "کاري تجربه", "education": "زده کړې", "languages": "ژبې", "skills": "مهارتونه", "projects": "پروژې", "awards": "جایزې", "publications": "خپرونې", "references": "سپارښتونکي"},
}

def template_for(key):
    try:
        return TEMPLATE_CATALOG[key]
    except KeyError as exc:
        raise ValueError("Unknown template version.") from exc

def default_design_options(template_key):
    configured = DESIGN_OPTIONS.get(template_key)
    if not configured:
        raise ValueError("Unknown template version.")
    return {"theme": configured["themes"][0], "font": configured["fonts"][0], "layout": configured["layouts"][0]}

def validate_design_options(template_key, options):
    configured = DESIGN_OPTIONS.get(template_key)
    if not configured or not isinstance(options, dict) or set(options) != {"theme", "font", "layout"}:
        raise ValueError("Unsupported design options.")
    if options["theme"] not in configured["themes"] or options["font"] not in configured["fonts"] or options["layout"] not in configured["layouts"]:
        raise ValueError("Unsupported design option for this template.")
    return dict(options)

def plain_text(value):
    return escape(str(value or ""), quote=True)

def render_html(payload):
    key = payload.get("template_key", "public-service-v1")
    template = template_for(key)
    language = payload.get("output_language", "en")
    if language not in template["supported_languages"]:
        raise ValueError("Unsupported output language.")
    content = payload.get("snapshot", {})
    personal = content.get("personal", {})
    ats = key == "ats-v1"
    professional = key == "professional-v1"
    design = payload.get("design_options", default_design_options(key))
    design = validate_design_options(key, design)
    colors = THEMES[design["theme"]]
    ink, accent, muted = colors["ink"], colors["accent"], colors["muted"]
    font_family = "Noto Serif" if design["font"] == "serif" else "Noto Sans"
    layout = design["layout"]
    rtl = language in {"fa", "ps"}
    direction = "rtl" if rtl else "ltr"
    align = "right" if rtl else "left"
    parts = ["<!doctype html><html lang='", language, "' dir='", direction, "'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width'><style>",
        "@page{size:A4;margin:17mm 16mm 18mm}*{box-sizing:border-box}body{font-family:'", font_family, "','Noto Naskh Arabic',serif;color:", ink, ";font-size:10pt;line-height:1.5;direction:", direction,
        ";text-align:", align, "}h1{font-size:23pt;line-height:1.2;margin:0 0 3mm;color:", ink, ";overflow-wrap:anywhere}h2{font-size:12pt;color:", accent, ";border-bottom:1px solid #d7e1e8;padding-bottom:1.5mm;margin:6mm 0 2.5mm;break-after:avoid}h3{font-size:10pt;margin:2mm 0 0;break-after:avoid}p{margin:1mm 0;overflow-wrap:anywhere}.subtitle{font-size:11pt;color:", accent, "}.contact,.muted{font-size:9pt;color:", muted, "}.entry{margin:0 0 3.5mm;break-inside:avoid}.dates{font-size:8.5pt;color:", muted, "}.entry p{white-space:pre-wrap}.skills{margin:0}.footer{position:fixed;bottom:-12mm;left:0;right:0;border-top:1px solid #d7e1e8;padding-top:2mm;color:", muted, ";font-size:8pt}.watermark{position:fixed;bottom:-11mm;left:0;right:0;text-align:center;color:#708090;font-size:7.5pt;border-top:1px solid #d7e1e8;padding-top:2mm}.keep{break-inside:avoid}html{-webkit-print-color-adjust:exact;print-color-adjust:exact}",
        "h1{", "border-bottom:2px solid "+accent+";padding-bottom:3mm" if professional else "", "}",
        ".layout-sidebar{display:grid;grid-template-columns:30% 1fr;gap:8mm}.layout-sidebar .side{background:#f4f6f7;padding:4mm}.layout-sidebar .main{min-width:0}" if layout == "sidebar" else "",
        "h2{color:#222;border-color:#888;text-transform:uppercase;letter-spacing:.3pt}h1{color:#111}" if ats else "", "</style></head><body>"]
    title = personal.get("full_name") or payload.get("title") or "CV"
    parts.append("<header class='keep'>")
    photo_data = payload.get("photo_data") if key != "ats-v1" else None
    if photo_data:
        if not isinstance(photo_data, str) or len(photo_data) > 700_000 or any(char not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=" for char in photo_data):
            raise ValueError("Invalid embedded photo data.")
        parts.extend(["<img class='portrait' alt='Profile photo' src='data:image/jpeg;base64,", photo_data, "'>"])
    parts.extend(["<h1>", plain_text(title), "</h1>"])
    if personal.get("professional_title"):
        parts.extend(["<div class='subtitle'>", plain_text(personal["professional_title"]), "</div>"])
    contact = " · ".join(str(personal.get(k, "")) for k in ("email", "phone") if personal.get(k))
    if contact:
        target.extend(["<p class='contact' dir='ltr'>", plain_text(contact), "</p>"])
    location = " · ".join(str(personal.get(k, "")) for k in ("city", "province", "district") if personal.get(k) and (k == "city" or personal.get(f"show_{k}", True)))
    if location:
        parts.extend(["<p class='contact'>", plain_text(location), "</p>"])
    private_afghan = " · ".join(str(personal.get(k, "")) for k in ("father_name", "tazkira_number") if personal.get(k) and personal.get(f"show_{k}", False))
    if private_afghan:
        parts.extend(["<p class='contact'>", plain_text(private_afghan), "</p>"])
    parts.append("</header>")
    sidebar_parts = []
    main_parts = []
    if personal.get("summary"):
        target = sidebar_parts if layout == "sidebar" else main_parts
        target.extend(["<section><h2>", plain_text(LABELS[language]["profile"]), "</h2><p>", plain_text(personal["summary"]), "</p></section>"])
    selected = set(payload.get("selected_sections", []))
    for section in template["sections"][1:]:
        if section in {"projects", "awards", "publications", "references"} and section not in selected:
            continue
        values = content.get(section, [])
        if not values:
            continue
        target = sidebar_parts if layout == "sidebar" and section in {"languages", "skills"} else main_parts
        target.extend(["<section><h2>", plain_text(LABELS[language][section]), "</h2>"])
        for row in values:
            if not isinstance(row, dict):
                target.extend(["<div class='entry'>", plain_text(row), "</div>"])
                continue
            if section == "references":
                heading = " — ".join(str(row.get(k, "")) for k in ("referee_name", "referee_role") if row.get(k))
            else:
                heading = " — ".join(str(row.get(k, "")) for k in ("position", "qualification", "title", "name", "language", "institution", "employer", "organization") if row.get(k))
            target.append("<article class='entry'>")
            if heading:
                target.extend(["<h3>", plain_text(heading), "</h3>"])
            date_line = " – ".join(str(row.get(k, "")) for k in ("start_date", "end_date", "date") if row.get(k))
            if date_line:
                target.extend(["<div class='dates'>", plain_text(date_line), "</div>"])
            detail = row.get("duties") or row.get("description") or row.get("field_of_study")
            if detail:
                target.extend(["<p>", plain_text(detail), "</p>"])
            if section == "skills" and row.get("skills"):
                target.extend(["<p>", plain_text(", ".join(row["skills"])), "</p>"])
            if section == "references" and row.get("consent_to_publish"):
                contact = " · ".join(row.get(k, "") for k in ("referee_email", "referee_phone") if row.get(k))
                if contact:
                    target.extend(["<p class='contact' dir='ltr'>", plain_text(contact), "</p>"])
            target.append("</article>")
        target.append("</section>")
    if layout == "sidebar":
        parts.append("<div class='layout-sidebar'><aside class='side'>" + "".join(sidebar_parts) + "</aside><main class='main'>" + "".join(main_parts) + "</main></div>")
    else:
        parts.extend(sidebar_parts)
        parts.extend(main_parts)
    if payload.get("watermark"):
        parts.append("<div class='watermark'>KabulCV · Free</div>")
    parts.append("</body></html>")
    return "".join(parts)
