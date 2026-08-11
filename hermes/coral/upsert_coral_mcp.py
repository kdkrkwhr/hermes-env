#!/usr/bin/env python3
"""config.yaml 의 mcp_servers.coral.url 을 idempotent upsert (주석/포맷 보존, 텍스트 기반).

env: CORAL_URL(필수), CORAL_PROFILE(로그용). argv[1]=config.yaml 경로.
3 케이스: coral 블록 존재→url 교체 / mcp_servers 존재·coral 없음→coral 삽입 / mcp_servers 없음→키 추가.
"""
import os, re, sys

path = sys.argv[1]
url = os.environ["CORAL_URL"]
prof = os.environ.get("CORAL_PROFILE", "?")
src = open(path, encoding="utf-8").read()

coral_block = (
    "  coral:\n"
    "    # AgentRadio/Coral 실시간 peer 사이드채널 (세션 hermes-fleet). "
    "secret은 서버 재생성 시 바뀜.\n"
    f"    url: \"{url}\"\n"
    "    timeout: 180\n"
    "    connect_timeout: 30\n"
)

# 1) 이미 coral 블록이 있으면 그 안의 url: 라인만 교체
if re.search(r"(?m)^  coral:\s*$", src):
    new, n = re.subn(
        r'(?ms)(^  coral:\s*$.*?^    url:\s*).*?$',
        lambda m: m.group(1) + f'"{url}"',
        src, count=1,
    )
    if n:
        open(path, "w", encoding="utf-8", newline="\n").write(new)
        print(f"[{prof}] coral.url 교체")
        sys.exit(0)

# 2) mcp_servers: 키가 있으면 바로 다음 줄에 coral 블록 삽입
m = re.search(r"(?m)^mcp_servers:\s*$", src)
if m:
    insert_at = src.find("\n", m.end())
    insert_at = insert_at + 1 if insert_at != -1 else len(src)
    new = src[:insert_at] + coral_block + src[insert_at:]
    open(path, "w", encoding="utf-8", newline="\n").write(new)
    print(f"[{prof}] mcp_servers 아래 coral 삽입")
    sys.exit(0)

# 3) mcp_servers 키가 아예 없으면 파일 끝에 추가
tail = "" if src.endswith("\n") else "\n"
open(path, "w", encoding="utf-8", newline="\n").write(src + tail + "mcp_servers:\n" + coral_block)
print(f"[{prof}] mcp_servers 키 신규 추가 + coral")
