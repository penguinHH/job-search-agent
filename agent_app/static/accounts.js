// Account picker + new-account guide. Each account has its own data folder; opening one restarts the server for it.
"use strict";

const I18N = {
  zh: {
    title: "选择账号", sub: "每个账号的档案、公司进度、邮件和文书都分别保存，互不可见。",
    newAcct: "新建账号", newSub: "用向导建立你自己的求职档案", last: "上次使用", open: "进入", opening: "正在打开 {name} …",
    back: "返回", next: "下一步", prev: "上一步", create: "创建并进入", creating: "正在创建…", optional: "可选",
    steps: ["账号", "基本信息", "学历与经历", "技能与语言", "求职偏好", "确认"],
    s0: "先给账号起个名字。界面和 agent 都会用它称呼你。", s1: "这些会写进档案的「基本信息」，用于填写表单和文书落款。只填你愿意让 agent 使用的。",
    s2: "每行一条，按时间写。例：2022.04–2027.03 东京大学 博士课程（化学）", s3: "agent 只会使用你在档案里写过的事实，写得越具体，文书越准确。",
    s4: "agent 会按这里的偏好给公司打分、挑选投递对象。", s5: "确认后会创建独立的数据文件夹，并复制一份公开的公司库。以后可以在「档案与知识」里随时修改。",
    name: "姓名（本名）", name_en: "英文 / 罗马字姓名", short_name: "称呼（例：明戈）", nickname: "昵称 / 英文名", avatar: "头像文字（1 个字）",
    tagline: "一句话身份（例：修士 · 2027 新卒）", lang: "界面语言",
    nationality: "国籍", visa: "在留资格 / 签证", location: "现居地", email: "求职用邮箱", phone: "电话",
    education: "学历", experience: "职历 / 实习 / 项目", skills: "研究与技术", publications: "论文与发表", languages: "语言（例：日语 N1）",
    roles: "想做的职位（按优先顺序）", industries: "感兴趣的行业", work_location: "工作地点 / 远程", work_language: "工作语言偏好",
    start: "可入职时间", exclude: "不考虑的方向", cv_text: "粘贴现有简历文本（可选，会存进档案材料）",
    needName: "请填写姓名", summary: "将创建的档案", failed: "失败：", empty: "还没有账号，先新建一个吧。",
  },
  ja: {
    title: "アカウントを選択", sub: "プロフィール、応募状況、メール、書類はアカウントごとに別々に保存され、互いに見えません。",
    newAcct: "新規アカウント", newSub: "ガイドに沿って自分のプロフィールを作成", last: "前回", open: "開く", opening: "{name} を開いています…",
    back: "戻る", next: "次へ", prev: "前へ", create: "作成して開く", creating: "作成中…", optional: "任意",
    steps: ["アカウント", "基本情報", "学歴・経歴", "スキル・語学", "希望条件", "確認"],
    s0: "アカウント名を決めましょう。画面とエージェントがこの名前で呼びかけます。", s1: "プロフィールの基本情報になり、フォーム入力や書類の署名に使われます。使ってよい情報だけ入力してください。",
    s2: "1 行に 1 件、時系列で。例：2022.04–2027.03 東京大学 博士課程（化学）", s3: "エージェントはプロフィールに書かれた事実だけを使います。具体的に書くほど書類が正確になります。",
    s4: "エージェントはこの希望に沿って企業を採点し、応募先を選びます。", s5: "専用のデータフォルダを作り、公開の企業リストをコピーします。あとから「プロフィール」でいつでも編集できます。",
    name: "氏名", name_en: "英語 / ローマ字氏名", short_name: "呼び名", nickname: "ニックネーム", avatar: "アイコン文字（1 文字）",
    tagline: "ひとこと（例：修士 · 2027卒）", lang: "表示言語",
    nationality: "国籍", visa: "在留資格 / ビザ", location: "現住所（市区町村まで）", email: "就活用メール", phone: "電話",
    education: "学歴", experience: "職歴・インターン・プロジェクト", skills: "研究・技術", publications: "論文・発表", languages: "語学（例：英語 TOEIC 900）",
    roles: "希望職種（優先順）", industries: "興味のある業界", work_location: "勤務地 / リモート", work_language: "希望する業務言語",
    start: "入社可能時期", exclude: "検討しない方向", cv_text: "既存の履歴書テキストを貼り付け（任意、資料として保存）",
    needName: "氏名を入力してください", summary: "作成するプロフィール", failed: "失敗：", empty: "アカウントがありません。新規作成してください。",
  },
  en: {
    title: "Choose an account", sub: "Each account keeps its own profile, pipeline, mail and documents — none of it is visible to the others.",
    newAcct: "New account", newSub: "Build your own job-search profile step by step", last: "Last used", open: "Open", opening: "Opening {name} …",
    back: "Back", next: "Next", prev: "Previous", create: "Create and open", creating: "Creating…", optional: "optional",
    steps: ["Account", "Basics", "Education & work", "Skills & languages", "Preferences", "Confirm"],
    s0: "Name your account. The app and the agent will call you by this name.", s1: "This becomes the Basics section of your profile, used for forms and signatures. Only enter what the agent may use.",
    s2: "One entry per line, in order. e.g. 2022.04–2027.03 University of Tokyo, PhD (Chemistry)", s3: "The agent only uses facts written in your profile — the more concrete, the better the documents.",
    s4: "The agent scores companies and picks where to apply based on these preferences.", s5: "A separate data folder is created with a copy of the public company list. You can edit everything later under Profile.",
    name: "Full name", name_en: "Name in English / romaji", short_name: "What to call you", nickname: "Nickname", avatar: "Avatar letter",
    tagline: "One-line identity (e.g. MSc · class of 2027)", lang: "Interface language",
    nationality: "Nationality", visa: "Residence status / visa", location: "Where you live", email: "Job-search e-mail", phone: "Phone",
    education: "Education", experience: "Work, internships, projects", skills: "Research & skills", publications: "Publications", languages: "Languages (e.g. Japanese N2)",
    roles: "Target roles (in order)", industries: "Industries of interest", work_location: "Location / remote", work_language: "Preferred working language",
    start: "Available from", exclude: "Not considering", cv_text: "Paste an existing CV (optional, saved with your materials)",
    needName: "Please enter your name", summary: "Profile to be created", failed: "Failed: ", empty: "No accounts yet — create one.",
  },
};
let LANG = (navigator.language || "zh").slice(0, 2);
if (!I18N[LANG]) LANG = "zh";
const T = (k, v = {}) => String(I18N[LANG][k] ?? I18N.zh[k] ?? k).replace(/\{(\w+)\}/g, (_, x) => v[x] ?? "");

