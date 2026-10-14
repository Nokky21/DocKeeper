# Procedures

For whoever maintains this repository. Every step says how to tell that it worked.

## Check everything before a commit

**When:** before every commit and every pull request.
**Requires:** `python3` 3.10 or newer (the suite also passes on the Python 3.9 that ships with macOS),
`git`, and Node 24 with `yarn` if you touch `site/`.
**Risk:** none, nothing here writes to the repository.

1. Run the unit tests: `python3 -m unittest`. They include the self-check of this repository, the
   same `check` that CI runs.
   <!-- dockeeper: tests/test_autocomprobacion.py#PruebasAutocomprobacion.test_el_repositorio_se_mantiene_limpio -->
   - Check: the last line says `OK`.
2. Run the check yourself to see every claim: `python3 bin/dockeeper check`.
   <!-- dockeeper: dockeeper/motor.py#comprobar -->
   - Check: the last line says `Result: green`.
3. If you touched `site/`, from that folder: `yarn test`, then `yarn build`. The test runs the
   scenarios of the browser demo through the TypeScript port of the check and compares every verdict
   and fingerprint with the Python engine.
   <!-- dockeeper: site/package.json:10 site/scripts/check-demo.ts#compare -->
   - Check: `demo OK` followed by the number of scenarios, then a finished build.

**If it fails:** a new message without its English text fails `tests/test_textos.py`; add the English
to the table in `dockeeper/textos.py`. A `CHANGED` in the self-check means you changed code that some
document talks about: see the next procedure.
<!-- dockeeper: tests/test_textos.py#PruebasTextos.test_cada_mensaje_tiene_version_en_ingles -->

## When you change code that the docs talk about

**When:** `check` reports `CHANGED`, or the self-check test fails, after you edited code.

1. Read the sentence next to the anchor and the code it points at. If the sentence is no longer
   true, rewrite it.
2. Reseal only that file: `python3 bin/dockeeper fix --aceptar --solo path/to/the/file.py`.
   <!-- dockeeper: dockeeper/motor.py#arreglar -->
   - Check: `check` says `Result: green`.
3. If `check` only reports `MOVED`, `python3 bin/dockeeper fix` follows the code without any review.

A claim of the README is repeated in its 22 translations with the same anchors, so one change of
code shows up 23 times. Review the English sentence once and reseal with `--solo` on the code file.

New anchors are sealed with `python3 bin/dockeeper scan --solo path/to/the/doc.md`, which prints the
block each anchor landed on so you can confirm it before committing.
<!-- dockeeper: dockeeper/motor.py#escanear -->

## Release a version

**When:** the changes for a version are on `main` and CI is green.
**Requires:** push rights to the repository, including tags.
**Risk:** a release is public as soon as the tag is pushed. Undo it by deleting the release on GitHub
and the tag with `git push --delete origin vX.Y.Z`.

1. Raise the version: `__version__` in `dockeeper/__init__.py`, the `@vX.Y.Z` of the GitHub Action
   in `README.md`, `docs/reference.md` and `site/src/components/More.astro`, the README translations,
   `site/package.json`, the version shown in `site/src/layouts/Base.astro` and the status line of
   `SPEC.md`.
   - Check: `python3 bin/dockeeper --version` prints the new version, and searching the repository
     for the old one finds only history.
2. If the release carries a decision, write it in the commit message on `Decision:` and `Why:` lines,
   so `dockeeper why` finds it and [the decisions page](decisions.md) can cite it.
   <!-- dockeeper: dockeeper/porque.py#historial -->
3. Commit as `chore(release): vX.Y.Z` and push `main`.
   - Check: the CI and Website workflows finish green.
4. Tag and push the tag: `git tag vX.Y.Z`, then `git push origin vX.Y.Z`. The release workflow
   refuses a tag that doesn't match the version, runs the tests and attaches `dockeeper-skill.zip`
   with `SKILL.md`, `LICENSE`, `README.md`, `bin`, `dockeeper` and `templates`.
   <!-- dockeeper: .github/workflows/release.yml:21 .github/workflows/release.yml:28 -->
   - Check: the release appears with its ZIP, and the ZIP from `releases/latest/download/` prints
     the new version with `python3 dockeeper/bin/dockeeper --version` once unzipped.

**If it fails:** `tag vX.Y.Z != version …` means step 1 missed `dockeeper/__init__.py`. Delete the
tag locally and on GitHub, fix the version, commit and tag again.

## Publish the website

**When:** anything under `site/` changes on `main`.

1. Push to `main`. The Website workflow runs the demo test and the build, then deploys to GitHub
   Pages. On pull requests it only builds.
   <!-- dockeeper: .github/workflows/pages.yml:6 .github/workflows/pages.yml:35 -->
   - Check: <https://nokky21.github.io/DocKeeper/> serves the change.

**Rollback:** revert the commit on `main`; the next deploy publishes the previous page.

## Translations and generated images

The README translations in `docs/i18n/` and the images in `site/public/assets/` (diagrams and real
terminal captures) are generated by maintainer tools kept outside the repository. Don't edit
`docs/i18n/*.md` by hand: change the English README, which is the reference, and the translations
follow when they are regenerated. Each translation says so at the end.
