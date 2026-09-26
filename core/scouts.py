"""Scouts — the agents that go out and locate opportunities.

A scout is a node with a mission. You deploy it against a *channel* (a place to
look) and it returns *opportunities*: concrete, scored candidates that come back
to the gate for your decision. Nothing a scout finds is acted on until you
arbitrate.

Two things matter here, and both are deliberate:

* **Sovereignty of sources.** A channel is pluggable. The built-in `DemoSource`
  always works offline so the system is never dead, but the `FeedSource` fetches
  real RSS/Atom feeds over plain HTTP using only the standard library. You point
  it at feeds you trust and it turns their items into scored candidates. No
  third-party SDK, no account, no data leaving your machine.

* **Honest scoring.** Every opportunity carries a value estimate, a confidence
  (0-1), an effort band, and a derived ROI score. The human's scarce resource is
  attention, so the hub ranks by expected value per unit of effort rather than by
  raw size.

A scout never decides. It proposes. The gate decides.
"""

import hashlib
import random
import re
import time
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET


# --- channels (where a scout looks) ---------------------------------------

CHANNELS = {
    "gigs": {
        "label": "Paid work",
        "blurb": "Freelance, contract, and consulting engagements.",
        "keywords": ["contract", "freelance", "consulting", "gig", "hiring",
                     "rfp", "scope of work", "retainer"],
    },
    "grants": {
        "label": "Grants & funding",
        "blurb": "Grants, prizes, and non-dilutive funding.",
        "keywords": ["grant", "funding", "prize", "award", "call for proposals",
                     "accelerator", "bounty"],
    },
    "deals": {
        "label": "Deals & arbitrage",
        "blurb": "Underpriced assets, resale spreads, and cost savings.",
        "keywords": ["for sale", "underpriced", "clearance", "surplus",
                     "liquidation", "wholesale", "discount", "deal"],
    },
    "leads": {
        "label": "Leads & partnerships",
        "blurb": "Prospects and partners worth a conversation.",
        "keywords": ["partnership", "collaboration", "integration", "pilot",
                     "customer", "prospect", "lead", "b2b"],
    },
    "gaps": {
        "label": "Market gaps",
        "blurb": "Unmet needs and product openings you could serve.",
        "keywords": ["need", "missing", "gap", "problem", "pain point",
                     "wanted", "request", "wish"],
    },
}


EFFORT_MULT = {"low": 1.0, "med": 0.6, "high": 0.35}


def roi_score(value, confidence, effort):
    """Expected value per unit of effort, normalised to a 0-100 scale.

    We use a soft curve (log) so that a few large opportunities do not drown out
    a steady stream of small, high-confidence ones — the human sees a spread.
    """
    import math
    ev = max(0.0, float(value)) * max(0.0, min(1.0, float(confidence))) * EFFORT_MULT.get(effort, 0.6)
    # log scale: ~$1k -> ~0, ~$1M -> ~100
    if ev <= 0:
        return 0.0
    score = (math.log10(ev) - 3.0) / 3.0 * 100.0
    return round(max(0.0, min(100.0, score)), 1)


# --- sources ---------------------------------------------------------------

class Source:
    """A place to look. Implementations return candidate dicts."""

    name = "source"

    def hunt(self, mission, channel, limit=6):
        raise NotImplementedError


