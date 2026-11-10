"""Fixed crisis resources (D-016).

When a user message carries a danger, self-harm or abuse signal, the harness puts a fixed, checked template
BEFORE whatever else the reply says (D-026; v1 put it after). The model never writes this text. Signals are
regexes; a cluster fires only when at least `min` of its distinct groups match in one message (D-069).
The default config is configs/safety/crisis-v3.yaml (config.CRISIS_YAML). crisis-v4.yaml (B7 frozen fix: v3 plus
indirect danger, self-harm and coercion wording) is selected by Pipeline on the full-v0 path only, where the
context note is checked too (check_turn). If a config fails to load or its sha256 differs from its pin, the
built-in copy of that version below is used: showing the numbers is the safe failure.
"""
import re
from dataclasses import dataclass

import yaml

from . import config

BUILTIN_TEMPLATE = ("If you're in immediate danger, call 911 (US). For crisis support, call or text 988 "
                    "(Suicide & Crisis Lifeline, US). Outside the US, call your local emergency number.")
# Must equal the signals in configs/safety/crisis-v2.yaml and crisis-v3.yaml exactly (D-026, D-069; tests check parity).
BUILTIN_SIGNALS = [
    "\\b(i|i'm|im|i am)\\b[^.?!]{0,12}\\b(not|don't|dont|do not|no longer)\\s+(feel\\s+)?safe\\b",
    "\\b(i'm|im|i am|we're|we are|someone is|he is|she is|they are)\\s+in\\s+(immediate\\s+)?danger\\b",
    '\\b(kill|hurt|harm|cut)(ing)?\\s+(myself|herself|himself|themselves|themself)\\b',
    '\\bsuicid(e|al)\\b',
    '\\bself[- ]?harm',
    '\\b(end\\s+my\\s+life|end\\s+it\\s+all|take\\s+my\\s+(own\\s+)?life)\\b',
    '\\b(i\\s+)?want\\s+to\\s+die\\b',
    '\\bno\\s+reason\\s+to\\s+(live|go\\s+on)\\b',
    '\\boverdos(e|ed|ing)\\b',
    "\\b(he|she|they|someone)('s|\\s+is|\\s+are|'re)?\\s+(going\\s+to|threatening\\s+to|trying\\s+to)\\s+(hurt|kill)\\s+(me|us)\\b",
    "\\b(can't|cant|cannot|can\\s+not)\\s+go\\s+on\\b(?!\\s+(the\\s+|a\\s+|that\\s+|this\\s+|my\\s+)?(record|stage|air|tv|camera|leave|vacation|holiday|tour|trip|date|call|stream|line|ride|website|site|internet)\\b)",
    "\\b(nobody|no\\s+one|no-one)\\s+(would|will|'d|is\\s+going\\s+to)\\s+(even\\s+)?(miss|notice)\\s+(me|if\\s+i)\\b",
    '\\b(he|she|they|someone|somebody|my\\s+(husband|wife|partner|boyfriend|girlfriend|dad|father|mom|mother|parent|stepdad|stepmom|stepfather|stepmother|ex|uncle|brother|sister|teacher|coach))\\s+(hits|hit|beats|beat|hurts|hurt|abuses|abused|kicks|kicked|chokes|choked|is\\s+(hitting|abusing|hurting|beating)|has\\s+been\\s+(hitting|abusing|hurting|beating)|used\\s+to\\s+(hit|beat|abuse|hurt))\\s+me\\b(?!\\s+up\\b)',
    "\\bi\\s+(was|am|'m|have\\s+been|got|was\\s+being|am\\s+being)\\s+(being\\s+)?(abused|assaulted|raped|molested|beaten)\\b",
]
# Must equal the clusters in configs/safety/crisis-v3.yaml exactly (D-069; tests check parity).
BUILTIN_CLUSTERS = [{'name': 'goodbye-planning', 'min': 2, 'groups': ['\\b(giv(e|ing)|gave)\\s+(away\\s+)?(my|all\\s+my|most\\s+of\\s+my)\\s+(stuff|things|belongings|possessions|clothes|books|records)(\\s+away)?\\b', '\\b(wrote|writing|written|write)\\s+(goodbye\\s+)?letters?\\s+(to|for)\\b|\\bgoodbye\\s+letters?\\b', '\\b(weirdly|strangely|oddly|suddenly|weird(ly)?|strange(ly)?)\\s+calm\\b|\\bat\\s+peace\\s+now\\b', '\\b(settl(e|ed|ing)|put(ting)?\\s+in\\s+order)\\s+(my\\s+)?(affairs|accounts)\\b|\\b(made|updated|wrote)\\s+(out\\s+)?my\\s+will\\b']}, {'name': 'physical-shelter', 'min': 2, 'groups': ['\\b(locked|hiding|hid|barricaded)\\s+(myself\\s+)?(in|inside)\\s+(the\\s+|my\\s+|a\\s+)?(bathroom|bedroom|room|closet|car)\\b|\\b(in|inside)\\s+the\\s+(bathroom|bedroom|room|closet)\\s+with\\s+the\\s+door\\s+locked\\b', "\\b(threw|throwing|thrown|smashed|smashing|punched|punching)\\s+(a|the|my)?\\s*(glass|plate|bottle|chair|things|stuff|something|phone|wall|door)\\b|\\b(i'll|i\\s+will|you'll|you\\s+will)\\s+regret\\s+(it|this)\\b|\\b(screaming|yelling|shouting)\\s+(at\\s+me|that\\s+i)\\b|\\b(has|with|grabbed)\\s+a\\s+(knife|gun|weapon|bat)\\b|\\btrying\\s+to\\s+(break|get)\\s+(in|the\\s+door)\\b"]}]
# B7 frozen fix (crisis-v4): v3 signals and clusters verbatim plus the additions below. Must equal
# configs/safety/crisis-v4.yaml exactly (tests/test_crisis_v4.py checks parity). Pipeline uses v4 on full-v0 only.
CRISIS_V4_YAML = config.CONFIGS / "safety" / "crisis-v4.yaml"
CRISIS_V4_PIN = config.CONFIGS / "safety" / "crisis-v4.sha256"
BUILTIN_SIGNALS_V4 = BUILTIN_SIGNALS + [
    "\\b(don't|dont|do not|no longer)\\s+want\\s+to\\s+(be\\s+alive|live|exist|wake\\s+up)\\b",
    '\\b(better\\s+off\\s+without\\s+me|better\\s+off\\s+if\\s+i\\s+(was|were)\\s+(gone|dead|not\\s+here))\\b',
    '\\b(go|going|gone)\\s+(quiet|away|dark)\\s+for\\s+good\\b',
    '\\b(trying\\s+to\\s+break|breaking|broke|broken)\\s+in(to)?\\s+(my|our|the)\\s+(home|house|apartment|flat|room|car|place)\\b',
    "\\b(he|she|they|my\\s+\\w+|the\\s+baby|someone)\\s+(isn't|isnt|is\\s+not|stopped|can't|cant|cannot)\\s+breathing\\b",
    '\\bthreaten(ed|s|ing)?\\s+to\\s+(hurt|kill|harm|beat|attack|stab|shoot)\\s+(me|us|them|him|her|my\\s+(kids|children|family|baby))\\b',
]
BUILTIN_CLUSTERS_V4 = BUILTIN_CLUSTERS + [{'name': 'trapped-hazard', 'min': 2, 'groups': ['\\b(car|truck|vehicle|we|i)\\s+(slid|skidded|crashed|flipped|rolled|went)\\s+(off|into|over)\\b|\\boff\\s+the\\s+road\\b|\\binto\\s+(a|the)\\s+(ditch|river|lake|canal)\\b|\\b(house|building|car|kitchen|room)\\s+is\\s+on\\s+fire\\b', "\\b(water|smoke|fire|flames)\\s+(is|are)\\s+(coming|pouring|getting|rising|spreading)\\b|\\b(seat\\s*belt|door|window)s?\\s+(is\\s+|are\\s+)?(jammed|stuck)\\b|\\b(i'm|im|i\\s+am|we're|we\\s+are)\\s+trapped\\b"]}, {'name': 'coercive-control', 'min': 2, 'groups': ["\\b(decides|controls|chooses|dictates)\\s+(what|who|where|when|how)\\s+i\\b|\\b(won't|wont|doesn't|does\\s+not|will\\s+not)\\s+let\\s+me\\s+(see|talk\\s+to|call|text|leave|go\\s+out|have\\s+money|work)\\b|\\b(i'm|im|i\\s+am)\\s+not\\s+allowed\\s+to\\s+(leave|go|see|talk|call|text|work)\\b|\\b(asking|ask|need)\\s+(for\\s+)?permission\\s+(before|to)\\s+(i\\s+)?(call|see|leave|go\\s+out|talk|text|eat|spend)\\b|\\bcontrols?\\s+(all\\s+)?(my|our|their|his|her)\\s+(money|phone|finances|bank\\s+account|cards?)\\b", "\\b(take|taking)\\s+(away\\s+)?(the|my|our)\\s+(kids|children|baby)\\b|\\b(tell|telling)\\s+everyone\\s+(i'm|im|i\\s+am)\\b|\\breads\\s+(everything|all\\s+my\\s+(messages|texts|emails))\\b|\\b(checks|goes\\s+through|tracks|monitors)\\s+(my\\s+)?(phone|messages|texts|location|emails)\\b|\\bcareful\\s+what\\s+i\\s+(type|say|write|text)\\b|\\bisolat(es|ed|ing)\\s+(me|them|him|her)\\b|\\b(shouts|yells|screams)\\s+at\\s+(me|them|him|her)\\s+until\\b"]}]


