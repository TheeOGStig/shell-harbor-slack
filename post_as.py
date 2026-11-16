#!/usr/bin/env python3
"""Post Shell Harbor team replies to Slack, each under its own name and portrait.

Usage:
    python post_as.py outbox/2026-11-16-0900-reply.json --dry-run   # check only
    python post_as.py outbox/2026-11-16-0900-reply.json             # post (needs SLACK_BOT_TOKEN)

The reply file looks like:
{
  "channel": "C0CGWTFJ74H",
  "thread_ts": "1794411761.067329",
  "messages": [
    {"persona": "Linda Okafor", "text": "..."}
  ]
}

The Slack app's bot token needs the chat:write and chat:write.customize scopes,
and the app must be a member of the channel. Standard library only.
"""
import argparse
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

ALLOWED_CHANNELS = {"C0CGWTFJ74H"}  # #claude only
MAX_MESSAGES = 4
MAX_TEXT = 3000
TS_RE = re.compile(r"^\d{9,11}\.\d{6}$")
HERE = Path(__file__).resolve().parent


def load_personas():
    with open(HERE / "personas.json", encoding="utf-8") as f:
        return json.load(f)


def validate(reply, personas):
    errors = []
    if reply.get("channel") not in ALLOWED_CHANNELS:
        errors.append(f"channel must be one of {sorted(ALLOWED_CHANNELS)}")
    ts = reply.get("thread_ts")
    if not isinstance(ts, str) or not TS_RE.match(ts):
        errors.append("thread_ts must be a Slack ts string like 1794411761.067329")
    msgs = reply.get("messages")
    if not isinstance(msgs, list) or not msgs:
        errors.append("messages must be a non-empty list")
        return errors
    if len(msgs) > MAX_MESSAGES:
        errors.append(f"at most {MAX_MESSAGES} messages per reply")
    for i, m in enumerate(msgs, 1):
        name = m.get("persona") if isinstance(m, dict) else None
        text = m.get("text") if isinstance(m, dict) else None
        if name not in personas:
            errors.append(f"message {i}: unknown persona {name!r} (must match personas.json exactly)")
        if not isinstance(text, str) or not text.strip():
            errors.append(f"message {i}: text is empty")
        elif len(text) > MAX_TEXT:
            errors.append(f"message {i}: text is {len(text)} chars (max {MAX_TEXT})")
    return errors


def display_name(name, persona):
    label = f"{name} · {persona['title']}" if persona.get("title") else name
    return label[:80]


def post(token, channel, thread_ts, username, icon_url, text):
    body = {
        "channel": channel,
        "thread_ts": thread_ts,
        "text": text,
        "username": username,
        "unfurl_links": False,
    }
    if icon_url:
        body["icon_url"] = icon_url
    req = urllib.request.Request(
        "https://slack.com/api/chat.postMessage",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.load(resp)
    if not result.get("ok"):
        raise RuntimeError(f"Slack error for {username}: {result.get('error')}")
    return result["ts"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    personas = load_personas()
    replies = []
    failed = False
    for path in args.files:
        try:
            with open(path, encoding="utf-8") as f:
                reply = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            print(f"FAIL {path}: {e}")
            failed = True
            continue
        errors = validate(reply, personas)
        if errors:
            failed = True
            print(f"FAIL {path}:")
            for e in errors:
                print(f"  - {e}")
        else:
            print(f"OK   {path}: {len(reply['messages'])} message(s) to thread {reply['thread_ts']}")
            replies.append(reply)
    if failed:
        sys.exit(1)
    if args.dry_run:
        for reply in replies:
            for m in reply["messages"]:
                p = personas[m["persona"]]
                print(f"  as {display_name(m['persona'], p)}: {m['text'][:80]}")
        return

    token = os.environ.get("SLACK_BOT_TOKEN")
    if not token:
        sys.exit("SLACK_BOT_TOKEN is not set")
    for reply in replies:
        for m in reply["messages"]:
            p = personas[m["persona"]]
            ts = post(token, reply["channel"], reply["thread_ts"],
                      display_name(m["persona"], p), p.get("icon_url"), m["text"])
            print(f"posted as {m['persona']} (ts {ts})")


if __name__ == "__main__":
    main()