class DemoSource(Source):
    """Deterministic-but-varied generator so the hub is never dead offline.

    This is a *framework demonstration*, not a claim about real markets: it
    produces plausible, well-formed candidates so the pipeline, scoring, gate,
    and pocketbook can be exercised end-to-end with zero network and zero
    dependencies. Point a scout at a real `FeedSource` for live signal.
    """

    name = "demo"

    _TEMPLATES = {
        "gigs": [
            ("{org} needs a 6-week {topic} build", "Scope-of-work published; fixed-fee engagement.", 8000, 42000),
            ("Retainer: ongoing {topic} support", "Monthly retainer for maintenance and iteration.", 3000, 9000),
            ("{org} RFP for {topic} integration", "Competitive RFP; short window to respond.", 15000, 90000),
            ("Fractional lead for {topic} rollout", "Part-time leadership while they hire.", 6000, 18000),
        ],
        "grants": [
            ("{topic} innovation grant", "Non-dilutive; application + prototype.", 25000, 150000),
            ("Open-source {topic} bounty", "Funded milestone work, public deliverable.", 4000, 20000),
            ("Regional {topic} accelerator", "Cash + credits for a pilot.", 20000, 60000),
            ("{topic} challenge prize", "Prize for the best working prototype.", 10000, 50000),
        ],
        "deals": [
            ("Surplus {topic} hardware, bulk", "Liquidation lot; resale spread likely.", 5000, 30000),
            ("Underpriced {topic} license transfer", "Transferable license below market.", 2000, 12000),
            ("Wholesale {topic} components", "Volume pricing; margin on resale.", 3000, 15000),
            ("Distressed {topic} inventory", "Quick sale; negotiate hard.", 4000, 25000),
        ],
        "leads": [
            ("{org} exploring a {topic} pilot", "Warm inbound; wants a scoped pilot.", 10000, 80000),
            ("Integration partner for {topic}", "Co-sell motion; rev-share.", 6000, 40000),
            ("{org} replacing an incumbent on {topic}", "Displacement opportunity.", 12000, 70000),
            ("Design partner for {topic}", "Early access in exchange for feedback.", 2000, 15000),
        ],
        "gaps": [
            ("No good {topic} tool for small teams", "Underserved segment; build or resell.", 8000, 60000),
            ("{topic} workflow is manual everywhere", "Automation wedge; recurring value.", 10000, 90000),
            ("{topic} compliance is a recurring pain", "Regulatory tailwind; high willingness to pay.", 15000, 120000),
            ("{topic} onboarding is broken", "Productized service; fast to ship.", 5000, 30000),
        ],
    }

    _ORGS = ["Northwind", "Cobalt Labs", "Meridian", "Harbor & Co", "Lumen Group",
             "Ironwood", "Vantage", "Bluepeak", "Stonebridge", "Aperture"]

    def hunt(self, mission, channel, limit=6):
        seed = hashlib.sha256(("%s|%s|%d" % (mission, channel, int(time.time() // 3600))).encode()).hexdigest()
        rng = random.Random(int(seed[:12], 16))
        tmpl = self._TEMPLATES.get(channel, self._TEMPLATES["gigs"])
        topic = _topic_from(mission)
        out = []
        for i in range(min(limit, len(tmpl))):
            title, summary, lo, hi = tmpl[i]
            org = rng.choice(self._ORGS)
            value = round(rng.uniform(lo, hi), -2)
            conf = round(rng.uniform(0.35, 0.92), 2)
            effort = rng.choice(["low", "med", "med", "high"])
            out.append({
                "title": title.format(org=org, topic=topic),
                "summary": summary,
                "source": "scout:%s/demo" % channel,
                "url": "",
                "value": value,
                "confidence": conf,
                "effort": effort,
                "category": channel,
            })
        return out


class FeedSource(Source):
    """Fetch real RSS/Atom feeds and turn items into scored candidates.

    Zero dependencies: urllib for the fetch, xml.etree for the parse. A feed is
    only as trustworthy as where you point it — that is the point. You own the
    list of sources.
    """

    name = "feed"

    def __init__(self, feeds, timeout=8):
        self.feeds = feeds or []
        self.timeout = timeout

    def hunt(self, mission, channel, limit=6):
        terms = _terms(mission) + CHANNELS.get(channel, {}).get("keywords", [])
        found = []
        for url in self.feeds:
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "AI-Node-Gate/0.3 scout"})
                with urllib.request.urlopen(req, timeout=self.timeout) as r:
                    raw = r.read()
                found.extend(self._parse(raw, url, terms))
            except (urllib.error.URLError, OSError, ValueError, ET.ParseError):
                continue
            if len(found) >= limit:
                break
        found.sort(key=lambda c: c["_relevance"], reverse=True)
        for c in found:
            c.pop("_relevance", None)
        return found[:limit]

    def _parse(self, raw, url, terms):
        try:
            root = ET.fromstring(raw)
        except ET.ParseError:
            return []
        items = root.iter("item")
        if not any(True for _ in items):
            items = root.iter("{http://www.w3.org/2005/Atom}entry")
        out = []
        for it in items:
            title = _text(it, "title") or _text(it, "{http://www.w3.org/2005/Atom}title")
            link = _text(it, "link") or _atom_link(it)
            desc = (_text(it, "description") or _text(it, "summary")
                    or _text(it, "{http://www.w3.org/2005/Atom}summary") or "")
            if not title:
                continue
            blob = (title + " " + desc).lower()
            rel = sum(1 for t in terms if t and t in blob)
            if terms and rel == 0:
                continue
            out.append({
                "title": title.strip()[:160],
                "summary": _strip_html(desc)[:280],
                "source": url,
                "url": link or "",
                "value": 0.0,        # unknown until a human sizes it
                "confidence": round(min(0.9, 0.3 + 0.12 * rel), 2),
                "effort": "med",
                "category": "feed",
                "_relevance": rel,
            })
        return out


# --- the scout -------------------------------------------------------------

class Scout:
    """Runs a mission against a source and returns scored opportunities."""

    def __init__(self, source=None):
        self.source = source or DemoSource()

    def run(self, mission, channel="gigs", limit=6):
        channel = channel if channel in CHANNELS else "gigs"
        raw = self.source.hunt(mission, channel, limit=limit)
        out = []
        for c in raw:
            value = float(c.get("value") or 0.0)
            conf = float(c.get("confidence") or 0.0)
            effort = c.get("effort") or "med"
            out.append({
                "title": c.get("title", "Untitled")[:200],
                "summary": c.get("summary", "")[:600],
                "source": c.get("source", "unknown"),
                "url": c.get("url", ""),
                "value": round(value, 2),
                "confidence": round(conf, 2),
                "effort": effort,
                "category": c.get("category", channel),
                "roi": roi_score(value, conf, effort),
            })
        out.sort(key=lambda o: o["roi"], reverse=True)
        return out


# --- helpers ---------------------------------------------------------------

_STOP = {"the", "a", "an", "and", "or", "for", "to", "of", "in", "on", "with",
         "find", "locate", "get", "new", "best", "any", "all", "me", "my"}


def _terms(mission):
    words = re.findall(r"[a-z0-9]+", (mission or "").lower())
    return [w for w in words if w not in _STOP and len(w) > 2]


def _topic_from(mission):
    words = _terms(mission)
    if not words:
        return "the target area"
    return " ".join(words[:3])


def _text(node, tag):
    el = node.find(tag)
    if el is not None and el.text:
        return el.text.strip()
    return ""


def _atom_link(node):
    for el in node.findall("{http://www.w3.org/2005/Atom}link"):
        if el.get("href"):
            return el.get("href")
    return ""


def _strip_html(s):
    return re.sub(r"<[^>]+>", " ", s or "").replace("&nbsp;", " ").strip()
