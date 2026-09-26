/* ==========================================================================
   AI-Node-Gate — Mobile Command Center (client)
   Deploy scouts · decide at the gate · grow the pocketbook.
   No framework, no build step. Talks to the self-hosted hub API.
   ========================================================================== */

(function () {
  "use strict";

  var S = {
    nodes: [], opportunities: [], missions: [], ledger: [],
    capability: {}, pocketbook: {}, arbitrator: {}, ledger_count: 0
  };
  var verifyMap = {};
  var channel = "gigs";
  var filter = "open";
  var channels = [
    { id: "gigs", label: "Paid work" },
    { id: "grants", label: "Grants" },
    { id: "deals", label: "Deals" },
    { id: "leads", label: "Leads" },
    { id: "gaps", label: "Gaps" }
  ];

  /* ---------- helpers ---------- */

  function el(id) { return document.getElementById(id); }
  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }
  function money(n) {
    n = Number(n || 0);
    if (n >= 1e6) return "$" + (n / 1e6).toFixed(n >= 1e7 ? 0 : 1) + "M";
    if (n >= 1e3) return "$" + (n / 1e3).toFixed(n >= 1e4 ? 0 : 1) + "k";
    return "$" + Math.round(n);
  }
  function full(n) { return "$" + Number(n || 0).toLocaleString(undefined, { maximumFractionDigits: 0 }); }
  function short(h, n) { return h ? h.slice(0, n || 14) : ""; }
  function api(path, method, body) {
    return fetch(path, {
      method: method || "GET",
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined
    }).then(function (r) { return r.json(); });
  }
  function toast(msg) {
    var t = el("toast");
    t.textContent = msg;
    t.classList.add("show");
    clearTimeout(t._t);
    t._t = setTimeout(function () { t.classList.remove("show"); }, 2600);
  }
  function timeAgo(ts) {
    var d = Date.now() / 1000 - ts;
    if (d < 60) return "just now";
    if (d < 3600) return Math.floor(d / 60) + "m ago";
    if (d < 86400) return Math.floor(d / 3600) + "h ago";
    return Math.floor(d / 86400) + "d ago";
  }
  function scoutName(id) {
    for (var i = 0; i < S.nodes.length; i++) if (S.nodes[i].id === id) return S.nodes[i].name;
    return "—";
  }

  /* ---------- render: header + capability ---------- */

  function renderHeader() {
    var c = S.capability || {};
    el("lvl-num").textContent = c.level || 1;
    el("lvl-tier").textContent = c.tier || "Scout";
    el("lvl-xp").textContent = (c.xp || 0) + " XP";
    var pct = Math.round(((c.into_level || 0) / 150) * 100);
    el("lvl-ring").style.setProperty("--pct", pct + "%");
    el("appbar-sub").textContent = S.arbitrator.fingerprint
      ? "arbitrator " + S.arbitrator.fingerprint
      : "sovereign · self-hosted · you decide";
  }

  /* ---------- render: deploy ---------- */

  function renderScoutSelect() {
    var sel = el("d-scout");
    if (!S.nodes.length) {
      sel.innerHTML = '<option value="">— no scouts yet —</option>';
      return;
    }
    var cur = sel.value;
    sel.innerHTML = S.nodes.map(function (n) {
      return '<option value="' + esc(n.id) + '">' + esc(n.name) +
        (n.role ? " · " + esc(n.role) : "") + "</option>";
    }).join("");
    if (cur) sel.value = cur;
  }

  function renderChannels() {
    el("d-channels").innerHTML = channels.map(function (c) {
      return '<button class="chip' + (c.id === channel ? " on" : "") +
        '" data-ch="' + c.id + '">' + esc(c.label) + "</button>";
    }).join("");
  }

  function renderMissions() {
    var box = el("mission-list");
    if (!S.missions.length) {
      box.innerHTML = '<div class="empty"><div class="ico">🛰️</div><p>No scouts deployed yet.</p></div>';
      return;
    }
    box.innerHTML = S.missions.slice(0, 8).map(function (m) {
      return '<div class="mission">' +
        '<div class="m-ico">🛰️</div>' +
        '<div class="m-body">' +
          '<div class="m-title">' + esc(m.mission) + '</div>' +
          '<div class="m-sub">' + esc(m.scout_name) + " · " + esc(m.channel) + " · " + esc(timeAgo(m.created_at)) + '</div>' +
        '</div>' +
        '<div class="m-found">' + (m.found || 0) + " found</div>" +
      "</div>";
    }).join("");
  }

  /* ---------- render: gate ---------- */

  function visibleOpps() {
    return S.opportunities.filter(function (o) {
      if (filter === "all") return true;
      if (filter === "open") return o.state === "pending" || o.state === "pursuing";
      return o.state === filter;
    });
  }

  function renderOpps() {
    var box = el("opp-list");
    var list = visibleOpps();
    if (!list.length) {
      box.innerHTML = '<div class="empty"><div class="ico">🎯</div><p>Nothing here yet. Deploy a scout to find opportunities.</p></div>';
      return;
    }
    box.innerHTML = list.map(function (o) {
      var actions = "";
      if (o.state === "pending") {
        actions = '<button class="btn green" data-act="approve" data-id="' + esc(o.id) + '">✓ Pursue</button>' +
                  '<button class="btn red" data-act="reject" data-id="' + esc(o.id) + '">✕ Pass</button>';
      } else if (o.state === "pursuing") {
        actions = '<button class="btn green" data-act="won" data-id="' + esc(o.id) + '">🏆 Won</button>' +
                  '<button class="btn ghost" data-act="lost" data-id="' + esc(o.id) + '">Lost</button>' +
                  '<button class="btn ghost" data-act="reopen" data-id="' + esc(o.id) + '">↺</button>';
      } else {
        actions = '<button class="btn ghost" data-act="reopen" data-id="' + esc(o.id) + '">↺ Reopen</button>';
      }
      var src = o.url
        ? '<a href="' + esc(o.url) + '" target="_blank" rel="noopener" style="color:var(--accent2)">source ↗</a>'
        : esc(o.source || "scout");
      return '<div class="opp" data-state="' + esc(o.state) + '">' +
        '<div class="opp-top">' +
          '<div style="flex:1;min-width:0">' +
            '<span class="tag ' + esc(o.category) + '">' + esc(o.category) + '</span>' +
            '<div class="opp-title" style="margin-top:7px">' + esc(o.title) + '</div>' +
            (o.summary ? '<div class="opp-sum">' + esc(o.summary) + '</div>' : "") +
          '</div>' +
          '<div class="state-badge ' + esc(o.state) + '">' + esc(o.state) + '</div>' +
        '</div>' +
        '<div class="opp-meta">' +
          '<span class="valuepill">' + full(o.value) + '</span>' +
          '<span class="roi">ROI ' + Math.round(o.roi || 0) + '</span>' +
          '<span>effort <b>' + esc(o.effort) + '</b></span>' +
          '<span>by <b>' + esc(o.scout_name || scoutName(o.scout_id)) + '</b></span>' +
        '</div>' +
        '<div class="conf"><span style="font-size:11px;color:var(--muted)">confidence</span>' +
          '<span class="bar"><span style="width:' + Math.round((o.confidence || 0) * 100) + '%"></span></span>' +
          '<span class="pc">' + Math.round((o.confidence || 0) * 100) + '%</span></div>' +
        '<div class="opp-meta" style="margin-top:8px"><span>' + src + '</span><span>·</span><span>' + esc(timeAgo(o.created_at)) + '</span></div>' +
        '<div class="opp-actions">' + actions + '</div>' +
      "</div>";
    }).join("");
  }

  /* ---------- render: pocketbook ---------- */

  function renderPocket() {
    var p = S.pocketbook || {};
    var c = S.capability || {};
    el("pk-expected").textContent = full(p.expected);
    el("pk-sub").textContent = "pipeline " + full(p.pipeline) + " across " +
      ((p.pending || 0) + (p.pursuing || 0)) + " open opportunities";
    el("pk-pipeline").textContent = money(p.pipeline);
    el("pk-won").textContent = money(p.won);
    el("pk-winrate").textContent = p.win_rate ? Math.round(p.win_rate * 100) + "%" : "—";
    el("pk-counts").textContent = ((p.pending || 0) + (p.pursuing || 0)) + " / " + (p.won_count || 0);

    var stages = [
      { k: "Pending", v: sumState("pending"), col: "var(--gold)" },
      { k: "Pursuing", v: sumState("pursuing"), col: "var(--accent2)" },
      { k: "Won", v: sumState("won"), col: "var(--green)" },
      { k: "Lost", v: sumState("lost"), col: "var(--red)" }
    ];
    var max = Math.max.apply(null, stages.map(function (s) { return s.v; }).concat([1]));
    el("pk-bars").innerHTML = stages.map(function (s) {
      var w = Math.round((s.v / max) * 100);
      return '<div class="barrow"><span class="lbl">' + s.k + '</span>' +
        '<span class="track"><span style="width:' + w + '%;background:' + s.col + '"></span></span>' +
        '<span class="amt">' + money(s.v) + '</span></div>';
    }).join("");

    el("cap-tier").textContent = c.tier || "Scout";
    el("cap-level").textContent = c.level || 1;
    el("cap-xp").textContent = (c.xp || 0) + " XP";
    el("cap-dec").textContent = c.decisions || 0;
    el("cap-won").textContent = c.won || 0;
    el("cap-progress").style.width = Math.round(((c.into_level || 0) / 150) * 100) + "%";
    el("cap-next").textContent = "Level " + ((c.level || 1) + 1) + " in " + (c.to_next || 150) +
      " XP. Capability is computed from the signed record — it reflects what actually happened.";
  }
  function sumState(st) {
    return S.opportunities.filter(function (o) { return o.state === st; })
      .reduce(function (a, o) { return a + Number(o.value || 0); }, 0);
  }

  /* ---------- render: record ---------- */

  function renderRecord(report) {
    if (report) {
      var rows = [];
      rows.push(check(report.ledger.ok, "Ledger chain intact (" + report.ledger.entries + " entries)"));
      var badP = report.proposals.filter(function (x) { return !x.signature_ok; }).length;
      rows.push(check(badP === 0, "Proposal signatures (" + report.proposals.length + " checked)"));
      var badD = report.decisions.filter(function (x) { return !x.signature_ok; }).length;
      rows.push(check(badD === 0, "Arbitrator signatures (" + report.decisions.length + " checked)"));
      el("integrity").innerHTML = rows.join("");
    }
    el("rec-arb").textContent = S.arbitrator.fingerprint || "—";
    el("rec-height").textContent = (S.ledger_count || 0) + " blocks";
    el("rec-nodes").textContent = S.nodes.length;
    el("rec-model").textContent = S._model || "—";
  }
  function check(ok, label) {
    return '<div class="check ' + (ok ? "ok" : "bad") + '"><span class="ico">' +
      (ok ? "✓" : "✗") + '</span><span>' + esc(label) + "</span></div>";
  }

  function renderLedger() {
    var box = el("ledger");
    if (!S.ledger.length) {
      box.innerHTML = '<div class="empty"><div class="ico">⛓️</div><p>The ledger is empty.</p></div>';
      return;
    }
    box.innerHTML = S.ledger.slice().reverse().map(function (e) {
      return '<div class="entry"><span class="idx">#' + esc(e.index) + '</span>' +
        '<div class="body"><span class="kind">' + esc(e.kind) + '</span>' +
        '<div class="msg">' + humanize(e) + '</div>' +
        '<div class="hash">' + esc(short(e.prev_hash, 12)) + '… → ' + esc(short(e.hash, 12)) + '…</div>' +
        "</div></div>";
    }).join("");
  }
  function humanize(e) {
    var p = e.payload || {}, k = e.kind;
    if (k === "hub.initialised") return "Hub initialised (v" + esc(p.version) + ").";
    if (k === "node.registered") return "<b>" + esc(p.name) + "</b> commissioned as a scout.";
    if (k === "node.removed") return "<b>" + esc(p.name) + "</b> removed.";
    if (k === "scout.deployed") return "<b>" + esc(p.scout_name) + "</b> deployed: <b>" + esc(p.mission) + "</b>.";
    if (k === "scout.returned") return "<b>" + esc(p.scout_name) + "</b> returned <b>" + esc(p.found) + "</b> opportunities.";
    if (k.indexOf("gate.opportunity.") === 0) return "You <b>" + esc(k.slice(17)) + "</b> — <b>" + esc(p.title) + "</b> (" + full(p.value) + ")" + (p.rationale ? ' <span class="lbl">“' + esc(p.rationale) + '”</span>' : "") + ".";
    if (k.indexOf("gate.") === 0) return "Human <b>" + esc(k.slice(5)) + "</b> — <b>" + esc(p.title) + "</b>.";
    if (k === "proposal.submitted") return "<b>" + esc(p.node_name || "") + "</b> proposed <b>" + esc(p.title) + "</b>.";
    return esc(k);
  }

  /* ---------- nav badge ---------- */

  function renderBadge() {
    var n = S.opportunities.filter(function (o) { return o.state === "pending"; }).length;
    var b = el("nav-badge");
    if (n > 0) { b.style.display = "flex"; b.textContent = n; }
    else b.style.display = "none";
  }

  /* ---------- data flow ---------- */

  function refresh() {
    return api("/api/state").then(function (s) {
      S = s;
      // Render the whole UI the instant state arrives — never block on the
      // (possibly slow) compute probe or the verify pass.
      renderHeader(); renderScoutSelect(); renderChannels(); renderMissions();
      renderOpps(); renderPocket(); renderBadge(); renderLedger();
      renderRecord(null);

      // Background: verify the signed record.
      api("/api/verify").then(function (v) {
        verifyMap = {};
        (v.proposals || []).forEach(function (p) { verifyMap[p.id] = p.signature_ok; });
        renderRecord(v);
      }).catch(function () { renderRecord(null); });

      // Background: probe local compute (fire-and-forget).
      api("/api/models").then(function (m) {
        S._model = m.available ? m.model + " (online)" : "offline (fallback)";
        renderRecord(null);
      }).catch(function () { S._model = "—"; renderRecord(null); });
    }).catch(function (e) {
      toast("Hub unreachable: " + e.message);
    });
  }

  /* ---------- actions ---------- */

  function deploy() {
    var scoutId = el("d-scout").value;
    var mission = el("d-mission").value.trim();
    if (!scoutId) { toast("Commission a scout first."); return; }
    if (!mission) { toast("Give the scout a mission."); return; }
    var btn = el("btn-deploy");
    btn.disabled = true; btn.textContent = "🛰️ Scout is out…";
    api("/api/scout/deploy", "POST", { scout_id: scoutId, mission: mission, channel: channel, limit: 6 })
      .then(function (r) {
        btn.disabled = false; btn.textContent = "🚀 Deploy scout";
        if (!r.ok) { toast(r.error || "Deploy failed"); return; }
        el("d-mission").value = "";
        toast("Scout returned " + r.opportunities.length + " opportunities.");
        filter = "open";
        setFilterChips();
        refresh();
        go("gate");
      }).catch(function (e) {
        btn.disabled = false; btn.textContent = "🚀 Deploy scout";
        toast("Deploy failed: " + e.message);
      });
  }

  function addScout() {
    var name = el("n-name").value.trim();
    var role = el("n-role").value.trim() || "Opportunity scout";
    if (!name) { toast("A scout needs a name."); return; }
    api("/api/nodes", "POST", { name: name, role: role, caps: ["scout", "hunt"] }).then(function (r) {
      if (!r.ok) { toast(r.error || "Failed"); return; }
      el("n-name").value = ""; el("n-role").value = "";
      toast("Commissioned " + name + ".");
      refresh();
    });
  }

  function decide(act, id) {
    var label = { approve: "Pursue", reject: "Pass", won: "Won", lost: "Lost", reopen: "Reopen" }[act] || act;
    api("/api/opportunity/decide", "POST", { opportunity_id: id, action: act, rationale: "" })
      .then(function (r) {
        if (!r.ok) { toast(r.error || "Failed"); return; }
        toast("Decision signed: " + label + ".");
        refresh();
      });
  }

  /* ---------- navigation ---------- */

  function go(screen) {
    document.querySelectorAll(".screen").forEach(function (s) { s.classList.remove("active"); });
    el("screen-" + screen).classList.add("active");
    document.querySelectorAll(".navbtn").forEach(function (b) {
      b.classList.toggle("on", b.getAttribute("data-screen") === screen);
    });
    window.scrollTo(0, 0);
  }

  function setFilterChips() {
    document.querySelectorAll("#gate-filters .chip").forEach(function (c) {
      c.classList.toggle("on", c.getAttribute("data-filter") === filter);
    });
  }

  /* ---------- wiring ---------- */

  function bind() {
    document.querySelectorAll(".navbtn").forEach(function (b) {
      b.addEventListener("click", function () { go(b.getAttribute("data-screen")); });
    });
    el("d-channels").addEventListener("click", function (e) {
      var c = e.target.closest("[data-ch]");
      if (!c) return;
      channel = c.getAttribute("data-ch");
      renderChannels();
    });
    el("gate-filters").addEventListener("click", function (e) {
      var c = e.target.closest("[data-filter]");
      if (!c) return;
      filter = c.getAttribute("data-filter");
      setFilterChips(); renderOpps();
    });
    el("btn-deploy").addEventListener("click", deploy);
    el("btn-add-scout").addEventListener("click", addScout);
    el("btn-verify").addEventListener("click", function () { toast("Verifying…"); refresh(); });
    el("opp-list").addEventListener("click", function (e) {
      var b = e.target.closest("[data-act]");
      if (b) decide(b.getAttribute("data-act"), b.getAttribute("data-id"));
    });
    el("n-name").addEventListener("keydown", function (e) { if (e.key === "Enter") addScout(); });
    el("d-mission").addEventListener("keydown", function (e) {
      if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) deploy();
    });
  }

  /* ---------- PWA install ---------- */

  var deferredPrompt = null;
  window.addEventListener("beforeinstallprompt", function (e) {
    e.preventDefault();
    deferredPrompt = e;
    el("install-banner").classList.add("show");
  });
  function bindInstall() {
    el("btn-install").addEventListener("click", function () {
      if (!deferredPrompt) { toast("Use your browser menu → Add to Home Screen."); return; }
      deferredPrompt.prompt();
      deferredPrompt.userChoice.then(function () { deferredPrompt = null; el("install-banner").classList.remove("show"); });
    });
  }

  /* ---------- boot ---------- */

  bind();
  bindInstall();
  refresh();
  setInterval(refresh, 10000);

  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("sw.js").catch(function () {});
  }
})();
