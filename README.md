# Insta_man

Instagram content scheduling and hashtag automation toolkit.

Full documentation, architecture, setup checklist and risk disclosures are
in [`CLAUDE.md`](./CLAUDE.md) — start there.

## Quick start

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -e .                # installs insta_man itself so `python -m insta_man.cli` works
cp .env.example .env            # fill in your credentials
cp content_library/queue.example.yaml content_library/queue.yaml  # add real posts

python -m insta_man.cli validate
python -m insta_man.cli list
python -m insta_man.cli run     # publishes whatever is due now
```

## Tests

```bash
pytest
```

## Diğer

- [`game/`](./game) — bağımsız, tarayıcı tabanlı bir HTML5 oyunu (Instagram
  otomasyonundan ayrı, ilgisiz).
- [`android-app/`](./android-app) — `game/`'i Google Play'e çıkarmak için
  Capacitor ile sarılmış Android projesi; kurulum ve yayınlama adımları
  için `android-app/README.md`'ye bak.
