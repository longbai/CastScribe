#!/usr/bin/env python3
"""Compatibility wrapper for the CastScribe CLI."""

from castscribe.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
