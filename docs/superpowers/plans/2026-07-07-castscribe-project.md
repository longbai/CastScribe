# CastScribe Project Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Package the existing media-to-text script as the CastScribe Python project and push it to `longbai/CastScribe`.

**Architecture:** Keep the current tested behavior, but split the single script into focused modules under `src/castscribe`. Provide both `python3 -m castscribe` and an installed `castscribe` console script through `pyproject.toml`.

**Tech Stack:** Python 3.10+, `yt-dlp`, macOS `yap`, non-macOS `faster-whisper`, `unittest`.

---

### Task 1: Package Skeleton

**Files:**
- Create: `pyproject.toml`
- Create: `src/castscribe/__init__.py`
- Create: `src/castscribe/__main__.py`
- Create: `src/castscribe/cli.py`

- [ ] Add packaging metadata with project name `castscribe`, dependency on `yt-dlp`, and console entry point `castscribe = "castscribe.cli:main"`.
- [ ] Add `__main__.py` that raises `SystemExit(main())`.
- [ ] Keep the CLI argument surface identical to the existing script.

### Task 2: Module Split

**Files:**
- Create: `src/castscribe/sources.py`
- Create: `src/castscribe/subtitles.py`
- Create: `src/castscribe/transcriber.py`
- Create: `src/castscribe/downloader.py`
- Create: `src/castscribe/pipeline.py`
- Modify: `media_to_text.py`

- [ ] Move source collection, local path detection, Apple Podcasts feed lookup, subtitle conversion, transcription, downloader, and processing pipeline into the focused modules.
- [ ] Keep `media_to_text.py` as a compatibility wrapper that imports `main` from `castscribe.cli`.
- [ ] Do not change output naming or download fallback behavior.

### Task 3: Tests and Docs

**Files:**
- Modify: `tests/test_media_to_text.py`
- Create: `tests/test_cli_entrypoint.py`
- Modify: `README.md`

- [ ] Update tests to import `castscribe` modules directly.
- [ ] Add tests that confirm `castscribe.cli.main` is callable and `media_to_text.main` remains a wrapper.
- [ ] Update README examples from `python3 media_to_text.py` to `python3 -m castscribe` and installed `castscribe`.

### Task 4: Verify and Push

**Files:**
- All created and modified project files.

- [ ] Run `python3 -m unittest discover -s tests`.
- [ ] Run `python3 -m py_compile` against package modules and tests.
- [ ] Initialize or reuse git repo, set remote to `git@github.com:longbai/CastScribe.git` or `https://github.com/longbai/CastScribe.git`, commit, and push.
