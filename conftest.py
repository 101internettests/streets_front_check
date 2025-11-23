import os
import pytest
# import allure
import time
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, Error as PlaywrightError
# Загружаем переменные окружения из .env файла
load_dotenv()


@pytest.fixture(scope="session")
def browser_fixture():
    """
    Фикстура для создания и управления браузером.
    Режим headless контролируется через .env файл
    """
    # Получаем значение HEADLESS из .env (по умолчанию True если не указано)
    headless = os.getenv("HEADLESS", "True").lower() == "true"

    with sync_playwright() as playwright:
        # Запускаем браузер с нужными настройками
        args = []
        # Полноэкранный режим для headed (в headless не влияет, но не мешает)
        if (os.getenv("FULLSCREEN", "true").lower() in ("1", "true", "yes")):
            args.append("--start-maximized")
        browser = playwright.chromium.launch(headless=headless, args=args)
        yield browser
        browser.close()


@pytest.fixture(scope="function")
def browser_fixture_ignore_https():
    """
    Фикстура для создания браузера с игнорированием ошибок HTTPS
    """
    headless = os.getenv("HEADLESS", "True").lower() == "true"

    with sync_playwright() as playwright:
        # Запускаем браузер с отключенной проверкой сертификатов
        browser = playwright.chromium.launch(
            headless=headless,
            ignore_https_errors=True
        )
        yield browser
        browser.close()


@pytest.fixture(scope="session")
def context_fixture(browser_fixture):
    """
    Фикстура для создания новой страницы в браузере
    """
    # Создаем контекст один раз на сессию, с опциональной блокировкой ассетов
    block_assets = (os.getenv("BLOCK_ASSETS") or "").lower() in ("1","true","yes")
    # Размеры окна/вьюпорта
    try:
        vp_w = int((os.getenv("VIEWPORT_WIDTH") or "1920").strip())
        vp_h = int((os.getenv("VIEWPORT_HEIGHT") or "1080").strip())
    except Exception:
        vp_w, vp_h = 1920, 1080

    context = browser_fixture.new_context(viewport={"width": vp_w, "height": vp_h})
    if block_assets:
        # Abort heavy resources by resource type (keep stylesheets to avoid layout/visibility issues)
        def _asset_blocker(route):
            try:
                rtype = route.request.resource_type
                if rtype in ("image", "media", "font"):
                    return route.abort()
            except Exception:
                pass
            return route.continue_()

        context.route("**/*", _asset_blocker)
    yield context
    context.close()


@pytest.fixture(scope="function")
def page_fixture(context_fixture):
    page = context_fixture.new_page()
    yield page
    page.close()


@pytest.fixture(scope="function")
def page_fixture_ignore_https(browser_fixture_ignore_https):
    """
    Фикстура для создания страницы с игнорированием ошибок HTTPS
    """
    context = browser_fixture_ignore_https.new_context(ignore_https_errors=True)
    page = context.new_page()
    yield page
    context.close()


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    # Сообщения после прохода отключены. Оставлен пустой хук.
    return