// Job Agent – single-page frontend (no build step). UI in 中文 / 日本語 / English.
"use strict";

// ================================================================== i18n
const I18N = {
  zh: {
    brand: "求职 Agent", brandSub: "日本科技创业公司求职",
    nav_dashboard: "总览", nav_chat: "Agent 对话", nav_approvals: "待审批", nav_pipeline: "进度看板", nav_companies: "公司库",
    nav_notes: "笔记", notesSub: "学习笔记、面试笔记和总的待办清单。agent 和 Claude Code 都会读写这里。", tab_study: "学习笔记", tab_interview: "面试笔记", tab_todo: "待办总览", noteStudy: "学习笔记", noteInterview: "面试笔记", noNotes: "还没有笔记", markDone: "标记完成", reopen: "重新打开", editNote: "编辑", saveNote: "保存", cancel: "取消", newNote: "新建笔记", noteTitle: "标题", noteCompany: "关联公司 ID（可空）", noteDue: "截止（可空）", done: "已完成", openN: "{n} 项未完成", general: "通用", hasStudy: "有学习笔记", hasInterview: "有面试笔记", prepNotes: "让 agent 更新笔记",
    rv_title: "文书审查", rv_running: "审查 agent 检查中…", rv_ok: "审查通过，没有发现问题", rv_n: "{n} 条修改建议", rv_applied: "已应用修改", rv_auto: "已自动修改（可撤销）", rv_failed: "审查失败", rv_dismissed: "已忽略", rv_applySel: "应用所选", rv_applyAll: "全部采用修订版", rv_dismiss: "忽略", rv_revert: "撤销修改", rv_showRevised: "查看修订版全文", rv_run: "让审查 agent 检查", rv_rerun: "重新审查", rv_del: "（删除）", sev_high: "重要", sev_medium: "建议", sev_low: "润色", rv_mode: "文书审查 sub agent", rv_modeSub: "主 agent 写好邮件或文书后，审查 agent 会按日英语法、敬语、文书写作原则和你的档案（防止编造）检查一遍。", rv_mode_off: "关闭", rv_mode_suggest: "提出建议，由我决定", rv_mode_auto: "高度自动：直接修改（保留原文可撤销）", rv_kb: "知识库：agent_app/reviewer_kb/（日语语法与敬语、英语语法、写作原则）；个人规则可写在 资料/reviewer_knowledge.md",
    nav_inbox: "收件箱", nav_documents: "文书", nav_profile: "档案与知识", nav_settings: "设置",
    sync: "同步", syncing: "同步中…", synced: "已同步", theme: "主题",
    prov_claude_api: "Claude API", prov_claude_cli: "Claude 订阅（CLI）", prov_openai: "开放模型（NemoClaw 风格）",
    provd_claude_api: "Anthropic API key，按用量计费，最稳定", provd_claude_cli: "调用本机 Claude Code CLI，使用你的 Claude 订阅额度",
    provd_openai: "OpenAI 兼容接口：NVIDIA NIM / DeepSeek / OpenRouter / Ollama 本地模型", notReady: "未配置",
    hello: "你好，{name}", heroSub: "今天也一起推进求职吧。agent 会调研、写文书、投递（需审批）并跟进回信。",
    st_companies: "公司库（A 类）", st_applied: "已投递", st_replies: "回复 / 面试", st_pending: "待审批", st_mail: "未读求职邮件", st_questions: "待答问题",
    followups: "需要跟进（投递 ≥7 天未回复）", pendingTitle: "待审批", recentMail: "最近的求职邮件", openQ: "等你回答的问题", funnel: "投递漏斗",
    none: "暂无", writeFollowup: "让 agent 写跟进", goApprove: "去审批", goAnswer: "去回答", noMail: "还没有抓取邮件",
    quick: ["检查两个邮箱有没有公司回信，帮我总结并起草回复", "从公司库再挑 10 家还没投的化学·材料类公司，调研后排名", "列出需要跟进的公司并写跟进邮件", "帮我准备下一场面试"],
    newChat: "新对话", del: "删除", confirmDel: "删除这个对话？", placeholder: "告诉 agent 要做什么…（Enter 发送，Shift+Enter 换行）",
    send: "发送", stop: "停止", thinking: "思考中…", gateNote: "发邮件和提交表单都会先进入「待审批」", interrupted: "连接中断：",
    welcomeT: "我能帮你做什么？", welcomeS: "查公司库、上网调研、写中日英文书、发邮件（需审批）、填网页表单（提交需审批）、读回信、记录进度。",
    caps: [["调研公司", "从公司库挑公司并给出评分排名"], ["投递", "写应募文、准备附件、填表单"], ["回信处理", "抓取邮件、总结、起草回复"], ["面试准备", "生成面试问答与自我介绍"], ["进度管理", "更新阶段、提醒跟进"], ["文书", "生成履歴書 / 英文简历"]],
    capPrompts: ["从公司库里挑 10 家最适合我的、还没联系过的公司，查看招聘页后评分排名", "帮我选一家还没投的高分公司，准备好投递（邮件进待审批，表单帮我填好）", "检查新邮件，总结公司回信并起草回复", "帮我准备下一场面试：可能的问题、回答要点和 1 分钟自我介绍（日语）", "看一下进度，告诉我今天该做什么", "根据最新档案重新生成全部简历 PDF"],
    approvalsSub: "agent 准备好的对外动作，批准后才会执行", noPending: "没有待审批的动作", history: "历史",
    email: "邮件", form: "网页表单", account: "发件账户", to: "收件人", cc: "抄送", subject: "主题", body: "正文",
    attachments: "附件（项目内相对路径，用 ; 分隔）", reject: "拒绝", saveEdit: "保存修改", approveSend: "批准并发送", confirmSend: "确认发送给",
    sent: "已发送", rejected: "已拒绝", saved: "已保存", page: "页面", buttonToClick: "要点击的按钮", note: "说明",
    captchaNote: "页面上有验证码：请在 agent 打开的 Chrome 窗口里自己完成验证并提交，然后点「我已手动提交」。",
    checkNote: "请先在 agent 打开的 Chrome 窗口里检查已填写的内容，确认无误后点「批准并点击」。",
    manualDone: "我已手动提交", approveClick: "批准并点击", kind: "类型", title: "标题", company: "公司", status: "状态", result: "结果", time: "时间",
    stat_done: "已执行", stat_rejected: "已拒绝", stat_failed: "失败",
    pipelineSub: "家 · 拖动卡片修改阶段", dueTag: "该跟进", score: "分", stageNote: "改为「{s}」，备注（可留空）：",
    kw: "关键词（公司名、技术、描述…）", allTypes: "全部类型", allStatus: "全部", notContacted: "未联系", contacted: "已联系", pref: "都道府县", minScore: "最低分",
    byScore: "按评分", byName: "按名称", recent: "最新加入", search: "搜索", evalThese: "让 agent 评估这些", total: "共 {n} 家",
    th_score: "评分", th_company: "公司", th_type: "类型", th_loc: "所在地", th_desc: "简介", th_contact: "联系方式", th_stage: "进度",
    careers: "招聘页", mail: "邮箱", contactForm: "表单", prev: "上一页", next: "下一页",
    website: "官网", careersPage: "招聘页", emails: "邮箱", loc: "所在地", field: "领域", univ: "相关大学", classA: "A 类（未上市未并购）", backup: "保底",
    research: "调研并评分", apply: "帮我投递", rescrape: "重新抓取官网", fitTitle: "匹配评估", fitRoles: "适合岗位：", concerns: "顾虑：",
    progress: "进度", noRecord: "还没有记录", record: "记录", mails: "邮件", docs: "文书", siteText: "官网简介", careersText: "招聘页内容（抓取）",
    inboxSub: "只保留与求职相关的邮件", unread: "未读", read: "已读", handled: "已处理", fetchMail: "抓取邮件", fetching: "抓取中…", newMails: "新邮件 {n} 封",
    noMails: "没有邮件。先在「设置」里为邮箱设置应用专用密码，再点「抓取邮件」。", from: "发件人", timeAcc: "时间 / 账户", unlinked: "未关联",
    summarize: "总结并起草回复", markHandled: "标记已处理", linkCompany: "关联公司", linkPrompt: "关联到公司 ID：", pickMail: "选择左侧的邮件",
    readyPdf: "可直接投递的 PDF", preview: "预览", download: "下载", regen: "根据档案重新生成：", rireki: "日文履歴書", resumeEn: "英文简历", resumeNoPhone: "英文简历（无电话）", all: "全部",
    generating: "生成中…", regenerated: "已重新生成", general: "通用", viewEdit: "查看/编辑", lang: "语言", updated: "更新", save: "保存",
    tabQ: "待答问题", tabProfile: "档案 profile.md", tabKnow: "共享知识库", answerPh: "你的回答…", notNeeded: "不需要了", submit: "提交", submitAgent: "提交并让 agent 更新文书",
    usedFor: "用于：", answered: "已回答", dropped: "已放弃", recorded: "已记录", urgent: "急",
    profileNote: "agent 的唯一事实依据：写申请材料时不会编造这里没有的经历。", knowNote: "Claude Code 会话与 agent 共享的经验和约定（投递渠道、注意事项、现状）。每次对话都会读入。",
    backend: "模型后端", backendSub: "选择 agent 用哪种模型运行", apiKey: "Anthropic API key", keySaved: "已保存到 Windows 凭据管理器", isSet: "已设置",
    notSet: "未设置", cliModel: "CLI 模型（可留空用默认）", cliNote: "使用本机 claude CLI 的登录状态（Claude 订阅）。agent 的工具通过 MCP 提供给 CLI。", preset: "预设",
    baseUrl: "接口地址（base URL）", modelName: "模型名", oaKey: "API key", oaNote: "NemoClaw 风格：开放模型 + OpenAI 兼容接口。模型名可以按服务商文档修改。",
    mailAccounts: "邮箱账户", mailNote: "Gmail / Google Workspace 需要「应用专用密码」：Google 账户 → 安全性 → 两步验证 → 应用专用密码。保存前会先试登录。",
    canUse: "可收发", verifySave: "验证并保存", defaultSend: "默认发件", loginOk: "登录成功，已保存", defaultChanged: "默认发件账户已更改",
    rules: "安全规则（固定）", rule1: "邮件只有在「待审批」里点「批准并发送」后才会发出。", rule2: "网页表单的提交按钮只有你批准后才会点击；验证码由你自己完成。",
    rule3: "登录、注册账户、输入密码都由你自己在 agent 打开的 Chrome 窗口里完成。", rule4: "agent 只用档案里的事实写材料，缺的信息会变成「待答问题」。",
    uiLang: "界面与 agent 语言", loadFail: "加载失败：", sendFail: "发送失败：",
    stages: { shortlisted: "候选", drafted: "准备中", sent: "已投递", replied: "已回复", interview: "面试", offer: "Offer", rejected: "未通过", closed: "结束" },
    types: { "1": "化学·材料", "2": "IT", "1,2": "化学+IT", other: "其他" },
  },
  ja: {
    brand: "就活エージェント", brandSub: "日本のテック系スタートアップ",
    nav_dashboard: "ダッシュボード", nav_chat: "エージェント", nav_approvals: "承認待ち", nav_pipeline: "選考ボード", nav_companies: "企業DB",
    nav_notes: "ノート", notesSub: "学習ノート・面接ノート・全体の To Do。エージェントと Claude Code の両方が読み書きします。", tab_study: "学習ノート", tab_interview: "面接ノート", tab_todo: "To Do 一覧", noteStudy: "学習ノート", noteInterview: "面接ノート", noNotes: "ノートはまだありません", markDone: "完了にする", reopen: "未完了に戻す", editNote: "編集", saveNote: "保存", cancel: "キャンセル", newNote: "新規ノート", noteTitle: "タイトル", noteCompany: "関連企業 ID（任意）", noteDue: "期限（任意）", done: "完了", openN: "未完了 {n} 件", general: "共通", hasStudy: "学習ノートあり", hasInterview: "面接ノートあり", prepNotes: "エージェントにノートを更新させる",
    rv_title: "文書レビュー", rv_running: "レビューエージェントが確認中…", rv_ok: "問題は見つかりませんでした", rv_n: "修正提案 {n} 件", rv_applied: "修正を反映済み", rv_auto: "自動で修正済み（元に戻せます）", rv_failed: "レビュー失敗", rv_dismissed: "無視しました", rv_applySel: "選択した提案を反映", rv_applyAll: "修正版をすべて採用", rv_dismiss: "無視", rv_revert: "元に戻す", rv_showRevised: "修正版の全文を表示", rv_run: "レビューエージェントに確認させる", rv_rerun: "再レビュー", rv_del: "（削除）", sev_high: "重要", sev_medium: "提案", sev_low: "推敲", rv_mode: "文書レビュー サブエージェント", rv_modeSub: "メインエージェントがメールや書類を作ると、レビューエージェントが日英文法・敬語・書類作成の原則・プロフィールとの事実整合をチェックします。", rv_mode_off: "オフ", rv_mode_suggest: "提案のみ（反映は自分で決める）", rv_mode_auto: "高度自動：直接修正（元に戻せます）", rv_kb: "知識ベース：agent_app/reviewer_kb/（日本語文法・敬語、英文法、書類の原則）。個人ルールは 資料/reviewer_knowledge.md に。",
    nav_inbox: "受信箱", nav_documents: "書類", nav_profile: "プロフィール", nav_settings: "設定",
    sync: "同期", syncing: "同期中…", synced: "同期しました", theme: "テーマ",
    prov_claude_api: "Claude API", prov_claude_cli: "Claude サブスク（CLI）", prov_openai: "オープンモデル（NemoClaw 風）",
    provd_claude_api: "Anthropic API キー（従量課金・最も安定）", provd_claude_cli: "ローカルの Claude Code CLI を使用（Claude サブスクの枠）",
    provd_openai: "OpenAI 互換 API：NVIDIA NIM / DeepSeek / OpenRouter / Ollama", notReady: "未設定",
    hello: "こんにちは、{name}さん", heroSub: "今日も就活を前に進めましょう。調査・書類作成・応募（承認制）・返信対応を行います。",
    st_companies: "企業DB（A区分）", st_applied: "応募済み", st_replies: "返信 / 面接", st_pending: "承認待ち", st_mail: "未読メール", st_questions: "未回答の質問",
    followups: "フォローが必要（応募後7日以上返信なし）", pendingTitle: "承認待ち", recentMail: "最近の選考メール", openQ: "回答待ちの質問", funnel: "選考ファネル",
    none: "なし", writeFollowup: "フォローメールを作成", goApprove: "承認へ", goAnswer: "回答へ", noMail: "まだメールを取得していません",
    quick: ["2つのメールボックスで企業からの返信を確認し、要約して返信案を作成", "未応募の化学・材料系企業を10社選び、調査してランキング", "フォローが必要な企業を挙げてフォローメールを作成", "次の面接の準備を手伝って"],
    newChat: "新しい会話", del: "削除", confirmDel: "この会話を削除しますか？", placeholder: "エージェントへの指示…（Enterで送信、Shift+Enterで改行）",
    send: "送信", stop: "停止", thinking: "考え中…", gateNote: "メール送信とフォーム提出は必ず「承認待ち」を経由します", interrupted: "接続が切れました：",
    welcomeT: "何をお手伝いしましょう？", welcomeS: "企業DB検索、Web調査、中日英の書類作成、メール送信（承認制）、フォーム入力（提出は承認制）、返信対応、進捗管理。",
    caps: [["企業調査", "企業を選んでスコアリング"], ["応募", "応募文・添付・フォーム入力"], ["返信対応", "メール取得・要約・返信案"], ["面接準備", "想定問答と自己紹介"], ["進捗管理", "ステージ更新とフォロー"], ["書類", "履歴書・英文レジュメ生成"]],
    capPrompts: ["企業DBから未連絡で最も合う10社を選び、採用ページを確認してスコアと順位を付けて", "未応募の高スコア企業を1社選んで応募準備をして（メールは承認待ちへ、フォームは入力まで）", "新着メールを確認して企業からの返信を要約し、返信案を作成して", "次の面接の準備：想定質問、回答の要点、1分間の自己紹介（日本語）", "進捗を見て、今日やるべきことを教えて", "最新のプロフィールで全ての履歴書PDFを再生成して"],
    approvalsSub: "エージェントが準備した対外アクション。承認後に実行されます", noPending: "承認待ちはありません", history: "履歴",
    email: "メール", form: "Webフォーム", account: "送信アカウント", to: "宛先", cc: "CC", subject: "件名", body: "本文",
    attachments: "添付（プロジェクト内の相対パス、; 区切り）", reject: "却下", saveEdit: "変更を保存", approveSend: "承認して送信", confirmSend: "送信してよろしいですか：",
    sent: "送信しました", rejected: "却下しました", saved: "保存しました", page: "ページ", buttonToClick: "クリックするボタン", note: "説明",
    captchaNote: "CAPTCHA があります。エージェントが開いた Chrome でご自身で認証・送信し、「手動で提出済み」を押してください。",
    checkNote: "エージェントが開いた Chrome で入力内容を確認してから「承認してクリック」を押してください。",
    manualDone: "手動で提出済み", approveClick: "承認してクリック", kind: "種類", title: "タイトル", company: "企業", status: "状態", result: "結果", time: "日時",
    stat_done: "実行済み", stat_rejected: "却下", stat_failed: "失敗",
    pipelineSub: "社 · カードをドラッグしてステージ変更", dueTag: "要フォロー", score: "点", stageNote: "「{s}」に変更。メモ（任意）：",
    kw: "キーワード（社名・技術・説明…）", allTypes: "すべての種類", allStatus: "すべて", notContacted: "未連絡", contacted: "連絡済み", pref: "都道府県", minScore: "最低点",
    byScore: "スコア順", byName: "名前順", recent: "新着順", search: "検索", evalThese: "エージェントに評価させる", total: "全 {n} 社",
    th_score: "スコア", th_company: "企業", th_type: "種類", th_loc: "所在地", th_desc: "概要", th_contact: "連絡先", th_stage: "進捗",
    careers: "採用ページ", mail: "メール", contactForm: "フォーム", prev: "前へ", next: "次へ",
    website: "Webサイト", careersPage: "採用ページ", emails: "メール", loc: "所在地", field: "分野", univ: "関連大学", classA: "A区分（未上場・未買収）", backup: "滑り止め",
    research: "調査してスコア付け", apply: "応募を準備", rescrape: "サイトを再取得", fitTitle: "マッチ評価", fitRoles: "適したポジション：", concerns: "懸念：",
    progress: "進捗", noRecord: "まだ記録がありません", record: "記録", mails: "メール", docs: "書類", siteText: "サイト概要", careersText: "採用ページ（取得内容）",
    inboxSub: "就活関連のメールだけを保存", unread: "未読", read: "既読", handled: "対応済み", fetchMail: "メール取得", fetching: "取得中…", newMails: "新着 {n} 件",
    noMails: "メールがありません。「設定」でアプリパスワードを設定してから「メール取得」を押してください。", from: "差出人", timeAcc: "日時 / アカウント", unlinked: "未紐付け",
    summarize: "要約して返信案", markHandled: "対応済みにする", linkCompany: "企業に紐付け", linkPrompt: "紐付ける企業ID：", pickMail: "左のメールを選択してください",
    readyPdf: "提出用 PDF", preview: "プレビュー", download: "ダウンロード", regen: "プロフィールから再生成：", rireki: "履歴書", resumeEn: "英文レジュメ", resumeNoPhone: "英文レジュメ（電話なし）", all: "すべて",
    generating: "生成中…", regenerated: "再生成しました", general: "共通", viewEdit: "表示/編集", lang: "言語", updated: "更新", save: "保存",
    tabQ: "未回答の質問", tabProfile: "プロフィール profile.md", tabKnow: "共有ナレッジ", answerPh: "回答…", notNeeded: "不要", submit: "送信", submitAgent: "送信して書類を更新",
    usedFor: "用途：", answered: "回答済み", dropped: "取り下げ", recorded: "記録しました", urgent: "急",
    profileNote: "エージェントの唯一の事実情報源です。ここにない経歴は書類に書きません。", knowNote: "Claude Code セッションとエージェントが共有する経験・ルール・現状。毎回の会話で読み込まれます。",
    backend: "モデル", backendSub: "エージェントを動かすモデルを選択", apiKey: "Anthropic API キー", keySaved: "Windows 資格情報マネージャーに保存しました", isSet: "設定済み",
    notSet: "未設定", cliModel: "CLI モデル（空欄で既定）", cliNote: "ローカルの claude CLI のログイン（Claude サブスク）を使用。ツールは MCP 経由で提供。", preset: "プリセット",
    baseUrl: "エンドポイント（base URL）", modelName: "モデル名", oaKey: "API キー", oaNote: "NemoClaw 風：オープンモデル + OpenAI 互換 API。モデル名は各社ドキュメントに合わせて変更できます。",
    mailAccounts: "メールアカウント", mailNote: "Gmail / Google Workspace は「アプリ パスワード」が必要です（Google アカウント → セキュリティ → 2段階認証 → アプリ パスワード）。保存前にログインを試します。",
    canUse: "送受信可", verifySave: "確認して保存", defaultSend: "既定の送信元", loginOk: "ログイン成功、保存しました", defaultChanged: "既定の送信元を変更しました",
    rules: "安全ルール（固定）", rule1: "メールは「承認待ち」で承認したときだけ送信されます。", rule2: "フォームの提出ボタンは承認後にのみクリック。CAPTCHA はご自身で。",
    rule3: "ログイン・アカウント作成・パスワード入力はご自身で行います。", rule4: "書類はプロフィールの事実のみで作成し、不足情報は質問リストに追加します。",
    uiLang: "表示・エージェントの言語", loadFail: "読み込み失敗：", sendFail: "送信失敗：",
    stages: { shortlisted: "候補", drafted: "準備中", sent: "応募済み", replied: "返信あり", interview: "面接", offer: "内定", rejected: "不合格", closed: "終了" },
    types: { "1": "化学・材料", "2": "IT", "1,2": "化学+IT", other: "その他" },
  },
  en: {
    brand: "Job Agent", brandSub: "Japan tech-startup search",
    nav_dashboard: "Dashboard", nav_chat: "Agent", nav_approvals: "Approvals", nav_pipeline: "Pipeline", nav_companies: "Companies",
    nav_notes: "Notes", notesSub: "Study notes, interview notes and the overall to-do list. Read and written by the agent and Claude Code.", tab_study: "Study", tab_interview: "Interviews", tab_todo: "To-do overview", noteStudy: "Study notes", noteInterview: "Interview notes", noNotes: "No notes yet", markDone: "Mark done", reopen: "Reopen", editNote: "Edit", saveNote: "Save", cancel: "Cancel", newNote: "New note", noteTitle: "Title", noteCompany: "Company ID (optional)", noteDue: "Due (optional)", done: "Done", openN: "{n} open", general: "General", hasStudy: "Has study notes", hasInterview: "Has interview notes", prepNotes: "Ask the agent to update notes",
    rv_title: "Writing review", rv_running: "Reviewer is checking…", rv_ok: "No issues found", rv_n: "{n} suggestions", rv_applied: "Changes applied", rv_auto: "Auto-corrected (can undo)", rv_failed: "Review failed", rv_dismissed: "Dismissed", rv_applySel: "Apply selected", rv_applyAll: "Use revised version", rv_dismiss: "Dismiss", rv_revert: "Undo", rv_showRevised: "Show full revised text", rv_run: "Ask the reviewer", rv_rerun: "Review again", rv_del: "(delete)", sev_high: "Important", sev_medium: "Suggestion", sev_low: "Polish", rv_mode: "Writing reviewer sub-agent", rv_modeSub: "After the main agent writes an e-mail or document, the reviewer checks Japanese/English grammar, keigo, writing principles and facts against your profile.", rv_mode_off: "Off", rv_mode_suggest: "Suggest – I decide", rv_mode_auto: "Highly automatic – apply directly (original kept for undo)", rv_kb: "Knowledge base: agent_app/reviewer_kb/ (Japanese grammar & keigo, English grammar, writing principles); personal rules in 资料/reviewer_knowledge.md",
    nav_inbox: "Inbox", nav_documents: "Documents", nav_profile: "Profile & notes", nav_settings: "Settings",
    sync: "Sync", syncing: "Syncing…", synced: "Synced", theme: "Theme",
    prov_claude_api: "Claude API", prov_claude_cli: "Claude subscription (CLI)", prov_openai: "Open models (NemoClaw-style)",
    provd_claude_api: "Anthropic API key, pay as you go, most reliable", provd_claude_cli: "Runs the local Claude Code CLI on your Claude subscription",
    provd_openai: "OpenAI-compatible: NVIDIA NIM / DeepSeek / OpenRouter / Ollama", notReady: "not set up",
    hello: "Hi {name}", heroSub: "Let's move the search forward. The agent researches, drafts, applies (with your approval) and follows up.",
    st_companies: "Companies (class A)", st_applied: "Applied", st_replies: "Replies / interviews", st_pending: "Approvals", st_mail: "Unread job mail", st_questions: "Open questions",
    followups: "Follow-ups due (no reply ≥7 days)", pendingTitle: "Waiting for approval", recentMail: "Recent job mail", openQ: "Questions for you", funnel: "Funnel",
    none: "Nothing", writeFollowup: "Draft follow-up", goApprove: "Review", goAnswer: "Answer", noMail: "No mail fetched yet",
    quick: ["Check both mailboxes for company replies, summarise and draft answers", "Pick 10 uncontacted chemistry/materials companies, research and rank them", "List follow-ups due and draft the emails", "Help me prepare for my next interview"],
    newChat: "New chat", del: "Delete", confirmDel: "Delete this chat?", placeholder: "Tell the agent what to do… (Enter to send, Shift+Enter for a new line)",
    send: "Send", stop: "Stop", thinking: "Thinking…", gateNote: "Emails and form submissions always go to Approvals first", interrupted: "Connection lost: ",
    welcomeT: "What can I do for you?", welcomeS: "Search the company DB, research online, write in Chinese/Japanese/English, send email (approved), fill web forms (submit approved), handle replies, track progress.",
    caps: [["Research", "Pick and score companies"], ["Apply", "Cover notes, attachments, forms"], ["Replies", "Fetch, summarise, draft replies"], ["Interviews", "Likely questions & self-intro"], ["Progress", "Stages and follow-ups"], ["Documents", "Regenerate CV PDFs"]],
    capPrompts: ["Pick the 10 best-fitting companies I have not contacted, check their careers pages, score and rank them", "Pick one high-scoring company I haven't applied to and prepare the application (emails to approvals, forms filled)", "Check new mail, summarise company replies and draft answers", "Prepare my next interview: likely questions, talking points and a 1-minute self-introduction in Japanese", "Look at my pipeline and tell me what to do today", "Regenerate all CV PDFs from the latest profile"],
    approvalsSub: "Outward actions prepared by the agent – nothing happens until you approve", noPending: "Nothing to approve", history: "History",
    email: "Email", form: "Web form", account: "Account", to: "To", cc: "Cc", subject: "Subject", body: "Body",
    attachments: "Attachments (project-relative paths, separated by ;)", reject: "Reject", saveEdit: "Save edits", approveSend: "Approve & send", confirmSend: "Send to",
    sent: "Sent", rejected: "Rejected", saved: "Saved", page: "Page", buttonToClick: "Button to click", note: "Note",
    captchaNote: "This page has a CAPTCHA: solve it and submit in the Chrome window the agent opened, then click “Submitted manually”.",
    checkNote: "Check the filled form in the Chrome window the agent opened, then click “Approve & click”.",
    manualDone: "Submitted manually", approveClick: "Approve & click", kind: "Type", title: "Title", company: "Company", status: "Status", result: "Result", time: "Time",
    stat_done: "done", stat_rejected: "rejected", stat_failed: "failed",
    pipelineSub: "companies · drag cards to change stage", dueTag: "follow up", score: "pts", stageNote: "Move to “{s}”. Note (optional):",
    kw: "Keywords (name, tech, description…)", allTypes: "All types", allStatus: "All", notContacted: "Not contacted", contacted: "Contacted", pref: "Prefecture", minScore: "Min score",
    byScore: "By score", byName: "By name", recent: "Newest", search: "Search", evalThese: "Let the agent evaluate", total: "{n} companies",
    th_score: "Score", th_company: "Company", th_type: "Type", th_loc: "Location", th_desc: "About", th_contact: "Contact", th_stage: "Stage",
    careers: "careers", mail: "email", contactForm: "form", prev: "Previous", next: "Next",
    website: "Website", careersPage: "Careers", emails: "Emails", loc: "Location", field: "Field", univ: "University", classA: "Class A (not listed / not acquired)", backup: "backup",
    research: "Research & score", apply: "Prepare application", rescrape: "Re-scrape site", fitTitle: "Fit", fitRoles: "Roles: ", concerns: "Concerns: ",
    progress: "Progress", noRecord: "No records yet", record: "Record", mails: "Mail", docs: "Documents", siteText: "About (website)", careersText: "Careers page (scraped)",
    inboxSub: "Only job-related mail is kept", unread: "Unread", read: "Read", handled: "Handled", fetchMail: "Fetch mail", fetching: "Fetching…", newMails: "{n} new",
    noMails: "No mail yet. Set app passwords in Settings, then click “Fetch mail”.", from: "From", timeAcc: "Time / account", unlinked: "not linked",
    summarize: "Summarise & draft reply", markHandled: "Mark handled", linkCompany: "Link company", linkPrompt: "Company ID:", pickMail: "Pick a message on the left",
    readyPdf: "Ready-to-send PDFs", preview: "Preview", download: "Download", regen: "Regenerate from profile:", rireki: "履歴書 (JP)", resumeEn: "English CV", resumeNoPhone: "English CV (no phone)", all: "All",
    generating: "Generating…", regenerated: "Regenerated", general: "General", viewEdit: "View/edit", lang: "Lang", updated: "Updated", save: "Save",
    tabQ: "Open questions", tabProfile: "Profile (profile.md)", tabKnow: "Shared knowledge", answerPh: "Your answer…", notNeeded: "Not needed", submit: "Submit", submitAgent: "Submit & update documents",
    usedFor: "Needed for: ", answered: "answered", dropped: "dropped", recorded: "Recorded", urgent: "urgent",
    profileNote: "The agent's only source of facts – it never writes experience that is not here.", knowNote: "Lessons, rules and current status shared by Claude Code sessions and the agent. Loaded into every conversation.",
    backend: "Model back-end", backendSub: "Choose what the agent runs on", apiKey: "Anthropic API key", keySaved: "Saved to Windows Credential Manager", isSet: "set",
    notSet: "not set", cliModel: "CLI model (blank = default)", cliNote: "Uses the local claude CLI login (your Claude subscription). Tools are provided to the CLI via MCP.", preset: "Preset",
    baseUrl: "Base URL", modelName: "Model", oaKey: "API key", oaNote: "NemoClaw-style: open models over an OpenAI-compatible API. Adjust the model name to your provider's docs.",
    mailAccounts: "Mail accounts", mailNote: "Gmail / Google Workspace needs an App Password (Google Account → Security → 2-Step Verification → App passwords). Login is tested before saving.",
    canUse: "ready", verifySave: "Verify & save", defaultSend: "Default sender", loginOk: "Login OK, saved", defaultChanged: "Default sender changed",
    rules: "Safety rules (fixed)", rule1: "Emails are only sent after you click “Approve & send”.", rule2: "Submit buttons on web forms are only clicked after your approval; CAPTCHAs are yours.",
    rule3: "Logins, account creation and passwords are always done by you.", rule4: "Documents use only facts from the profile; missing facts become questions.",
    uiLang: "UI & agent language", loadFail: "Failed to load: ", sendFail: "Send failed: ",
    stages: { shortlisted: "Shortlist", drafted: "Preparing", sent: "Applied", replied: "Replied", interview: "Interview", offer: "Offer", rejected: "Rejected", closed: "Closed" },
    types: { "1": "Chem/Materials", "2": "IT", "1,2": "Chem+IT", other: "Other" },
  },
};
let LANG = "zh";
const T = (k, vars) => { let s = (I18N[LANG] && I18N[LANG][k]) ?? I18N.zh[k] ?? k; if (vars) for (const [a, b] of Object.entries(vars)) s = s.replace(`{${a}}`, b); return s; };
const STAGES = ["shortlisted", "drafted", "sent", "replied", "interview", "offer", "rejected", "closed"];
const STAGE_COLOR = { shortlisted: "", drafted: "orange", sent: "blue", replied: "green", interview: "green", offer: "green", rejected: "red", closed: "" };
const STAGE_HEX = { shortlisted: "#cfcfcb", drafted: "#d8b47c", sent: "#94afe0", replied: "#86c1a2", interview: "#4f9f75", offer: "#2b7d52", rejected: "#e0a3a8", closed: "#cfcfcb" };