@dataclass
class CrisisCheck:
    fired: bool
    matched: str
    template: str
    version: str
    sha256: str
    error: str = ""

    def to_dict(self):
        return dict(self.__dict__)


class CrisisResources:
    def __init__(self, path=None, pin_path=None, builtin=None):
        self.path = path or config.CRISIS_YAML
        self.pin_path = pin_path or config.CRISIS_PIN
        self.error, self.sha256, self.version = "", "", "builtin"
        fb_pats, fb_clus = builtin or (BUILTIN_SIGNALS, BUILTIN_CLUSTERS)   # fallback copy for this version
        self.template, pats, clus = BUILTIN_TEMPLATE, fb_pats, fb_clus
        try:
            self.sha256 = config.sha256_file(self.path)
            with open(self.pin_path) as fh:
                pinned = fh.read().strip()
            if self.sha256 != pinned:
                raise ValueError("crisis config sha256 != pin")
            with open(self.path) as fh:
                doc = yaml.safe_load(fh)
            self.template = " ".join(doc["template"].split())
            self.version = doc["version"]
            pats = doc["signals"]
            clus = doc.get("clusters") or []
        except Exception as e:
            self.error = f"{type(e).__name__}: {e} (built-in template used)"
            self.template, pats, self.version = BUILTIN_TEMPLATE, fb_pats, "builtin"
            clus = fb_clus
        self.signals = [re.compile(p, re.I) for p in pats]
        self.clusters = [(c["name"], int(c["min"]), [re.compile(g, re.I) for g in c["groups"]]) for c in clus]

    def check(self, text):
        t = (text or "").replace("\u2019", "'")
        for p in self.signals:
            m = p.search(t)
            if m:
                return CrisisCheck(True, m.group(0), self.template, self.version, self.sha256, self.error)
        for name, need, groups in self.clusters:  # D-069: >= need distinct groups in one message
            hits = [m.group(0) for m in (g.search(t) for g in groups) if m]
            if len(hits) >= need:
                return CrisisCheck(True, name + ': ' + ' | '.join(hits), self.template, self.version, self.sha256, self.error)
        return CrisisCheck(False, "", "", self.version, self.sha256, self.error)

    def check_turn(self, text, context_note=""):
        """B7 frozen fix (full-v0 only): check the user's words, then the context note shown with them."""
        chk = self.check(text)
        if chk.fired or not context_note:
            return chk
        note = self.check(context_note)
        if note.fired:
            note.matched = "context_note: " + note.matched
        return note if note.fired else chk

    @staticmethod
    def append(output, chk):
        """Add the fixed text once, BEFORE the reply (D-026); never replaces the reply.

        The name is kept for callers. Scoring reads the model text from before this step."""
        if not chk.fired:
            return output
        return (chk.template + "\n\n" + output.strip()) if output.strip() else chk.template
