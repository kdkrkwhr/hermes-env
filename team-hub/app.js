// hermes-team-hub — vanilla JS, no build step, runs on GitHub Pages or any static host.
// Source of truth for fleet data mirrors hermes-env/docs/workflow-cungya.md.

const FLEET = {
  pm: {
    color: "violet", emoji: "🧭", name: "PM", full: "Project Manager / 아키텍트",
    role: "요구사항 분석 → 칸반 카드 분해 + 담당 배정",
    profile: "pm", discord: "1534806088762003476", assignee: "pm",
    report: "① 분해·배정 완료 시 브리핑",
    menu: [
      "업무가 들어오면 요구사항을 분석·세분화해 기능 정의서(Task List)로 쪼갠다.",
      "각 태스크에 담당 크루를 명시해 할당: `[할당: dev] …`, `[할당: infra] …`, `[할당: qa] …`.",
      "할당 대상 — Dev(개발 리드)=전반적 개발 / Infra(인프라)=인프라 보조 / QA(채점·테스트) / Ops(비서·보고).",
      "보고/문서는 `$E2E_ROOT/reports/` 에 반영한다 (제품 레포 내부 금지).",
      "호칭은 '대장님'으로 통일.",
    ],
  },
  dev: {
    color: "emerald", emoji: "💻", name: "Dev", full: "Developer / 개발 리드",
    role: "전반적인 개발 구현 (PM이 할당한 태스크)",
    profile: "dev", discord: "1513699678556782703", assignee: "dev",
    report: "② 작업 완료 시 한 줄 요약 (권장)",
    menu: [
      "PM이 발행한 칸반 카드의 코딩을 전담한다.",
      "Infra(infra)의 인프라 지원을 받아 개발을 진행한다.",
      "말투는 10년 넘은 친구 톤 (반말, 편한 톤) — '대장님' 호칭 유지.",
      "작업 중 coral에 FYI 무전으로 진행 상황을 중계한다.",
    ],
  },
  infra: {
    color: "amber", emoji: "🛠️", name: "Infra", full: "Infrastructure Developer",
    role: "Dev 개발 보조 + 인프라 설정/구축/배포",
    profile: "infra", discord: "1535078180077965354", assignee: "infra",
    report: "② 작업 완료 시 한 줄 요약 (권장)",
    menu: [
      "Dev(dev)의 개발을 보조하되 인프라적인 부분을 담당한다.",
      "인프라 설정/구축/배포를 수행한다.",
      "호칭은 '대장님'으로 통일.",
      "블로커 발생 시 coral에 URGENT 무전으로 Dev/PM에게 전달.",
    ],
  },
  qa: {
    color: "cyan", emoji: "🔍", name: "QA", full: "Quality Assurance",
    role: "Dev/Infra 결과물 체크리스트 채점·테스트 (PASS/REJECT)",
    profile: "qa", discord: "1513768982472032266", assignee: "qa",
    report: "④ QA 종료 시 상세 (PASS/REJECT·사유) — 필수",
    menu: [
      "Dev/Infra가 작업한 결과물을 체크리스트 기준으로 채점·테스트한다.",
      "PASS → 칸반 Done + Ops에게 이관 / REJECT → 담당자에게 수정 요구 + In Progress 복귀.",
      "말투는 친구 톤 (반말) — '대장님' 호칭 유지.",
      "검수 시작 시 ③ 보고 트리거(한 줄 요약) 대상.",
    ],
  },
  ops: {
    color: "rose", emoji: "🍄", name: "Ops", full: "Operations & Secretary",
    role: "칸반 모니터링(유일 디스패처) + 대장님 5단계 보고",
    profile: "ops", discord: "— (텍스트 페르소나)", assignee: "ops",
    report: "① ④ ⑤ 보고 트리거 담당 (상세 브리핑 필수)",
    menu: [
      "다른 에이전트들의 작업 완료 상태를 모니터링하고, 이벤트를 대장님(#work)에게 정형화해 보고한다.",
      "유일 디스패처 — `kanban.dispatch_in_gateway: true`, `default_assignee: pm`.",
      "보고 트리거 5단계: ① 분해·배정 ② 완료요약 ③ QA착수 ④ QA종료 ⑤ 워크스트림 완료.",
      "카드 없이 dev/infra에 작업 지시 금지 — 모든 구현은 칸반 카드 경유.",
      "확인 필요 작업은 blocked 카드로 생성해 dispatcher race 방지.",
    ],
  },
};

const $app = document.getElementById("app");
const $nav = document.getElementById("topnav");

function el(html) {
  const t = document.createElement("template");
  t.innerHTML = html.trim();
  return t.content.firstChild;
}

