import asyncio, json, re, time, random, aiohttp
from playwright.async_api import async_playwright, TimeoutError

with open("cfg.json", "r", encoding="utf-8") as f:
    config = json.load(f)

flags = config["flags"]
flags["notifications"]["seen"] = set(flags["notifications"]["seen"])

SUCCESS_URL = config["SUCCESS_URL"].rstrip("/")
TELEGRAM_TOKEN = config["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = config["TELEGRAM_CHAT_ID"]
LOGIN = config["LOGIN"]
PASSWORD = config["PASSWORD"]

async def send_telegram(session, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        async with session.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text}, timeout=10) as resp:
            if resp.status != 200:
                print(f"❌ Ошибка Telegram API: Статус {resp.status}")
    except Exception as e:
        print(f"❌ Ошибка отправки в Telegram: {e}")

async def generate_gemini_reply(session, gemini_cfg, context_text):
    api_key = gemini_cfg.get("api_key")
    role = gemini_cfg.get("role", "Ты пользователь форума, вежливо и коротко ответь на сообщение.")
    if not api_key:
        return None

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={api_key}"
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": f"Системная инструкция / роль: {role}\n\nСообщение с форума, на которое нужно ответить:\n{context_text}"}
                ]
            }
        ]
    }
    try:
        async with session.post(url, json=payload, timeout=12) as resp:
            if resp.status == 200:
                data = await resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                return text
            print(f"❌ Ошибка Gemini API: Статус {resp.status}")
    except Exception as e:
        print(f"❌ Ошибка запроса к Gemini: {e}")
    return None

async def handle_2fa(page):
    if not await page.query_selector('h1:has-text("Требуется двухфакторная аутентификация")'):
        return True
    print("\033[1m🔐 Обнаружена 2FA!\033[0m")
    prov = "email" if await page.query_selector('a[href*="provider=email"]') else "Google"
    code = input(f"\033[1mВведите код 2FA ({prov}): \033[0m")
    await page.fill('input[name="code"]', code)
    await page.click('button:has-text("Подтвердить")')
    try:
        await page.wait_for_url(f"{SUCCESS_URL}*", timeout=8000)
        return True
    except TimeoutError:
        print("\033[1m❌ Неверный код 2FA!\033[0m")
        return False

