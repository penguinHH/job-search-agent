"""Form-filling assistant: drives a visible Chrome window via Playwright.

The agent can open pages, read form fields, fill / select / check / upload, and click
ordinary buttons. Anything that submits an application goes through the approval queue,
and CAPTCHAs, logins and account creation are left to the user (they see the same window).
Playwright's sync API must stay on one thread, so all calls are marshalled to a worker thread.
"""
import queue
import threading
from pathlib import Path

from . import store

PROFILE_DIR = store.HOME / "data" / "browser_profile"
SUBMIT_WORDS = ("submit", "apply", "send", "送信", "応募", "提出", "登録", "エントリー", "確定", "完了", "申し込")

SNAPSHOT_JS = r"""
() => {
  const out = [];
  let n = 0;
  const vis = e => !!(e.offsetParent || e.type === 'file' || e.getClientRects().length);
  const labelOf = e => {
    let t = '';
    if (e.id) { const l = document.querySelector(`label[for="${CSS.escape(e.id)}"]`); if (l) t = l.innerText; }
    if (!t && e.closest('label')) t = e.closest('label').innerText;
    if (!t) t = e.getAttribute('aria-label') || e.placeholder || '';
    if (!t || t.length < 2) {
      const box = e.closest('li,tr,dl,fieldset,[role=listitem],p,div');
      t = (box && box.innerText || '').trim();
    }
    if (!t) t = e.name || '';
    return t.replace(/\s+/g, ' ').slice(0, 120);
  };
  for (const e of document.querySelectorAll('input,textarea,select,button,[role=button],[role=checkbox],[role=radio],a[href]')) {
    if (e.tagName === 'INPUT' && e.type === 'hidden') continue;
    if (e.tagName === 'A' && !/応募|apply|entry|エントリー|next|次へ/i.test(e.innerText)) continue;
    if (!vis(e)) continue;
    const id = 'a' + (n++);
    e.setAttribute('data-agent-id', id);
    const f = {id, tag: e.tagName.toLowerCase(), type: e.type || e.getAttribute('role') || '', label: labelOf(e)};
    if (e.tagName === 'SELECT') f.options = [...e.options].map(o => o.text.trim()).slice(0, 60);
    if ('value' in e && e.type !== 'file' && e.tagName !== 'BUTTON') f.value = String(e.value || '').slice(0, 80);
    if (e.type === 'checkbox' || e.type === 'radio') { f.checked = e.checked; f.value = e.value; }
    if (e.getAttribute('aria-checked')) f.checked = e.getAttribute('aria-checked') === 'true';
    if (e.tagName === 'BUTTON' || e.tagName === 'A' || e.type === 'submit' || e.getAttribute('role') === 'button')
      f.text = (e.innerText || e.value || '').trim().slice(0, 60);
    if (e.required) f.required = true;
    out.push(f);
  }
  const captcha = !!document.querySelector('iframe[src*="recaptcha"],iframe[src*="turnstile"],.cf-turnstile,.g-recaptcha,[data-sitekey]');
  return {url: location.href, title: document.title, captcha, fields: out.slice(0, 250),
          text: document.body.innerText.replace(/\s+/g, ' ').slice(0, 3000)};
}
"""


class BrowserWorker:
    def __init__(self):
        self.q = queue.Queue()
        self.thread = None
        self.ctx = None
        self.page = None

    def _run(self):
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            PROFILE_DIR.mkdir(parents=True, exist_ok=True)
            try:
                self.ctx = p.chromium.launch_persistent_context(str(PROFILE_DIR), channel="chrome", headless=False,
                                                                viewport=None, args=["--start-maximized"])
            except Exception:
                self.ctx = p.chromium.launch_persistent_context(str(PROFILE_DIR), headless=False, viewport=None)
            self.page = self.ctx.pages[0] if self.ctx.pages else self.ctx.new_page()
            while True:
                fn, box, ev = self.q.get()
                if fn is None:
                    break
                try:
                    box["result"] = fn()
                except Exception as e:  # noqa: BLE001 - returned to the agent as an error string
                    box["error"] = f"{type(e).__name__}: {e}"
                ev.set()
            self.ctx.close()

    def call(self, fn, timeout=120):
        if not self.thread or not self.thread.is_alive():
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()
        box, ev = {}, threading.Event()
        self.q.put((fn, box, ev))
        if not ev.wait(timeout):
            raise TimeoutError("browser did not respond")
        if "error" in box:
            raise RuntimeError(box["error"])
        return box.get("result")

    # ------------------------------------------------------------- operations
    def _current(self):
        pages = [p for p in self.ctx.pages if not p.is_closed()]
        self.page = pages[-1] if pages else self.ctx.new_page()   # follow tabs the site opened
        return self.page

    def open(self, url):
        def f():
            pg = self._current()
            pg.goto(url, wait_until="domcontentloaded", timeout=60000)
            pg.wait_for_timeout(1500)
            return pg.evaluate(SNAPSHOT_JS)
        return self.call(f)

    def snapshot(self):
        return self.call(lambda: self._current().evaluate(SNAPSHOT_JS))

    def _loc(self, fid):
        return self._current().locator(f'[data-agent-id="{fid}"]').first

    def fill(self, fid, value):
        def f():
            loc = self._loc(fid)
            loc.fill(value, timeout=10000)
            return {"ok": True}
        return self.call(f)

    def select(self, fid, option):
        def f():
            self._loc(fid).select_option(label=option, timeout=10000)
            return {"ok": True}
        return self.call(f)

    def check(self, fid, checked=True):
        def f():
            loc = self._loc(fid)
            tag = loc.evaluate("e => e.tagName")
            if tag == "INPUT":
                loc.set_checked(checked, timeout=10000, force=True)
            else:
                loc.click(timeout=10000)
            return {"ok": True}
        return self.call(f)

    def upload(self, fid, paths):
        def f():
            files = [str(store.HOME / p) if (store.HOME / p).exists() else str(Path(p)) for p in paths]
            self._loc(fid).set_input_files(files, timeout=10000)
            return {"ok": True, "files": files}
        return self.call(f)

    def click(self, fid):
        def f():
            pg = self._current()
            self._loc(fid).click(timeout=15000)
            pg.wait_for_timeout(2500)
            return self._current().evaluate(SNAPSHOT_JS)
        return self.call(f)

    def screenshot(self):
        def f():
            path = store.HOME / "data" / "browser_last.png"
            self._current().screenshot(path=str(path))
            return str(path)
        return self.call(f)

    @staticmethod
    def looks_like_submit(field):
        t = f"{field.get('text', '')} {field.get('label', '')} {field.get('type', '')}".lower()
        return field.get("type") == "submit" or any(w.lower() in t for w in SUBMIT_WORDS)


browser = BrowserWorker()
