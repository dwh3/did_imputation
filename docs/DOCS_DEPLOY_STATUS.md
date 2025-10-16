# Docs Deploy Status — $(git rev-parse --short HEAD)

- Updated `mkdocs.yml` with:
  - `site_url: https://dwh3.github.io/did_imputation/`
  - `repo_url: https://github.com/dwh3/did_imputation`
  - `use_directory_urls: false`
  - Navigation pointing to `index.md` and `PARITY.md`.
- Documentation files present in `docs/`: `index.md`, `PARITY.md`, `SPEC.md`, `RELEASE_STATUS.md`.
- Build command: `.venv/Scripts/python.exe -m mkdocs build --strict` (status: ✅).
- Deploy command: `.venv/Scripts/python.exe -m mkdocs gh-deploy --clean --message "docs: fix project-site base path and links"` (status: ✅).
- Published site: <https://dwh3.github.io/did_imputation/>.

📌 Maintainer reminder: In GitHub → **Settings → Pages**, ensure **Source = gh-pages (root)** and allow a few minutes for CDN cache invalidation before testing navigation.
