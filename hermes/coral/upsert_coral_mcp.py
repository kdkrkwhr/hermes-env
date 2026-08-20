#!/usr/bin/env python3
"""config.yaml 에 coral MCP 를 idempotent upsert (주석/포맷 보존, 텍스트 기반).

두 가지를 함께 처리한다:
  1) mcp_servers.coral (url/timeout) — 연결 정보
  2) toolsets 에 `coral` 추가 — 이게 없으면 `mcp test` 는 Connected 라도
     에이전트에게 mcp_coral_* 가 노출되지 않아 무전 불가 (2026-08-20 실전 함정).

env: CORAL_URL(필수), CORAL_PROFILE(로그용). argv[1]=config.yaml 경로.
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


def ensure_mcp(src):
    """mcp_servers.coral.url upsert. returns (new_src, msg)."""
    # 1) coral 블록 존재 → url 라인만 교체
    if re.search(r"(?m)^  coral:\s*$", src):
        new, n = re.subn(
            r'(?ms)(^  coral:\s*$.*?^    url:\s*).*?$',
            lambda m: m.group(1) + f'"{url}"', src, count=1,
        )
        if n:
            return new, "coral.url 교체"
    # 2) mcp_servers: 존재 → 바로 아래 coral 삽입
    m = re.search(r"(?m)^mcp_servers:\s*$", src)
    if m:
        at = src.find("\n", m.end())
        at = at + 1 if at != -1 else len(src)
        return src[:at] + coral_block + src[at:], "mcp_servers 아래 coral 삽입"
    # 3) mcp_servers 없음 → 파일 끝에 추가
    tail = "" if src.endswith("\n") else "\n"
    return src + tail + "mcp_servers:\n" + coral_block, "mcp_servers 신규 + coral"


def ensure_toolset(src):
    """toolsets 리스트에 coral 을 멱등 추가. returns (new_src, msg_or_None)."""
    m = re.search(r"(?m)^toolsets:[ \t]*(.*)$", src)
    if not m:
        tail = "" if src.endswith("\n") else "\n"
        return src + tail + "toolsets:\n  - coral\n", "toolsets 신규 + coral"
    inline = m.group(1).strip()
    # flow 스타일: toolsets: [a, b]
    if inline.startswith("["):
        if re.search(r"[\"']?\bcoral\b[\"']?", inline):
            return src, None
        new_inline = re.sub(r"\]\s*$", ", coral]", inline)
        return src[:m.start(1)] + new_inline + src[m.end():], "coral toolset 추가"
    # block 스타일: 다음 줄들의 '  - item'
    start = src.find("\n", m.end())
    start = start + 1 if start != -1 else len(src)
    lines = src[start:].split("\n")
    items = []
    for ln in lines:
        if re.match(r"^[ \t]*-[ \t]", ln):
            items.append(ln)
        else:
            break
    block = "\n".join(items)
    if re.search(r"(?m)^[ \t]*-[ \t]*coral[ \t]*$", block):
        return src, None
    if not items:
        return src[:start] + "  - coral\n" + src[start:], "coral toolset 추가"
    at = start + len(block)
    return src[:at] + "\n  - coral" + src[at:], "coral toolset 추가"


src, mcp_msg = ensure_mcp(src)
src, ts_msg = ensure_toolset(src)
open(path, "w", encoding="utf-8", newline="\n").write(src)
print(f"[{prof}] {mcp_msg}" + (f" + {ts_msg}" if ts_msg else " (toolset 이미 있음)"))