const $ = (s) => document.querySelector(s);
const LOGO = '<svg class="i" viewBox="0 0 24 24"><path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z"/></svg>';
function h(tag, attrs = {}, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === null || v === undefined || v === false) continue;
    if (k === "class") el.className = v;
    else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else if (k === "html") el.innerHTML = v;
    else el.setAttribute(k, v === true ? "" : v);
  }
  for (const kid of kids.flat(Infinity)) if (kid !== null && kid !== undefined && kid !== false) el.append(kid instanceof Node ? kid : String(kid));
  return el;
}
async function api(path, opts = {}) {
  const o = { headers: { "Content-Type": "application/json" }, ...opts };
  if (o.body && typeof o.body !== "string") o.body = JSON.stringify(o.body);
  const r = await fetch(path, o);
  if (!r.ok) { let m = r.statusText; try { m = (await r.json()).detail || m; } catch (_) {} throw new Error(m); }
  return r.json();
}
try { const t = localStorage.getItem("theme"); if (t) document.documentElement.dataset.theme = t; } catch (_) {}

function langSeg(onChange) {
  return h("div", { class: "seg" }, [["zh", "中"], ["ja", "日"], ["en", "EN"]].map(([v, l]) =>
    h("button", { class: LANG === v ? "on" : "", onclick: () => { LANG = v; document.documentElement.lang = v; onChange(); } }, l)));
}

// ------------------------------------------------------------------ picker
async function picker() {
  document.documentElement.lang = LANG;
  const { accounts, last } = await api("/api/accounts");
  const root = $("#root"); root.innerHTML = "";
  const tile = (a) => h("button", { class: "acct-tile", onclick: () => openAccount(a) },
    h("div", { class: "avatar lg" }, a.avatar || "🙂"),
    h("div", { class: "who" }, h("b", {}, [a.name, a.nickname].filter(Boolean).join(" · ")),
      h("small", {}, (a.subtitle || {})[LANG] || a.name_en || "")),
    a.slug === last ? h("span", { class: "badge blue" }, T("last")) : null);
  root.append(
    h("div", { class: "acct-head" }, h("div", { class: "logo", html: LOGO }), h("div", {}, h("h1", {}, T("title")), h("p", { class: "muted" }, T("sub"))), langSeg(picker)),
    h("div", { class: "acct-list" },
      accounts.length ? accounts.map(tile) : h("p", { class: "muted" }, T("empty")),
      h("button", { class: "acct-tile new", onclick: () => guide() },
        h("div", { class: "avatar lg" }, "+"), h("div", { class: "who" }, h("b", {}, T("newAcct")), h("small", {}, T("newSub"))))));
}

