"""E-posta bildirimi - sadece otomasyon kendi kendini durdurduğunda
kullanılır (bkz. health.py). Binance/MT5/US Signals botlarının
notifier.py'siyle aynı desen (SMTP_SSL, aynı Gmail hesabı).
NOTIFY_EMAIL_ENABLED=false veya kimlik bilgileri eksikse sessizce atlanır
- bildirim gönderilemiyor olması otomasyonu durdurmamalı."""

from __future__ import annotations

import logging
import smtplib
from email.mime.text import MIMEText

from insta_man.config import Config

logger = logging.getLogger("insta_man.notifier")


def send_email(config: Config, subject: str, body: str) -> None:
    if not config.notify_email_enabled:
        return
    if not (config.smtp_user and config.smtp_app_password and config.notify_email_to):
        logger.warning("Bildirim maili atlanıyor: SMTP_USER/SMTP_APP_PASSWORD/NOTIFY_EMAIL_TO eksik.")
        return

    msg = MIMEText(body, _charset="utf-8")
    msg["Subject"] = f"[Instagram Bot] {subject}"
    msg["From"] = config.smtp_from or config.smtp_user
    msg["To"] = config.notify_email_to

    try:
        with smtplib.SMTP_SSL(config.smtp_host, config.smtp_port, timeout=15) as server:
            server.login(config.smtp_user, config.smtp_app_password)
            server.sendmail(msg["From"], [config.notify_email_to], msg.as_string())
    except Exception:
        logger.exception("Bildirim maili gönderilemedi.")
