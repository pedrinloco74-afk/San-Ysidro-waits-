# Jazz Nails

Spanish-language, mobile-friendly salon website linking bookings to https://www.instagram.com/jazz.nailsspa717/.

## Local development

```sh
npm ci
npm run dev
```

## Public deployment

GitHub Pages is deployed by `.github/workflows/deploy-pages.yml` when changes are pushed to `arena/99e2a0c9-san-ysidro-waits`.

Public URL: https://pedrinloco74-afk.github.io/San-Ysidro-waits-/

The workflow builds with the repository subpath, then deploys only `dist/` (not the reference images or source files). The manicure editorial image is AI-generated inspiration, not a portfolio photo.
