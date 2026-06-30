from __future__ import annotations

import logging
import time
from urllib.parse import quote

import aiohttp
from bs4 import BeautifulSoup
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .const import BASE_URL

_LOGGER = logging.getLogger(__name__)


class AladdinAuthError(Exception):
    """Raised when authentication fails."""


class AladdinConnectionError(Exception):
    """Raised on network issues."""


class AladdinApiClient:
    def __init__(self, hass, username: str, password: str, school_id: str) -> None:
        self._hass = hass
        self._username = username
        self._password = password
        self._school_id = school_id
        self._session: aiohttp.ClientSession | None = None

    async def _ensure_session(self) -> None:
        if self._session is None or self._session.closed:
            self._session = async_create_clientsession(self._hass)

    async def async_login(self) -> None:
        await self._ensure_session()
        url = f"{BASE_URL}/signin/{self._school_id}"
        payload = (
            f"url=%2F%3Fp%3Dq"
            f"&username={quote(self._username)}"
            f"&password={quote(self._password)}"
            f"&block=&oauth_token="
        )
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        try:
            async with self._session.post(url, data=payload, headers=headers) as resp:
                resp.raise_for_status()
        except aiohttp.ClientError as err:
            raise AladdinConnectionError(f"Login request failed: {err}") from err

        cookies = self._session.cookie_jar.filter_cookies(url)
        if "sessionid" not in cookies or "xsd" not in cookies:
            raise AladdinAuthError("Login failed: sessionid or xsd cookie not found")

    async def async_get_notifications(self) -> list[dict]:
        await self._ensure_session()
        url = f"{BASE_URL}/notifications"
        params = {
            "get_notifications": "y",
            "_": str(int(time.time() * 1000)),
        }

        try:
            async with self._session.get(url, params=params) as resp:
                resp.raise_for_status()
                data = await resp.json()
        except aiohttp.ClientError as err:
            raise AladdinConnectionError(
                f"Notifications request failed: {err}"
            ) from err
        except (ValueError, TypeError) as err:
            raise AladdinAuthError(
                "Non-JSON response, session may have expired"
            ) from err

        html = data.get("html", "")
        return self._parse_notifications(html)

    def _parse_notifications(self, html: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        notifications = []

        for container in soup.select("div.thumbnail_container.notification"):
            notif_id = (
                container.get("id", "")
                .replace("not_", "")
                .replace("_parent", "")
            )

            from_name = container.select_one("span.noti_from")
            from_name = from_name.get_text(strip=True) if from_name else None

            preview_snip = container.select_one("span.noti_text_snip")
            preview_snip = preview_snip.get_text(strip=True) if preview_snip else None

            timestamp = container.select_one("span.not_shorttime")
            timestamp = timestamp.get_text(strip=True) if timestamp else None

            full_text_div = container.select_one(
                "div.noti_text_expanded div.text p"
            )
            full_text = (
                full_text_div.get_text(strip=True) if full_text_div else None
            )

            to_span = container.select_one("span.noti_to")
            to_val = to_span.get_text(strip=True) if to_span else None

            sent_p = container.select_one("p.not_fulltime")
            sent_time = None
            if sent_p:
                b = sent_p.find("b")
                if b:
                    sent_time = b.get_text(strip=True).replace("Sent: ", "")

            notifications.append({
                "id": notif_id,
                "from": from_name,
                "to": to_val,
                "timestamp": sent_time or timestamp,
                "preview": preview_snip,
                "full_text": full_text,
            })

        return notifications

    async def async_close(self) -> None:
        if self._session is not None and not self._session.closed:
            await self._session.close()
