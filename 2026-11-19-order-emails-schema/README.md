# 20 messy order emails vs a schema check

Week 1 of a small series on checking agent output before it reaches a tool.

An agent turns hotel-supply order emails into estimates (SKU, quantity, price).
Every output goes through the same Pydantic schema check as
[2026-11-05-schema-check](../2026-11-05-schema-check). The question: of the
estimates the agent gets wrong, how many does the schema stop?

Sample data only. The catalog, customers and emails are made up.

## What's in the test set

- `catalog.csv`: 15 items with prices.
- `orders.json`: 20 order emails, each with the correct answer.
  - 14 have a clear right answer: plain orders, typos ("hnd towls"), "a dozen",
    number words, a reply thread, a changed mind, Spanish.
  - 6 should go to a person, because no estimate can be right: no quantity,
    "the usual", an item not in the catalog, two delivery addresses, a price the
    customer quotes that isn't the catalog price, and "2 cs" with no case size.

The agent prompt does not offer a "send to a person" option. That's on
purpose: this run measures what a plain extract-then-check setup does.

## Run it

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...
python extract.py    # calls the model once per email, writes outputs.jsonl
python evaluate.py   # schema check + comparison, writes results.md
```

`evaluate.py` needs no API key, so you can re-score the saved outputs.

## Results (run on 2026-11-16, claude-opus-5-5, effort low, 1 run)

Full table in `results.md`, raw model output in `outputs.jsonl`.

- All 14 clear orders came back correct and passed the schema.
- Of the 6 that should go to a person, the schema blocked 2:
  - order 6 (no quantity): the model set quantity to 0, which fails `gt=0`.
  - order 7 ("the usual"): the model returned an empty item list.
- 4 passed the schema as clean-looking estimates:
  - order 8: priced the 10 pillows and dropped the 50 beach umbrellas.
  - order 15: merged two delivery addresses into one line of 18 pillows.
  - order 17: used the catalog price (2.75) where the customer quoted $2.
  - order 19: put 2 towels as a placeholder for "2 cs" (2 cases, size unknown).
- The model wrote an extra `notes` field on orders 6, 8 and 19 saying a person
  should confirm. The schema has no `notes` field and Pydantic ignores unknown
  fields by default, so on orders 8 and 19 the warning was silently dropped
  and the estimate looked clean.
- No correct estimate was blocked.

Limits: 20 emails, one model, one run, low effort, and a prompt with no
"send to a person" option. Small numbers; read them as a direction, not a rate.

Next: add plain rules (catalog lookup, price check, one address per estimate)
and give the model a real way to flag an order for review.
