# integrallis.com

Source for the Integrallis corporate site — a static site served by GitHub Pages
from `docs/` at [integrallis.com](https://integrallis.com).

## Layout

```
docs/            the site, served as-is (no build step)
  assets/        css, js, self-hosted fonts, images
  */index.html   redirect stubs preserving URLs from the previous site
scripts/         Medium feed sync, analytics enable/disable
.github/         SEO audit workflow
```

## Working on it

There is no build. Edit the HTML and CSS directly, then:

```bash
python3 -m http.server 8000 --directory docs
```

Fonts are self-hosted, so the site makes no third-party requests.

## Checks

`.github/workflows/seo-audit.yml` runs [RankCLI](https://rankcli.dev) against the
built pages on every pull request that touches `docs/`, and against the live site
weekly.

```bash
npx -y @rankcli/cli@latest audit -u http://localhost:8000/ --max-pages 10
```

## Licence

Site content © Integrallis Software, LLC. Self-hosted fonts ship under the SIL
Open Font License; see `docs/assets/fonts/`.
