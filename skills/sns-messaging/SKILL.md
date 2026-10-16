---
name: sns-messaging
description: How to write job-search messages on SNS / chat-style channels (LinkedIn messages, Wantedly messages, X / Facebook DMs, Slack-like recruiter chats) for the candidate, and how they differ from e-mail. Use this skill whenever a reply or first message goes through LinkedIn, Wantedly, a DM or any chat UI - e.g. "帮我在LinkedIn回复", "Wantedly上的消息怎么回", "给他发个DM", "对方在LinkedIn联系我了" - and also when timing a message ("17点半发送"). Keep using the japan-job-search skill for facts, pipeline updates and company research; this skill only governs tone, length and format of chat messages.
---

# SNS / chat messages for the job search

E-mail and SNS are different genres. Writing a LinkedIn message like a business e-mail (宛名ブロック、
「お世話になっております」、長い自己紹介、署名) reads as stiff and copy-pasted. Chat messages are short,
start with the point, and mirror the other person's tone. Facts still come only from the profile, and the
company must be researched on its live site first (company descriptions in the database can be stale).

## Before writing
1. Read the whole thread and match the counterpart: length, politeness level, emoji use. A CEO who writes
   two lines gets a short reply, not an essay.
2. Check the company's current business on its site / latest news (not just the database). If the person
   corrected something, acknowledge it in one line - no long apology.
3. Know what you want from this message (one ask: a chat, a time slot, a question answered).

## Japanese SNS tone (LinkedIn / Wantedly / DM)
- Polite です・ます, but light: 「ありがとうございます」「失礼しました」「ぜひお話を伺いたいです」「〜できたら嬉しいです」.
  Avoid e-mail formulas: 「お世話になっております」「何卒よろしくお願い申し上げます」「〜させていただきたく存じます」.
- Address: start with 「田中さん、」 merged into the first sentence (no 「株式会社〇〇 代表取締役 〇〇様」 block). Use 様 only if the
  other side writes very formally.
- No signature block (name / affiliation / e-mail / phone) - the profile shows who you are. Add contact details
  only when they ask.
- Length: 3–8 short lines (~150–350 字). One topic per message; split if needed.
- Conclusion first, then one or two reasons with a concrete detail, then the ask.
- Line breaks between ideas; no bullet lists unless giving time slots.
- Emoji: none by default; one simple emoji is fine only if the other side uses them.
- Honesty about gaps still applies, in one short clause (「〇〇を本番で運用した経験はまだありませんが」).

## English SNS tone
- "Hi <first name>," → 2–5 short sentences → clear ask → "Best," + first name (or just the name).
- Contractions are fine (I'm, I'd). No "Dear Sir/Madam", no formal sign-off block.

## Time slots and scheduling
- Check the user's calendars (every connected Google Calendar) and the pipeline
  (other interviews, test deadlines) first; offer 2–3 slots, or say the earlier slots still work.
- When the user wants the message sent at a specific time, fill it in at that time and send it then; tell the
  user the exact time it went out.

## After sending
- Record it: `python jobdb.py stage <id> replied --note "<date> LinkedIn 返信: …"`.
- If a meeting is agreed: add it to Google Calendar, create an interview note (agent notes, kind=interview).

## Example (LinkedIn, Japanese)
Counterpart (fictional): 「実はその事業はもう譲渡していて…改めて調べていただいて、良さそうであればお時間いただきたいです。」

```
田中さん、ご指摘ありがとうございます。古い情報のままお送りしてしまい、失礼しました。
改めてサイトを拝見して、現在の〇〇の取り組みにとても興味を持ちました。

自分でも LLM エージェントを作っていて、△△の設計に関心があるので、ぜひお話を伺いたいです（□□を本番で運用した経験はまだありません）。

日程は先日お送りした候補でも、別の日でも大丈夫です。お時間いただけたら嬉しいです。
```

## Fact check
Run the writing reviewer (`reviewer.check({"text": msg}, "sns_message", "ja", company_id)`) before sending: it
flags claims that the profile does not support and suggests the profile fact instead.

## Self-check
- Would this look natural as a chat bubble? If it has a 宛名 block, a signature or 「お世話になっております」, cut them.
- Is it shorter than the e-mail version would be? Does the first sentence answer what they asked?
- Every fact traceable to the profile; company facts checked on the live site.
