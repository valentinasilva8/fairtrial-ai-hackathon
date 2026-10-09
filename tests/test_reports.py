"""Tests for src/reports.py, using short made-up snippets (no CFJ text)."""

import pandas as pd

from src.reports import (
    body_paragraphs,
    extract_arguments,
    find_grade,
    hrc_decisions,
    is_trial_report,
    summarize_report,
    tag,
)

PARA_LEGALITY = (
    "The provision is insufficiently precise and therefore fails the legality prong, because it "
    "gives the authorities unfettered discretion to decide which speech is punished in practice."
)
PARA_PROPORTION = (
    "Even if the aim were a legitimate objective, a prison sentence is not the least intrusive "
    "means available, so the restriction fails the test of necessity and proportionality."
)


def test_grade_as_heading():
    assert find_grade("CONCLUSION & GRADE\n\n      GRADE:     D\n") == ("D", "GRADE: D")


def test_grade_in_a_sentence():
    grade, src = find_grade("The expert assigned this trial a grade of “F”: the court ignored the defense.")
    assert grade == "F"
    assert "assigned this trial a grade of" in src


def test_grade_across_line_break():
    assert find_grade("the panel assigned these trials a\ngrade of C because")[0] == "C"


def test_no_grade():
    assert find_grade("A thematic report on sedition laws.") == ("", "")


def test_grading_scale_text_is_not_a_grade():
    assert find_grade("Experts should assign a grade of A, B, C, D, or F to the trial")[0] == ""


def test_hrc_decisions_deduplicated():
    text = "See CCPR/C/64/D/574/1994, para 12. Also U.N. Doc. CCPR/C/64/D/574/1994 and CCPR/C/89/D/1348/2005."
    assert hrc_decisions(text) == ["CCPR/C/64/D/574/1994", "CCPR/C/89/D/1348/2005"]


def test_tags():
    assert "legality_vagueness" in tag(PARA_LEGALITY)
    assert {"legitimate_aim", "necessity_proportionality"} <= set(tag(PARA_PROPORTION))
    assert tag("The hearing was adjourned to a later date by the court clerk.") == []


def test_footnotes_dropped_from_paragraphs():
    page = "\n".join([PARA_LEGALITY, "", "Short line.", "", "Body text " * 20, "", "",
                      "203 Human Rights Committee, General Comment No. 34, para. 25, a long footnote line."])
    paras = body_paragraphs(page)
    assert PARA_LEGALITY in paras
    assert not any(p.startswith("203 Human Rights") for p in paras)


def test_extract_arguments_keeps_page_and_text():
    args = extract_arguments(["Intro page with nothing relevant.", PARA_LEGALITY])
    assert args == [{"page": 2, "categories": ["legality_vagueness"], "text": PARA_LEGALITY}]


def test_trial_url():
    assert is_trial_report("https://cfj.org/reports/cambodia-v-kak-sovannchhay/")
    assert not is_trial_report("https://cfj.org/reports/the-crime-of-sedition-what-comes-next/")


def test_summarize_report_row():
    row = summarize_report("https://cfj.org/reports/x-v-y/", "X v. Y",
                           ["Article 19 of the ICCPR.", PARA_LEGALITY, "GRADE: D"])
    assert row["grade"] == "D" and row["kind"] == "trial" and row["freedom_of_expression"]
    assert row["legality_vagueness"] >= 1


def test_committed_index_is_consistent():
    d = pd.read_csv("data/trialwatch_reports.csv", dtype={"grade": str})
    assert d["url"].is_unique
    graded = d[d["grade"].notna()]
    assert graded["grade"].isin(list("ABCDF")).all()
    # every grade carries the text it was read from
    assert graded["grade_source"].notna().all()
    assert graded.apply(lambda r: r["grade"] in r["grade_source"], axis=1).all()