// ================================================================== helpers
const $ = (s, el = document) => el.querySelector(s);
function h(tag, attrs = {}, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === null || v === undefined || v === false) continue;
    if (k === "class") el.className = v;
    else if (k === "style") el.style.cssText = v;
    else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else if (k === "html") el.innerHTML = v;
    else el.setAttribute(k, v === true ? "" : v);
  }
  for (const kid of kids.flat(Infinity)) {
    if (kid === null || kid === undefined || kid === false) continue;
    el.append(kid instanceof Node ? kid : document.createTextNode(String(kid)));
  }
  return el;
}
const ICONS = {
  dashboard: '<rect x="3" y="3" width="7" height="9" rx="1.5"/><rect x="14" y="3" width="7" height="5" rx="1.5"/><rect x="14" y="12" width="7" height="9" rx="1.5"/><rect x="3" y="16" width="7" height="5" rx="1.5"/>',
  chat: '<path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.4A8 8 0 1 1 21 12z"/><path d="M8.5 11h.01M12 11h.01M15.5 11h.01"/>',
  approvals: '<path d="M9 11l3 3 8-8"/><path d="M20 12v7a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h9"/>',
  pipeline: '<rect x="3" y="4" width="5" height="16" rx="1.5"/><rect x="10" y="4" width="5" height="11" rx="1.5"/><rect x="17" y="4" width="4" height="7" rx="1.5"/>',
  companies: '<path d="M3 21h18"/><path d="M5 21V7l7-4v18"/><path d="M19 21V11l-7-4"/><path d="M9 9h.01M9 13h.01M9 17h.01"/>',
  inbox: '<path d="M22 12h-6l-2 3h-4l-2-3H2"/><path d="M5.5 5h13l3.5 7v6a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2v-6z"/>',
  documents: '<path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><path d="M14 3v6h6M8 13h8M8 17h5"/>',
  profile: '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
  settings: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/>',
  spark: '<path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z"/><path d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8z"/>',
  sync: '<path d="M21 12a9 9 0 0 1-15.5 6.3L3 16"/><path d="M3 12a9 9 0 0 1 15.5-6.3L21 8"/><path d="M21 3v5h-5M3 21v-5h5"/>',
  moon: '<path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/>',
  send: '<path d="M22 2L11 13"/><path d="M22 2l-7 20-4-9-9-4z"/>',
  mail: '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="M22 6l-10 7L2 6"/>', check: '<path d="M20 6L9 17l-5-5"/>',
  building: '<path d="M3 21h18M6 21V5a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v16"/>', help: '<circle cx="12" cy="12" r="9"/><path d="M9.1 9a3 3 0 0 1 5.8 1c0 2-3 2.5-3 4.5M12 17.5h.01"/>',
  plus: '<path d="M12 5v14M5 12h14"/>', x: '<path d="M18 6L6 18M6 6l12 12"/>', clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 3"/>',
  notes: '<path d="M4 4.5A2.5 2.5 0 0 1 6.5 2H20v17H6.5A2.5 2.5 0 0 0 4 21.5z"/><path d="M4 21.5V4.5M8 7h8M8 11h6"/>',
  interview: '<rect x="9" y="2" width="6" height="11" rx="3"/><path d="M5 10a7 7 0 0 0 14 0M12 17v4M8 21h8"/>',
  bot: '<rect x="4" y="8" width="16" height="12" rx="3"/><path d="M12 4v4M9 13h.01M15 13h.01M9 17h6"/>',
};
const icon = (n) => { const s = document.createElementNS("http://www.w3.org/2000/svg", "svg"); s.setAttribute("viewBox", "0 0 24 24"); s.setAttribute("class", "i"); s.innerHTML = ICONS[n] || ""; return s; };
async function api(path, opts = {}) {
  const o = { headers: { "Content-Type": "application/json" }, ...opts };
  if (o.body && typeof o.body !== "string") o.body = JSON.stringify(o.body);
  const r = await fetch(path, o);
  if (!r.ok) { let msg = r.statusText; try { msg = (await r.json()).detail || msg; } catch (_) {} throw new Error(msg); }
  return r.json();
}
function toast(msg, ms = 2600) { const t = h("div", { class: "toast" }, msg); document.body.append(t); setTimeout(() => t.remove(), ms); }
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const SL = (s) => T("stages")[s] || s;
const stageBadge = (s) => s ? h("span", { class: `badge ${STAGE_COLOR[s] || ""}` }, SL(s)) : h("span", { class: "muted" }, "—");
const typeBadge = (t) => h("span", { class: "badge" }, T("types")[t] || t || "—");
const scoreEl = (s) => s == null ? h("span", { class: "muted" }, "—") : h("span", { class: "score " + (s >= 80 ? "s-hi" : s >= 60 ? "s-mid" : "s-lo") }, s);