async def check_notifs(page, http_session):
    try:
        with open("cfg.json", "r", encoding="utf-8") as f:
            cfg = json.load(f)
            auto_reply = cfg.get("flags", {}).get("reply", True)
            responses = cfg.get("random_responses", ["Спасибо за сообщение!"])
            gemini_cfg = cfg.get("gemini", {})
    except Exception:
        auto_reply, responses, gemini_cfg = flags.get("reply", True), ["Спасибо за сообщение!"], {}

    await page.goto(f"{SUCCESS_URL}/account/alerts", wait_until="domcontentloaded")

    alerts = []
    for it in await page.query_selector_all("li[data-alert-id]"):
        aid = await it.get_attribute("data-alert-id")
        if aid not in flags["notifications"]["seen"]:
            link = await it.query_selector("a.fauxBlockLink-blockLink")
            rel_url = await link.get_attribute("href") if link else None
            text = re.sub(r'^[A-Za-z0-9]\s+', '', (await it.inner_text()).replace("\n", " ").strip())
            alerts.append({"id": aid, "text": text, "rel_url": rel_url})

    for alert in alerts:
        aid, text, rel_url = alert["id"], alert["text"], alert["rel_url"]
        flags["notifications"]["seen"].add(aid)
        print(f"\033[1m[{time.strftime('%H:%M:%S')}] 📣 Новое уведомление: {text}\033[0m")

        if not rel_url:
            await send_telegram(http_session, f"📣 Новое уведомление:\n{text}")
            continue

        full_url = (SUCCESS_URL + rel_url) if rel_url.startswith("/") else rel_url
        try:
            await page.goto(full_url, wait_until="domcontentloaded")
        except Exception as e:
            print("❌ Ошибка перехода:", e)
            continue

        nick_m = re.match(r'^(.*?) (ответил|стал|упомянул|оставил|написал)', text)
        nick_name = re.sub(r'^[A-Za-z0-9]\s+', '', nick_m.group(1).strip()) if nick_m else "Система"

        post_m = re.search(r'posts[=/](\d+)', full_url)
        post_id = post_m.group(1) if post_m else None

        prof_m = re.search(r'profile-posts[=/](\d+)', full_url)
        prof_id = prof_m.group(1) if prof_m else None

        message_text, member_id = "", "1"

        if post_id:
            el = await page.query_selector(f'#js-post-{post_id}, article[data-content="post-{post_id}"]')
            if el:
                msg_el = await el.query_selector('div.message-userContent div.bbWrapper, div.bbWrapper')
                if msg_el: message_text = (await msg_el.inner_text()).strip()
                user_a = await el.query_selector('a[data-user-id]')
                if user_a: member_id = await user_a.get_attribute("data-user-id")
        elif prof_id or "profile-posts" in full_url:
            el = await page.query_selector(f'#js-profilePost-{prof_id}' if prof_id else 'article.message--simple')
            if el:
                msg_el = await el.query_selector('article.message-body div.bbWrapper, div.bbWrapper')
                if msg_el: message_text = (await msg_el.inner_text()).strip()

        if not message_text:
            try:
                msg_el = await page.query_selector('article.message-body div.bbWrapper, div.bbWrapper')
                if msg_el: message_text = (await msg_el.inner_text()).strip()
            except Exception: pass

        tg_msg = f"🔔 Уведомление: {text}\n\n"
        if message_text: tg_msg += f"💬 Текст:\n{message_text}\n\n"
        tg_msg += f"🔗 Ссылка: {full_url}"
        await send_telegram(http_session, tg_msg)

        if not auto_reply:
            continue

        reply = None
        if gemini_cfg.get("enabled", False):
            prompt_context = message_text if message_text else text
            reply = await generate_gemini_reply(http_session, gemini_cfg, prompt_context)

        if not reply:
            reply = random.choice(responses)

        if prof_id or "profile-posts" in full_url:
            try:
                container = await page.query_selector(f'#js-profilePost-{prof_id}' if prof_id else 'article.message--simple') or page
                ph = await container.query_selector('.editorPlaceholder-placeholder, div[data-xf-click="editor-placeholder"]')
                if ph:
                    await ph.click()
                    await page.wait_for_timeout(200)

                inp = None
                for sel in ["div[contenteditable='true']", "textarea[name='message_html']", "textarea[name='message']", "textarea.input"]:
                    target = await container.query_selector(sel)
                    if target and await target.is_visible():
                        inp = target
                        break

                if inp:
                    if await inp.get_attribute("contenteditable") == "true":
                        await inp.fill(reply)
                    else:
                        await inp.type(reply)

                    btn = await container.query_selector('form[action*="add-comment"] button[type="submit"]')
                    if btn:
                        await btn.click()
                        print("💬 Комментарий в профиле отправлен!")
                        await page.wait_for_timeout(500)
                        continue
            except Exception as e:
                print("❌ Ошибка ответа в профиле:", e)

        editor = await page.query_selector("div[contenteditable='true'], textarea[name='message']")
        if editor and await editor.is_visible():
            try:
                await editor.click()
                if await editor.get_attribute("contenteditable") == "true" and post_id:
                    await editor.fill(f'[QUOTE="{nick_name}, post: {post_id}, member: {member_id}"]\n{message_text}\n[/QUOTE]\n{reply}')
                else:
                    await editor.fill(reply)

                for sel in ["button.button--primary.button--icon--reply", "button.button--primary", "button[type='submit']"]:
                    try:
                        await page.click(sel, timeout=800)
                        print("💬 Ответ в теме отправлен!")
                        break
                    except Exception: continue
                await page.wait_for_timeout(500)
            except Exception as e:
                print("❌ Ошибка ответа в теме:", e)

async def run():
    async with aiohttp.ClientSession() as http_session:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            print("\033[1m🌐 Авторизация...\033[0m")
            await page.goto(f"{SUCCESS_URL}/login/")
            await page.fill('input[name="login"]', LOGIN)
            await page.fill('input[name="password"]', PASSWORD)
            await page.click('button:has-text("Войти")')

            try:
                await page.wait_for_url(f"{SUCCESS_URL}*", timeout=5000)
            except TimeoutError:
                if "login" in page.url:
                    print("\033[1m❌ Неверный логин или пароль в cfg.json!\033[0m")
                    return

            if not await handle_2fa(page):
                return

            print("\033[1m✅ Мониторинг запущен...\033[0m")
            await page.goto(f"{SUCCESS_URL}/account/alerts")
            
            for it in await page.query_selector_all("li[data-alert-id]"):
                flags["notifications"]["seen"].add(await it.get_attribute("data-alert-id"))

            while True:
                await check_notifs(page, http_session)
                await asyncio.sleep(2.5)

if __name__ == "__main__":
    try:
        asyncio.run(run())
    except Exception as e:
        print(f"\033[1m❌ Произошла ошибка: {e}\033[0m")
