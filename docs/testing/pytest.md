# Pytest Guidance

## Running
```
python -m pytest
```

## Live Tests (Optional)
- Live Azure tests should be **skipped by default**.
- Enable with an explicit flag, e.g. `RUN_LIVE_AZURE=1`.

## Safety
- Never log raw tokens.
- Use fixture claim JSON for offline assertions.