function md(src) {
  const lines = esc(src || "").split("\n");
  let out = "", inList = null, inCode = false, table = [];
  const inline = (s) => s.replace(/`([^`]+)`/g, "<code>$1</code>").replace(/\*\*([^*]+)\*\*/g, "<b>$1</b>")
    .replace(/\[([^\]]+)\]\((https?:[^)]+)\)/g, '<a href="$2" target="_blank">$1</a>')
    .replace(/(^|\s)(https?:\/\/[^\s<]+)/g, '$1<a href="$2" target="_blank">$2</a>');
  const flushTable = () => {
    if (!table.length) return;
    const real = table.filter((r) => !/^\|?(\s*:?-+:?\s*\|)+\s*:?-*:?\s*\|?$/.test(r));
    const cells = (r) => r.replace(/^\||\|$/g, "").split("|").map((c) => inline(c.trim()));
    out += "<table>" + real.map((r, i) => "<tr>" + cells(r).map((c) => i ? `<td>${c}</td>` : `<th>${c}</th>`).join("") + "</tr>").join("") + "</table>";
    table = [];
  };
  const closeList = () => { if (inList) { out += `</${inList}>`; inList = null; } };
  for (const line of lines) {
    if (line.startsWith("```")) { closeList(); flushTable(); out += inCode ? "</pre>" : "<pre>"; inCode = !inCode; continue; }
    if (inCode) { out += line + "\n"; continue; }
    if (/^\s*\|.*\|\s*$/.test(line)) { closeList(); table.push(line.trim()); continue; } else flushTable();
    let m;
    if (/^\s*(-{3,}|\*{3,})\s*$/.test(line)) { closeList(); out += "<hr>"; }
    else if ((m = line.match(/^(#{1,4})\s+(.*)/))) { closeList(); out += `<h3>${inline(m[2])}</h3>`; }
    else if ((m = line.match(/^\s*[-*]\s+(.*)/))) { if (inList !== "ul") { closeList(); out += "<ul>"; inList = "ul"; } out += `<li>${inline(m[1])}</li>`; }
    else if ((m = line.match(/^\s*\d+[.)]\s+(.*)/))) { if (inList !== "ol") { closeList(); out += "<ol>"; inList = "ol"; } out += `<li>${inline(m[1])}</li>`; }
    else if ((m = line.match(/^&gt;\s?(.*)/))) { closeList(); out += `<blockquote>${inline(m[1])}</blockquote>`; }
    else if (!line.trim()) closeList();
    else { closeList(); out += `<p>${inline(line)}</p>`; }
  }
  closeList(); flushTable(); if (inCode) out += "</pre>";
  return out;
}

// ================================================================== shell (sidebar + topbar)
let SETTINGS = null, BADGES = {}, OWNER = {};
const NAV = ["dashboard", "chat", "approvals", "pipeline", "companies", "inbox", "notes", "documents", "profile"];
function renderSide() {
  const side = $("#side"); side.innerHTML = "";
  const cur = (location.hash.slice(1) || "dashboard").split("/")[0];
  const navBtn = (p, count, hot) => h("button", { class: "nav" + (cur === p ? " active" : ""), onclick: () => go(p) }, icon(p), T("nav_" + p), count ? h("span", { class: "count" + (hot ? " hot" : "") }, count) : null);
  side.append(
    h("div", { class: "brand" }, h("div", { class: "logo" }, icon("spark")), h("div", {}, h("b", {}, T("brand")), h("small", {}, T("brandSub")))),
    ...NAV.map((p) => navBtn(p, { approvals: BADGES.pending_actions, inbox: BADGES.new_mail, profile: BADGES.open_questions }[p], p === "approvals")),
    h("div", { class: "spacer" }),
    navBtn("settings"),
    h("div", { class: "sep" }),
    h("div", { class: "me" }, h("div", { class: "avatar" }, OWNER.avatar || "🙂"), h("div", {}, h("div", { class: "n" }, [OWNER.name, OWNER.nickname].filter(Boolean).join(" ")), h("div", { class: "s" }, (OWNER.subtitle || {})[LANG] || ""))));
}
function renderTop(title) {
  const top = $("#topbar"); top.innerHTML = "";
  const prov = SETTINGS?.provider || "claude_api";
  const ready = SETTINGS?.providers?.[prov]?.ready;
  const provBtn = h("button", { class: "pill", onclick: (e) => providerMenu(e.currentTarget) }, h("span", { class: "dot" + (ready ? "" : " off") }), T("prov_" + prov), h("span", { class: "muted" }, "▾"));
  const seg = h("div", { class: "seg" }, [["zh", "中"], ["ja", "日"], ["en", "EN"]].map(([v, l]) => h("button", { class: LANG === v ? "on" : "", onclick: () => setLang(v) }, l)));
  const syncBtn = h("button", { class: "pill", onclick: async () => {
    syncBtn.disabled = true; syncBtn.lastChild.textContent = T("syncing");
    try { const r = await api("/api/sync", { method: "POST" }); toast(`${T("synced")} · mail +${r.mail ?? 0} · docs +${r.documents_added}${r.errors.length ? " · " + r.errors[0] : ""}`, 4000); refreshBadges(); route(); }
    catch (e) { toast(e.message, 5000); }
    syncBtn.disabled = false; syncBtn.lastChild.textContent = T("sync");
  } }, icon("sync"), h("span", {}, T("sync")));
  top.append(h("div", { class: "title" }, title), provBtn, seg, syncBtn,
    h("button", { class: "iconbtn", title: T("theme"), onclick: toggleTheme }, icon("moon")));
}
function providerMenu(anchor) {
  document.querySelector(".menu")?.remove();
  const r = anchor.getBoundingClientRect();
  const m = h("div", { class: "menu", style: `top:${r.bottom + 6}px;left:${r.left}px` },
    ["claude_api", "claude_cli", "openai"].map((p) => h("div", { class: "opt" + (SETTINGS.provider === p ? " on" : ""), onclick: async () => { await api("/api/settings/agent", { method: "POST", body: { provider: p } }); m.remove(); await loadSettings(); toast(T("prov_" + p)); route(); } },
      h("span", { class: "pill", style: "height:auto;padding:4px;border:0" }, h("span", { class: "dot" + (SETTINGS.providers[p].ready ? "" : " off") })),
      h("div", {}, h("div", { class: "t" }, T("prov_" + p), SETTINGS.providers[p].ready ? null : h("span", { class: "badge orange", style: "margin-left:6px" }, T("notReady"))), h("div", { class: "d" }, T("provd_" + p))))),
    h("div", { class: "opt", onclick: () => { m.remove(); go("settings"); } }, h("div", { class: "d" }, T("nav_settings") + " →")));
  document.body.append(m);
  setTimeout(() => document.addEventListener("click", function off(e) { if (!m.contains(e.target)) { m.remove(); document.removeEventListener("click", off); } }), 0);
}
async function setLang(l) { LANG = l; document.documentElement.lang = l; await api("/api/settings/agent", { method: "POST", body: { lang: l } }); await loadSettings(); route(); }
function toggleTheme() {
  const cur = document.documentElement.dataset.theme || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  const next = cur === "dark" ? "light" : "dark"; document.documentElement.dataset.theme = next;
  try { localStorage.setItem("theme", next); } catch (_) {}
}
try { const t = localStorage.getItem("theme"); if (t) document.documentElement.dataset.theme = t; } catch (_) {}
async function loadSettings() { SETTINGS = await api("/api/settings"); OWNER = SETTINGS.owner || {}; LANG = SETTINGS.lang || "zh"; document.documentElement.lang = LANG; }
async function refreshBadges() { try { BADGES = await api("/api/stats"); renderSide(); } catch (_) {} }
setInterval(refreshBadges, 30000);

// ================================================================== routing
const pages = {};
function go(page, arg) { location.hash = arg ? `${page}/${arg}` : page; }
async function route() {
  if (!SETTINGS) await loadSettings();
  const [page, arg] = (location.hash.slice(1) || "dashboard").split("/");
  renderSide(); renderTop(T("nav_" + (pages[page] ? page : "dashboard")));
  const main = $("#main"); main.innerHTML = ""; main.style.overflow = page === "chat" ? "hidden" : "auto";
  try { await (pages[page] || pages.dashboard)(main, arg); } catch (e) { main.append(h("div", { class: "page" }, h("div", { class: "errbox" }, T("loadFail") + e.message))); }
}
window.addEventListener("hashchange", route);
async function askAgent(text) { const { id } = await api("/api/chats", { method: "POST" }); sessionStorage.setItem("pendingPrompt", text); go("chat", id); }

// ================================================================== dashboard
pages.dashboard = async (main) => {
  const s = await api("/api/stats"); BADGES = s; renderSide();
  const p = s.pipeline;
  const applied = ["sent", "replied", "interview", "offer", "rejected"].reduce((a, k) => a + (p[k] || 0), 0);
  const stat = (n, l, ic, cls, page) => h("div", { class: "card stat", onclick: () => go(page) }, h("div", { class: "ic " + cls }, icon(ic)), h("div", {}, h("div", { class: "n" }, n), h("div", { class: "l" }, l)));
  const total = Object.values(p).reduce((a, b) => a + b, 0) || 1;
  main.append(h("div", { class: "page" },
    h("div", { class: "card hero" }, h("div", { class: "grow" }, h("h1", {}, T("hello", { name: (LANG === "en" ? OWNER.nickname || OWNER.name_en : OWNER.short_name) || "" })), h("p", {}, T("heroSub")),
      h("div", { class: "chips", style: "margin:14px 0 0;max-width:none" }, T("quick").map((t) => h("span", { class: "chip", onclick: () => askAgent(t) }, t))))),
    h("div", { class: "grid cols-6", style: "margin-top:16px" },
      stat(s.companies, T("st_companies"), "building", "c-indigo", "companies"), stat(applied, T("st_applied"), "send", "c-sky", "pipeline"),
      stat((p.replied || 0) + (p.interview || 0), T("st_replies"), "chat", "c-green", "pipeline"), stat(s.pending_actions, T("st_pending"), "approvals", "c-orange", "approvals"),
      stat(s.new_mail, T("st_mail"), "mail", "c-sky", "inbox"), stat(s.open_questions, T("st_questions"), "help", "c-rose", "profile")),
    h("div", { class: "card", style: "margin-top:16px" }, h("h2", {}, T("funnel")),
      h("div", { class: "bar" }, STAGES.filter((k) => p[k]).map((k) => h("span", { style: `width:${(p[k] / total) * 100}%;background:${STAGE_HEX[k]}`, title: `${SL(k)} ${p[k]}` }))),
      h("div", { class: "row", style: "margin-top:10px" }, STAGES.map((k) => h("span", { class: "badge", style: "gap:6px" }, h("span", { style: `width:8px;height:8px;border-radius:50%;background:${STAGE_HEX[k]}` }), `${SL(k)} ${p[k] || 0}`)))),
    h("div", { class: "grid cols-2", style: "margin-top:16px" },
      h("div", { class: "card" }, h("h2", {}, icon("clock"), T("followups")),
        s.followups_due.length ? h("div", { class: "list" }, s.followups_due.map((f) => h("div", { class: "li" },
          h("div", { class: "grow ellipsis" }, h("a", { href: "#", onclick: (e) => { e.preventDefault(); openCompany(f.id); } }, f.name)),
          h("span", { class: "muted small" }, (f.sent_at || "").slice(0, 10)),
          h("button", { class: "btn sm", onclick: () => askAgent(`#${f.id} ${f.name}: no reply for over a week. Draft a polite follow-up email in the company's language and queue it for approval.`) }, T("writeFollowup"))))) : h("div", { class: "empty" }, T("none"))),
      h("div", { class: "card" }, h("h2", {}, icon("approvals"), T("pendingTitle")),
        s.pending.length ? h("div", { class: "list" }, s.pending.map((a) => h("div", { class: "li" }, h("span", { class: "badge orange" }, a.kind === "email" ? T("email") : T("form")), h("div", { class: "grow ellipsis" }, a.title), h("span", { class: "muted small" }, a.company || "")))) : h("div", { class: "empty" }, T("noPending")),
        h("div", { class: "row end" }, h("button", { class: "btn sm", onclick: () => go("approvals") }, T("goApprove") + " →"))),
      h("div", { class: "card" }, h("h2", {}, icon("mail"), T("recentMail")),
        s.recent_mail.length ? h("div", { class: "list" }, s.recent_mail.map((m) => h("div", { class: "li" }, m.status === "new" ? h("span", { class: "badge blue" }, T("unread")) : null,
          h("div", { class: "grow ellipsis" }, h("a", { href: "#inbox/" + m.id }, m.subject)), h("span", { class: "muted small ellipsis", style: "max-width:150px" }, m.company || m.from_name || m.from_addr)))) : h("div", { class: "empty" }, T("noMail"))),
      h("div", { class: "card" }, h("h2", {}, icon("help"), T("openQ")),
        s.questions.length ? h("div", { class: "list" }, s.questions.map((q) => h("div", { class: "li" }, q.priority === "high" ? h("span", { class: "badge red" }, T("urgent")) : null, h("div", { class: "grow" }, q.question)))) : h("div", { class: "empty" }, T("none")),
        h("div", { class: "row end" }, h("button", { class: "btn sm", onclick: () => go("profile") }, T("goAnswer") + " →"))))));
};

// ================================================================== chat
const TOOL_LABEL = {
  zh: { search_companies: "查公司库", get_company: "查看公司", add_company: "添加公司", enrich_company: "抓取官网", score_company: "评分", update_stage: "更新进度", get_pipeline: "查看进度", get_profile: "读取档案", edit_profile: "修改档案", list_questions: "查看问题", ask_user: "向你提问", record_answer: "记录回答", fetch_url: "读取网页", save_document: "保存文书", list_documents: "查看文书", read_document: "读取文件", build_resume: "生成简历", queue_email: "邮件 → 待审批", check_inbox: "收邮件", read_mail: "读邮件", link_mail: "关联邮件", browser_open: "浏览器打开", browser_read: "读取表单", browser_fill: "填写", browser_select: "选择", browser_check: "勾选", browser_upload: "上传", browser_click: "点击", web_search: "网络搜索", search_web: "网络搜索", WebSearch: "网络搜索", WebFetch: "读取网页" },
  ja: { search_companies: "企業DB検索", get_company: "企業詳細", add_company: "企業追加", enrich_company: "サイト取得", score_company: "スコア", update_stage: "進捗更新", get_pipeline: "進捗確認", get_profile: "プロフィール", edit_profile: "プロフィール編集", list_questions: "質問一覧", ask_user: "質問を追加", record_answer: "回答記録", fetch_url: "Web取得", save_document: "書類保存", list_documents: "書類一覧", read_document: "ファイル読込", build_resume: "履歴書生成", queue_email: "メール → 承認待ち", check_inbox: "メール取得", read_mail: "メール閲覧", link_mail: "メール紐付け", browser_open: "ブラウザで開く", browser_read: "フォーム読取", browser_fill: "入力", browser_select: "選択", browser_check: "チェック", browser_upload: "アップロード", browser_click: "クリック", web_search: "Web検索", search_web: "Web検索", WebSearch: "Web検索", WebFetch: "Web取得" },
};
const toolLabel = (n) => (TOOL_LABEL[LANG] || {})[n] || TOOL_LABEL.zh[n] || n;
function toolEl(name, input, result, isErr, running) {
  const inputStr = input ? JSON.stringify(input, null, 1).slice(0, 1500) : "";
  const brief = input ? Object.values(input).filter((v) => typeof v !== "object").join(" · ").slice(0, 100) : "";
  const el = h("details", { class: "tool" + (isErr ? " err" : "") },
    h("summary", {}, running ? h("span", { class: "spin" }) : (isErr ? "⚠" : h("span", { class: "ok" }, "✓")), h("b", {}, toolLabel(name)), h("span", { class: "ellipsis" }, brief)),
    h("div", { class: "body" }, (inputStr ? inputStr + "\n→ " : "") + (result ?? "…")));
  if (inputStr) el.dataset.input = inputStr;
  return el;
}
pages.chat = async (main, arg) => {
  let list = await api("/api/chats");
  let chatId = arg ? Number(arg) : list[0]?.id;
  if (!chatId) chatId = (await api("/api/chats", { method: "POST" })).id;
  if (!list.find((c) => c.id === chatId)) list = await api("/api/chats");
  const msgs = h("div", { class: "msgs" });
  const input = h("textarea", { placeholder: T("placeholder"), rows: 2 });
  const sendBtn = h("button", { class: "btn primary" }, icon("send"), T("send"));
  const stopBtn = h("button", { class: "btn", hidden: true }, T("stop"));
  const provName = (p) => T("prov_" + (p || SETTINGS.provider));
  main.append(h("div", { class: "chat" },
    h("div", { class: "chat-list" },
      h("button", { class: "btn primary", style: "width:100%;justify-content:center;margin-bottom:12px", onclick: async () => go("chat", (await api("/api/chats", { method: "POST" })).id) }, icon("plus"), T("newChat")),
      list.map((c) => h("div", { class: "chat-item" + (c.id === chatId ? " active" : ""), onclick: () => go("chat", c.id) }, icon("chat"),
        h("span", { class: "ellipsis" }, c.title === "新对话" ? T("newChat") : c.title),
        h("span", { class: "x", title: T("del"), onclick: async (e) => { e.stopPropagation(); if (confirm(T("confirmDel"))) { await api(`/api/chats/${c.id}`, { method: "DELETE" }); go("chat"); } } }, "✕")))),
    h("div", { class: "chat-main" }, msgs,
      h("div", { class: "composer" },
        h("div", { class: "box" }, input, h("div", { class: "row", style: "margin-top:6px" }, h("span", { class: "muted small", style: "margin-right:auto" }, "" + T("gateNote") + " · " + provName()), stopBtn, sendBtn))))));

  const chat = await api(`/api/chats/${chatId}`);
  const turnEl = (who) => {
    const bubble = h("div", { class: "bubble" });
    const t = h("div", { class: "turn " + who }, h("div", { class: "who " + (who === "user" ? "me" : "bot") }, who === "user" ? (OWNER.avatar || "🙂") : icon("bot")), bubble);
    msgs.append(t); return bubble;
  };
  let bubble = null;
  for (const e of chat.events) {
    if (e.t === "user") { turnEl("user").append(e.text); bubble = turnEl("bot"); bubble.append(h("div", { class: "prov" }, icon("spark"), provName(e.provider))); continue; }
    if (!bubble) bubble = turnEl("bot");
    if (e.t === "text") bubble.append(h("div", { class: "md", html: md(e.text) }));
    else if (e.t === "tool") bubble.append(toolEl(e.name, e.input, e.result, e.err));
    else if (e.t === "error") bubble.append(h("div", { class: "errbox" }, e.text));
  }
  if (!chat.events.length) {
    msgs.append(h("div", { class: "welcome" }, h("div", { class: "logo" }, icon("spark")), h("h2", {}, T("welcomeT")), h("div", { class: "muted" }, T("welcomeS")),
      h("div", { class: "caps" }, T("caps").map(([t, d], i) => h("div", { class: "cap", onclick: () => send(T("capPrompts")[i]) }, h("b", {}, t), h("span", { class: "muted" }, d))))));
  }
  msgs.scrollTop = msgs.scrollHeight;

  let busy = false;
  async function send(text) {
    if (!text.trim() || busy) return;
    busy = true; sendBtn.disabled = true; stopBtn.hidden = false; input.value = "";
    msgs.querySelector(".welcome")?.remove();
    turnEl("user").append(text);
    const box = turnEl("bot");
    box.append(h("div", { class: "prov" }, icon("spark"), provName()));
    let textEl = null, textBuf = "", thinkEl = null;
    const spinner = h("div", { class: "muted row" }, h("span", { class: "spin" }), T("thinking"));
    box.append(spinner); msgs.scrollTop = msgs.scrollHeight;
    const pending = {};
    try {
      const r = await fetch(`/api/chats/${chatId}/send`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text }) });
      const reader = r.body.getReader(); const dec = new TextDecoder(); let buf = "";
      for (;;) {
        const { value, done } = await reader.read(); if (done) break;
        buf += dec.decode(value, { stream: true });
        let i;
        while ((i = buf.indexOf("\n\n")) >= 0) {
          const line = buf.slice(0, i); buf = buf.slice(i + 2);
          if (!line.startsWith("data: ")) continue;
          const ev = JSON.parse(line.slice(6));
          if (ev.type === "text") {
            if (!textEl) { textEl = h("div", { class: "md" }); textBuf = ""; box.insertBefore(textEl, spinner); }
            textBuf += ev.text; textEl.innerHTML = md(textBuf);
          } else if (ev.type === "thinking_start") { thinkEl = h("div", { class: "thinking" }); box.insertBefore(thinkEl, spinner); }
          else if (ev.type === "thinking") { if (thinkEl) thinkEl.textContent += ev.text; }
          else if (ev.type === "tool_use") {
            textEl = null;
            const el = toolEl(ev.name, ev.input, ev.server ? "(server)" : null, false, !ev.server);
            if (ev.id) pending[ev.id] = el; box.insertBefore(el, spinner);
          } else if (ev.type === "tool_result") {
            const old = pending[ev.id]; const el = toolEl(ev.name || old?.querySelector("b")?.textContent, null, ev.content, ev.is_error);
            if (old) { el.querySelector(".body").textContent = (old.dataset.input ? old.dataset.input + "\n→ " : "") + ev.content; old.replaceWith(el); }
            if (/queue_email|browser_click/.test(ev.name)) refreshBadges();
          } else if (ev.type === "turn_end") { textEl = null; if (thinkEl && !thinkEl.textContent.trim()) thinkEl.remove(); thinkEl = null; }
          else if (ev.type === "error") box.insertBefore(h("div", { class: "errbox" }, ev.text), spinner);
          msgs.scrollTop = msgs.scrollHeight;
        }
      }
    } catch (e) { box.append(h("div", { class: "errbox" }, T("interrupted") + e.message)); }
    spinner.remove(); busy = false; sendBtn.disabled = false; stopBtn.hidden = true; refreshBadges();
  }
  sendBtn.onclick = () => send(input.value);
  stopBtn.onclick = () => api(`/api/chats/${chatId}/stop`, { method: "POST" });
  input.addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.shiftKey && !e.isComposing) { e.preventDefault(); send(input.value); } });
  const pp = sessionStorage.getItem("pendingPrompt"); if (pp) { sessionStorage.removeItem("pendingPrompt"); send(pp); }
  input.focus();
};

