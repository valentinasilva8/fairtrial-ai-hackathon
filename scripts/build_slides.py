"""Build the pitch deck from the hackathon template, with numbers read live from the data.

Re-run after any data or feature change and the slides update:
    pip install python-pptx
    python scripts/build_slides.py            # -> pitch/Precedent_and_Practice.pptx

Template: final_ppt_example.pptx (slides 1-11 are the pitch template; 12-20 an example deck,
three of whose layouts are reused). Stock portraits are removed so nobody mistakes them for
our team or a real user.
"""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.argument_bank import EXCERPTS, past_cases  # noqa: E402
from src.data import load_all, public_cases  # noqa: E402
from src.sensitivity import SCENARIOS, run  # noqa: E402

TEMPLATE = ROOT / "final_ppt_example.pptx"
APP_URL = "https://fairtrial-ai-hackathongit-cyvqxeqekcqd4hjsqr7b5w.streamlit.app/"
OUT = ROOT / "pitch" / "Precedent_and_Practice.pptx"

MAROON, CORAL, LAVENDER, MINT, WHITE = "4D1808", "D77B62", "D1D5FA", "DEFED9", "FFFFFF"

# Fixed facts from the pipeline runs (see docs/ARGUMENT_BANK.md); everything else is computed.
REPORT_PAGES = 96          # entries on cfj.org/reports (sitemap and "96 results")
DISTINCT_REPORTS = 90      # 96 pages minus 6 translations/summaries (docs/TRIALWATCH_REPORTS.md)
ARGUMENT_PARAGRAPHS = 2381  # tagged paragraphs (five labels), all found on their cited page
CATEGORY_ACCURACY = "about 75–80%"  # hand-read sample of 40 arguments (earlier label set)


# ---------------------------------------------------------------- numbers --
def numbers() -> dict:
    data = load_all()
    cases = public_cases(data.cases)
    sens = run(cases)
    base = sens.iloc[0]
    readings = sens[sens["scenario"].isin([
        "Baseline", "Officials can still be victims", "R1 also covers hate-speech complaints",
        "Septia: owner complained personally"])]
    bank = past_cases()
    reports = pd.read_csv(ROOT / "data" / "trialwatch_reports.csv", keep_default_na=False)
    decisions = set()
    for line in open(EXCERPTS):
        rec = json.loads(line)
        decisions.update(rec.get("hrc_decisions", []))
    log = pd.read_csv(ROOT / "data" / "verification_log.csv", keep_default_na=False)
    impacts = pd.read_csv(ROOT / "data" / "trialwatch_impact_evidence.csv", keep_default_na=False)
    tests = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q"], cwd=ROOT,
                           capture_output=True, text=True).stdout
    n_tests = next((ln.split()[0] for ln in tests.splitlines() if "tests collected" in ln or "test collected" in ln), "?")
    return {
        "barred": int(base["barred"]), "past": int(base["counted"]),
        "low": int(readings["barred"].min()), "high": int(readings["barred"].max()),
        "no_r1": int(sens.loc[sens["scenario"] == "Without R1", "barred"].iloc[0]),
        "pdfs": len(reports), "graded": int((reports["grade"] != "").sum()),
        "core": len(bank), "countries": bank["country"].nunique(), "decisions": len(decisions),
        "confirmed": int(bank["outcome_confirmed"].sum()), "good": int(bank["good_outcome"].sum()),
        "improved": int(bank["outcome_improved"].sum()),
        "impacts": len(impacts), "signed": int((log["verified_by"] != "").sum()), "cases": len(log),
        "sensitive": int(data.cases["sensitive"].sum()), "tests": n_tests,
        "scenarios": len(SCENARIOS),
        "authors": int((reports.loc[reports["url"].isin(bank["report_url"]), "author"] != "").sum()),
    }


# ---------------------------------------------------------------- helpers --
def shape(slide, shape_id):
    return next(s for s in slide.shapes if s.shape_id == shape_id)


