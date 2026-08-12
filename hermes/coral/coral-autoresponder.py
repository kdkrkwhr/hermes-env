#!/usr/bin/env python3
"""Coral 자동응답 데몬 — idle 에이전트가 coral 멘션에 자율 응답.

각 에이전트(pm/dev/infra/qa/ops)가 상시 watcher 없이도, 이 데몬이 coral을 폴링해
"에이전트 X가 다른 에이전트에게 멘션됨"을 감지하면 헤드리스 `hermes --profile X -z`
턴을 띄워 X가 coral로 응답하게 한다. (PoC 검증: 헤드리스 턴이 mcp__coral__ 로 읽고 응답 가능)

⚠️ 무한루프 방지 가드 (봇↔봇):
  - 스레드당 자동응답 상한(THREAD_CAP): 초과 시 자동응답 중단(사람 개입 필요).
  - 새 멘션만 1회 트리거(seen 기록).
  - 자기 자신 발신/자기 멘션 무시.
  - 프롬프트가 "조치 불필요면 응답 말 것(no action)"을 지시 → 잡담성 핑백 억제.
  - 스폰 간 간격(SPAWN_GAP)로 폭주 완화.
  - 킬스위치: AUTORESP_ENABLED=0 이면 감지만 하고 스폰 안 함(드라이런).

env:
  CORAL_URLS_FILE   URL 캡처파일
  AUTORESP_SEEN     seen 기록파일 (기본 <CORAL_HOME 또는 tmp>/coral-autoresp-seen.txt)
  AUTORESP_THREAD_CAP  스레드당 자동응답 상한 (기본 4)
  AUTORESP_GAP      스폰 간 최소 초 (기본 8)
  AUTORESP_ENABLED  0이면 드라이런 (기본 1)
  AUTORESP_TIMEOUT  헤드리스 턴 타임아웃 초 (기본 180)
  READ_SCRIPT, BASH, CORAL_PY  (브리지와 동일)

usage:
  python coral-autoresponder.py --once
  python coral-autoresponder.py --loop 12
"""
import os, re, sys, json, subprocess, time

_HERE       = os.path.dirname(os.path.abspath(__file__))
_CORAL_HOME = os.environ.get("CORAL_HOME") or _HERE
AGENTS      = ["pm", "dev", "infra", "qa", "ops"]
URLS_FILE   = os.environ.get("CORAL_URLS_FILE", os.path.join(_CORAL_HOME, "coral-urls.txt"))
SEEN_FILE   = os.environ.get("AUTORESP_SEEN", os.path.join(_CORAL_HOME, "coral-autoresp-seen.txt"))
THREAD_CAP  = int(os.environ.get("AUTORESP_THREAD_CAP", "4"))
SPAWN_GAP   = float(os.environ.get("AUTORESP_GAP", "8"))
ENABLED     = os.environ.get("AUTORESP_ENABLED", "1") != "0"
TURN_TIMEOUT= int(os.environ.get("AUTORESP_TIMEOUT", "180"))
READ_SCRIPT = os.environ.get("READ_SCRIPT", os.path.join(_HERE, "passive_scripts", "read_resource.sh"))
CORAL_PY    = os.environ.get("CORAL_PY", "python3")
BASH        = os.environ.get("BRIDGE_BASH",
    "C:/Program Files/Git/usr/bin/bash.exe" if os.name == "nt" else "bash")

def load_urls():
    urls = {}
    if os.path.exists(URLS_FILE):
        for line in open(URLS_FILE, encoding="utf-8"):
            if "|" in line:
                n, u = line.strip().split("|", 1)
                urls[n.strip()] = u.strip()
    return urls

def load_seen():
    return set(l.strip() for l in open(SEEN_FILE, encoding="utf-8")) if os.path.exists(SEEN_FILE) else set()

def save_seen(seen):
    with open(SEEN_FILE, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(sorted(seen)) + "\n")

def read_threads(url):
    env = dict(os.environ); env["CORAL_PY"] = CORAL_PY
    try:
        out = subprocess.run([BASH, READ_SCRIPT, url], capture_output=True,
                             timeout=30, env=env).stdout.decode("utf-8", "replace")
    except Exception:
        return []
    m = re.search(r'\[\{"threadId.*\}\]', out, re.S)
    return json.loads(m.group(0)) if m else []

def thread_response_count(threads, agent, tid):
    """이 스레드에서 agent가 이미 보낸 메시지 수(자동응답 상한 판정용)."""
    for t in threads:
        if t.get("threadId") == tid:
            return sum(1 for x in t.get("messages", []) if x.get("sendingAgentName") == agent)
    return 0