// ================================================================== approvals
// ================================================================== reviewer sub-agent panel
const SEV_CLASS = { high: "red", medium: "orange", low: "" };
function reviewPanel(target_kind, target_ref, r, onChanged) {
  const box = h("div", { class: "review" });
  const run = async () => { const nr = await api("/api/reviews", { method: "POST", body: { target_kind, target_ref } }); r = nr; render(); };
  async function refresh() { r = await api(`/api/reviews/${r.id}`); render(); }
  function render() {
    box.innerHTML = "";
    const head = h("div", { class: "row review-head" }, icon("check"), h("b", {}, T("rv_title")));
    box.append(head);
    if (!r) { head.append(h("span", { class: "muted small" }, "—"), h("button", { class: "btn sm", style: "margin-left:auto", onclick: run }, icon("spark"), T("rv_run"))); return; }
    if (r.status === "running") { head.append(h("span", { class: "muted small" }, h("span", { class: "spin" }), " ", T("rv_running"))); setTimeout(() => { if (box.isConnected) refresh(); }, 3000); return; }
    if (r.status === "failed") { head.append(h("span", { class: "badge red" }, T("rv_failed")), h("button", { class: "btn sm", style: "margin-left:auto", onclick: run }, T("rv_rerun"))); box.append(h("div", { class: "muted small" }, r.error || "")); return; }
    const issues = r.issues || [];
    const label = r.status === "dismissed" ? T("rv_dismissed") : r.status === "applied" ? (r.mode === "auto" ? T("rv_auto") : T("rv_applied")) : issues.length ? T("rv_n", { n: issues.length }) : T("rv_ok");
    head.append(h("span", { class: "badge " + (r.status === "applied" || !issues.length ? "green" : "orange") }, label), h("button", { class: "btn sm", style: "margin-left:auto", onclick: run }, T("rv_rerun")));
    if (r.summary) box.append(h("div", { class: "small", style: "margin:6px 0" }, r.summary));
    const checks = [];
    if (issues.length) box.append(h("div", { class: "review-list" }, issues.map((it) => {
      const cb = h("input", { type: "checkbox", checked: it.severity !== "low" && !it.applied, disabled: r.status !== "done" });
      checks.push(cb);
      return h("label", { class: "review-item" + (it.applied ? " applied" : "") }, cb,
        h("div", { class: "grow" }, h("div", { class: "row", style: "gap:6px" }, h("span", { class: "badge " + (SEV_CLASS[it.severity] || "") }, T("sev_" + it.severity)), h("span", { class: "badge" }, it.category || ""), it.field ? h("span", { class: "muted small" }, it.field) : null),
          h("div", { class: "diff" }, h("del", {}, it.quote || ""), " → ", h("ins", {}, it.suggestion === "" ? T("rv_del") : it.suggestion || "")),
          h("div", { class: "muted small" }, it.reason || "")));
    })));
    if (issues.length) box.append(h("details", { class: "small" }, h("summary", {}, T("rv_showRevised")),
      ...Object.entries(r.revised || {}).map(([k, v]) => h("div", {}, h("div", { class: "muted small" }, k), h("div", { class: "pre" }, v)))));
    const act = h("div", { class: "row end", style: "margin-top:8px" });
    const done = async (p) => { try { await p; toast(T("saved")); if (onChanged) onChanged(); } catch (e) { toast(e.message, 6000); } };
    if (r.status === "done" && issues.length) act.append(
      h("button", { class: "btn sm", onclick: () => done(api(`/api/reviews/${r.id}/dismiss`, { method: "POST" })) }, T("rv_dismiss")),
      h("button", { class: "btn sm", onclick: () => done(api(`/api/reviews/${r.id}/apply`, { method: "POST", body: { issues: checks.map((c, i) => c.checked ? i : -1).filter((i) => i >= 0) } })) }, T("rv_applySel")),
      h("button", { class: "btn sm primary", onclick: () => done(api(`/api/reviews/${r.id}/apply`, { method: "POST", body: {} })) }, T("rv_applyAll")));
    if (r.status === "applied") act.append(h("button", { class: "btn sm", onclick: () => done(api(`/api/reviews/${r.id}/revert`, { method: "POST" })) }, T("rv_revert")));
    if (act.childNodes.length) box.append(act);
  }
  render();
  return box;
}

