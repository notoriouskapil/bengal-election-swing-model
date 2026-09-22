# data/raw

One file: `bengal_elections.db`, 676 KB, SQLite.

## Where it came from

I built it in an earlier project of mine, `bengal-election-analysis`, from
Election Commission of India statistical reports for the West Bengal Legislative
Assembly elections of 2021 and 2026. The pipeline there reads the Commission's
published workbooks, cleans them, and asserts its own output against the totals
in the Commission's Highlight report before writing this file.

**That repository has no LICENSE file.** The data originates with the Election
Commission either way, but until a licence is added there, the reuse terms for
this copy are unstated. Sort that out before making this repo public.

Copied in on 22 September 2026. Treat it as read-only: nothing in `src/`
should ever write to it. Generated tables go to `data/model/`.

## What's in it

| table | rows | what |
|---|---|---|
| `constituencies` | 294 | ac_no, name, reservation, district, region |
| `results` | 5,052 | every candidate, both years, with votes and position |
| `winners` | 587 | winner and runner-up per seat per year, with margins |
| `electorate` | 588 | registered electors and votes polled per seat per year |
| `nota` | 588 | NOTA votes per seat per year |
| `seat_status` | 588 | `polled` or `no_poll` |
| `name_flags` | 8 | rows where the source name string needed handling |

The 588s are 294 seats times two years. `winners` is one short of that because
Falta (`ac_no` 144) has a `no_poll` row for 2026 and no winner.

There are also two views, `v_results` and `v_winners`, which join the fact tables
to `constituencies`.

## Things that will bite you

Carried over from the earlier write-up, because I lost time to all three:

**Join on `ac_no`, never on constituency name.** Names match 0 of 294 across the
two years. 2026 carries an `(SC)`/`(ST)` suffix, 2021 doesn't.

**Falta polled in 2021 and not in 2026.** Filter on `seat_status` or you get 294
rows where you expected 293, and one seat showing turnout falling by 87 points.

**Use `margin_pct_polled`, not `margin_pct_electors`.** Both columns exist. The
first matches the convention published figures use, and it's the one the swing
model needs.

**Turnout runs about 0.13 points under the published figure.** The Commission's
"votes polled" includes 89,773 rejected votes that the detailed results don't
itemise, so they aren't in here.

One more, for anything that touches the 2026 electorate: the register shrank from
roughly 73.2 million to 68.1 million between the two elections, which inflates
reported turnout. Whatever the swing model does with turnout, it has to deal with
that, and it isn't a small correction.
