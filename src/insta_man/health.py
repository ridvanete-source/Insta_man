"""Devre kesici (circuit breaker) - tekrarlanan publish hatalarına karşı.

2026-09-08'de bulunan gerçek olay: session geçersiz olduğunda hem VPS timer
hem GitHub Actions cron'u her saatlik çalıştırmada sessizce başarısız oluyor,
Instagram'ın login endpoint'ini 100+ kez döverek 429/rate-limit'e sebep
oluyordu - kimseye haber gitmiyordu, 57+ saat fark edilmedi. Bu modül:

1. Art arda FAILURE_THRESHOLD başarısız çalıştırmadan sonra otomasyonu
   kendi kendine durdurur (yeni login denemesi yapmaz - rate limit'i
   kötüleştirmez).
2. Eşik aşıldığında BİR KEZ e-posta uyarısı gönderir (her çalıştırmada
   tekrar tekrar değil).
3. Durum content_library/health_state.json'a yazılır ve queue.yaml ile
   aynı şekilde git'e commit'lenir - VPS/GitHub Actions/yerel makine
   arasında paylaşılan tek bir sayaç olsun diye (hangisi önce fark ederse
   o bildirir, diğeri sessiz kalır).

Sorun çözülünce content_library/health_state.json silinmeli (ya da
consecutive_failures'ı elle 0 yapılmalı) ki otomasyon tekrar denemeye
başlasın - run_and_sync.sh/.ps1 ve auto-post.yml bunu otomatik yapmaz,
kasıtlı olarak elle bir "sorun çözüldü" onayı gerektirir.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from insta_man import notifier
from insta_man.config import Config

HEALTH_FILE = Path("content_library/health_state.json")
FAILURE_THRESHOLD = 3  # art arda kaç başarısız çalıştırmadan sonra durup uyarılsın


@dataclass
class HealthState:
    consecutive_failures: int = 0
    last_error: str | None = None
    last_failure_at: str | None = None
    notified_at: str | None = None  # bu kesinti için uyarı gönderildiyse doldurulur


def _load() -> HealthState:
    if HEALTH_FILE.exists():
        return HealthState(**json.loads(HEALTH_FILE.read_text(encoding="utf-8")))
    return HealthState()


def _save(state: HealthState) -> None:
    HEALTH_FILE.parent.mkdir(parents=True, exist_ok=True)
    HEALTH_FILE.write_text(json.dumps(asdict(state), indent=2, ensure_ascii=False), encoding="utf-8")


def should_skip_run() -> HealthState | None:
    """Eşik aşılmış VE zaten bildirim gönderilmişse mevcut durumu döner
    (çağıran bu durumda hiç run_once() denemesin, yeni login denemesi
    yapmasın) - aksi halde None döner (normal çalıştırmaya devam)."""
    state = _load()
    if state.consecutive_failures >= FAILURE_THRESHOLD and state.notified_at:
        return state
    return None


def record_success() -> None:
    _save(HealthState())  # tam sıfırlama - bir sonraki kesintide tekrar bildirebilsin


def record_failure(config: Config, error: str) -> None:
    state = _load()
    state.consecutive_failures += 1
    state.last_error = error[:500]
    state.last_failure_at = datetime.now(timezone.utc).isoformat()
    if state.consecutive_failures >= FAILURE_THRESHOLD and not state.notified_at:
        state.notified_at = datetime.now(timezone.utc).isoformat()
        notifier.send_email(
            config,
            "Otomasyon durdu (art arda hata)",
            f"{state.consecutive_failures} art arda başarısız çalıştırma sonrası "
            f"Instagram otomasyonu kendi kendini durdurdu - yeni login denemesi "
            f"yapmayacak (rate limit'i kötüleştirmemek için).\n\n"
            f"Son hata:\n{state.last_error}\n\n"
            f"Muhtemel sebep: .ig_session.json geçersiz oldu. Düzeltmek için: "
            f"session'ı manuel yeniden oluşturun (2FA gerekebilir), sonra "
            f"content_library/health_state.json dosyasını silin/sıfırlayın ki "
            f"otomasyon tekrar denemeye başlasın.",
        )
    _save(state)
