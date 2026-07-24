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

The post body originally displayed `post.markdown_content` as plain content. The CSS already includes prose styles for headings, paragraphs, lists, and spacing so the page was ready for rendered Markdown.

The post body now converts stored Markdown into sanitized HTML before rendering. This fixes raw Markdown markers appearing in the article, including heading hashes, bold markers, and fenced-code syntax. The renderer supports headings, paragraphs, lists, links, tables, and fenced code while sanitizing the generated HTML before it reaches the template. Caching the rendered result remains a later concern.

The rendered post body is now cached in Redis under `post:{slug}:html`. A post detail request checks Redis first, renders and stores the sanitized HTML on a miss, and falls back to database rendering when Redis is unavailable. Cache invalidation is exposed through `invalidate_post(slug)` for the future admin write routes; comments will remain outside this cache in their own phase.

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
10. Markdown rendering and sanitized article content
11. Redis cache wrapper for rendered post bodies
12. JWT user login foundation
13. Protected create-post form with CSRF validation

The latest refinement pass added visible `:focus-visible` states for keyboard users, subtle post-card and pagination hover states, mobile navigation wrapping, tighter small-screen article typography, and a reduced-motion media query. These changes improve usability while preserving the restrained editorial design from the template references.

The article body is converted from Markdown into sanitized HTML before it is passed to the post-detail template. The rendered result is now cached under `post:{slug}:html` through `app/cache.py`. Cache reads, writes, and invalidation are isolated behind helper functions, and Redis errors are logged and ignored so the public page continues rendering from the database when Redis is unavailable. The cache intentionally stores only the post body; comments will remain outside it when the comments phase is implemented.

The access model keeps the homepage and published post pages public. The first authentication unit adds `/login`, JWT creation and validation helpers, and a user-facing sign-in form styled with the existing Invariant editorial system. Successful authentication uses an expiring JWT in an `HttpOnly` cookie; registration, user-scoped write routes, and CSRF protection are still the next authentication steps.

The header and footer now expose a `Sign in` entry point without changing the public reading experience. The current create-post form is an implementation placeholder from the earlier admin-labeled step and will be moved to the authenticated user workflow as registration and user-scoped routes are completed.

The shared header places `Sign in` as the rightmost navigation item. It uses the copper accent and a subtle divider so account access is discoverable without competing with the public reading links. On narrow screens, the divider is removed and the item wraps with the rest of the navigation. The component is named `site-nav__account` to reflect that it is for normal users, not a special admin-only entry point.

The next admin unit adds a protected create-post form at `/admin/posts/new` and a `POST /admin/posts` route. The route requires a valid JWT, checks a separate double-submit CSRF token, validates slug uniqueness and the optional publish date, and assigns the new post to the authenticated user. Edit and delete routes are intentionally not included yet.

Current next implementation step:

1. Add user registration and move the create-post workflow under the authenticated user model.
2. Call `invalidate_post(slug)` after a post is edited.
3. Validate Redis hit, miss, and invalidation behavior with Redis or a fake Redis client.
4. Keep comments outside the rendered post-body cache when that phase begins.

## Validation Used

The following checks were run after the latest frontend edits:

```powershell
.\.venv\Scripts\python.exe -c "from jinja2 import Environment, FileSystemLoader; env=Environment(loader=FileSystemLoader('app/templates')); [env.get_template(t) for t in ['base.html','index.html','post_detail.html','partials/header.html','partials/footer.html','partials/post_card.html']]; print('templates ok')"

.\.venv\Scripts\python.exe -m compileall app
```

Both passed. The auth templates load and JWT creation/decoding still round-trips correctly. The next live validation should target `/login` and the user registration flow; the earlier `/admin/login` wording is no longer the intended product model.