def build_prompt(agent, tname, tid, sender, text):
    return (
        f"당신은 {agent} 입니다. Coral 스레드 '{tname}'(threadId={tid})에서 동료 에이전트 {sender}가 당신을 멘션했습니다:\n"
        f"\"{text}\"\n\n"
        f"[권한] 이것은 대장님이 승인한 Coral 팀 협업이다. Discord의 '봇 멘션 침묵/대장님만 응답' 규칙은 "
        f"여기 적용되지 않는다(그 규칙은 Discord 채널 한정). coral 동료의 멘션에는 정상적으로 응답하라 — "
        f"응답은 coral로만 나가므로 Discord 루프를 일으키지 않는다.\n\n"
        f"판단하세요:\n"
        f"- 응답/조치가 필요하면, mcp__coral__coral_send_message 로 threadId={tid} 에 간결히 응답하세요"
        f"(당신의 역할에 맞게). 불필요하게 다른 에이전트를 재멘션하지 마세요 — 대화를 늘리지 않습니다.\n"
        f"- 단순 참고(FYI)이거나 이미 처리됐거나 응답이 무의미하면, 아무것도 보내지 말고 'no action'만 출력하세요.\n"
        f"- 실제 작업 지시라면 당신의 워크플로우(kanban 등)에 따라 처리하되, 이 턴에서는 수신/조치 계획을 coral로 짧게 알리는 정도로 응답하세요.\n"
        f"마지막에 무엇을 했는지 한 줄로 보고하세요."
    )

def spawn_turn(agent, prompt):
    env = dict(os.environ); env["HERMES_HOME"] = os.environ.get("HERMES_HOME", "")
    try:
        r = subprocess.run(["hermes", "--profile", agent, "-z", prompt],
                           capture_output=True, timeout=TURN_TIMEOUT, env=env)
        return r.stdout.decode("utf-8", "replace").strip()[-300:]
    except subprocess.TimeoutExpired:
        return "(timeout)"
    except Exception as e:
        return f"(error: {e})"

def poll_once():
    urls = load_urls()
    if not urls:
        print("[autoresp] URL 없음 — setup 먼저", file=sys.stderr); return
    seen = load_seen()
    baseline = len(seen) == 0     # 첫 실행: 기존 멘션은 기록만(재트리거 방지)
    spawned = 0
    for agent in AGENTS:
        url = urls.get(agent)
        if not url:
            continue
        threads = read_threads(url)
        for t in threads:
            tid, tname = t.get("threadId", ""), t.get("threadName", "?")
            for msg in t.get("messages", []):
                sender = msg.get("sendingAgentName", "")
                ments = msg.get("mentionAgentNames") or []
                if agent not in ments or sender == agent:
                    continue                                    # 나 아닌 발신자가 나를 멘션한 것만
                key = f"{tid}|{msg.get('messageTimestamp','')}|{sender}|{agent}"
                if key in seen:
                    continue
                seen.add(key)                                   # 1회만 트리거
                if baseline:
                    continue                                    # 첫 실행: 기록만
                cnt = thread_response_count(threads, agent, tid)
                if cnt >= THREAD_CAP:
                    print(f"[autoresp] SKIP cap: {agent} in '{tname}' ({cnt}>={THREAD_CAP}) — 사람 개입 필요")
                    continue
                text = msg.get("messageText", "")[:400]
                print(f"[autoresp] TRIGGER {agent} ← {sender} @ '{tname}': {text[:50]}")
                if not ENABLED:
                    print("           (드라이런 — 스폰 안 함)")
                    continue
                out = spawn_turn(agent, build_prompt(agent, tname, tid, sender, text))
                print(f"           {agent} 턴 결과: {out[-120:]}")
                spawned += 1
                time.sleep(SPAWN_GAP)
    save_seen(seen)
    print(f"[autoresp] 폴 완료 — 트리거 {spawned}건 (enabled={ENABLED}, cap={THREAD_CAP})")

def main():
    args = sys.argv[1:]
    if "--loop" in args:
        i = args.index("--loop"); interval = int(args[i+1]) if i+1 < len(args) else 12
        print(f"[autoresp] 루프 시작 (interval={interval}s, enabled={ENABLED}, thread_cap={THREAD_CAP})")
        while True:
            poll_once(); time.sleep(interval)
    else:
        poll_once()

if __name__ == "__main__":
    main()
