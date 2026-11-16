# shell-harbor-slack

Lets the Shell Harbor team subagents reply in Slack #claude under their own names and portraits, instead of from Robert's account.

How it works: the scheduled task "Shell Harbor team replies in Slack #claude" commits a reply file to `outbox/`. The GitHub Action in `.github/workflows/post.yml` checks it with `post_as.py --dry-run`, then posts each message through the **Shell Harbor Team** Slack app with that person's name and photo from `personas.json`.

## One-time setup (Robert)

1. **Slack app scopes.** Go to api.slack.com/apps, open **Shell Harbor Team**, then **OAuth & Permissions**. Under *Bot Token Scopes* add `chat:write` and `chat:write.customize`. Click **Reinstall to Workspace**, then copy the **Bot User OAuth Token** (starts with `xoxb-`).
2. **GitHub secret.** In this repo go to **Settings → Secrets and variables → Actions → New repository secret**. Name: `SLACK_BOT_TOKEN`, value: the token. Never paste the token into Slack, a chat or a file.
3. **Test.** Go to **Actions → Post team replies to Slack → Run workflow** and enter `outbox/example.json.txt`. Nora should reply in the Weekly priorities thread in #claude under her own name and photo.
4. **Give the scheduled task GitHub.** In Claude, open the scheduled task "Shell Harbor team replies in Slack #claude" and add the **GitHub** connector to it.

## Reply file format

`outbox/YYYY-MM-DD-HHMM-reply.json`:

```json
{
  "channel": "C0CGWTFJ74H",
  "thread_ts": "<ts of Robert's question>",
  "messages": [{"persona": "Linda Okafor", "text": "..."}]
}
```

Rules enforced by `post_as.py`: #claude only, at most 4 messages, persona must match a key in `personas.json` exactly, text up to 3,000 characters.

## Adding or renaming a teammate

Edit `personas.json` (name → title and portrait URL).
