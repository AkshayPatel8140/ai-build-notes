# Schema check before a tool call

The model returns JSON. Before it reaches a tool (an accounting API, a database, an email), it has to pass a Pydantic schema. If it fails, the tool never runs and the errors go back to the model or to a person.

A schema checks the shape of the data, not whether it's right. A valid SKU for the wrong item still passes.

## Run it

```bash
pip install -r requirements.txt
python schema_check.py
```

Output:

```
{'status': 'created', 'items': 1}
{'status': 'blocked', 'errors': ['Input should be a valid integer, unable to parse string as an integer', 'Input should be greater than or equal to 0']}
```

Sample data only.

LinkedIn post: {{link after posting}}