function rolePanel(key, d, detailed = true) {
  const node = el(`
    <section class="panel c-${d.color}">
      <h3><span class="stripe" style="display:inline-block;width:6px;height:16px;border-radius:3px;background:var(--${d.color});margin-right:8px;"></span>${d.emoji} ${d.name} — ${d.full} <span class="badge">assignee: ${d.assignee}</span></h3>
      <dl class="kv">
        <dt>역할</dt><dd>${d.role}</dd>
        <dt>Hermes 프로필</dt><dd><code>${d.profile}</code></dd>
        <dt>Discord 봇 ID</dt><dd><code>${d.discord}</code></dd>
        <dt>보고 트리거</dt><dd>${d.report}</dd>
      </dl>
      <h3 style="margin-top:18px;">역할별 메뉴</h3>
      <ul class="clean">${d.menu.map((m) => `<li>${m}</li>`).join("")}</ul>
    </section>
  `);
  return node;
}

function viewHome() {
  const grid = el(`<div class="fleet"></div>`);
  for (const [k, d] of Object.entries(FLEET)) {
    const c = el(`
      <div class="card c-${d.color}" data-go="${k}">
        <span class="stripe"></span>
        <span class="emoji">${d.emoji}</span>
        <h3>${d.name}</h3>
        <div class="role">${d.full}</div>
        <div class="meta">assignee: <code>${d.assignee}</code> · ${d.role}</div>
      </div>
    `);
    c.addEventListener("click", () => go(k));
    grid.appendChild(c);
  }

  const flow = el(`
    <section class="panel">
      <h3>워크플로우 흐름</h3>
      <div class="flow">
        <div class="step">대장님 지시<br>(Discord #work)</div>
        <div class="arrow">→</div>
        <div class="step">PM(pm)<br>분해·배정</div>
        <div class="arrow">→</div>
        <div class="step">Dev(dev)+<br>Infra(infra)</div>
        <div class="arrow">→</div>
        <div class="step">QA(qa)<br>검수</div>
        <div class="arrow">→</div>
        <div class="step">Ops(ops)<br>보고</div>
      </div>
      <p class="sub" style="margin-top:14px;">Kanban(<code>127.0.0.1:9119</code>)이 작업 상태의 단일 진실원(SoT). Coral은 실시간 peer 사이드채널(보완).</p>
    </section>
  `);

  const overview = el(`
    <section class="panel">
      <h3>플릿 한눈에</h3>
      <table class="rep">
        <thead><tr><th>페르소나</th><th>정체성</th><th>assignee</th><th>Discord ID</th><th>핵심</th></tr></thead>
        <tbody>
          ${Object.values(FLEET).map((d) => `
            <tr>
              <td><b>${d.emoji} ${d.name}</b></td>
              <td>${d.full}</td>
              <td><code>${d.assignee}</code></td>
              <td><code>${d.discord}</code></td>
              <td>${d.role}</td>
            </tr>`).join("")}
        </tbody>
      </table>
    </section>
  `);

  const wrap = el(`<div class="view"></div>`);
  wrap.appendChild(el(`<h2 class="section">팀 허브 홈</h2>`));
  wrap.appendChild(el(`<p class="sub">5인조 멀티에이전트(PM/Dev/Infra/QA/Ops)의 역할별 메뉴와 hermes-env 부트스트랩을 한 곳에서. 카드를 누르면 역할 상세로.</p>`));
  wrap.appendChild(grid);
  wrap.appendChild(flow);
  wrap.appendChild(overview);
  return wrap;
}

function viewRole(key) {
  const d = FLEET[key];
  const wrap = el(`<div class="view"></div>`);
  wrap.appendChild(el(`<h2 class="section">${d.emoji} ${d.name} — ${d.full}</h2>`));
  wrap.appendChild(el(`<p class="sub">Hermes 프로필 <code>${d.profile}</code> · 칸반 assignee <code>${d.assignee}</code></p>`));
  wrap.appendChild(rolePanel(key, d));
  wrap.appendChild(el(`
    <section class="panel">
      <h3>SOUL / COORD 규칙 (요약)</h3>
      <ul class="clean">
        <li>각 프로필의 <code>SOUL.md.template</code>에 역할 페르소나가 박혀 있다 (<code>hermes-env/hermes/profiles/${d.profile}/</code>).</li>
        <li><code>[COORD]</code> 섹션: Coral 실시간 peer 사이드채널 사용 규칙 (FYI/URGENT 무전, 2–5초 wait_for_mention).</li>
        <li>카드 상태 전이·배정은 Kanban. Coral은 보완 대화용.</li>
      </ul>
    </section>
  `));
  return wrap;
}