def set_text(sh, lines, size=None, bold=None):
    """Replace a text box's text, keeping the first run's formatting for every line."""
    tx = sh.text_frame._txBody
    sizes = [size] + [ln[1].get("size") for ln in lines if not isinstance(ln, str)]
    if any(sizes):
        body = tx.find(qn("a:bodyPr"))
        for fit in ("a:normAutofit", "a:spAutoFit"):
            for el in body.findall(qn(fit)):
                body.remove(el)
        # thin top/bottom padding so the text fits the short template boxes (Keynote shrinks overflow)
        body.set("tIns", "18288")
        body.set("bIns", "18288")
    first = tx.find(qn("a:p"))
    ppr = first.find(qn("a:pPr"))
    run = first.find(qn("a:r"))
    rpr = run.find(qn("a:rPr")) if run is not None else None
    for p in tx.findall(qn("a:p")):
        tx.remove(p)
    for line in lines:
        text, opts = (line, {}) if isinstance(line, str) else line
        p = etree.SubElement(tx, qn("a:p"))
        if ppr is not None:
            p.append(copy.deepcopy(ppr))
        r = etree.SubElement(p, qn("a:r"))
        rp = copy.deepcopy(rpr) if rpr is not None else etree.SubElement(r, qn("a:rPr"))
        if rpr is not None:
            r.append(rp)
        sz = opts.get("size", size)
        if sz:
            rp.set("sz", str(int(sz * 100)))
        b = opts.get("bold", bold)
        if b is not None:
            rp.set("b", "1" if b else "0")
        etree.SubElement(r, qn("a:t")).text = text


def remove(slide, *shape_ids):
    for el in list(slide.shapes._spTree.iter()):
        if el.tag.endswith("}cNvPr") and el.get("id") and int(el.get("id")) in shape_ids:
            node = el.getparent().getparent()
            node.getparent().remove(node)


def box(slide, x, y, w, h, text, fill=None, color=MAROON, size=11, bold=False, align=PP_ALIGN.LEFT, name="box"):
    shp = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    shp.name = name
    shp.shadow.inherit = False
    if fill:
        shp.fill.solid()
        shp.fill.fore_color.rgb = RGBColor.from_string(fill)
    else:
        shp.fill.background()
    shp.line.fill.background()
    tf = shp.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.08)
    lines = text if isinstance(text, list) else [text]
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        r = p.add_run()
        r.text = line
        r.font.size = Pt(size)
        r.font.bold = bold if i == 0 else False
        r.font.color.rgb = RGBColor.from_string(color)
    return shp


def arrow(slide, x1, y1, x2, y2):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    c.line.color.rgb = RGBColor.from_string(CORAL)
    c.line.width = Pt(1.5)
    ln = c.line._get_or_add_ln()
    etree.SubElement(ln, qn("a:tailEnd"), type="triangle")


def notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


