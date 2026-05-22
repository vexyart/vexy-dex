<!-- this_file: examples/expected/mkdocs_blog_post.md -->

# Expected output — `mkdocs_blog_post.py`

Captured 2026-05-22. Slide counts vary with the live page and engine metrics.

- Input: <https://blog.fontlab.com/2026/05/07/from-bland-to-bold-with-vexy-lines/>
- Classified: **mkdocs-material** (confidence 1.00)
- Stage: 1920×1080

```json
{
  "source": "https://blog.fontlab.com/2026/05/07/from-bland-to-bold-with-vexy-lines/",
  "framework": "mkdocs-material",
  "slides": 7,
  "results": [
    { "strategy": "playwright", "ok": true, "slides": 6 },
    { "strategy": "weasyprint", "ok": true, "slides": 12 }
  ]
}
```

A real article (not the blog index). The MkDocs importer extracts
`article.md-content__inner`, drops sidebar/header/footer/search, and splits by
heading — code blocks and tables ride along intact. WeasyPrint is the natural
fit for clean documentation HTML and packs more, text-tight slides (12) than
Playwright's looser layout (6). Pick per slide across the two folders.
