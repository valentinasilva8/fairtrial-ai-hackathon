# Verification log

`verification_log.csv` records who checked each case and what they checked. One row per case in `cases_seed.csv`.

When you finish a check, put your initials in that column (e.g. `SS`). When the whole row is done, fill `verified_by` and `date_done`, then set `verified=true` in `cases_seed.csv`.

| column | tick when you have checked… |
|---|---|
| complainant | `complainant` and `complainant_type` against the source (drives R1/R2) |
| article | `article` (27(3), 28(2), hoax, other…) |
| outcome | `outcome` and `outcome_detail` dates and sentences |
| labels | `public_interest` and `harm_shown` (label independently; see TEAM_PLAN section 3) |
| sources | `source` has the report page number and a second-source URL where possible |
| events | 4–8 rows added to `events.csv` for this case |
| sensitive | whether `sensitive` should be true |

Leave a box blank if you couldn't confirm it, and say why in `notes`. Never invent facts to fill a box.
