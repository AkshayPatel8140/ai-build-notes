from pydantic import BaseModel, Field, ValidationError


class LineItem(BaseModel):
    sku: str = Field(min_length=1)
    quantity: int = Field(gt=0)
    unit_price: float = Field(ge=0)


class Estimate(BaseModel):
    customer_email: str
    items: list[LineItem] = Field(min_length=1)


def create_estimate(estimate: Estimate) -> dict:
    # Replace with your real API call.
    return {"status": "created", "items": len(estimate.items)}


def run_tool(agent_output: str) -> dict:
    try:
        estimate = Estimate.model_validate_json(agent_output)
    except ValidationError as err:
        # Don't call the tool. Send the errors back to the model or to a person.
        return {"status": "blocked", "errors": [e["msg"] for e in err.errors()]}
    return create_estimate(estimate)


if __name__ == "__main__":
    good = '{"customer_email": "buyer@example.com", "items": [{"sku": "TWL-100", "quantity": 12, "unit_price": 4.5}]}'
    bad = '{"customer_email": "buyer@example.com", "items": [{"sku": "TWL-100", "quantity": "a dozen", "unit_price": -4.5}]}'

    print(run_tool(good))
    print(run_tool(bad))