pages.approvals = async (main) => {
  const all = await api("/api/actions");
  const RV = Object.fromEntries((await api("/api/reviews?target_kind=action")).map((r) => [String(r.target_ref), r]));
  const pending = all.filter((a) => a.status === "pending"), done = all.filter((a) => a.status !== "pending");
  const page = h("div", { class: "page" }, h("div", { class: "muted", style: "margin-bottom:14px" }, T("approvalsSub")));
  if (!pending.length) page.append(h("div", { class: "card empty" }, T("noPending")));
  for (const a of pending) page.append(a.kind === "email" ? emailCard(a) : formCard(a));
  page.append(h("h2", { style: "margin-top:26px" }, T("history")),
    h("div", { class: "card", style: "padding:0;overflow:auto" }, h("table", { class: "tbl" },
      h("tr", {}, ["#", T("kind"), T("title"), T("company"), T("status"), T("result"), T("time")].map((x) => h("th", {}, x))),
      done.slice(0, 80).map((a) => h("tr", {}, h("td", {}, a.id), h("td", {}, a.kind === "email" ? T("email") : T("form")), h("td", {}, a.title), h("td", {}, a.company || ""),
        h("td", {}, h("span", { class: `badge ${{ done: "green", failed: "red" }[a.status] || ""}` }, T("stat_" + a.status))),
        h("td", { class: "muted small", style: "max-width:300px" }, (a.result || "").slice(0, 120)), h("td", { class: "muted small" }, (a.decided_at || a.created_at || "").slice(5, 16)))))));
  main.append(page);

  function emailCard(a) {
    const p = a.payload;
    const to = h("input", { class: "input", style: "flex:1", value: (p.to || []).join(", ") });
    const cc = h("input", { class: "input", style: "flex:1", value: (p.cc || []).join(", ") });
    const subj = h("input", { class: "input", style: "width:100%", value: p.subject });
    const body = h("textarea", { class: "input", rows: 14 }, p.body);
    const att = h("input", { class: "input", style: "width:100%", value: (p.attachments || []).join("; ") });
    const acc = h("select", { class: "input" }, (SETTINGS.accounts || []).map((x) => h("option", { value: x.id, selected: p.account === x.id }, `${x.label} · ${x.address}`)));
    const collect = () => ({ ...p, account: acc.value, to: to.value.split(/[,;]\s*/).filter(Boolean), cc: cc.value.split(/[,;]\s*/).filter(Boolean), subject: subj.value, body: body.value, attachments: att.value.split(/;\s*/).filter(Boolean) });
    return h("div", { class: "card", style: "margin-bottom:16px" },
      h("div", { class: "row", style: "margin-bottom:10px" }, h("span", { class: "badge orange" }, icon("mail"), T("email")), h("b", {}, a.company || ""), h("span", { class: "muted small" }, p.purpose || ""), h("span", { class: "muted small", style: "margin-left:auto" }, `#${a.id} · ${a.created_at}`)),
      h("div", { class: "field" }, h("label", {}, `${T("account")} / ${T("to")} / ${T("cc")}`), h("div", { class: "row" }, acc, to, cc)),
      h("div", { class: "field" }, h("label", {}, T("subject")), subj),
      h("div", { class: "field" }, h("label", {}, T("body")), body),
      h("div", { class: "field" }, h("label", {}, T("attachments")), att, h("div", { class: "row" }, (p.attachments || []).map((f) => h("a", { href: `/api/file?path=${encodeURIComponent(f)}&download=1`, target: "_blank", class: "badge blue" }, f.split("/").pop())))),
      reviewPanel("action", a.id, RV[String(a.id)], () => route()),
      h("div", { class: "row end" },
        h("button", { class: "btn danger", onclick: async () => { await api(`/api/actions/${a.id}/reject`, { method: "POST", body: {} }); toast(T("rejected")); route(); } }, T("reject")),
        h("button", { class: "btn", onclick: async () => { const r = await api(`/api/actions/${a.id}`, { method: "PUT", body: { payload: collect() } }); toast(r.problems?.length ? r.problems.join("; ") : T("saved")); } }, T("saveEdit")),
        h("button", { class: "btn ok", onclick: async (e) => {
          if (!confirm(`${T("confirmSend")} ${to.value}?`)) return;
          e.currentTarget.disabled = true;
          try { await api(`/api/actions/${a.id}`, { method: "PUT", body: { payload: collect() } }); const r = await api(`/api/actions/${a.id}/approve`, { method: "POST" }); toast(r.result || T("sent")); route(); }
          catch (err) { toast(T("sendFail") + err.message, 6000); e.target.disabled = false; }
        } }, icon("send"), T("approveSend"))));
  }
  function formCard(a) {
    const p = a.payload;
    return h("div", { class: "card", style: "margin-bottom:16px" },
      h("div", { class: "row", style: "margin-bottom:8px" }, h("span", { class: "badge orange" }, T("form")), h("b", {}, a.company || ""), h("span", { class: "muted small", style: "margin-left:auto" }, `#${a.id} · ${a.created_at}`)),
      h("div", { class: "kv" }, h("div", { class: "k" }, T("page")), h("div", {}, h("a", { href: p.url, target: "_blank" }, p.title || p.url)),
        h("div", { class: "k" }, T("buttonToClick")), h("div", {}, h("b", {}, p.button || p.field_id)), h("div", { class: "k" }, T("note")), h("div", {}, p.summary || "—")),
      p.captcha ? h("div", { class: "warnbox" }, T("captchaNote")) : h("div", { class: "muted" }, T("checkNote")),
      h("div", { class: "row end", style: "margin-top:12px" },
        h("button", { class: "btn danger", onclick: async () => { await api(`/api/actions/${a.id}/reject`, { method: "POST", body: {} }); route(); } }, T("reject")),
        h("button", { class: "btn", onclick: async () => { await api(`/api/actions/${a.id}/mark_done`, { method: "POST" }); toast(T("recorded")); route(); } }, T("manualDone")),
        p.captcha ? null : h("button", { class: "btn ok", onclick: async (e) => { e.currentTarget.disabled = true; try { const r = await api(`/api/actions/${a.id}/approve`, { method: "POST" }); toast(r.result || "ok"); route(); } catch (err) { toast(err.message, 6000); } } }, T("approveClick"))));
  }
};

