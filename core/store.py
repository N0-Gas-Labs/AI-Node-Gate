"""Store — durable persistence in a single SQLite file you own.

Sovereignty starts with data you can hold. The entire hub lives in one SQLite
file on your disk, with no server to rent and no account to depend on. Copy the
file and you have copied the hub. The schema is deliberately plain so that any
tool — or any person with a text editor — can inspect it.

The connection is shared across the server's worker threads, so every public
method is serialised behind a lock. For a single-operator hub this is more than
enough, and it keeps the implementation free of any pooling machinery.
"""

import functools
import os
import sqlite3
import threading
import time

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS nodes (
    id         TEXT PRIMARY KEY,
    name       TEXT NOT NULL,
    role       TEXT,
    caps       TEXT,
    status     TEXT DEFAULT 'idle',
    pubkey     TEXT,
    created_at REAL
);

CREATE TABLE IF NOT EXISTS proposals (
    id            TEXT PRIMARY KEY,
    title         TEXT NOT NULL,
    description   TEXT,
    node_id       TEXT,
    target_id     TEXT,
    priority      TEXT DEFAULT 'med',
    depends_on    TEXT,
    state         TEXT DEFAULT 'pending',
    signature     TEXT,
    created_at    REAL
);

CREATE TABLE IF NOT EXISTS decisions (
    id           TEXT PRIMARY KEY,
    proposal_id  TEXT,
    action       TEXT,
    rationale    TEXT,
    actor_pubkey TEXT,
    signature    TEXT,
    created_at   REAL
);

CREATE TABLE IF NOT EXISTS ledger (
    idx          INTEGER PRIMARY KEY,
    prev_hash    TEXT,
    ts           TEXT,
    kind         TEXT,
    payload_json TEXT,
    hash         TEXT
);

CREATE TABLE IF NOT EXISTS missions (
    id            TEXT PRIMARY KEY,
    scout_id      TEXT,
    scout_name    TEXT,
    mission       TEXT,
    channel       TEXT,
    source        TEXT,
    status        TEXT DEFAULT 'running',
    found         INTEGER DEFAULT 0,
    created_at    REAL
);

