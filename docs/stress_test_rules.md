# Reform Stress Test — rules

Source: CFJ report "Protecting Online Speech in Indonesia" (in `references/`), which summarizes the revised EIT Law (Law No. 1/2024) and Constitutional Court Decisions No. 105/PUU-XXII/2024 and 115/PUU-XXII/2024.
**Status: draft — confirm with TrialWatch mentor before demo. All outputs are "for lawyer review".**

## Inputs per case
| field | values |
|---|---|
| article | `27(3)` defamation · `28(2)` hate speech · `hoax` (Law 1/1946 Art. 14/15) · other |
| complainant_type | `individual_victim` · `public_official` · `government_body` · `company` · `group` · `representative` (lawyer/agent, not the victim) · `police` · `unknown` |
| public_interest | true if speech exposed alleged wrongdoing / matter of public concern (corruption, environment, labor abuse, human rights) |
| harm_shown | true if the record shows real, imminent harm (violence, threat), not only offence / hurt feelings |

## Rules
**R1 — Victim must be an individual (defamation, 27(3) / new 27A).**
Court held "victim" applies only to individuals, excluding corporations, government agencies, public officials (per CFJ report) and groups.
→ If article is defamation AND complainant_type in {public_official, government_body, company, group}: **LIKELY BARRED**.

**R2 — Complaint must come from the victim personally.**
→ If article is defamation AND complainant_type = representative: **LIKELY BARRED**. (Example: Dr. Richard Lee — court invalidated suspect status.)

**R3 — Hate speech (28(2)) requires real, imminent harm.**
Court: state intervention is legitimate only if the expression poses "a real and imminent danger".
→ If article is 28(2) AND harm_shown = false: **AT RISK** (likely fails the harm test).

**R4 — Public-interest defense (Article 45(7)(a) of amended law).**
→ If public_interest = true: **AT RISK** (strong defense available).

## Output
- `LIKELY BARRED` if R1 or R2 fires
- `AT RISK` if R3 or R4 fires (and not barred)
- `STILL PROSECUTABLE` otherwise
- Always return: list of rules fired, one-line reason each, source quote.

## Watch-out to show judges
The new Criminal Code (Arts. 433, 240, 218–219) can still punish criticism of officials and institutions — prosecutions may **move** from the ITE Law rather than stop. Flag cases charged under these articles as `displacement_watch`.
