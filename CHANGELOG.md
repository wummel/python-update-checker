# Changelog

## 1.5.0

Release date: 29.10.2026

- Parse and use a `requires-python` version found in `pyproject.toml`

## 1.4.0

Release date: 09.09.2026

- Support legacy `[tool.uv.dev-dependencies]`
- Warn when poetry-specific dependencies are detected

## 1.3.0

Release date: 08.09.2026

- Skip directory packages in uv.lock

## 1.2.0

Release date: 07.09.2026

- Skip git packages in uv.lock

## 1.1.0

Release date: 07.09.2026

- Check referenced requirements.txt files.

## 1.0.0

Release date: 07.09.2026

- Increase uv.lock file size limit to 10MB.

## 0.12.0

Release date: 07.09.2026

- Move version check after skip checks.
- Added project urls.

## 0.11.0

Release date: 07.09.2026

- Skip local path packages in uv.lock

## 0.10.0

Release date: 04.09.2026

- Add `--exclude-package` option.

## 0.9.0

Release date: 04.09.2026

- Skip editable packages in uv.lock
- Add puc module `__version__` variable and add `--version` option
- Switch to x.y.z version number scheme

## 0.8

Release date: 03.09.2026

- Skip virtual packages in uv.lock

## 0.7

Release date: 03.09.2026

- Add this changelog.
- Add `--verbose` to uv when running `puc --debug`.