function viewSetup() {
  const wrap = el(`<div class="view"></div>`);
  wrap.appendChild(el(`<h2 class="section">셋업 — hermes-env 부트스트랩</h2>`));
  wrap.appendChild(el(`<p class="sub">새 PC에서 Hermes Agent가 <code>AGENT_BOOTSTRAP.md</code>를 읽고 그대로 세팅. 이 허브는 그 결과물(팀 구조)을 정적 사이트로 보여준다.</p>`));

  wrap.appendChild(el(`
    <section class="panel">
      <h3>0단계 — 경로 3개 질문 (건너뛰기 금지)</h3>
      <table class="rep">
        <thead><tr><th>#</th><th>질문</th><th>변수</th></tr></thead>
        <tbody>
          <tr><td>1</td><td>작업 루트 디렉토리 (프로젝트 코드)</td><td><code>PROJECT_ROOT</code></td></tr>
          <tr><td>2</td><td>E2E 루트 (ssot, reports 등)</td><td><code>E2E_ROOT</code></td></tr>
          <tr><td>3</td><td>Hermes 설치 경로 (기본 $HOME/.hermes)</td><td><code>HERMES_HOME</code></td></tr>
        </tbody>
      </table>
    </section>
  `));

  const steps = [
    ["1", "선행 조건 확인", "git, python3 3.10+, OS 확인 (Windows는 git-bash 기준)."],
    ["2", "디렉토리 구조 생성", "$PROJECT_ROOT, $E2E_ROOT/ssot, $E2E_ROOT/reports, $HERMES_HOME/profiles."],
    ["3", "Hermes config 배치", "config.yaml.template → $HERMES_HOME/config.yaml. ops만 dispatch_in_gateway:true, default_assignee:pm."],
    ["3-1", "페르소나 SOUL 배치 (선택)", "5개 프로필 SOUL.md.template → SOUL.md. 기존 SOUL 덮어쓰므로 동의 필수."],
    ["3-2", "AgentRadio/Coral 연동 (선택)", "실시간 peer 메시징. coral-server.jar + MCP URL 주입."],
    ["4", "스킬 배치", "$BOOTSTRAP_REPO/hermes/skills/* → $HERMES_HOME/skills/. 레거시 절대경로 스캔."],
    ["5", "환경변수 / 시크릿", ".env.example → $E2E_ROOT/.env.local. 값은 새 머신에서 수동 입력. Git 커밋 금지."],
    ["6", "SSoT 클론 (선택)", "$E2E_ROOT/ssot 에 spec/DDL/ADR 레포 클론."],
    ["7", "최종 검증 리포트", "7항목 표로 완료 여부 출력. 미완료는 '완료'라 보고하지 않음."],
  ];
  const stepsWrap = el(`<section class="panel"><h3>부트스트랩 단계</h3><div class="steps"></div></section>`);
  const sbody = stepsWrap.querySelector(".steps");
  for (const [n, t, p] of steps) {
    sbody.appendChild(el(`
      <div class="steprow">
        <div class="num">${n}</div>
        <div class="body"><b>${t}</b><p>${p}</p></div>
      </div>
    `));
  }
  wrap.appendChild(stepsWrap);

  wrap.appendChild(el(`
    <section class="panel">
      <h3>연계 포인트</h3>
      <ul class="clean">
        <li>이 정적 사이트(<code>team-hub/</code>)는 hermes-env 레포에 포함돼 GitHub Pages로 호스팅 가능.</li>
        <li>역할 데이터는 <code>docs/workflow-cungya.md</code> §1 매핑을 단일 진실원으로 삼음.</li>
        <li>호칭 '대장님' 통일, 칸반 assignee는 프로필명(pm/dev/infra/qa/ops).</li>
        <li>상세: <a href="https://github.com/kdkrkwhr/hermes-env" target="_blank" rel="noopener">hermes-env repo</a> · <code>docs/</code> (conventions, kanban-fleet, workflow-cungya, agentradio-coral).</li>
      </ul>
    </section>
  `));
  return wrap;
}

const VIEWS = {
  home: viewHome,
  pm: () => viewRole("pm"),
  dev: () => viewRole("dev"),
  infra: () => viewRole("infra"),
  qa: () => viewRole("qa"),
  ops: () => viewRole("ops"),
  setup: viewSetup,
};

function go(view) {
  const render = VIEWS[view] || viewHome;
  $app.innerHTML = "";
  $app.appendChild(render());
  [...$nav.querySelectorAll(".navbtn")].forEach((b) =>
    b.classList.toggle("active", b.dataset.view === view)
  );
  window.scrollTo({ top: 0, behavior: "smooth" });
}

$nav.addEventListener("click", (e) => {
  const btn = e.target.closest(".navbtn");
  if (btn) go(btn.dataset.view);
});

// deep-link: #pm / #setup etc.
const initial = (location.hash || "#home").slice(1);
go(VIEWS[initial] ? initial : "home");
