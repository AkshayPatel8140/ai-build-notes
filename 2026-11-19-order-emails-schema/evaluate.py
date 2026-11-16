import csv
import json
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError

HERE = Path(__file__).parent


class LineItem(BaseModel):
    sku: str = Field(min_length=1)
    quantity: int = Field(gt=0)
    unit_price: float = Field(ge=0)


class Estimate(BaseModel):
    customer_email: str
    items: list[LineItem] = Field(min_length=1)


def strip_fences(text):
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else ""
        text = text.rsplit("```", 1)[0]
    return text.strip()


def is_correct(estimate, expected, prices):
    if expected == "needs_person":
        return False
    got = sorted((i.sku, i.quantity) for i in estimate.items)
    want = sorted((e["sku"], e["quantity"]) for e in expected)
    if got != want:
        return False
    return all(abs(i.unit_price - prices[i.sku]) < 0.001 for i in estimate.items)


def main():
    with open(HERE / "catalog.csv") as f:
        prices = {r["sku"]: float(r["price"]) for r in csv.DictReader(f)}
    orders = {o["id"]: o for o in json.loads((HERE / "orders.json").read_text())}
    outputs = [json.loads(line) for line in (HERE / "outputs.jsonl").read_text().splitlines()]

    counts = {"right_passed": 0, "right_blocked": 0, "wrong_blocked": 0, "wrong_passed": 0}
    rows = []
    for out in outputs:
        order = orders[out["id"]]
        try:
            estimate = Estimate.model_validate_json(strip_fences(out["output"]))
            blocked, reason = False, ""
            right = is_correct(estimate, order["expected"], prices)
        except ValidationError as err:
            blocked, reason = True, err.errors()[0]["type"]
            right = False

        if right:
            key = "right_blocked" if blocked else "right_passed"
        else:
            key = "wrong_blocked" if blocked else "wrong_passed"
        counts[key] += 1
        rows.append((out["id"], order["expected"] == "needs_person", key, reason))

    lines = ["| order | should go to a person | result | schema error |", "| --- | --- | --- | --- |"]
    for oid, person, key, reason in rows:
        lines.append(f"| {oid} | {'yes' if person else 'no'} | {key} | {reason} |")
    wrong = counts["wrong_blocked"] + counts["wrong_passed"]
    lines += [
        "",
        f"Orders: {len(rows)}",
        f"Correct estimates: {counts['right_passed'] + counts['right_blocked']}",
        f"Wrong estimates: {wrong}",
        f"Wrong ones the schema blocked: {counts['wrong_blocked']}",
        f"Wrong ones that passed the schema: {counts['wrong_passed']}",
        f"Correct ones the schema blocked: {counts['right_blocked']}",
    ]
    (HERE / "results.md").write_text("\n".join(lines) + "\n")

    print(f"{'order':<7}{'person?':<9}{'result':<15}schema error")
    for oid, person, key, reason in rows:
        print(f"{oid:<7}{'yes' if person else 'no':<9}{key:<15}{reason}")
    print()
    print("\n".join(lines[-6:]))


if __name__ == "__main__":
    main()
