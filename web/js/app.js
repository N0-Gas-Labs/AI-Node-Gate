/* ==========================================================================
   AI-Node-Gate — Sovereign Hub console (client)
   Talks to the self-hosted hub API. No framework, no build step.
   ========================================================================== */

(function () {
  "use strict";

  var state = { nodes: [], proposals: [], decisions: [], ledger: [], arbitrator: {} };
  var verifyMap = {};   // proposal id -> signature_ok
  var ledgerCount = 0;

  /* ---------- helpers ---------- */

  function el(id) { return document.getElementById(id); }

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  function short(h, n) { return h ? h.slice(0, n || 12) : ""; }

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
    t._t = setTimeout(function () { t.classList.remove("show"); }, 2400);
  }

  function nodeName(id) {
    for (var i = 0; i < state.nodes.length; i++) if (state.nodes[i].id === id) return state.nodes[i].name;
    return "—";
  }

  function isBlocked(p) {
    if (!p.depends_on) return false;
    for (var i = 0; i < state.proposals.length; i++) {
      if (state.proposals[i].id === p.depends_on) {
        var s = state.proposals[i].state;
        return s !== "done" && s !== "approved";
      }
    }
    return false;
  }

  /* ---------- render ---------- */

  function renderStats() {
    el("s-nodes").textContent = state.nodes.length;
    var pending = state.proposals.filter(function (p) { return p.state === "pending"; }).length;
    var approved = state.proposals.filter(function (p) {
      return p.state === "approved" || p.state === "in_progress" || p.state === "done";
    }).length;
    el("s-pending").textContent = pending;
    el("s-approved").textContent = approved;
    el("s-ledger").textContent = ledgerCount;
    el("ledger-height").textContent = ledgerCount + " blocks";
    el("arb-fp").textContent = state.arbitrator.fingerprint || "—";
  }

  function renderNodes() {
    el("node-count").textContent = state.nodes.length;
    var box = el("node-list");
    if (!state.nodes.length) { box.innerHTML = '<div class="empty">No nodes yet.</div>'; return; }
    box.innerHTML = state.nodes.map(function (n) {
      var caps = (n.caps || []).map(function (c) { return '<span class="chip">' + esc(c) + "</span>"; }).join("");
      return '<div class="node">' +
        '<span class="dot ' + esc(n.status) + '"></span>' +
        '<div class="meta">' +
          '<div class="name">' + esc(n.name) + '</div>' +
          '<div class="role">' + esc(n.role || "unassigned") + '</div>' +
          '<div class="fp">fp ' + esc(n.fingerprint || "—") + '</div>' +
          (caps ? '<div class="caps">' + caps + '</div>' : "") +
        '</div>' +
        '<button class="btn sm ghost" data-del="' + esc(n.id) + '" title="Remove">✕</button>' +
      '</div>';
    }).join("");
  }

  function renderSelects() {
    var nodeOpts = state.nodes.length
      ? state.nodes.map(function (n) { return '<option value="' + esc(n.id) + '">' + esc(n.name) + "</option>"; }).join("")
      : '<option value="">— no nodes —</option>';
    el("p-node").innerHTML = nodeOpts;
    el("p-target").innerHTML = '<option value="">— unassigned —</option>' + nodeOpts;
    var depOpts = state.proposals
      .filter(function (p) { return p.state !== "rejected"; })
      .map(function (p) { return '<option value="' + esc(p.id) + '">' + esc(p.title) + "</option>"; }).join("");
    el("p-depends").innerHTML = '<option value="">— none —</option>' + depOpts;
  }

  function badge(s) { return '<span class="badge ' + esc(s) + '">' + esc(s.replace("_", " ")) + "</span>"; }
  function priBadge(p) { return '<span class="badge pri-' + esc(p) + '">' + esc(p) + "</span>"; }

  function renderProposals() {
    var box = el("prop-list");
    if (!state.proposals.length) { box.innerHTML = '<div class="empty">No proposals yet.</div>'; return; }

    box.innerHTML = state.proposals.map(function (p) {
      var blocked = isBlocked(p);
      var sigOk = verifyMap[p.id];
      var sig = sigOk === undefined ? "" :
        (sigOk ? '<span class="sig-ok">✓ signature verified</span>' : '<span class="sig-bad">✗ signature invalid</span>');

      var actions = [];
      if (p.state === "pending") {
        actions.push('<input class="rationale" data-rat="' + esc(p.id) + '" placeholder="rationale (optional)" />');
        actions.push('<button class="btn sm green" data-act="approve" data-id="' + esc(p.id) + '"' + (blocked ? " disabled" : "") + ">✓ Approve</button>");
        actions.push('<button class="btn sm red" data-act="reject" data-id="' + esc(p.id) + '">✕ Reject</button>');
        actions.push('<button class="btn sm amber" data-act="amend" data-id="' + esc(p.id) + '">✎ Amend</button>');
        actions.push('<button class="btn sm purple" data-act="delegate" data-id="' + esc(p.id) + '">⇄ Delegate</button>');
      } else if (p.state === "approved") {
        actions.push('<button class="btn sm primary" data-act="start" data-id="' + esc(p.id) + '">▶ Start</button>');
        actions.push('<button class="btn sm ghost" data-act="reopen" data-id="' + esc(p.id) + '">↺ Reopen</button>');
      } else if (p.state === "in_progress") {
        actions.push('<button class="btn sm purple" data-act="complete" data-id="' + esc(p.id) + '">✔ Complete</button>');
      } else {
        actions.push('<button class="btn sm ghost" data-act="reopen" data-id="' + esc(p.id) + '">↺ Reopen</button>');
      }

      var dep = "";
      if (p.depends_on) {
        var dt = "removed";
        for (var i = 0; i < state.proposals.length; i++) if (state.proposals[i].id === p.depends_on) dt = state.proposals[i].title;
        dep = '<div class="prop-meta"><span>↳ depends on <b>' + esc(dt) + "</b></span>" + (blocked ? '<span class="sig-bad">blocked</span>' : '<span class="sig-ok">ready</span>') + "</div>";
      }

      return '<div class="prop" data-state="' + esc(p.state) + '">' +
        '<div class="prop-top"><div>' +
          '<div class="prop-title">' + esc(p.title) + '</div>' +
          (p.description ? '<div class="prop-desc">' + esc(p.description) + '</div>' : "") +
        '</div><div>' + badge(p.state) + " " + priBadge(p.priority) + "</div></div>" +
        '<div class="prop-meta">' +
          "<span>by " + esc(nodeName(p.node_id)) + "</span><span class='sep'>·</span>" +
          "<span>→ " + esc(p.target_id ? nodeName(p.target_id) : "unassigned") + "</span><span class='sep'>·</span>" +
          "<span>" + esc(new Date(p.created_at * 1000).toLocaleString()) + "</span>" +
          (sig ? "<span class='sep'>·</span>" + sig : "") +
        "</div>" + dep +
        '<div class="prop-actions">' + actions.join("") + "</div>" +
      "</div>";
    }).join("");
  }

  function renderLedger() {
    var box = el("ledger");
    el("ledger-chip").textContent = ledgerCount + " entries";
    if (!state.ledger.length) { box.innerHTML = '<div class="empty">The ledger is empty.</div>'; return; }
    var rows = state.ledger.slice().reverse();
    box.innerHTML = rows.map(function (e) {
      var msg = e.payload ? humanize(e) : "";
      return '<div class="entry">' +
        '<span class="idx">#' + esc(e.index) + "</span>" +
        '<div class="body">' +
          '<span class="kind">' + esc(e.kind) + "</span>" +
          '<div class="msg">' + msg + "</div>" +
          '<div class="hash"><span class="arrow">↳</span> ' + esc(short(e.prev_hash, 16)) + '… → ' + esc(short(e.hash, 16)) + '…</div>' +
        "</div>" +
      "</div>";
    }).join("");
  }

  function humanize(e) {
    var p = e.payload || {};
    var k = e.kind;
    if (k === "hub.initialised") return "Hub initialised (v" + esc(p.version) + ", " + esc(p.mode) + ").";
    if (k === "node.registered") return "<b>" + esc(p.name) + "</b> registered" + (p.role ? " as " + esc(p.role) : "") + ".";
    if (k === "node.removed") return "<b>" + esc(p.name) + "</b> removed.";
    if (k === "proposal.submitted") return "<b>" + esc(p.node_name || "") + "</b> proposed <b>" + esc(p.title) + "</b>.";
    if (k.indexOf("gate.") === 0) return "Human <b>" + esc(k.slice(5)) + "</b> — <b>" + esc(p.title) + "</b>" + (p.rationale ? ' <span class="lbl">“' + esc(p.rationale) + '”</span>' : "") + ".";
    return esc(k);
  }

  function renderModel(m) {
    el("model-endpoint").textContent = m.endpoint;
    el("model-name").textContent = m.model;
    var b = el("model-badge");
    b.textContent = m.available ? "online" : "offline (fallback)";
    b.style.color = m.available ? "var(--green)" : "var(--amber)";
  }

  function renderIntegrity(report) {
    var box = el("integrity");
    var rows = [];
    rows.push(check(report.ledger.ok, "Ledger chain intact (" + report.ledger.entries + " entries)"));
    var badP = report.proposals.filter(function (x) { return !x.signature_ok; }).length;
    rows.push(check(badP === 0, "Proposal signatures (" + report.proposals.length + " checked)"));
    var badD = report.decisions.filter(function (x) { return !x.signature_ok; }).length;
    rows.push(check(badD === 0, "Arbitrator signatures (" + report.decisions.length + " checked)"));
    box.innerHTML = rows.join("");
    el("s-integrity").textContent = report.ok ? "OK" : "FAIL";
    el("s-integrity").style.color = report.ok ? "var(--green)" : "var(--red)";
    if (!report.ledger.ok && report.ledger.problems.length) {
      box.innerHTML += '<div class="check bad"><span class="ico">!</span><span class="lbl">' + esc(report.ledger.problems[0]) + "</span></div>";
    }
  }

  function check(ok, label) {
    return '<div class="check ' + (ok ? "ok" : "bad") + '"><span class="ico">' + (ok ? "✓" : "✗") + '</span><span class="lbl">' + esc(label) + "</span></div>";
  }

  /* ---------- data flow ---------- */

  function refresh() {
    return api("/api/state").then(function (s) {
      state = s;
      ledgerCount = s.ledger_count;
      return api("/api/verify");
    }).then(function (v) {
      verifyMap = {};
      v.proposals.forEach(function (p) { verifyMap[p.id] = p.signature_ok; });
      renderStats(); renderNodes(); renderSelects(); renderProposals(); renderLedger();
      renderIntegrity(v);
      return api("/api/models");
    }).then(renderModel).catch(function (e) {
      toast("Could not reach the hub: " + e.message);
    });
  }

  /* ---------- actions ---------- */

  function addNode() {
    var name = el("n-name").value.trim();
    var role = el("n-role").value.trim();
    var caps = el("n-caps").value.split(",").map(function (c) { return c.trim(); }).filter(Boolean);
    if (!name) { toast("A node needs a name."); return; }
    api("/api/nodes", "POST", { name: name, role: role, caps: caps }).then(function (r) {
      if (!r.ok) { toast(r.error || "Failed"); return; }
      el("n-name").value = ""; el("n-role").value = ""; el("n-caps").value = "";
      toast("Registered " + name + " and minted its keypair.");
      refresh();
    });
  }

  function addProposal() {
    var title = el("p-title").value.trim();
    var nodeId = el("p-node").value;
    if (!title) { toast("A proposal needs a title."); return; }
    if (!nodeId) { toast("Register a node first."); return; }
    api("/api/proposals", "POST", {
      node_id: nodeId, title: title, description: el("p-desc").value.trim(),
      target_id: el("p-target").value || null, priority: el("p-priority").value,
      depends_on: el("p-depends").value || null
    }).then(function (r) {
      if (!r.ok) { toast(r.error || "Failed"); return; }
      el("p-title").value = ""; el("p-desc").value = "";
      toast("Proposal signed and submitted to the gate.");
      refresh();
    });
  }

  function draft() {
    var nodeId = el("p-node").value;
    var intent = el("p-title").value.trim() || el("p-desc").value.trim();
    if (!nodeId) { toast("Register a node first."); return; }
    if (!intent) { toast("Give the node an intent to draft from."); return; }
    toast("Drafting with a local model…");
    api("/api/draft", "POST", { node_id: nodeId, intent: intent }).then(function (r) {
      if (!r.ok) { toast(r.error || "Failed"); return; }
      var lines = r.draft.split("\n");
      el("p-title").value = (lines[0] || "").replace(/^DRAFT[^:]*:?/i, "").replace(/^Objective:?/i, "").trim().slice(0, 90) || el("p-title").value;
      el("p-desc").value = r.draft;
      toast("Draft ready (" + r.source + "). Review, then sign & submit.");
    });
  }

  function arbitrate(act, id) {
    var rationale = "";
    var input = document.querySelector('[data-rat="' + id + '"]');
    if (input) rationale = input.value.trim();

    if (act === "amend") {
      var cur = null;
      state.proposals.forEach(function (p) { if (p.id === id) cur = p; });
      var next = window.prompt("Amend the proposal title:", cur ? cur.title : "");
      if (next === null) return;
      rationale = rationale || "amended title";
      api("/api/arbitrate", "POST", { proposal_id: id, action: "amend", rationale: rationale }).then(function () {
        // amend title via a follow-up is out of scope for the API; note it
        toast("Amended (rationale recorded)."); refresh();
      });
      return;
    }
    if (act === "delegate") {
      var names = state.nodes.map(function (n, i) { return (i + 1) + ") " + n.name; }).join("\n");
      var choice = window.prompt("Delegate to which node?\n" + names, "1");
      var idx = parseInt(choice, 10) - 1;
      if (isNaN(idx) || !state.nodes[idx]) return;
      rationale = rationale || ("delegated to " + state.nodes[idx].name);
    }

    api("/api/arbitrate", "POST", { proposal_id: id, action: act, rationale: rationale }).then(function (r) {
      if (!r.ok) { toast(r.error || "Failed"); return; }
      toast("Decision signed: " + act + ".");
      refresh();
    });
  }

  function delNode(id) {
    api("/api/nodes/" + id, "DELETE").then(function () { toast("Node removed."); refresh(); });
  }

  /* ---------- wiring ---------- */

  function bind() {
    el("btn-add-node").addEventListener("click", addNode);
    el("btn-add-prop").addEventListener("click", addProposal);
    el("btn-draft").addEventListener("click", draft);
    el("btn-verify").addEventListener("click", function () { toast("Verifying…"); refresh(); });
    el("btn-refresh").addEventListener("click", refresh);

    el("prop-list").addEventListener("click", function (e) {
      var b = e.target.closest("[data-act]");
      if (b) arbitrate(b.getAttribute("data-act"), b.getAttribute("data-id"));
    });
    el("node-list").addEventListener("click", function (e) {
      var b = e.target.closest("[data-del]");
      if (b) delNode(b.getAttribute("data-del"));
    });
    ["n-name", "n-role", "n-caps"].forEach(function (id) {
      el(id).addEventListener("keydown", function (e) { if (e.key === "Enter") addNode(); });
    });
    el("p-title").addEventListener("keydown", function (e) { if (e.key === "Enter") addProposal(); });
  }

  bind();
  refresh();
  setInterval(refresh, 8000);
})();
