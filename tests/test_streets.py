# import allure
import time

import pytest
from urllib.parse import urlparse, parse_qs
from main_steps import MainSteps
from locators import LocationPopup
from playwright.sync_api import Error as PlaywrightError
from google_sheets import append_row_to_sheet
import os


class TestForms:
    # "1. Отправка заявки из  попапа Выгодное спецпредложение! по нажатию фиксированной красной кнопки звонка в правом нижнем углу")
    def test_streets(self, page_fixture, example_url):
        page = page_fixture
        page.goto(example_url)
        steps = MainSteps(page=page)
        try:
           if page.locator(LocationPopup.YES_BUTTON).count() > 0:
            steps.close_popup_location()
        except Exception:
            pass
        steps.close_cookie()
        steps.open_popup_for_colorful_button()
        # избегаем лишних задержек, опираемся на обработчик response ниже
        # "Перехватить запрос и ответ API улиц"
        # Динамически формируем endpoint для текущего домена (например rtk-ru.online, mts-home.online)
        parsed_example = urlparse(example_url)
        base = f"{parsed_example.scheme or 'https'}://{parsed_example.netloc}"
        endpoint = f"{base}/wp-json/cf7proxy/v1/streets"
        # Ожидаем ответ от ручки подсказок улиц (домен/путь могут отличаться)
        streets_path = "/wp-json"
        try:
            timeout_ms = int((os.getenv("STREETS_TIMEOUT_MS") or "20000").strip())
        except Exception:
            timeout_ms = 20000
        if (os.getenv("DEBUG_STREETS") or "").lower() in ("1", "true", "yes"):
            print(f"[Streets] Waiting for response containing '{streets_path}' and 'streets' with timeout {timeout_ms} ms")
        resp = None
        req = None
        # Слушаем все ответы на время ввода
        caught_responses = []
        def _on_response(r):
            try:
                if r.request.method in ("GET","POST") and (streets_path in r.url) and ("streets" in r.url):
                    caught_responses.append(r)
                    if (os.getenv("DEBUG_STREETS") or "").lower() in ("1", "true", "yes"):
                        print(f"[Streets] Caught response: {r.url} (status={r.status})")
            except Exception:
                pass
        page.on("response", _on_response)
        try:
            steps.send_popup_profit()
            try:
                listen_ms = int((os.getenv("STREETS_LISTEN_MS") or "4000").strip())
            except Exception:
                listen_ms = 3000
            page.wait_for_timeout(listen_ms)
            if caught_responses:
                resp = caught_responses[-1]
                req = resp.request
                if (os.getenv("DEBUG_STREETS") or "").lower() in ("1", "true", "yes"):
                    print(f"[Streets] Using last response: {resp.url}")
            else:
                if (os.getenv("DEBUG_STREETS") or "").lower() in ("1", "true", "yes"):
                    print("[Streets] No matching responses collected during typing")
        finally:
            try:
                page.off("response", _on_response)
            except Exception:
                pass

        region_id = ""
        query_val = ""
        city = ""
        if req is not None:
            parsed = urlparse(req.url)
            qs = parse_qs(parsed.query)
            region_id = (qs.get("region_id", [""])[0] or "").strip()
            query_val = (qs.get("query", [""])[0] or "").strip()
        else:
            try:
                cookies_str = page.evaluate("document.cookie") or ""
                parts = [p.strip() for p in cookies_str.split(";") if p.strip()]
                jar = {}
                for p in parts:
                    if "=" in p:
                        k, v = p.split("=", 1)
                        jar[k.strip()] = v.strip()
                region_id = (jar.get("region_id") or "").strip()
                query_val = (jar.get("query") or "").strip()
            except Exception:
                region_id = region_id or ""
                query_val = query_val or ""

        # Пытаемся определить город из JSON ответа (если он есть)
        if resp is not None:
            try:
                payload = resp.json()
                items = payload.get("data") or []
                if items:
                    subtitle = (items[0].get("subtitle") or "").strip()
                    if subtitle:
                        city = subtitle.split(",")[0].strip()
            except Exception:
                city = city or ""

            # Параметры Google Sheets
        spreadsheet_id = (os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID") or os.getenv("SPREADSHEET_ID") or "").strip()
        worksheet_name = (os.getenv("GOOGLE_SHEETS_WORKSHEET") or "Итоги3").strip() or "Итоги3"
        assert spreadsheet_id, "Не указан SPREADSHEET_ID или GOOGLE_SHEETS_SPREADSHEET_ID в .env"

        # Формат записи: url, city, region_id, query — собираем для батч-записи в конце сессии
        try:
            add_row = globals().get("collect_row") or None
        except Exception:
            add_row = None
        # Если фикстура недоступна через globals (pytest контекст), пробуем через request, иначе запишем напрямую
        try:
            from inspect import currentframe
            frame = currentframe()
            req = frame.f_locals.get("request") if frame else None
            if (not add_row) and req and hasattr(req.session, "_collected_rows"):
                def add_row(row):
                    req.session._collected_rows.append(row)
        except Exception:
            pass

        row = [example_url, city, region_id, query_val]
        if callable(add_row):
            add_row(row)
        else:
            append_row_to_sheet(
                spreadsheet_id=spreadsheet_id,
                worksheet_name=worksheet_name,
                values=row,
            )
