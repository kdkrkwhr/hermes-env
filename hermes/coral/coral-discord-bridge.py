#!/usr/bin/env python3
"""Coral → Discord 미러 브리지.

5개 에이전트 URL로 coral 전체 스레드/메시지를 폴링해, 새 메시지를 Discord 채널로 미러링한다.
에이전트끼리 coral 사이드채널로 주고받는 대화를 대장님이 Discord에서 그대로 볼 수 있게 한다.

- 첫 실행: 현재 메시지를 baseline(=이미 본 것)으로 기록만 하고 안 보냄(과거 도배 방지).
  과거까지 전부 보내려면 --backfill.
- 이후: 새 메시지만 `[coral#thread] sender → @mentions: text` 형태로 전송.
- dedup: threadId|timestamp|sender 키. 여러 에이전트 뷰에 중복 등장해도 1회만.

env:
  CORAL_URLS_FILE  URL 캡처파일 (기본 /tmp/coral-urls.txt) — 'name|url' 라인
  BRIDGE_SEEN      seen 기록파일 (기본 /tmp/coral-bridge-seen.txt)
  BRIDGE_CHANNEL   Discord 타겟 (기본 discord:#agent-multi)
  BRIDGE_PROFILE   hermes send 프로필 (기본 ops)
  READ_SCRIPT      read_resource.sh 경로
  CORAL_PY         read_resource.sh용 python (기본 python)

usage:
  python coral-discord-bridge.py --once            # 1회 폴링
  python coral-discord-bridge.py --loop 10         # 10초 간격 무한
  python coral-discord-bridge.py --once --backfill # 기존 메시지도 전송
"""
import os, re, sys, json, subprocess, time

_HERE       = os.path.dirname(os.path.abspath(__file__))
_CORAL_HOME = os.environ.get("CORAL_HOME") or _HERE
URLS_FILE   = os.environ.get("CORAL_URLS_FILE", os.path.join(_CORAL_HOME, "coral-urls.txt"))
SEEN_FILE   = os.environ.get("BRIDGE_SEEN", os.path.join(_CORAL_HOME, "coral-bridge-seen.txt"))
CHANNEL     = os.environ.get("BRIDGE_CHANNEL", "discord:#agent-multi")
PROFILE     = os.environ.get("BRIDGE_PROFILE", "ops")
# read_resource.sh — 기본은 이 스크립트 옆 agents/probe/... 가 아니라 AgentRadio passive_scripts.
# 이식 시 READ_SCRIPT 를 실제 경로로 지정(install-coral.sh 가 AgentRadio 를 받는 위치).
READ_SCRIPT = os.environ.get("READ_SCRIPT", os.path.join(_HERE, "passive_scripts", "read_resource.sh"))
CORAL_PY    = os.environ.get("CORAL_PY", "python3")
# Windows에선 bare 'bash'가 WSL bash를 잡아 Windows 경로 스크립트에서 멈춤 → git-bash 명시.
BASH        = os.environ.get("BRIDGE_BASH",
    "C:/Program Files/Git/usr/bin/bash.exe" if os.name == "nt" else "bash")

def load_urls():
    urls = {}
    if not os.path.exists(URLS_FILE):
        return urls
    for line in open(URLS_FILE, encoding="utf-8"):
        line = line.strip()
        if "|" in line:
            name, url = line.split("|", 1)
            urls[name.strip()] = url.strip()
    return urls

def load_seen():
    if not os.path.exists(SEEN_FILE):
        return set()
    return set(l.strip() for l in open(SEEN_FILE, encoding="utf-8") if l.strip())

def save_seen(seen):
    with open(SEEN_FILE, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(sorted(seen)) + "\n")

def read_threads(url):
    """read_resource.sh <url> → coral://state의 threads json 파싱."""
    env = dict(os.environ); env["CORAL_PY"] = CORAL_PY
    try:
        out = subprocess.run([BASH, READ_SCRIPT, url], capture_output=True,
                             timeout=30, env=env).stdout.decode("utf-8", "replace")
    except Exception:
        return []
    m = re.search(r'\[\{"threadId.*\}\]', out, re.S)
    if not m:
        return []
    try:
        return json.loads(m.group(0))
    except Exception:
        return []

def collect_messages(urls):
    """모든 URL의 스레드를 union. 반환: {key: (thread, msg)}."""
    msgs = {}
    for url in urls.values():
        for t in read_threads(url):
            tname = t.get("threadName", "?")
            for msg in t.get("messages", []):
                key = f"{t.get('threadId','')}|{msg.get('messageTimestamp','')}|{msg.get('sendingAgentName','')}"
                msgs[key] = (tname, msg)
    return msgs

def send_discord(text):
    subprocess.run(["hermes", "--profile", PROFILE, "send", "--to", CHANNEL],
                   input=text.encode("utf-8"), capture_output=True)

def fmt(tname, msg):
    sender = msg.get("sendingAgentName", "?")
    ment = msg.get("mentionAgentNames") or []
    at = (" → @" + ",".join(ment)) if ment else ""
    return f"🔗 [coral#{tname}] {sender}{at}: {msg.get('messageText','')}"

def poll_once(backfill=False):
    urls = load_urls()
    if not urls:
        print("URL 캡처파일 없음/빔 — setup 먼저 실행", file=sys.stderr); return
    seen = load_seen()
    first_run = len(seen) == 0
    msgs = collect_messages(urls)
    new = [(k, v) for k, v in msgs.items() if k not in seen]
    # 첫 실행(baseline) & not backfill → 기록만, 전송 안 함
    silent = first_run and not backfill
    sent = 0
    for k, (tname, msg) in sorted(new, key=lambda kv: kv[1][1].get("messageTimestamp", "")):
        if not silent:
            send_discord(fmt(tname, msg)); sent += 1
        seen.add(k)
    save_seen(seen)
    tag = "baseline(기록만)" if silent else f"미러 {sent}건"
    print(f"[bridge] 스레드 {len({m[0] for m in msgs.values()})} · 메시지 {len(msgs)} · 신규 {len(new)} → {tag}")

def main():
    args = sys.argv[1:]
    backfill = "--backfill" in args
    if "--loop" in args:
        i = args.index("--loop")
        interval = int(args[i+1]) if i+1 < len(args) else 10
        print(f"[bridge] 루프 시작 (interval={interval}s, channel={CHANNEL})")
        while True:
            poll_once(backfill); backfill = False  # backfill은 첫 패스만
            time.sleep(interval)
    else:
        poll_once(backfill)

if __name__ == "__main__":
    main()
