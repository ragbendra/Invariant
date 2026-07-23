import bleach
import markdown


ALLOWED_TAGS = bleach.sanitizer.ALLOWED_TAGS.union(
    {
        "blockquote",
        "br",
        "code",
        "h1",
        "h2",
        "h3",
        "h4",
        "hr",
        "li",
        "ol",
        "p",
        "pre",
        "strong",
        "table",
        "tbody",
        "td",
        "th",
        "thead",
        "tr",
        "ul",
    }
)

ALLOWED_ATTRIBUTES = {
    "a": {"href", "title"},
}


def render_markdown(source: str) -> str:
    rendered = markdown.markdown(
        source,
        extensions=["fenced_code", "tables"],
    )
    return bleach.clean(
        rendered,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols={"http", "https", "mailto"},
    )