// ================================================================== pipeline
pages.pipeline = async (main) => {
  const { items } = await api("/api/pipeline");
  const page = h("div", { class: "page wide" }, h("div", { class: "muted", style: "margin-bottom:14px" }, `${items.length} ${T("pipelineSub")}`));
  const board = h("div", { class: "kanban" });
  for (const st of STAGES) {
    const its = items.filter((i) => i.stage === st);
    const col = h("div", { class: "col", style: `border-top-color:${STAGE_HEX[st]}` },
      h("h3", {}, h("span", {}, SL(st)), h("span", { class: "badge" }, its.length)),
      its.map((it) => h("div", { class: "kcard" + (it.followup_due ? " due" : ""), draggable: "true", ondragstart: (e) => e.dataTransfer.setData("text/plain", it.id), onclick: () => openCompany(it.id) },
        h("div", { class: "row", style: "gap:6px;flex-wrap:nowrap" }, h("div", { class: "t ellipsis grow" }, it.name),
          it.interview_notes ? h("span", { class: "note-ic interview", title: T("hasInterview") }, icon("interview")) : null,
          it.study_notes ? h("span", { class: "note-ic study", title: T("hasStudy") }, icon("notes")) : null),
        h("div", { class: "row", style: "gap:4px;margin-top:4px" }, typeBadge(it.types), it.score != null ? scoreEl(it.score) : null, it.followup_due ? h("span", { class: "badge orange" }, T("dueTag")) : null),
        h("div", { class: "n" }, it.note || ""), h("div", { class: "muted", style: "font-size:11px;margin-top:4px" }, (it.created_at || "").slice(0, 16)))));
    col.addEventListener("dragover", (e) => { e.preventDefault(); col.classList.add("drop"); });
    col.addEventListener("dragleave", () => col.classList.remove("drop"));
    col.addEventListener("drop", async (e) => {
      e.preventDefault(); col.classList.remove("drop");
      const id = e.dataTransfer.getData("text/plain"); const note = prompt(T("stageNote", { s: SL(st) }), "");
      if (note === null) return;
      await api(`/api/companies/${id}/stage`, { method: "POST", body: { stage: st, note } }); route();
    });
    board.append(col);
  }
  page.append(board); main.append(page);
};

// ================================================================== companies
const CF = { q: "", type: "", applied: "", min_score: "", prefecture: "", order: "score", offset: 0 };
pages.companies = async (main) => {
  const page = h("div", { class: "page wide" });
  const q = h("input", { class: "input", placeholder: T("kw"), value: CF.q, style: "width:300px" });
  const type = h("select", { class: "input" }, [["", T("allTypes")], ["1", T("types")["1"]], ["2", "IT"], ["1,2", T("types")["1,2"]], ["other", T("types").other]].map(([v, l]) => h("option", { value: v, selected: CF.type === v }, l)));
  const applied = h("select", { class: "input" }, [["", T("allStatus")], ["no", T("notContacted")], ["yes", T("contacted")]].map(([v, l]) => h("option", { value: v, selected: CF.applied === v }, l)));
  const pref = h("input", { class: "input", placeholder: T("pref"), value: CF.prefecture, style: "width:110px" });
  const minScore = h("input", { class: "input", placeholder: T("minScore"), type: "number", value: CF.min_score, style: "width:100px" });
  const order = h("select", { class: "input" }, [["score", T("byScore")], ["name", T("byName")], ["recent", T("recent")]].map(([v, l]) => h("option", { value: v, selected: CF.order === v }, l)));
  const result = h("div", { class: "card", style: "padding:0;overflow:auto" });
  const count = h("span", { class: "badge blue" });
  page.append(h("div", { class: "row", style: "margin-bottom:14px" }, q, type, applied, pref, minScore, order,
    h("button", { class: "btn primary", onclick: () => { CF.offset = 0; load(); } }, T("search")), count,
    h("button", { class: "btn", style: "margin-left:auto", onclick: () => askAgent(`Company DB filter: type=${type.value || "all"}, ${applied.value === "no" ? "not contacted" : "any status"}, keywords=${q.value || "none"}. Pick the 10 best fits for me, check their careers pages, score and rank them.`) }, icon("spark"), T("evalThese"))), result);
  q.addEventListener("keydown", (e) => { if (e.key === "Enter") { CF.offset = 0; load(); } });
  async function load() {
    Object.assign(CF, { q: q.value, type: type.value, applied: applied.value, prefecture: pref.value, min_score: minScore.value, order: order.value });
    const params = new URLSearchParams({ q: q.value, type: type.value, applied: applied.value, prefecture: pref.value, order: order.value, limit: 100, offset: CF.offset });
    if (minScore.value) params.set("min_score", minScore.value);
    const r = await api("/api/companies?" + params);
    count.textContent = T("total", { n: r.total });
    result.innerHTML = "";
    result.append(h("table", { class: "tbl" },
      h("tr", {}, ["th_score", "th_company", "th_type", "th_loc", "th_desc", "th_contact", "th_stage"].map((k) => h("th", {}, T(k)))),
      r.items.map((c) => h("tr", { class: "click", onclick: () => openCompany(c.id) },
        h("td", {}, scoreEl(c.score)), h("td", {}, h("b", {}, c.name), c.name_ja && c.name_ja !== c.name ? h("div", { class: "muted small" }, c.name_ja) : null),
        h("td", {}, typeBadge(c.types)), h("td", { class: "muted" }, c.prefecture || ""),
        h("td", { class: "muted", style: "max-width:440px;font-size:13px" }, (c.description || "").slice(0, 110)),
        h("td", {}, h("div", { class: "row", style: "gap:4px" }, c.careers_url ? h("span", { class: "badge green" }, T("careers")) : null, c.contact_emails ? h("span", { class: "badge" }, T("mail")) : null, c.contact_form_url ? h("span", { class: "badge" }, T("contactForm")) : null)),
        h("td", {}, stageBadge(c.stage))))));
    result.append(h("div", { class: "row", style: "padding:12px" },
      h("button", { class: "btn sm", disabled: CF.offset === 0, onclick: () => { CF.offset = Math.max(0, CF.offset - 100); load(); } }, "← " + T("prev")),
      h("span", { class: "muted small" }, `${CF.offset + 1}–${Math.min(CF.offset + 100, r.total)}`),
      h("button", { class: "btn sm", disabled: CF.offset + 100 >= r.total, onclick: () => { CF.offset += 100; load(); } }, T("next") + " →")));
  }
  main.append(page); load();
};

// notes shown inside the company drawer: interview notes open, study notes collapsible
function companyNotes(c, close) {
  const iv = (c.notes || []).filter((n) => n.kind === "interview"), st = (c.notes || []).filter((n) => n.kind === "study");
  const out = [];
  if (iv.length) out.push(h("div", { class: "section card note-card interview" },
    h("h2", {}, icon("interview"), T("noteInterview")),
    iv.map((n) => h("details", { open: true }, h("summary", {}, h("b", {}, n.title), h("span", { class: "muted small", style: "margin-left:8px" }, (n.updated_at || "").slice(0, 16)),
      h("a", { href: "#notes/" + n.id, style: "margin-left:auto", onclick: close }, T("editNote"))), noteBody(n)))));
  if (st.length) out.push(h("div", { class: "section card note-card study" },
    h("h2", {}, icon("notes"), T("noteStudy"), h("span", { class: "badge", style: "margin-left:8px" }, T("openN", { n: st.filter((n) => n.status !== "done").length }))),
    st.map((n) => h("details", {}, h("summary", {}, n.status === "done" ? h("span", { class: "badge green" }, T("done")) : null, h("b", {}, n.title), n.due ? h("span", { class: "badge orange", style: "margin-left:6px" }, n.due) : null,
      h("a", { href: "#notes/" + n.id, style: "margin-left:auto", onclick: close }, T("editNote"))), noteBody(n)))));
  return out;
}
function noteBody(n) { const d = h("div", { class: "md" }); d.innerHTML = md(n.body || ""); return d; }

