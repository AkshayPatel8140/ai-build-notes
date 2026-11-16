import csv
import json
from pathlib import Path

import anthropic

MODEL = "claude-opus-5-5"
HERE = Path(__file__).parent

SYSTEM = """You turn customer order emails into estimates for a hotel supply company.
Use only SKUs from the catalog below, with their catalog prices.
Reply with JSON only, no other text, in this shape:
{"customer_email": "...", "items": [{"sku": "...", "quantity": 0, "unit_price": 0.0}]}

Catalog (sku, name, unit, price):
"""


def build_system_prompt():
    with open(HERE / "catalog.csv") as f:
        rows = list(csv.DictReader(f))
    lines = [f"{r['sku']}, {r['name']}, {r['unit']}, {r['price']}" for r in rows]
    return SYSTEM + "\n".join(lines)


def main():
    system = build_system_prompt()
    orders = json.loads((HERE / "orders.json").read_text())
    client = anthropic.Anthropic()

    with open(HERE / "outputs.jsonl", "w") as out:
        for order in orders:
            response = client.beta.messages.create(
                model=MODEL,
                max_tokens=2000,
                system=system,
                output_config={"effort": "low"},
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
                messages=[{"role": "user", "content": f"From: {order['from']}\n\n{order['email']}"}],
            )
            text = "".join(b.text for b in response.content if b.type == "text")
            out.write(json.dumps({
                "id": order["id"],
                "model": response.model,
                "stop_reason": response.stop_reason,
                "output": text,
            }) + "\n")
            print(f"order {order['id']}: {response.stop_reason}")


if __name__ == "__main__":
    main()
