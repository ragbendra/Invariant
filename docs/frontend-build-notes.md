# Frontend Build Notes

This document records the frontend work completed so far and the reasoning behind the current structure. The goal is to build the blog like a normal frontend project while still respecting the backend/spec phases.

## Source of Truth

The main implementation guide is `blog_build_plan.md`.

The files in `templatedesign/` are used as visual references. The current frontend mainly borrows from:

- `Classic Blog Grid.png`
- `Classic Blog Post Detail.png`
- `Classic With Side Blog.png`

The design references include more UI than the current backend supports, so unsupported sections are represented as layout scaffolding or disabled placeholders instead of fake working features.

## What We Changed

### 1. Removed Premature Template Content

The earlier frontend had hardcoded demo sections such as:

- sidebar widgets
- top authors
- categories
- Instagram grid
- related posts
- social share bar
- static featured/popular posts

Those were removed because they were not backed by current routes or data. This made the code easier to reason about and brought the frontend closer to the project spec.

### 2. Reintroduced Frontend Structure

After the cleanup, the layout was rebuilt in a more realistic frontend workflow:

1. Build global layout shell.
2. Build header component.
3. Build footer component.
4. Build active page body.
5. Leave future areas as placeholders until the backend/spec supports them.

This mirrors how frontend work is usually organized: the page frame comes first, then the current route body, then later sections.

## Template Structure

### `base.html`

`base.html` is the root layout for every page.

It contains:

- the document `<head>`
- stylesheet link
- shared header include
- main content block
- shared footer include

Current shape:

```jinja2
{% include "partials/header.html" %}

<main class="site-main">
    {% block content %}{% endblock %}
</main>

{% include "partials/footer.html" %}
```

This keeps page templates focused on page-specific content.

### `partials/header.html`

The header is a reusable component.

It contains:

- `Invariant` brand mark
- primary navigation
- disabled future navigation items

The disabled links visually communicate intended future structure without pretending those pages exist yet.

Current nav items:

- Home
- Blog
- Single Post placeholder
- Other Pages placeholder

### `partials/footer.html`

The footer is also reusable.

It contains:

- brand area
- short project description
- simple Explore links
- contact placeholder
- copyright text

This gives the site a complete frontend frame while keeping it simple and editable.

### `index.html`

The homepage is the active body page right now.

It contains:

- hero area
- page summary
- section heading
- dynamic post list
- pagination
- empty right-side panel scaffold

The post list uses real backend data:

```jinja2
{% for post in posts %}
    {% include "partials/post_card.html" %}
{% endfor %}
```

### `partials/post_card.html`

The post card is a repeated component used by the homepage.

It renders:

- visual media placeholder
- published date
- post title
- excerpt
- read-more link

The media block is currently decorative because the `Post` model does not yet include an image field. This keeps the design close to the template without adding unsupported data.

### `post_detail.html`

The detail page follows the classic post-detail reference.

It renders:

- article label
- post title
- published date
- media placeholder
- excerpt lede
- markdown content
- article navigation

The excerpt lede uses `post.excerpt`, so the page has an editorial introduction without adding fake content.

The current post body displays `post.markdown_content` as plain content. Markdown-to-HTML rendering belongs later when the spec reaches body parsing/caching. The CSS already includes prose styles for headings, paragraphs, lists, and spacing so the frontend is ready for rendered markdown later.

## CSS Organization

All current frontend styles live in:

```text
app/static/css/style.css
```

The stylesheet is organized around:

- design tokens in `:root`
- global base styles
- header/navigation
- page hero
- page body layout
- post cards
- pagination
- post detail page
- footer
- responsive breakpoints

## Design Direction

The current design is based on the new classic blog references:

- clean white background
- strong black typography
- copper accent color
- geometric logo mark
- spacious article grid
- simple editorial footer

The earlier generic blue palette was removed.

Current primary palette:

```css
--color-bg: #ffffff;
--color-surface: #f7f5f2;
--color-text: #181716;
--color-muted: #77716a;
--color-border: #e8e2da;
--color-primary: #181716;
--color-accent: #b66a3c;
```

## Placeholder Policy

Placeholders are allowed when they represent layout structure only.

Current examples:

- disabled nav items for future pages
- right-side layout panel on the homepage
- media blocks for posts

Placeholders should not:

- submit forms
- pretend to load real data
- link to routes that do not exist
- contain hardcoded fake blog content

## Current Frontend Build Order

Completed:

1. Global layout shell
2. Header partial
3. Footer partial
4. Homepage body
5. Post card component
6. Post detail layout
7. Responsive CSS foundation
8. Post detail lede and prose styling
9. Responsive and keyboard interaction refinement

The latest refinement pass added visible `:focus-visible` states for keyboard users, subtle post-card and pagination hover states, mobile navigation wrapping, tighter small-screen article typography, and a reduced-motion media query. These changes improve usability while preserving the restrained editorial design from the template references.

Recommended next frontend step:

1. Run the app in browser.
2. Compare homepage against `Classic Blog Grid.png`.
3. Adjust spacing, typography, and responsive behavior.
4. Compare post detail against `Classic Blog Post Detail.png`.
5. Only then move to new sections or routes.

## Validation Used

The following checks were run after the latest frontend edits:

```powershell
.\.venv\Scripts\python.exe -c "from jinja2 import Environment, FileSystemLoader; env=Environment(loader=FileSystemLoader('app/templates')); [env.get_template(t) for t in ['base.html','index.html','post_detail.html','partials/header.html','partials/footer.html','partials/post_card.html']]; print('templates ok')"

.\.venv\Scripts\python.exe -m compileall app
```

Both passed. Live route checks also confirmed that `/health`, `/`, the stylesheet, and a seeded post detail page return successfully, while an unknown post returns `404`.