async function openCompany(id) {
  const c = await api(`/api/companies/${id}`);
  const close = () => { bg.remove(); dr.remove(); };
  const bg = h("div", { class: "drawer-bg", onclick: close });
  const stageSel = h("select", { class: "input" }, STAGES.map((s) => h("option", { value: s }, SL(s))));
  const note = h("input", { class: "input", placeholder: T("note"), style: "flex:1" });
  const m = c.match;
  const list = (s) => { try { return JSON.parse(s || "[]"); } catch (_) { return [s]; } };
  const link = (u) => u ? h("a", { href: u, target: "_blank" }, u) : "—";
  const dr = h("div", { class: "drawer" },
    h("div", { class: "row" }, h("div", { class: "logo", style: "width:42px;height:42px" }, icon("building")), h("div", { class: "grow" }, h("div", { style: "font-size:19px;font-weight:800" }, c.name), c.name_ja ? h("div", { class: "muted small" }, c.name_ja) : null), scoreEl(m?.score), h("button", { class: "iconbtn", onclick: close }, icon("x"))),
    h("div", { class: "row", style: "margin-top:10px" }, typeBadge(c.types), h("span", { class: "badge" }, c.category === "A" ? T("classA") : c.category || ""), c.tier ? h("span", { class: "badge orange" }, T("backup")) : null, ...(c.sources || "").split(",").filter(Boolean).map((s) => h("span", { class: "badge sky" }, s))),
    h("div", { class: "kv" }, h("div", { class: "k" }, T("website")), h("div", {}, link(c.website)), h("div", { class: "k" }, T("careersPage")), h("div", {}, link(c.careers_url)),
      h("div", { class: "k" }, T("emails")), h("div", {}, c.contact_emails || "—"), h("div", { class: "k" }, T("contactForm")), h("div", {}, link(c.contact_form_url)),
      h("div", { class: "k" }, T("loc")), h("div", {}, [c.prefecture, c.address].filter(Boolean).join(" ") || "—"), h("div", { class: "k" }, T("field")), h("div", {}, c.tech_field || "—"),
      h("div", { class: "k" }, T("univ")), h("div", {}, c.university || "—")),
    h("div", { class: "row" },
      h("button", { class: "btn primary", onclick: () => { close(); askAgent(`Research #${c.id} ${c.name}: check the careers page and recent news, evaluate fit, score it, and tell me which role to apply for and through which channel.`); } }, icon("spark"), T("research")),
      h("button", { class: "btn", onclick: () => { close(); askAgent(`Prepare an application to #${c.id} ${c.name}: confirm the role and channel, write the application text in the company's language (email → approval queue; web form → fill it in the browser and wait for my approval before submitting).`); } }, icon("send"), T("apply")),
      h("button", { class: "btn", onclick: async (e) => { e.currentTarget.disabled = true; await api(`/api/companies/${c.id}/enrich`, { method: "POST" }); close(); openCompany(c.id); } }, icon("sync"), T("rescrape"))),
    ...companyNotes(c, close),
    m ? h("div", { class: "section card" }, h("h2", {}, `${T("fitTitle")} · ${m.score}`), h("div", {}, h("b", {}, T("fitRoles")), list(m.fit_roles).join(" / ")),
      h("ul", {}, list(m.reasons).map((r) => h("li", {}, r))), list(m.concerns).length ? h("div", { class: "muted" }, T("concerns") + list(m.concerns).join("; ")) : null) : null,
    h("div", { class: "section" }, h("h2", {}, T("progress")),
      c.history.length ? h("div", { class: "list" }, c.history.map((o) => h("div", { class: "li" }, stageBadge(o.stage), h("div", { class: "grow small" }, o.note || ""), h("span", { class: "muted small" }, (o.created_at || "").slice(0, 16))))) : h("div", { class: "muted" }, T("noRecord")),
      h("div", { class: "row", style: "margin-top:10px" }, stageSel, note, h("button", { class: "btn", onclick: async () => { await api(`/api/companies/${c.id}/stage`, { method: "POST", body: { stage: stageSel.value, note: note.value } }); close(); openCompany(c.id); } }, T("record")))),
    c.mails.length ? h("div", { class: "section" }, h("h2", {}, T("mails")), h("div", { class: "list" }, c.mails.map((x) => h("div", { class: "li" }, h("a", { href: "#inbox/" + x.id, onclick: close }, x.subject), h("span", { class: "muted small", style: "margin-left:auto" }, x.date))))) : null,
    c.documents.length ? h("div", { class: "section" }, h("h2", {}, T("docs")), h("div", { class: "list" }, c.documents.map((d) => h("div", { class: "li" }, h("span", { class: "badge" }, d.kind), h("a", { href: `/api/file?path=${encodeURIComponent(d.path)}&download=1`, target: "_blank" }, d.title || d.path.split(/[\\/]/).pop()), h("span", { class: "muted small", style: "margin-left:auto" }, d.status))))) : null,
    h("div", { class: "section" }, h("h2", {}, T("siteText")), h("div", { class: "pre" }, c.description || c.homepage_text || "—")),
    c.careers_text ? h("div", { class: "section" }, h("h2", {}, T("careersText")), h("div", { class: "pre" }, c.careers_text)) : null);
  document.body.append(bg, dr);
}

// ================================================================== inbox
pages.inbox = async (main, arg) => {
  const page = h("div", { class: "page wide" });
  const listBox = h("div", { class: "card", style: "padding:0" }), view = h("div", { class: "card" });
  const status = h("select", { class: "input" }, [["", T("allStatus")], ["new", T("unread")], ["read", T("read")], ["handled", T("handled")]].map(([v, l]) => h("option", { value: v }, l)));
  const fetchBtn = h("button", { class: "btn primary", onclick: async () => {
    fetchBtn.disabled = true; fetchBtn.lastChild.textContent = T("fetching");
    try { const r = await api("/api/inbox/fetch", { method: "POST", body: { days: 21 } }); toast(T("newMails", { n: r.new })); load(); } catch (e) { toast(e.message, 6000); }
    fetchBtn.disabled = false; fetchBtn.lastChild.textContent = T("fetchMail");
  } }, icon("inbox"), h("span", {}, T("fetchMail")));
  page.append(h("div", { class: "row", style: "margin-bottom:14px" }, h("span", { class: "muted" }, T("inboxSub")), h("span", { style: "margin-left:auto" }), status, fetchBtn), h("div", { class: "split" }, listBox, view));
  status.onchange = load;
  async function load() {
    const items = await api("/api/inbox?status=" + status.value);
    listBox.innerHTML = "";
    if (!items.length) listBox.append(h("div", { class: "empty" }, T("noMails")));
    for (const m of items) listBox.append(h("div", { class: `mailrow ${m.status}` + (String(m.id) === arg ? " active" : ""), onclick: () => go("inbox", m.id) },
      h("div", { class: "row" }, h("span", { class: "s ellipsis grow" }, m.subject || "—"), m.status === "new" ? h("span", { class: "badge blue" }, T("unread")) : null),
      h("div", { class: "row muted small" }, h("span", { class: "ellipsis grow" }, m.company ? m.company : (m.from_name || m.from_addr)), h("span", {}, (m.date || "").slice(5, 16)))));
  }
  async function show(id) {
    const m = await api(`/api/inbox/${id}`);
    view.innerHTML = ""; if (!m) return;
    view.append(h("h2", { style: "font-size:17px" }, m.subject),
      h("div", { class: "kv" }, h("div", { class: "k" }, T("from")), h("div", {}, `${m.from_name || ""} <${m.from_addr}>`), h("div", { class: "k" }, T("timeAcc")), h("div", {}, `${m.date} · ${m.account}`),
        h("div", { class: "k" }, T("company")), h("div", {}, m.company ? h("a", { href: "#", onclick: (e) => { e.preventDefault(); openCompany(m.company_id); } }, m.company) : h("span", { class: "muted" }, T("unlinked")))),
      h("div", { class: "row", style: "margin-bottom:12px" },
        h("button", { class: "btn primary", onclick: () => askAgent(`Read mail #${m.id} ("${m.subject}"), summarise it, update the company's stage, and draft a reply into the approval queue.`) }, icon("spark"), T("summarize")),
        h("button", { class: "btn", onclick: async () => { await api(`/api/inbox/${m.id}`, { method: "POST", body: { status: "handled" } }); toast(T("handled")); load(); } }, icon("check"), T("markHandled")),
        h("button", { class: "btn", onclick: async () => { const cid = prompt(T("linkPrompt")); if (cid) { await api(`/api/inbox/${m.id}`, { method: "POST", body: { company_id: Number(cid) } }); show(m.id); load(); } } }, T("linkCompany"))),
      h("div", { class: "pre", style: "max-height:none" }, m.body));
  }
  main.append(page); await load(); if (arg) show(arg); else view.append(h("div", { class: "empty" }, T("pickMail")));
};

// ================================================================== documents
// ================================================================== notes (study / interview / to-do)
let NOTE_TAB = "study";
pages.notes = async (main, arg) => {
  const page = h("div", { class: "page wide" });
  let all = await api("/api/notes");
  if (arg) { const n = all.find((x) => String(x.id) === String(arg)); if (n) NOTE_TAB = n.kind; }
  const tabs = h("div", { class: "tabs" });
  const listBox = h("div", { class: "card", style: "padding:0" }), view = h("div", { class: "card" });
  page.append(h("div", { class: "row", style: "margin-bottom:10px" }, h("span", { class: "muted" }, T("notesSub")), h("span", { style: "margin-left:auto" }),
    h("button", { class: "btn", onclick: () => askAgent("Read my notes (list_notes), check the pipeline and recent mail, then update the study notes, interview notes and the overall to-do note so they match the current state.") }, icon("spark"), T("prepNotes")),
    h("button", { class: "btn primary", onclick: () => edit({ kind: NOTE_TAB, title: "", body: "", company_id: null, status: "open" }) }, icon("plus"), T("newNote"))),
    tabs, h("div", { class: "split" }, listBox, view));
  function renderTabs() {
    tabs.innerHTML = "";
    for (const k of ["study", "interview", "todo"]) {
      const n = all.filter((x) => x.kind === k && (k === "interview" || x.status !== "done")).length;
      tabs.append(h("button", { class: NOTE_TAB === k ? "active" : "", onclick: () => { NOTE_TAB = k; renderTabs(); renderList(); } }, icon(k === "interview" ? "interview" : "notes"), " ", T("tab_" + k), n ? h("span", { class: "badge", style: "margin-left:6px" }, n) : null));
    }
  }
  function renderList(selId) {
    listBox.innerHTML = "";
    const its = all.filter((x) => x.kind === NOTE_TAB);
    if (!its.length) { listBox.append(h("div", { class: "muted", style: "padding:16px" }, T("noNotes"))); view.innerHTML = ""; return; }
    for (const n of its) {
      listBox.append(h("div", { class: "li click note-li" + (n.status === "done" ? " done" : ""), onclick: () => show(n.id) },
        h("div", { class: "grow" }, h("div", { class: "ellipsis" }, h("b", {}, n.title)),
          h("div", { class: "muted small" }, n.company ? `${n.company} · ` : `${T("general")} · `, (n.updated_at || n.created_at || "").slice(0, 16))),
        n.due ? h("span", { class: "badge orange" }, n.due) : null, n.status === "done" ? h("span", { class: "badge green" }, T("done")) : null));
    }
    show(selId || (its.find((x) => String(x.id) === String(arg)) || its[0]).id);
  }
  async function show(id) {
    const n = await api(`/api/notes/${id}`);
    view.innerHTML = "";
    view.append(h("div", { class: "row", style: "margin-bottom:8px" },
      h("div", { class: "grow" }, h("div", { style: "font-size:17px;font-weight:750" }, n.title),
        h("div", { class: "muted small" }, n.company ? h("a", { href: "javascript:void 0", onclick: () => openCompany(n.company_id) }, n.company) : T("general"), n.due ? ` · ${n.due}` : "")),
      n.kind !== "interview" ? h("button", { class: "btn sm", onclick: async () => { await api(`/api/notes/${n.id}/status`, { method: "POST", body: { status: n.status === "done" ? "open" : "done" } }); all = await api("/api/notes"); renderTabs(); renderList(n.id); } }, icon("check"), n.status === "done" ? T("reopen") : T("markDone")) : null,
      h("button", { class: "btn sm", onclick: () => edit(n) }, T("editNote")),
      h("button", { class: "btn sm", onclick: async () => { if (!confirm(T("del") + "?")) return; await api(`/api/notes/${n.id}`, { method: "DELETE" }); all = await api("/api/notes"); renderTabs(); renderList(); } }, icon("x"))),
      noteBody(n));
  }
  function edit(n) {
    view.innerHTML = "";
    const title = h("input", { class: "input", placeholder: T("noteTitle"), value: n.title || "", style: "width:100%" });
    const kind = h("select", { class: "input" }, ["study", "interview", "todo"].map((k) => h("option", { value: k, selected: n.kind === k }, T("tab_" + k))));
    const cid = h("input", { class: "input", placeholder: T("noteCompany"), value: n.company_id ?? "", style: "width:170px" });
    const due = h("input", { class: "input", placeholder: T("noteDue"), value: n.due || "", style: "width:150px" });
    const body = h("textarea", { class: "input", style: "width:100%;height:60vh;font-family:var(--mono);font-size:13px" });
    body.value = n.body || "";
    view.append(h("div", { class: "row", style: "margin-bottom:8px" }, kind, cid, due), title, h("div", { style: "height:8px" }), body,
      h("div", { class: "row", style: "margin-top:8px;justify-content:flex-end" },
        h("button", { class: "btn", onclick: () => n.id ? show(n.id) : renderList() }, T("cancel")),
        h("button", { class: "btn primary", onclick: async () => {
          const saved = await api("/api/notes", { method: "POST", body: { id: n.id, kind: kind.value, title: title.value || "untitled", body: body.value, company_id: cid.value ? Number(cid.value) : null, due: due.value || null, status: n.status || "open" } });
          toast(T("saved")); all = await api("/api/notes"); NOTE_TAB = saved.kind; renderTabs(); renderList(saved.id);
        } }, T("saveNote"))));
  }
  renderTabs(); renderList(arg);
  main.append(page);
};

