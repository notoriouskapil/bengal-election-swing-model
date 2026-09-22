# Bengal Election Swing Model

Does a uniform statewide swing predict the 2026 West Bengal assembly result from
the 2021 one, and which seats does it get wrong?

**Work in progress.** Right now this is a skeleton with the source database
dropped into `data/raw/`. Nothing is modelled yet.

## Why I'm doing this

I cleaned the Election Commission's reports for both elections earlier this year
and wrote up what changed. TMC fell from 215 seats to 80, BJP rose from 77 to
207, and about 15 points of vote share moved between them. Fifteen points of
vote, 135 seats.

That write-up was descriptive. It showed the seat swing was that big because most
2021 margins were small — 197 of 294 seats sat under 15 points — but I never
tested whether you could have called the seat count from the vote swing alone.

So that's the question. Take the 2021 result, apply one statewide swing to every
constituency, recount the winners, compare against 2026. Uniform swing is the
oldest baseline in election forecasting and it is deliberately stupid: no
candidate quality, no incumbency, no turnout, nothing local. The interesting part
is the residual. Which seats does it miss, and do the misses have anything in
common?

## Rough plan

1. Build a seat-level feature table from the database, with tests that reconcile
   it back to the totals the Commission publishes.
2. Uniform swing as the baseline, then models that add seat-level features on
   top and see whether they beat it.
3. Work out which features actually move a prediction, and where the model
   breaks.
4. Monte Carlo over the swing itself, so the output is a seat distribution
   rather than one number.
5. A small Streamlit app with a swing slider.

Steps 3 to 5 assume 1 and 2 produce something worth explaining. If uniform swing
turns out to nail it, that's a finding too and the project gets shorter.

## Layout

```
data/raw/      bengal_elections.db, the input (read-only, never written to)
data/model/    feature tables generated from it
src/           features.py, models.py, simulate.py
notebooks/     04_models, 05_explain, 06_simulation
app/           streamlit_app.py
tests/         reconciliation and unit tests
figures/       plots
results/       model output; results/sims/ is gitignored, it gets large
docs/          model_card.md
```

Numbering on the notebooks starts at 04 because 01 to 03 were the cleaning and
descriptive work, and those live in the other repo.

## Running it

There is nothing to run yet. Setup, for when there is:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

`run_all.sh` will rebuild everything end to end once there is an end to end. At
the moment it prints what each step will do and exits.

## Attribution

The database under `data/raw/` came out of my earlier project,
`bengal-election-analysis`, which built it from Election Commission of India
statistical reports for the West Bengal Legislative Assembly, 2021 and 2026. The
Commission is the source for every number in it. See
[data/raw/README.md](data/raw/README.md) for the detail and for the known
problems with the data, which are worth reading before you trust a join.

Code here is mine and MIT licensed, see [LICENSE](LICENSE). The election data
isn't mine and the licence doesn't cover it.
