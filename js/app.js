/* ==========================================================================
   AI-Node-Gate — Hub logic
   Nodes · Proposals · The Gate (arbitration) · Ledger
   State is persisted in localStorage under a single key.
   ========================================================================== */

(function () {
  "use strict";

  var STORAGE_KEY = "ai-node-gate:v1";

  /* ---------- State ---------- */

  var state = {
    nodes: [],
    proposals: [],
    ledger: []
  };

  var ui = { filter: "all" };

  function uid(prefix) {
    return (prefix || "id") + "-" + Math.random().toString(36).slice(2, 8) + Date.now().toString(36).slice(-3);
  }

  function nowISO() {
    return new Date().toISOString();
  }

  function save() {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch (e) {
      console.warn("Could not persist state:", e);
    }
  }

  function load() {
    try {
      var raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        var parsed = JSON.parse(raw);
        state.nodes = parsed.nodes || [];
        state.proposals = parsed.proposals || [];
        state.ledger = parsed.ledger || [];
      }
    } catch (e) {
      console.warn("Could not load state:", e);
    }
  }

  /* ---------- Ledger ---------- */

  function log(kind, msg) {
    state.ledger.unshift({ id: uid("ev"), ts: nowISO(), kind: kind, msg: msg });
    if (state.ledger.length > 400) state.ledger.length = 400;
  }

  /* ---------- Lookups ---------- */

  function nodeById(id) {
    for (var i = 0; i < state.nodes.length; i++) if (state.nodes[i].id === id) return state.nodes[i];
    return null;
  }

  function propById(id) {
    for (var i = 0; i < state.proposals.length; i++) if (state.proposals[i].id === id) return state.proposals[i];
    return null;
  }

  function nodeName(id) {
    var n = nodeById(id);
    return n ? n.name : "—";
  }

  function isBlocked(p) {
    if (!p.dependsOn) return false;
    var dep = propById(p.dependsOn);
    if (!dep) return false;
    return dep.state !== "done" && dep.state !== "approved";
  }

  /* ---------- Rendering ---------- */

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  function renderStats() {
    document.getElementById("stat-nodes").textContent = state.nodes.length;
    var pending = state.proposals.filter(function (p) { return p.state === "pending"; }).length;
    var approved = state.proposals.filter(function (p) { return p.state === "approved" || p.state === "in_progress" || p.state === "done"; }).length;
    document.getElementById("stat-pending").textContent = pending;
    document.getElementById("stat-approved").textContent = approved;
    document.getElementById("stat-ledger").textContent = state.ledger.length;
  }

  function renderNodes() {
    var el = document.getElementById("node-list");
    document.getElementById("node-count").textContent = state.nodes.length;
    if (!state.nodes.length) {
      el.innerHTML = '<div class="empty">No nodes yet. Register one above.</div>';
      return;
    }
    el.innerHTML = state.nodes.map(function (n) {
      var caps = (n.caps || []).map(function (c) { return '<span class="chip">' + esc(c) + "</span>"; }).join("");
      return (
        '<div class="node">' +
          '<span class="dot ' + esc(n.status) + '" title="' + esc(n.status) + '"></span>' +
          '<div class="meta">' +
            '<div class="name">' + esc(n.name) + "</div>" +
            '<div class="role">' + esc(n.role || "unassigned role") + "</div>" +
            (caps ? '<div class="caps">' + caps + "</div>" : "") +
          "</div>" +
          '<button class="btn sm ghost" data-del-node="' + esc(n.id) + '" title="Remove node">✕</button>' +
        "</div>"
      );
    }).join("");
  }

  function renderSelects() {
    var byNode = document.getElementById("prop-node");
    var target = document.getElementById("prop-target");
    var dep = document.getElementById("prop-depends");

    var nodeOpts = state.nodes.length
      ? state.nodes.map(function (n) { return '<option value="' + esc(n.id) + '">' + esc(n.name) + "</option>"; }).join("")
      : '<option value="">— no nodes —</option>';

    byNode.innerHTML = nodeOpts;
    target.innerHTML = '<option value="">— unassigned —</option>' + nodeOpts;

    var depOpts = state.proposals
      .filter(function (p) { return p.state !== "rejected"; })
      .map(function (p) { return '<option value="' + esc(p.id) + '">' + esc(p.title) + "</option>"; }).join("");
    dep.innerHTML = '<option value="">— none —</option>' + depOpts;
  }

  function badge(state_) {
    return '<span class="badge ' + esc(state_) + '">' + esc(state_.replace("_", " ")) + "</span>";
  }

  function priBadge(p) {
    return '<span class="badge pri-' + esc(p) + '">' + esc(p) + "</span>";
  }

  function renderProposals() {
    var el = document.getElementById("prop-list");
    var list = state.proposals.filter(function (p) {
      return ui.filter === "all" ? true : p.state === ui.filter;
    });

    if (!list.length) {
      el.innerHTML = '<div class="empty">Nothing here yet.</div>';
      return;
    }

    el.innerHTML = list.map(function (p) {
      var blocked = isBlocked(p);
      var actions = [];

      if (p.state === "pending") {
        actions.push('<button class="btn sm green" data-act="approve" data-id="' + esc(p.id) + '"' + (blocked ? ' disabled title="Blocked by a dependency"' : "") + ">✓ Approve</button>");
        actions.push('<button class="btn sm red" data-act="reject" data-id="' + esc(p.id) + '">✕ Reject</button>');
        actions.push('<button class="btn sm amber" data-act="amend" data-id="' + esc(p.id) + '">✎ Amend</button>');
        actions.push('<button class="btn sm purple" data-act="delegate" data-id="' + esc(p.id) + '">⇄ Delegate</button>');
      } else if (p.state === "approved") {
        actions.push('<button class="btn sm primary" data-act="start" data-id="' + esc(p.id) + '">▶ Start</button>');
        actions.push('<button class="btn sm ghost" data-act="reopen" data-id="' + esc(p.id) + '">↺ Reopen</button>');
      } else if (p.state === "in_progress") {
        actions.push('<button class="btn sm purple" data-act="complete" data-id="' + esc(p.id) + '">✔ Complete</button>');
      } else if (p.state === "rejected" || p.state === "done") {
        actions.push('<button class="btn sm ghost" data-act="reopen" data-id="' + esc(p.id) + '">↺ Reopen</button>');
      }

      var depLine = "";
      if (p.dependsOn) {
        var dep = propById(p.dependsOn);
        depLine = '<div class="deps">↳ depends on: <b>' + esc(dep ? dep.title : "removed") + "</b>" +
          (blocked ? ' <span class="blocked-note">(blocked)</span>' : " (ready)") + "</div>";
      }

      return (
        '<div class="prop" data-state="' + esc(p.state) + '">' +
          '<div class="prop-top">' +
            "<div>" +
              '<div class="prop-title">' + esc(p.title) + "</div>" +
              (p.desc ? '<div class="prop-desc">' + esc(p.desc) + "</div>" : "") +
            "</div>" +
            "<div>" + badge(p.state) + " " + priBadge(p.priority) + "</div>" +
          "</div>" +
          '<div class="prop-meta">' +
            "<span>raised by " + esc(nodeName(p.nodeId)) + "</span>" +
            '<span class="sep">·</span>' +
            "<span>assigned " + esc(p.targetId ? nodeName(p.targetId) : "unassigned") + "</span>" +
            '<span class="sep">·</span>' +
            "<span>" + esc(new Date(p.createdAt).toLocaleString()) + "</span>" +
          "</div>" +
          depLine +
          (actions.length ? '<div class="prop-actions">' + actions.join("") + "</div>" : "") +
        "</div>"
      );
    }).join("");
  }

  function renderLedger() {
    var el = document.getElementById("ledger");
    if (!state.ledger.length) {
      el.innerHTML = '<div class="empty">The ledger is empty.</div>';
      return;
    }
    el.innerHTML = state.ledger.map(function (e) {
      return (
        '<div class="entry">' +
          '<span class="ts">' + esc(new Date(e.ts).toLocaleTimeString()) + "</span>" +
          '<span class="kind">' + esc(e.kind) + "</span>" +
          '<span class="msg">' + e.msg + "</span>" +
        "</div>"
      );
    }).join("");
  }

  function render() {
    renderStats();
    renderNodes();
    renderSelects();
    renderProposals();
    renderLedger();
  }

  /* ---------- Actions ---------- */

  function toast(msg) {
    var t = document.getElementById("toast");
    t.textContent = msg;
    t.classList.add("show");
    clearTimeout(t._timer);
    t._timer = setTimeout(function () { t.classList.remove("show"); }, 2200);
  }

  function addNode() {
    var name = document.getElementById("node-name").value.trim();
    var role = document.getElementById("node-role").value.trim();
    var caps = document.getElementById("node-caps").value.split(",").map(function (c) { return c.trim(); }).filter(Boolean);
    if (!name) { toast("A node needs a name."); return; }

    var node = { id: uid("node"), name: name, role: role, caps: caps, status: "idle" };
    state.nodes.push(node);
    log("node", "<b>" + esc(name) + "</b> registered" + (role ? " as " + esc(role) : "") + ".");
    document.getElementById("node-name").value = "";
    document.getElementById("node-role").value = "";
    document.getElementById("node-caps").value = "";
    save(); render(); toast("Node registered: " + name);
  }

  function addProposal() {
    var title = document.getElementById("prop-title").value.trim();
    var desc = document.getElementById("prop-desc").value.trim();
    var nodeId = document.getElementById("prop-node").value;
    var targetId = document.getElementById("prop-target").value;
    var priority = document.getElementById("prop-priority").value;
    var dependsOn = document.getElementById("prop-depends").value;

    if (!title) { toast("A proposal needs a title."); return; }
    if (!nodeId) { toast("Register a node first."); return; }

    var p = {
      id: uid("prop"),
      title: title,
      desc: desc,
      nodeId: nodeId,
      targetId: targetId || null,
      priority: priority,
      dependsOn: dependsOn || null,
      state: "pending",
      createdAt: nowISO()
    };
    state.proposals.unshift(p);
    log("proposal", "<b>" + esc(nodeName(nodeId)) + "</b> proposed <b>" + esc(title) + "</b> — awaiting the gate.");
    document.getElementById("prop-title").value = "";
    document.getElementById("prop-desc").value = "";
    save(); render(); toast("Proposal submitted for arbitration.");
  }

  function setState(id, newState) {
    var p = propById(id);
    if (!p) return;
    p.state = newState;
  }

  function arbitrate(act, id) {
    var p = propById(id);
    if (!p) return;

    if (act === "approve") {
      if (isBlocked(p)) { toast("Blocked by a dependency."); return; }
      setState(id, "approved");
      log("gate", "Human <b>approved</b> <b>" + esc(p.title) + "</b>.");
      toast("Approved.");
    } else if (act === "reject") {
      setState(id, "rejected");
      log("gate", "Human <b>rejected</b> <b>" + esc(p.title) + "</b>.");
      toast("Rejected.");
    } else if (act === "amend") {
      var next = window.prompt("Amend the proposal title:", p.title);
      if (next === null) return;
      var old = p.title;
      p.title = next.trim() || p.title;
      p.state = "pending";
      log("gate", "Human <b>amended</b> proposal: \"" + esc(old) + "\" → \"" + esc(p.title) + "\".");
      toast("Amended and returned to the gate.");
    } else if (act === "delegate") {
      if (!state.nodes.length) { toast("No nodes to delegate to."); return; }
      var names = state.nodes.map(function (n, i) { return (i + 1) + ") " + n.name; }).join("\n");
      var choice = window.prompt("Delegate to which node?\n" + names, "1");
      var idx = parseInt(choice, 10) - 1;
      if (isNaN(idx) || !state.nodes[idx]) return;
      p.targetId = state.nodes[idx].id;
      log("gate", "Human <b>delegated</b> <b>" + esc(p.title) + "</b> to <b>" + esc(state.nodes[idx].name) + "</b>.");
      toast("Delegated to " + state.nodes[idx].name + ".");
    } else if (act === "start") {
      setState(id, "in_progress");
      if (p.targetId) { var n = nodeById(p.targetId); if (n) n.status = "active"; }
      log("exec", "<b>" + esc(p.title) + "</b> started" + (p.targetId ? " by " + esc(nodeName(p.targetId)) : "") + ".");
      toast("In progress.");
    } else if (act === "complete") {
      setState(id, "done");
      if (p.targetId) { var n2 = nodeById(p.targetId); if (n2) n2.status = "idle"; }
      log("exec", "<b>" + esc(p.title) + "</b> completed.");
      toast("Completed.");
    } else if (act === "reopen") {
      setState(id, "pending");
      log("gate", "<b>" + esc(p.title) + "</b> reopened at the gate.");
      toast("Reopened.");
    }
    save(); render();
  }

  function delNode(id) {
    var n = nodeById(id);
    if (!n) return;
    state.nodes = state.nodes.filter(function (x) { return x.id !== id; });
    log("node", "<b>" + esc(n.name) + "</b> removed from the registry.");
    save(); render();
  }

  function reset() {
    if (!window.confirm("Clear all nodes, proposals, and ledger entries? This cannot be undone.")) return;
    state = { nodes: [], proposals: [], ledger: [] };
    log("system", "Hub reset. Fresh slate.");
    save(); render();
    toast("Hub reset.");
  }

  /* ---------- Wiring ---------- */

  function bind() {
    document.getElementById("btn-add-node").addEventListener("click", addNode);
    document.getElementById("btn-add-prop").addEventListener("click", addProposal);
    document.getElementById("btn-reset").addEventListener("click", reset);

    document.getElementById("prop-list").addEventListener("click", function (e) {
      var btn = e.target.closest("[data-act]");
      if (btn) arbitrate(btn.getAttribute("data-act"), btn.getAttribute("data-id"));
    });

    document.getElementById("node-list").addEventListener("click", function (e) {
      var btn = e.target.closest("[data-del-node]");
      if (btn) delNode(btn.getAttribute("data-del-node"));
    });

    document.getElementById("filters").addEventListener("click", function (e) {
      var btn = e.target.closest("[data-filter]");
      if (!btn) return;
      ui.filter = btn.getAttribute("data-filter");
      Array.prototype.forEach.call(document.querySelectorAll("#filters .btn"), function (b) {
        b.classList.toggle("on", b === btn);
      });
      renderProposals();
    });

    ["node-name", "node-role", "node-caps"].forEach(function (id) {
      document.getElementById(id).addEventListener("keydown", function (e) {
        if (e.key === "Enter") addNode();
      });
    });
    document.getElementById("prop-title").addEventListener("keydown", function (e) {
      if (e.key === "Enter") addProposal();
    });
  }

  /* ---------- Boot ---------- */

  function seedIfEmpty() {
    if (state.nodes.length || state.proposals.length) return;
    state.nodes = [
      { id: uid("node"), name: "Atlas", role: "Planner", caps: ["plan", "prioritise", "route"], status: "idle" },
      { id: uid("node"), name: "Muse", role: "Researcher", caps: ["research", "summarise"], status: "idle" },
      { id: uid("node"), name: "Forge", role: "Builder", caps: ["build", "draft", "execute"], status: "idle" },
      { id: uid("node"), name: "Verity", role: "Critic", caps: ["review", "test", "challenge"], status: "idle" }
    ];
    log("system", "Hub initialised with four seed nodes. Awaiting proposals.");
  }

  load();
  seedIfEmpty();
  bind();
  render();
})();
