# Model card

Empty on purpose. I'm filling this in as I go rather than writing it at the end,
because the honest version of "what this model can't do" is easiest to write
while I'm still annoyed about it.

Headings are placeholders from the repo setup commit.

## What it does

One line, once there is a model.

## Intended use

Coursework and my own curiosity. It is a retrospective fit of one election to the
one before it in a single state, so it is not a forecast of anything, and a seat
projection out of it should not be read as a prediction.

## Data

`data/raw/bengal_elections.db`, built from Election Commission of India
statistical reports for the West Bengal Legislative Assembly, 2021 and 2026.
Provenance and known problems: [../data/raw/README.md](../data/raw/README.md).

## Features

TBD, phase 1.

## Baseline

Uniform statewide swing. Every model gets compared against it.

## Evaluation

TBD, phase 2. Two numbers at minimum: error on the statewide seat total, and
per-seat accuracy. The first can look good while the second is bad, if the
misses cancel out.

## Known limitations

Starting the list now, these three are already true:

- Two elections, one state. There is no held-out election to test against, so
  anything that looks like validation here is really in-sample fitting, and I
  should say so loudly wherever a number gets quoted.
- The 2026 electoral roll shrank by about 5 million names and I don't know why.
  Anything using turnout inherits that.
- No candidate-level features. Cross-year name matching in this data fans out
  badly, so incumbency is out of reach.

## Ethical notes

TBD. At least: this is about aggregate seat arithmetic, not about voters, and
nothing here supports a claim about why anyone voted the way they did.