CREATE TABLE IF NOT EXISTS opportunities (
    id           TEXT PRIMARY KEY,
    mission_id   TEXT,
    scout_id     TEXT,
    scout_name   TEXT,
    title        TEXT NOT NULL,
    summary      TEXT,
    source       TEXT,
    url          TEXT,
    category     TEXT,
    value        REAL DEFAULT 0,
    confidence   REAL DEFAULT 0,
    effort       TEXT DEFAULT 'med',
    roi          REAL DEFAULT 0,
    state        TEXT DEFAULT 'pending',
    rationale    TEXT,
    created_at   REAL,
    decided_at   REAL
);
"""


def synchronized(method):
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        with self._lock:
            return method(self, *args, **kwargs)
    return wrapper


class Store:
    def __init__(self, path):
        self.path = path
        self._lock = threading.RLock()
        first = not os.path.exists(path)
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        with self._lock:
            self.conn.executescript(SCHEMA)
            self.conn.commit()
        self._is_new = first

    @property
    def is_new(self):
        return self._is_new

    def close(self):
        with self._lock:
            self.conn.close()

    # --- meta --------------------------------------------------------------

    @synchronized
    def get_meta(self, key, default=None):
        row = self.conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default

    @synchronized
    def set_meta(self, key, value):
        self.conn.execute(
            "INSERT INTO meta(key,value) VALUES(?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
        self.conn.commit()

    # --- nodes -------------------------------------------------------------

    @synchronized
    def add_node(self, node):
        self.conn.execute(
            "INSERT INTO nodes(id,name,role,caps,status,pubkey,created_at) "
            "VALUES(:id,:name,:role,:caps,:status,:pubkey,:created_at)",
            node,
        )
        self.conn.commit()

    @synchronized
    def list_nodes(self):
        return [dict(r) for r in self.conn.execute("SELECT * FROM nodes ORDER BY created_at")]

    @synchronized
    def get_node(self, node_id):
        r = self.conn.execute("SELECT * FROM nodes WHERE id=?", (node_id,)).fetchone()
        return dict(r) if r else None

    @synchronized
    def set_node_status(self, node_id, status):
        self.conn.execute("UPDATE nodes SET status=? WHERE id=?", (status, node_id))
        self.conn.commit()

    @synchronized
    def delete_node(self, node_id):
        self.conn.execute("DELETE FROM nodes WHERE id=?", (node_id,))
        self.conn.commit()

    # --- proposals ---------------------------------------------------------

    @synchronized
    def add_proposal(self, p):
        self.conn.execute(
            "INSERT INTO proposals(id,title,description,node_id,target_id,priority,"
            "depends_on,state,signature,created_at) VALUES(:id,:title,:description,"
            ":node_id,:target_id,:priority,:depends_on,:state,:signature,:created_at)",
            p,
        )
        self.conn.commit()

    @synchronized
    def list_proposals(self):
        return [dict(r) for r in self.conn.execute("SELECT * FROM proposals ORDER BY created_at DESC")]

    @synchronized
    def get_proposal(self, pid):
        r = self.conn.execute("SELECT * FROM proposals WHERE id=?", (pid,)).fetchone()
        return dict(r) if r else None

    @synchronized
    def update_proposal(self, pid, **fields):
        cols = ", ".join("%s=?" % k for k in fields)
        self.conn.execute("UPDATE proposals SET %s WHERE id=?" % cols, list(fields.values()) + [pid])
        self.conn.commit()

    # --- decisions ---------------------------------------------------------

    @synchronized
    def add_decision(self, d):
        self.conn.execute(
            "INSERT INTO decisions(id,proposal_id,action,rationale,actor_pubkey,"
            "signature,created_at) VALUES(:id,:proposal_id,:action,:rationale,"
            ":actor_pubkey,:signature,:created_at)",
            d,
        )
        self.conn.commit()

    @synchronized
    def list_decisions(self):
        return [dict(r) for r in self.conn.execute("SELECT * FROM decisions ORDER BY created_at")]

    # --- ledger ------------------------------------------------------------

    @synchronized
    def ledger_entries(self):
        return [dict(r) for r in self.conn.execute(
            "SELECT idx AS \"index\", prev_hash, ts, kind, payload_json, hash "
            "FROM ledger ORDER BY idx")]

    @synchronized
    def ledger_tip(self):
        r = self.conn.execute(
            "SELECT idx AS \"index\", prev_hash, ts, kind, payload_json, hash "
            "FROM ledger ORDER BY idx DESC LIMIT 1").fetchone()
        return dict(r) if r else None

    @synchronized
    def ledger_count(self):
        return self.conn.execute("SELECT COUNT(*) c FROM ledger").fetchone()["c"]

    @synchronized
    def append_ledger(self, entry):
        self.conn.execute(
            "INSERT INTO ledger(idx,prev_hash,ts,kind,payload_json,hash) "
            "VALUES(?,?,?,?,?,?)",
            (entry["index"], entry["prev_hash"], entry["ts"], entry["kind"],
             entry["payload_json"], entry["hash"]),
        )
        self.conn.commit()


    # --- missions (scout deployments) -------------------------------------

    @synchronized
    def add_mission(self, m):
        self.conn.execute(
            "INSERT INTO missions(id,scout_id,scout_name,mission,channel,source,"
            "status,found,created_at) VALUES(:id,:scout_id,:scout_name,:mission,"
            ":channel,:source,:status,:found,:created_at)",
            m,
        )
        self.conn.commit()

    @synchronized
    def list_missions(self):
        return [dict(r) for r in self.conn.execute("SELECT * FROM missions ORDER BY created_at DESC")]

    @synchronized
    def get_mission(self, mid):
        r = self.conn.execute("SELECT * FROM missions WHERE id=?", (mid,)).fetchone()
        return dict(r) if r else None

    @synchronized
    def update_mission(self, mid, **fields):
        cols = ", ".join("%s=?" % k for k in fields)
        self.conn.execute("UPDATE missions SET %s WHERE id=?" % cols, list(fields.values()) + [mid])
        self.conn.commit()

    # --- opportunities -----------------------------------------------------

    @synchronized
    def add_opportunity(self, o):
        self.conn.execute(
            "INSERT INTO opportunities(id,mission_id,scout_id,scout_name,title,"
            "summary,source,url,category,value,confidence,effort,roi,state,"
            "rationale,created_at,decided_at) VALUES(:id,:mission_id,:scout_id,"
            ":scout_name,:title,:summary,:source,:url,:category,:value,:confidence,"
            ":effort,:roi,:state,:rationale,:created_at,:decided_at)",
            o,
        )
        self.conn.commit()

    @synchronized
    def list_opportunities(self):
        return [dict(r) for r in self.conn.execute(
            "SELECT * FROM opportunities ORDER BY created_at DESC")]

    @synchronized
    def get_opportunity(self, oid):
        r = self.conn.execute("SELECT * FROM opportunities WHERE id=?", (oid,)).fetchone()
        return dict(r) if r else None

    @synchronized
    def update_opportunity(self, oid, **fields):
        cols = ", ".join("%s=?" % k for k in fields)
        self.conn.execute("UPDATE opportunities SET %s WHERE id=?" % cols, list(fields.values()) + [oid])
        self.conn.commit()


def utc_now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