# ------------------------------------------------------------------ build --
def build(n: dict):
    prs = Presentation(TEMPLATE)
    S = {i + 1: s for i, s in enumerate(prs.slides)}

    # 1 · Title
    set_text(shape(S[1], 570), ["PRECEDENT &", "PRACTICE",
                                ("A human rights advocacy tracker built on TrialWatch's fairness reports", {"size": 16})])
    set_text(shape(S[1], 573), ["TRACK 3 · ADVOCACY & IMPACT", "Shreya · Valentina · Ungu · Layla · Yuki"])
    notes(S[1], "TrialWatch has graded dozens of trials of journalists and critics. We turn those reports into "
                "arguments, precedents and sourced UN submissions for the next person prosecuted for speech.")

    # 2 · Agenda (template wording already fits)
    notes(S[2], "Problem, solution, how the service works, team, then the live demo.")

    # 3 · Challenges
    set_text(shape(S[3], 617), ["TrialWatch's human rights analysis is buried in PDFs, advocacy starts from a "
                                 "blank page, and reforms go unmeasured."])
    set_text(shape(S[3], 622), size=13, bold=True, lines=[f"{DISTINCT_REPORTS} reports, not searchable"])
    set_text(shape(S[3], 625), size=12, lines=[f"TrialWatch has {n['graded']} graded reports, but a lawyer can't find how a "
                                 "similar case was argued, which UN decisions applied, or what followed."])
    set_text(shape(S[3], 623), size=13, bold=True, lines=["Letters written from scratch"])
    set_text(shape(S[3], 620), size=12, lines=["Facts sit in court records, NGO reports and news in several languages; "
                                 "each UN submission is written by hand."])
    set_text(shape(S[3], 624), size=13, bold=True, lines=["Reforms nobody measures"])
    set_text(shape(S[3], 621), size=12, lines=["Indonesia revised its speech law (2024–25) and police pledged to comply; "
                                 "no one tracks whether prosecutions stop."])
    notes(S[3], "Three gaps: reforms nobody measures, TrialWatch's own reports aren't searchable by argument, "
                "and advocacy letters start from a blank page.")

    # 4 · Solution
    set_text(shape(S[4], 642), ["ARGUMENT BANK"])
    set_text(shape(S[4], 641), [f"{n['core']} TrialWatch reports on trials in {n['countries']} countries. For any case: the closest "
                                 "trials, good outcomes first, and their arguments on legality, vagueness, broadness, "
                                 "necessity and proportionality, with author and page."])
    set_text(shape(S[4], 644), ["SOURCED UN LETTER"])
    set_text(shape(S[4], 643), ["A Special Rapporteur submission where every sentence cites its source, quotes "
                                 "are checked word for word, and a lawyer approves."])
    set_text(shape(S[4], 646), ["REFORM STRESS TEST"])
    set_text(shape(S[4], 645), [f"Where a law just changed: {n['barred']} of {n['past']} past Indonesian cases would "
                                 f"likely be barred today ({n['low']}–{n['high']} across legal readings)."])
    notes(S[4], "One answer to each challenge: measure the reform, search what worked, draft the advocacy.")

    # 5 · Service
    s5a, s5b = shape(S[5], 672), shape(S[5], 671)
    s5a.top, s5a.height = Inches(1.55), Inches(1.2)
    s5b.top, s5b.height = Inches(2.95), Inches(1.5)
    set_text(s5a, ["One tool that follows TrialWatch's own process: Monitoring → Evaluation → Advocacy."], size=16, bold=True)
    set_text(s5b, size=12, lines=[f"Built from all {REPORT_PAGES} report listings on cfj.org · a simple web app · "
                                 "AI only where it helps, and always checked"])
    notes(S[5], "Built on TrialWatch's own reports and grading, in TrialWatch's own process.")

    # 16 · Human rights impact (reuses the example's service layout)
    set_text(shape(S[16], 898), ["HUMAN RIGHTS IMPACT"])
    s16a = shape(S[16], 902)
    s16a.top, s16a.height = Inches(1.5), Inches(1.6)
    set_text(s16a, size=13, lines=["Behind each row is a person. Septia Dwi Pertiwi was detained 5+ months before a "
                                  "court found her posts true. Fatia & Haris spent about 3 years under prosecution "
                                  "for discussing a human rights report."])
    s16 = shape(S[16], 901)
    s16.top, s16.height = Inches(3.3), Inches(1.9)
    set_text(s16, size=12, lines=[f"{n['good']} of the {n['core']} reported cases had a good outcome after TrialWatch's work: "
                   "acquittal, dropped charges, overturned conviction, release, or a UN finding of arbitrary "
                   f"detention. {n['improved']} convictions were later overturned (e.g. Bao Choy, Stella Nyanzi); a "
                   "verified update log keeps this current. We show what followed, never what caused it."])
    notes(S[16], "The tool lets TrialWatch spot a case the reform should have stopped on the day the complaint is "
                 "filed, before months of detention add up.")

    # 6 · How it works
    set_text(shape(S[6], 685), ["1 · Find what worked before"])
    set_text(shape(S[6], 684), ["Pick a case or describe a new one; matches say why",
                                "Arguments grouped by the five labels, with author and page",
                                "Good outcomes first, each confirmed with a source"])
    set_text(shape(S[6], 687), ["2 · Check the reform (where a law changed)"])
    set_text(shape(S[6], 686), ["Rules R1–R4 run as transparent code, no AI",
                                f"Sensitivity analysis: {n['scenarios']} legal readings, {n['low']}–{n['high']} of {n['past']}",
                                "Paste a news story: Gemini suggests inputs with checked quotes"])
    set_text(shape(S[6], 689), ["3 · Draft the advocacy"])
    set_text(shape(S[6], 688), ["Letter built only from numbered sources",
                                "Code rejects uncited sentences and invented quotes",
                                "A second check flags weak sentences; a named lawyer approves"])
    notes(S[6], "Walk the three steps on Fatia & Haris in the demo.")

    # 7 · Pipeline diagram
    set_text(shape(S[7], 701), ["SERVICE PIPELINE"])
    steps = [
        ("TrialWatch reports", f"{REPORT_PAGES} cfj.org listings, {n['pdfs']} PDFs"),
        ("Parse, no AI", f"{n['graded']} grades · {n['authors']} authors · {ARGUMENT_PARAGRAPHS:,} arguments · "
                         f"{n['decisions']} UN decisions"),
        ("People confirm", f"{n['confirmed']}/{n['core']} outcomes · {n['impacts']} impact sentences"),
        ("Match current case", "stress test + closest past trials, with reasons"),
        ("Sourced UN letter", "citation check · support check · lawyer approves"),
    ]
    w, gap, y = 1.62, 0.3, 1.9
    for i, (head, body) in enumerate(steps):
        x = 0.25 + i * (w + gap)
        box(S[7], x, y, w, 1.5, [head, body], fill=MAROON if i in (0, 4) else LAVENDER,
            color=WHITE if i in (0, 4) else MAROON, size=10.5, bold=True, name=f"step{i + 1}")
        if i < len(steps) - 1:
            arrow(S[7], x + w + 0.03, y + 0.75, x + w + gap - 0.03, y + 0.75)
    box(S[7], 0.25, 3.85, 9.4, 0.9,
        ["AI is used in two places only: suggesting case facts from a news story, and drafting the letter.",
         "Both are checked by code against the sources, then approved by a person."],
        fill=MINT, size=11, bold=True, name="ai_note")
    notes(S[7], "Everything left of the letter is deterministic and tested. People confirm outcomes and impacts.")

    # 8 · Why TrialWatch lawyers use it (persona slide; stock portrait and usage bars removed)
    remove(S[8], 715, 730, 728, 732, 734, 737, 740, 743, 746, 749)
    box(S[8], 0.15, 1.42, 2.77, 1.40, ["TrialWatch", "legal monitor"], fill=LAVENDER, size=16, bold=True,
        align=PP_ALIGN.CENTER, name="persona")
    s8t = shape(S[8], 718)
    s8t.width = Inches(8.2)
    set_text(s8t, ["WHY TRIALWATCH LAWYERS USE IT"])
    set_text(shape(S[8], 720), ["Our user (illustrative)"])
    set_text(shape(S[8], 733), ["Reviews new speech prosecutions and drafts UN submissions under time pressure."])
    set_text(shape(S[8], 719), ["Goal: “Show me how we argued a case like this, what happened, "
                                 "and give me a draft I can check.”"])
    set_text(shape(S[8], 724), ["Needs"])
    set_text(shape(S[8], 723), ["Find precedent fast, cite TrialWatch's own findings, act the day a complaint is filed."])
    set_text(shape(S[8], 721), ["Pain points"])
    set_text(shape(S[8], 722), [f"{DISTINCT_REPORTS} reports to read, sources in several languages, letters from scratch."])
    set_text(shape(S[8], 726), ["How we help"])
    set_text(shape(S[8], 725), ["Minutes, not a day: closest cases, arguments with page links, a sourced draft to approve."])
    set_text(shape(S[8], 729), size=12, bold=True, lines=["EASY · web app, no install"])
    set_text(shape(S[8], 727), size=12, bold=True, lines=["CHECKABLE · every claim links to its page"])
    set_text(shape(S[8], 731), size=12, bold=True, lines=["SPECIFIC · built from TrialWatch's own reports"])
    notes(S[8], "The user is illustrative, not a real person.")

    # 14 · Responsible AI (reuses the example's challenges layout)
    set_text(shape(S[14], 846), ["RESPONSIBLE AI"])
    set_text(shape(S[14], 852), size=13, bold=True, lines=["No AI where rules will do"])
    set_text(shape(S[14], 855), size=12, lines=["Stress test, parsing, grades and matching are plain, tested code. "
                                  "AI only suggests inputs and drafts letters."])
    set_text(shape(S[14], 853), size=13, bold=True, lines=["Every claim has a source"])
    set_text(shape(S[14], 850), size=12, lines=["Quotes checked word for word; uncited sentences rejected; each argument "
                                             "credited to its report's author; a person approves."])
    set_text(shape(S[14], 854), size=13, bold=True, lines=["Honest and safe"])
    set_text(shape(S[14], 851), size=12, lines=[f"No predictions: “followed”, never “caused”. {n['sensitive']} at-risk people hidden "
                                  "and never sent to AI. Only cited excerpts published, © CFJ."])
    notes(S[14], "Responsible AI is 20% of judging: deterministic core, sources everywhere, human approval.")

    # 17 · Validation (reuses the example's how-it-works layout)
    set_text(shape(S[17], 913), ["VALIDATION"])
    set_text(shape(S[17], 915), ["Sources check out"])
    set_text(shape(S[17], 914), [f"{ARGUMENT_PARAGRAPHS:,} / {ARGUMENT_PARAGRAPHS:,} arguments on the page they cite",
                                 f"{n['impacts']} / {n['impacts']} impact sentences on the page they cite",
                                 f"Authors for {n['authors']} / {n['core']} reports, each with its source sentence"])
    set_text(shape(S[17], 917), ["People confirmed the data"])
    set_text(shape(S[17], 916), [f"{n['confirmed']} / {n['core']} TrialWatch outcomes confirmed with a source",
                                 f"{n['signed']} of {n['cases']} Indonesian cases signed off by a teammate"])
    set_text(shape(S[17], 919), ["We know our limits"])
    set_text(shape(S[17], 918), [f"Headline {n['barred']} of {n['past']}; {n['low']}–{n['high']} across legal readings",
                                 f"Argument categories {CATEGORY_ACCURACY} right in a hand-read sample",
                                 f"{n['tests']} automated tests on every change"])
    notes(S[17], "Every number on these slides is recomputed from the data by scripts/build_slides.py.")

    # 9 · Next steps
    set_text(shape(S[9], 777), ["NEXT STEPS"])
    for sid, text in [(774, "Today"), (775, "With TrialWatch"), (776, "Next reform")]:
        set_text(shape(S[9], sid), [text])
    set_text(shape(S[9], 768), ["DEMO & HANDOVER"])
    set_text(shape(S[9], 771), ["Live app, open-source repo and written guide. Every number here recomputed from the data."])
    set_text(shape(S[9], 769), ["LAWYER REVIEW"])
    set_text(shape(S[9], 772), ["Confirm rules R1–R4 and the argument categories with TrialWatch lawyers; "
                                 "add the 73-case Indonesia dataset."])
    set_text(shape(S[9], 770), ["SCALE"])
    set_text(shape(S[9], 773), ["Swap the rules file for the next country's reform; add a live news intake "
                                 "that feeds a review queue."])
    notes(S[9], "The tool is ready to hand over; the next step is lawyer review.")

    # 10 · Team (stock portraits removed; five members)
    remove(S[10], 782, 787, 792, 793, 795, 805)
    team = [
        (0.15, "Shreya", "Stress test & Argument Bank", "Rule engine, sensitivity analysis, Argument Bank, UN letter"),
        (2.92, "Valentina", "App & case data", "Repository, case tracker page, case verification"),
        (5.70, "Ungu", "Case research & impacts", "Indonesian case verification, impact categories"),
        (8.48, "Layla", "Data lead & pitch", "Meila & Asrul cases, sensitive-case review, slides"),
    ]
    slots = [(797, 798), (801, 802), (799, 800), (803, 804)]
    for (x, name, role, bio), (name_id, bio_id) in zip(team, slots):
        box(S[10], x, 1.42, 1.38, 1.40, name[0], fill=LAVENDER, size=40, bold=True, align=PP_ALIGN.CENTER,
            name=f"initial_{name}")
        name_box = shape(S[10], name_id)
        name_box.height = Inches(0.6)
        set_text(name_box, [(name, {"bold": True, "size": 12}), (role, {"size": 9})])
        set_text(shape(S[10], bio_id), [bio])
    box(S[10], 4.31, 1.42, 1.38, 1.40, "Y", fill=MINT, size=40, bold=True, align=PP_ALIGN.CENTER, name="initial_Yuki")
    yk = box(S[10], 4.31, 2.84, 1.38, 0.6, ["Yuki", "Outcome checks"], size=12, bold=True, name="name_Yuki")
    yk.text_frame.paragraphs[1].runs[0].font.size = Pt(9)
    box(S[10], 4.31, 3.46, 1.38, 1.6, f"Confirmed all {n['core']} TrialWatch outcomes, each with a source",
        size=9, name="bio_Yuki")
    notes(S[10], "Five data science students; legal claims come from cited sources, not our own judgment.")

    # 11 · Demo
    set_text(shape(S[11], 811), ["Live Demo"])
    set_text(shape(S[11], 812), ["Questions and feedback welcome, especially from TrialWatch's lawyers: "
                                  "are our rules and argument categories right?"])
    set_text(shape(S[11], 813), ["LIVE APP", APP_URL.removeprefix("https://").rstrip("/"),
                                  "OPEN SOURCE", "github.com/valentinasilva8/fairtrial-ai-hackathon",
                                  "Code MIT · report excerpts © Clooney Foundation for Justice",
                                  "Independent project, not endorsed by CFJ, TrialWatch or Columbia Law School"])
    notes(S[11], "Demo: Home → Stress Test (Fatia & Haris) → Argument Bank → UN Letter. Start from the Home link.")

    # order and drop the rest of the example deck
    order = [1, 2, 3, 4, 5, 16, 6, 7, 8, 14, 17, 9, 10, 11]
    lst = prs.slides._sldIdLst
    ids = list(lst)
    for i, el in enumerate(ids, 1):
        if i not in order:
            prs.part.drop_rel(el.get(qn("r:id")))
        lst.remove(el)
    for i in order:
        lst.append(ids[i - 1])

    OUT.parent.mkdir(exist_ok=True)
    prs.save(OUT)
    return OUT


if __name__ == "__main__":
    nums = numbers()
    print(nums)
    print("wrote", build(nums))
