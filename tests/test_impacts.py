"""Tests for src/impacts.py, using made-up sentences (no CFJ text)."""

from src.impacts import (
    CATEGORIES,
    FROM_ANNEX,
    has_impact,
    impact_evidence,
    names_defendant,
    quantities,
)

NAMES = ["Anna Rowe"]


def page(*paragraphs: str) -> str:
    return "\n\n".join(paragraphs)


def found(text: str, names=NAMES) -> dict:
    return impact_evidence([text], names)


def test_conviction_and_sentence():
    ev = found(page("Ms. Rowe was convicted and sentenced to two years in prison for her posts."))
    assert ev["conviction_sentence"][0]["page"] == 1


def test_detention():
    ev = found(page("Ms. Rowe was detained for three months before her trial began."))
    assert ev["pretrial_detention"]


def test_mistreatment():
    ev = found(page("Ms. Rowe was held in solitary confinement and denied medical care."))
    assert ev["mistreatment"]


def test_reputational_harm():
    ev = found(page("Ms. Rowe's reputation was damaged after state media published her name."))
    assert ev["reputational_harm"]


def test_other_restrictions():
    ev = found(page("Ms. Rowe was fined and her passport was confiscated by the court."))
    assert ev["other_restrictions"]


def test_prolonged_proceedings():
    ev = found(page("Ms. Rowe remained a suspect for years while the investigation continued."))
    assert ev["prolonged_proceedings"]


def test_numbers_are_kept_exactly_as_written():
    assert quantities("Ms. Rowe was detained for five months.") == ["five months"]
    assert quantities("She was sentenced to 2 years and fined 5 million rupiah.") == ["2 years", "5 million rupiah"]
    assert quantities("Ms. Rowe paid a fine of Rp 5,000,000 and served 18 months.") == ["18 months", "Rp 5,000,000"]
    assert quantities("It was the three-year anniversary of his death and a 30-year-old man.") == []
    assert quantities("She was held without a date.") == []


def test_a_number_not_in_the_sentence_is_never_added():
    ev = found(page("Ms. Rowe was detained before trial."))
    assert ev["pretrial_detention"][0]["quantities"] == []


def test_sentence_about_another_person_is_excluded():
    ev = found(page("Mr. Lane was convicted and sentenced to one year. Ms. Rowe attended the hearing."))
    assert not ev["conviction_sentence"]
    assert not names_defendant("Mr. Lane was convicted.", NAMES)


def test_a_shared_name_part_alone_does_not_count():
    names = ["Kong Raiya"]
    assert names_defendant("Mr. Raiya was detained.", names)
    assert names_defendant("Kong Raiya was detained.", names)
    assert not names_defendant("Kong Mas was convicted of insult.", names)


def test_sentence_with_only_a_pronoun_is_excluded():
    ev = found(page("Ms. Rowe attended every hearing. She was detained for two weeks."))
    assert not ev["pretrial_detention"]


def test_footnotes_are_skipped():
    body = "\n".join(["Ms. Rowe attended the court on the first day of the trial."] * 12)
    notes = "\n12 Ms. Rowe was convicted and sentenced to four years, see Case No. 5, para. 7.\n13 Id."
    assert not found(body + notes)["conviction_sentence"]


def test_citation_text_is_skipped():
    ev = found(page("In Smith v. State, No. 45, p. 12, Ms. Rowe was convicted of sedition."))
    assert not ev["conviction_sentence"]


def test_acquittal_is_not_a_conviction():
    ev = found(page("Ms. Rowe was found not guilty by the court."))
    assert not ev["conviction_sentence"]


def test_negated_statements_are_excluded():
    assert not found(page("Ms. Rowe was not convicted in this case."))["conviction_sentence"]
    assert not found(page("At no time before trial was Ms. Rowe detained in police custody."))["pretrial_detention"]


def test_hypotheticals_are_excluded():
    ev = found(page("If Ms. Rowe had been detained, this would violate Article 9."))
    assert not ev["pretrial_detention"]


def test_statutory_penalty_is_not_the_sentence_imposed():
    ev = found(page("Ms. Rowe was charged under a provision that provides for a prison sentence of up to five years."))
    assert not ev["conviction_sentence"]


def test_someone_elses_quoted_words_are_excluded():
    ev = found(page('Ms. Rowe told the guard, "You are torturing me," and later left the room.'))
    assert not ev["mistreatment"]


def test_honorific_does_not_cut_the_sentence():
    ev = found(page("Ms. Rowe was detained on March 3 for allegedly insulting the president."))
    assert ev["pretrial_detention"][0]["sentence"].startswith("Ms. Rowe was detained")


def test_a_footnote_number_does_not_glue_sentences_together():
    text = page("Ms. Rowe was arrested at home.44 She was later detained for six days at the central station.")
    ev = found(text)
    assert not ev["pretrial_detention"]  # second sentence has only a pronoun
    ev = found(page("The police arrived early.44 Ms. Rowe was detained for six days at the central station."))
    assert ev["pretrial_detention"][0]["sentence"].startswith("Ms. Rowe was detained")