pages.documents = async (main) => {
  const { documents, finals } = await api("/api/documents");
  const RV = Object.fromEntries((await api("/api/reviews?target_kind=document")).map((r) => [r.target_ref, r]));
  const rvBadge = (d) => { const r = RV[d.path]; if (!r) return null; const n = (r.issues || []).length;
    return h("span", { class: "badge " + (r.status === "running" ? "" : r.status === "failed" ? "red" : r.status === "applied" || !n ? "green" : "orange"), title: T("rv_title") },
      r.status === "running" ? "…" : r.status === "applied" ? "✓" : r.status === "failed" ? "!" : n ? String(n) : "✓"); };
  const page = h("div", { class: "page wide" });
  const buildBtn = (variant, label) => h("button", { class: "btn", onclick: async (e) => { const b = e.currentTarget; b.disabled = true; b.textContent = T("generating"); try { await api("/api/documents/build", { method: "POST", body: { variant } }); toast(T("regenerated")); route(); } catch (err) { toast(err.message, 6000); b.disabled = false; } } }, label);
  page.append(h("div", { class: "card" }, h("h2", {}, icon("documents"), T("readyPdf")),
    h("div", { class: "grid cols-3" }, finals.map((f) => h("div", { class: "card", style: "box-shadow:none;display:flex;gap:10px;align-items:center" }, h("div", { class: "stat" }, h("div", { class: "ic c-rose" }, icon("documents"))), h("div", { class: "grow ellipsis small" }, f.split("/").pop()),
      h("a", { class: "btn sm", href: `/api/file?path=${encodeURIComponent(f)}`, target: "_blank" }, T("preview")), h("a", { class: "btn sm", href: `/api/file?path=${encodeURIComponent(f)}&download=1` }, T("download"))))),
    h("div", { class: "row", style: "margin-top:12px" }, h("span", { class: "muted" }, T("regen")), buildBtn("rirekisho", T("rireki")), buildBtn("en", T("resumeEn")), buildBtn("en_no_phone", T("resumeNoPhone")), buildBtn("all", T("all")))));
  const editor = h("div");
  page.append(h("div", { class: "card", style: "margin-top:16px;padding:0;overflow:auto" }, h("table", { class: "tbl" },
    h("tr", {}, [T("kind"), T("title"), T("company"), T("lang"), T("status"), T("rv_title"), T("updated"), ""].map((x) => h("th", {}, x))),
    documents.map((d) => h("tr", {}, h("td", {}, h("span", { class: "badge" }, d.kind)), h("td", {}, d.title || d.path.split(/[\\/]/).pop()), h("td", {}, d.company || T("general")), h("td", {}, d.lang),
      h("td", {}, h("span", { class: `badge ${{ final: "green", submitted: "blue", needs_info: "orange" }[d.status] || ""}` }, d.status)), h("td", {}, rvBadge(d)), h("td", { class: "muted small" }, (d.updated_at || d.created_at || "").slice(0, 16)),
      h("td", {}, /\.(md|txt)$/i.test(d.path) ? h("button", { class: "btn sm", onclick: () => edit(d.path) }, T("viewEdit")) : h("a", { class: "btn sm", href: `/api/file?path=${encodeURIComponent(d.path)}&download=1` }, T("download"))))))), editor);
  async function edit(path) {
    const rel = path.replace(/\\/g, "/").replace(/^.*?\/outbox\//, "outbox/");
    const f = await api(`/api/file?path=${encodeURIComponent(rel)}`);
    const ta = h("textarea", { class: "input mono", rows: 26 }, f.text);
    editor.innerHTML = "";
    editor.append(h("div", { class: "card", style: "margin-top:16px" }, h("div", { class: "row", style: "margin-bottom:10px" }, h("b", {}, rel), h("span", { style: "margin-left:auto" }),
      h("button", { class: "btn primary", onclick: async () => { await api("/api/file", { method: "PUT", body: { path: rel, text: ta.value } }); toast(T("saved")); } }, T("save"))), ta,
      reviewPanel("document", path, RV[path], async () => { const f2 = await api(`/api/file?path=${encodeURIComponent(rel)}`); ta.value = f2.text; })));
    editor.scrollIntoView({ behavior: "smooth" });
  }
  main.append(page);
};

// ================================================================== profile, questions, knowledge
let profileTab = "q";
pages.profile = async (main) => {
  const [p, qs, kn] = await Promise.all([api("/api/profile"), api("/api/questions?status=all"), api("/api/knowledge")]);
  const open = qs.filter((q) => q.status === "open"), closed = qs.filter((q) => q.status !== "open");
  const page = h("div", { class: "page" });
  const tabs = h("div", { class: "tabs" }, [["q", `${T("tabQ")} (${open.length})`], ["p", T("tabProfile")], ["k", T("tabKnow")]].map(([k, l]) => h("button", { class: profileTab === k ? "on" : "", onclick: () => { profileTab = k; route(); } }, l)));
  page.append(tabs);
  if (profileTab === "q") {
    page.append(h("div", { class: "grid cols-2" },
      h("div", {}, open.length ? open.map((q) => {
        const inp = h("textarea", { class: "input", rows: 2, placeholder: T("answerPh") });
        return h("div", { class: "card", style: "margin-bottom:12px" },
          h("div", { class: "row" }, q.priority === "high" ? h("span", { class: "badge red" }, T("urgent")) : null, h("span", { class: "badge" }, q.topic || "—"), h("span", { class: "muted small" }, "#" + q.id)),
          h("div", { style: "margin:8px 0;font-weight:500" }, q.question), q.needed_for ? h("div", { class: "muted small", style: "margin-bottom:6px" }, T("usedFor") + q.needed_for) : null, inp,
          h("div", { class: "row end", style: "margin-top:8px" },
            h("button", { class: "btn sm danger", onclick: async () => { await api(`/api/questions/${q.id}/answer`, { method: "POST", body: { answer: "", drop: true } }); route(); } }, T("notNeeded")),
            h("button", { class: "btn sm", onclick: () => { if (inp.value.trim()) askAgent(`Answer to question #${q.id} "${q.question}": ${inp.value}\nRecord the answer, update profile.md and any affected documents.`); } }, T("submitAgent")),
            h("button", { class: "btn sm primary", onclick: async () => { if (!inp.value.trim()) return; await api(`/api/questions/${q.id}/answer`, { method: "POST", body: { answer: inp.value } }); toast(T("recorded")); route(); } }, T("submit"))));
      }) : h("div", { class: "card empty" }, T("none"))),
      h("div", { class: "card" }, h("h2", {}, T("answered")), h("div", { class: "list" }, closed.slice(0, 50).map((q) => h("div", { class: "li", style: "align-items:flex-start" },
        h("span", { class: `badge ${q.status === "answered" ? "green" : ""}` }, q.status === "answered" ? T("answered") : T("dropped")), h("div", { class: "grow" }, h("div", { class: "small" }, q.question), h("div", { class: "muted small" }, q.answer || ""))))))));
  } else {
    const isP = profileTab === "p";
    const ta = h("textarea", { class: "input mono", rows: 32 }, isP ? p.markdown : kn.text);
    page.append(h("div", { class: "card" }, h("div", { class: "row", style: "margin-bottom:8px" }, h("span", { class: "muted" }, isP ? T("profileNote") : T("knowNote")), h("span", { style: "margin-left:auto" }),
      h("button", { class: "btn primary", onclick: async () => { await api(isP ? "/api/profile" : "/api/knowledge", { method: "PUT", body: isP ? { markdown: ta.value } : { text: ta.value } }); toast(T("saved")); } }, T("save"))), ta));
  }
  main.append(page);
};

// ================================================================== settings
pages.settings = async (main) => {
  await loadSettings(); const s = SETTINGS;
  const page = h("div", { class: "page" });
  const provCard = (p, body) => h("div", { class: "provcard" + (s.provider === p ? " on" : ""), onclick: async (e) => { if (e.target.closest("input,select,button")) return; await api("/api/settings/agent", { method: "POST", body: { provider: p } }); route(); } },
    h("div", { class: "t" }, h("span", { class: "pill", style: "height:auto;padding:0;border:0;background:none" }, h("span", { class: "dot" + (s.providers[p].ready ? "" : " off") })), T("prov_" + p), s.provider === p ? h("span", { class: "badge blue" }, "✓") : null),
    h("div", { class: "d" }, T("provd_" + p)), h("div", { style: "margin-top:10px" }, body));
  // claude api
  const key = h("input", { class: "input", type: "password", placeholder: s.api_key_set ? T("isSet") : "sk-ant-…", style: "width:100%" });
  const apiBody = h("div", {}, h("div", { class: "row" }, key, h("button", { class: "btn", onclick: async () => { if (!key.value) return; await api("/api/settings/apikey", { method: "POST", body: { key: key.value } }); toast(T("keySaved")); route(); } }, T("save"))), h("div", { class: "muted small", style: "margin-top:6px" }, `${T("apiKey")}: ${s.api_key_set ? T("isSet") : T("notSet")} · ${s.model}`));
  // cli
  const cliModel = h("select", { class: "input" }, [["", "default"], ["opus", "opus"], ["sonnet", "sonnet"], ["haiku", "haiku"]].map(([v, l]) => h("option", { value: v, selected: s.cli_model === v }, l)));
  cliModel.onchange = async () => { await api("/api/settings/agent", { method: "POST", body: { cli_model: cliModel.value } }); toast(T("saved")); };
  const cliBody = h("div", {}, h("div", { class: "row" }, h("span", { class: "small muted" }, T("cliModel")), cliModel), h("div", { class: "muted small", style: "margin-top:6px" }, T("cliNote")), h("div", { class: "mono", style: "margin-top:4px;font-size:11px" }, s.providers.claude_cli.detail));
  // openai-compatible
  const oa = s.openai || {};
  const preset = h("select", { class: "input" }, Object.entries(s.presets).map(([k, v]) => h("option", { value: k, selected: oa.preset === k }, v.label)));
  const base = h("input", { class: "input", style: "width:100%", value: oa.base_url || "", placeholder: "https://…/v1" });
  const model = h("input", { class: "input", style: "width:100%", value: oa.model || "" });
  const oakey = h("input", { class: "input", type: "password", style: "width:100%", placeholder: s.openai_keys[oa.preset] ? T("isSet") : "API key" });
  preset.onchange = () => { const pr = s.presets[preset.value]; base.value = pr.base_url; model.value = pr.model; oakey.placeholder = s.openai_keys[preset.value] ? T("isSet") : "API key"; };
  const oaBody = h("div", {},
    h("div", { class: "field" }, h("label", {}, T("preset")), preset), h("div", { class: "field" }, h("label", {}, T("baseUrl")), base),
    h("div", { class: "field" }, h("label", {}, T("modelName")), model), h("div", { class: "field" }, h("label", {}, T("oaKey")), oakey),
    h("div", { class: "row" }, h("span", { class: "muted small grow" }, T("oaNote")), h("button", { class: "btn primary", onclick: async () => { await api("/api/settings/agent", { method: "POST", body: { openai: { preset: preset.value, base_url: base.value.trim(), model: model.value.trim() }, openai_key: oakey.value } }); toast(T("saved")); route(); } }, T("save"))));
  const rvMode = h("div", { class: "row", style: "gap:8px;flex-wrap:wrap" }, ["off", "suggest", "auto"].map((m) => h("label", { class: "provcard" + (s.review_mode === m ? " on" : ""), style: "flex:1;min-width:200px;cursor:pointer" },
    h("input", { type: "radio", name: "rvmode", checked: s.review_mode === m, onchange: async () => { await api("/api/settings/agent", { method: "POST", body: { review_mode: m } }); toast(T("saved")); route(); } }), " ", h("b", {}, T("rv_mode_" + m)))));
  page.append(h("div", { class: "card", style: "margin-bottom:16px" }, h("h2", {}, icon("check"), T("rv_mode")), h("div", { class: "muted", style: "margin:-6px 0 12px" }, T("rv_modeSub")), rvMode, h("div", { class: "muted small", style: "margin-top:8px" }, T("rv_kb"))));
  page.append(h("div", { class: "card" }, h("h2", {}, icon("spark"), T("backend")), h("div", { class: "muted", style: "margin:-6px 0 12px" }, T("backendSub")),
    h("div", { class: "grid cols-3" }, provCard("claude_api", apiBody), provCard("claude_cli", cliBody), provCard("openai", oaBody))));
  page.append(h("div", { class: "card", style: "margin-top:16px" }, h("h2", {}, T("uiLang")),
    h("div", { class: "seg" }, [["zh", "中文"], ["ja", "日本語"], ["en", "English"]].map(([v, l]) => h("button", { class: LANG === v ? "on" : "", onclick: () => setLang(v) }, l)))));
  page.append(h("div", { class: "card", style: "margin-top:16px" }, h("h2", {}, icon("mail"), T("mailAccounts")), h("div", { class: "muted small", style: "margin-bottom:10px" }, T("mailNote")),
    s.accounts.map((a) => {
      const pw = h("input", { class: "input", type: "password", placeholder: a.has_password ? T("isSet") : "app password", style: "width:220px" });
      return h("div", { class: "li" }, h("div", { class: "grow" }, h("b", {}, a.label), " ", h("span", { class: "muted small" }, a.address)),
        a.has_password ? h("span", { class: "badge green" }, T("canUse")) : h("span", { class: "badge orange" }, T("notSet")), pw,
        h("button", { class: "btn", onclick: async (e) => { if (!pw.value) return; const b = e.currentTarget; b.disabled = true; try { await api(`/api/settings/mail/${a.id}/password`, { method: "POST", body: { password: pw.value } }); toast(T("loginOk")); route(); } catch (err) { toast(err.message, 6000); b.disabled = false; } } }, T("verifySave")),
        h("label", { class: "row small", style: "gap:4px" }, h("input", { type: "radio", name: "defacc", checked: s.default_account === a.id, onchange: async () => { await api("/api/settings/default_account", { method: "POST", body: { account: a.id } }); toast(T("defaultChanged")); } }), T("defaultSend")));
    })));
  page.append(h("div", { class: "card", style: "margin-top:16px" }, h("h2", {}, "" + T("rules")), h("ul", { style: "margin:0" }, ["rule1", "rule2", "rule3", "rule4"].map((r) => h("li", {}, T(r))))));
  main.append(page);
};

route();
