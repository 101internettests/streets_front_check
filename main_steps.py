import time
try:
    import allure
except Exception:
    class _AllureStub:
        def title(self, *_args, **_kwargs):
            def _decorator(func):
                return func
            return _decorator

        class step:
            def __init__(self, *_args, **_kwargs):
                pass

            def __enter__(self):
                return None

            def __exit__(self, exc_type, exc, tb):
                return False

    allure = _AllureStub()

from locators import LocationPopup, Profit
from base_page import BasePage


class MainSteps(BasePage):
    @allure.title("Закрыть баннер cookies при наличии")
    def close_cookie(self):
        # Быстрый упрощенный клик без долгих ожиданий
        candidates: list[str] = []
        if hasattr(Profit, "ACCEPT_COOKIES"):
            candidates.append(getattr(Profit, "ACCEPT_COOKIES"))
        # Универсальная кнопка согласия/cookie
        candidates.append(
            "xpath=//button[contains(translate(., 'COOKIE', 'cookie'),'cookie') or contains(.,'Принять') or contains(.,'Соглас') or contains(.,'Ок') or contains(.,'OK')][1]"
        )

        for sel in candidates:
            if not sel:
                continue
            loc = self.page.locator(sel).first
            try:
                if loc.count() == 0:
                    continue
            except Exception:
                continue
            try:
                loc.click(timeout=500)
                return
            except Exception:
                try:
                    loc.click(force=True, timeout=250)
                    return
                except Exception:
                    try:
                        loc.evaluate("el => el.click()")
                        return
                    except Exception:
                        continue

    @allure.title("Ответить в всплывашке, что нахожусь в Москве")
    def close_popup_location(self):
        self.page.locator(LocationPopup.YES_BUTTON).click()

    @allure.title("Нажать на плавающую красную кнопку с телефоном в правом нижнем углу")
    def open_popup_for_colorful_button(self):
        btn = self.page.locator(Profit.COLORFUL_BUTTON).first
        try:
            btn.wait_for(state="visible", timeout=5000)
        except Exception:
            pass
        try:
            btn.scroll_into_view_if_needed(timeout=1000)
        except Exception:
            pass
        try:
            btn.click(timeout=2000)
            return
        except Exception:
            try:
                btn.click(force=True, timeout=1000)
                return
            except Exception:
                try:
                    btn.evaluate("el => el.click()")
                    return
                except Exception:
                    self.page.wait_for_timeout(300)
                    btn.click(force=True, timeout=1000)

    @allure.title("Начать вписывать улицу")
    def send_popup_profit(self):
        with allure.step("Заполнить попап и отправить заявку"):
            self.page.locator(Profit.STREET).type("Лени", delay=0)

    @allure.title("Начать вписывать улицу ртк")
    def send_rtk(self):
        with allure.step("Заполнить попап и отправить заявку"):
            self.page.locator(Profit.RTK_STREET).type("Лени", delay=0)
