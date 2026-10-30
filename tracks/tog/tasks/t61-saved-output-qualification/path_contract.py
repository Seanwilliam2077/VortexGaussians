"""Separator compatibility for exactly three frozen T60 evidence destinations."""
from pathlib import Path, PureWindowsPath

ALLOWED = frozenset({'local/checkpoints.jsonl', 'local/reference-evaluation.json',
                     'local/ordinary-model-screen.json'})


def resolve_evidence(root: Path, value: str, expected: str) -> Path:
    if expected not in ALLOWED or not isinstance(value, str) or not value:
        raise ValueError('unlisted or empty evidence path')
    windows = PureWindowsPath(value)
    if windows.drive or windows.root or value.startswith(('/', '\\')) or ':' in value:
        raise ValueError('absolute, drive or UNC evidence path')
    normalized = value.replace('\\', '/')
    if any(part in ('', '.', '..') for part in normalized.split('/')):
        raise ValueError('empty, dot or parent path component')
    if normalized != expected:
        raise ValueError('evidence destination does not match its exact allowlist entry')
    root = Path(root).resolve()
    destination = root.joinpath(*normalized.split('/')).resolve()
    if not destination.is_relative_to(root):
        raise ValueError('resolved evidence path escapes the expected directory')
    return destination