async function openAccount(a) {
  $("#root").innerHTML = "";
  $("#root").append(h("div", { class: "acct-wait" }, h("div", { class: "spinner" }), T("opening", { name: a.name })));
  await api(`/api/accounts/${a.slug}/open`, { method: "POST" });
  // the server restarts for this account; wait until the agent answers, then load it
  for (let i = 0; i < 120; i++) {
    await new Promise((r) => setTimeout(r, 700));
    try { const r = await fetch("/api/whoami"); if (r.ok) { location.href = "/"; return; } } catch (_) {}
  }
  location.reload();
}

// ------------------------------------------------------------------ new-account guide
const STEPS = [
  { intro: "s0", fields: [["name", "input", true], ["name_en"], ["short_name"], ["nickname"], ["avatar"], ["tagline"]] },
  { intro: "s1", fields: [["nationality"], ["visa"], ["location"], ["email"], ["phone"]] },
  { intro: "s2", fields: [["education", "textarea"], ["experience", "textarea"]] },
  { intro: "s3", fields: [["skills", "textarea"], ["publications", "textarea"], ["languages", "textarea"]] },
  { intro: "s4", fields: [["roles"], ["industries"], ["work_location"], ["work_language"], ["start"], ["exclude"]] },
  { intro: "s5", fields: [["cv_text", "textarea"]] },
];
const DATA = {};

function guide(step = 0) {
  document.documentElement.lang = LANG;
  const root = $("#root"); root.innerHTML = "";
  const s = STEPS[step];
  const err = h("div", { class: "muted small", style: "color:var(--bad);min-height:20px" });
  const fields = s.fields.map(([key, kind = "input", required]) => {
    const el = kind === "textarea" ? h("textarea", { class: "input", rows: key === "cv_text" ? 8 : 4 }) : h("input", { class: "input" });
    el.value = DATA[key] || "";
    el.addEventListener("input", () => { DATA[key] = el.value; });
    return h("div", { class: "field" }, h("label", {}, T(key), required ? " *" : h("span", { class: "faint" }, ` · ${T("optional")}`)), el);
  });
  const valid = () => { if (step === 0 && !(DATA.name || "").trim()) { err.textContent = T("needName"); return false; } return true; };
  const progress = h("ol", { class: "steps" }, (I18N[LANG].steps || I18N.zh.steps).map((n, i) => h("li", { class: i === step ? "on" : i < step ? "done" : "" }, n)));
  const body = [h("p", { class: "muted" }, T(s.intro)), ...fields];
  if (step === STEPS.length - 1) body.unshift(summary());
  const create = async (btn) => {
    btn.disabled = true; btn.textContent = T("creating");
    try { const a = await api("/api/accounts", { method: "POST", body: { ...DATA, lang: LANG } }); await openAccount(a); }
    catch (e) { err.textContent = T("failed") + e.message; btn.disabled = false; btn.textContent = T("create"); }
  };
  root.append(
    h("div", { class: "acct-head" }, h("div", { class: "logo", html: LOGO }), h("div", {}, h("h1", {}, T("newAcct")), h("p", { class: "muted" }, T("newSub"))), langSeg(() => guide(step))),
    progress,
    h("div", { class: "card guide" }, body, err,
      h("div", { class: "row end" },
        h("button", { class: "btn ghost", onclick: () => (step ? guide(step - 1) : picker()) }, step ? T("prev") : T("back")),
        step < STEPS.length - 1
          ? h("button", { class: "btn primary", onclick: () => valid() && guide(step + 1) }, T("next"))
          : h("button", { class: "btn primary", onclick: (e) => create(e.currentTarget) }, T("create")))));
  root.querySelector("input, textarea")?.focus();
}

function summary() {
  const keys = ["name", "name_en", "tagline", "nationality", "visa", "location", "email", "roles", "start"];
  return h("div", { class: "card summary" }, h("b", {}, T("summary")),
    h("dl", {}, keys.filter((k) => (DATA[k] || "").trim()).map((k) => [h("dt", {}, T(k)), h("dd", {}, DATA[k])])),
    ...["education", "experience", "skills"].filter((k) => (DATA[k] || "").trim()).map((k) =>
      h("div", { class: "small" }, h("span", { class: "muted" }, T(k) + "："), DATA[k].split("\n").filter(Boolean).length + " ✓")));
}

picker().catch((e) => { $("#root").textContent = e.message; });