def test_page_numbers_follow_the_pdf():
    pages = ["Nothing relevant happened here at all on this page.", "Ms. Rowe was detained for two days after the march."]
    ev = impact_evidence(pages, NAMES)
    assert ev["pretrial_detention"][0]["page"] == 2


def test_the_grading_annex_text_is_ignored():
    annex = "Grading methodology: the extent of the harm related to the charges, such as Anna Rowe being convicted and sentenced."
    assert not any(found(page(annex)).values())


def test_has_impact_and_categories():
    ev = found(page("Ms. Rowe was detained for two days."))
    flags = has_impact(ev)
    assert flags["pretrial_detention"] and not flags["mistreatment"]
    assert set(flags) == set(CATEGORIES)
    assert set(FROM_ANNEX) <= set(CATEGORIES)


def test_a_number_belongs_only_to_the_category_it_sits_next_to():
    text = page("Ms. Rowe received a suspended sentence of two years' imprisonment, with credit for time served in pre-trial detention.")
    ev = found(text)
    assert ev["conviction_sentence"][0]["quantities"] == ["two years"]
    assert ev["pretrial_detention"][0]["quantities"] == []


# --- the sheet rows, loading and the lines shown to a user ------------------

import csv

from src.impacts import (
    case_row,
    evidence_rows,
    impact_lines,
    impact_markdown,
    impacts_for,
    is_confirmed,
    load_impacts,
    page_link,
)

REP = {"url": "https://cfj.org/reports/x-v-rowe/", "title": "Country v. Anna Rowe", "grade": "D",
       "pdf_url": "https://cfj.org/x.pdf"}


def test_page_link_uses_the_pdf_page():
    assert page_link("https://cfj.org/x.pdf", 7) == "https://cfj.org/x.pdf#page=7"
    assert page_link("", 7) == ""


def test_case_row_has_yes_no_evidence_page_and_link():
    ev = found(page("Ms. Rowe was detained for five months before her trial began."))
    row = case_row(REP, NAMES, ev)
    assert row["pretrial_detention"] == "yes" and row["mistreatment"] == "no"
    assert row["pretrial_detention_quantities"] == "five months"
    assert row["pretrial_detention_page"] == 1
    assert row["pretrial_detention_source_url"] == "https://cfj.org/x.pdf#page=1"
    assert row["mistreatment_sentence"] == "" and row["mistreatment_source_url"] == ""
    assert row["verified_by"] == "" and row["notes"] == ""


def test_case_row_keeps_what_people_filled_in():
    prev = {"verified_by": "A. Checker", "notes": "page 4 confirmed"}
    row = case_row(REP, NAMES, found(page("Ms. Rowe was detained for two days.")), prev)
    assert row["verified_by"] == "A. Checker" and row["notes"] == "page 4 confirmed"


def test_case_row_with_no_evidence_is_all_no():
    row = case_row(REP, NAMES, {c: [] for c in CATEGORIES})
    assert all(row[c] == "no" for c in CATEGORIES)


def test_evidence_rows_list_every_sentence():
    ev = found(page("Ms. Rowe was detained for two days. Ms. Rowe was convicted of sedition."))
    rows = evidence_rows(REP, ev)
    assert {r["category"] for r in rows} == {"pretrial_detention", "conviction_sentence"}
    assert all(r["source_url"].startswith("https://cfj.org/x.pdf#page=") for r in rows)


def write_sheet(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def test_impact_lines_are_unconfirmed_until_verified_by_is_filled(tmp_path):
    ev = found(page("Ms. Rowe was detained for five months before her trial began."))
    sheet = tmp_path / "impacts.csv"
    write_sheet(sheet, [case_row(REP, NAMES, ev)])
    lines = impacts_for(REP["url"], load_impacts(sheet))
    assert [ln["category"] for ln in lines] == ["pretrial_detention"]
    assert lines[0]["quantities"] == ["five months"] and lines[0]["confirmed"] is False
    assert lines[0]["url"].endswith("#page=1")

    write_sheet(sheet, [case_row(REP, NAMES, ev, {"verified_by": "A. Checker"})])
    row = load_impacts(sheet)[REP["url"]]
    assert is_confirmed(row) and impact_lines(row)[0]["confirmed"] is True


def test_missing_sheet_or_report_gives_no_lines(tmp_path):
    assert load_impacts(tmp_path / "nope.csv") == {}
    assert impacts_for("https://cfj.org/reports/unknown/", {}) == []


def test_impact_markdown_marks_status_and_keeps_numbers():
    ev = found(page("Ms. Rowe was detained for five months before her trial began."))
    row = case_row(REP, NAMES, ev)
    md = "\n".join(impact_markdown(impact_lines(row)))
    assert "**Detention** (five months) · *unconfirmed*" in md and "[page 1](https://cfj.org/x.pdf#page=1)" in md
    row = case_row(REP, NAMES, ev, {"verified_by": "A. Checker"})
    assert "*confirmed*" in "\n".join(impact_markdown(impact_lines(row)))
    assert impact_markdown([]) == []

