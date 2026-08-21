# Runnable examples

Every script here backs a docs page: docs render named regions from these
files, so the code in the docs is always real, executed code. `concepts/`
holds one script per Concepts page, with small snippets each showing one
library abstraction.

## Running

Start LocalNet (`algokit localnet start`), then from the repo root:

```bash
uv run --frozen python -m examples.concepts.algorand_client   # one example
uv run --frozen pytest tests/test_examples.py                 # all examples
uv run --frozen pytest tests/test_examples.py -k algorand     # one, via pytest
```

No env vars needed — examples use `AlgorandClient.default_localnet()`.
Always pass `--frozen` so `uv run` doesn't churn `uv.lock`.

The pytest run executes every script end-to-end and validates the snippet
markers, and runs in CI on every PR.

## Snippet markers

A region is the code between the **same** comment line appearing **exactly
twice**:

```python
# example: SEND_PAYMENT
algorand.send.payment(
    PaymentParams(sender=account_a.address, receiver=account_b.address, amount=AlgoAmount.from_algo(1))
)
# example: SEND_PAYMENT
```

- Names are `UPPER_SNAKE_CASE`, matching the `algokit-utils-ts` equivalent
  where one exists.
- Regions can't nest or overlap.
- Keep imports, setup, prints and asserts **outside** the markers — only the
  region is rendered, and it must be clean and copy-pasteable.
- `_`-prefixed files (e.g. `_helpers.py`) are shared setup, never rendered.

## Writing a new example

Copy the shape of `concepts/transactions.py`: module docstring with
prerequisites, `main()` with marked regions, asserts outside the markers,
`if __name__ == "__main__": main()`. The test harness picks it up
automatically.

## Rendering in a docs page

```mdx
import RemoteCode from "/src/components/RemoteCode.astro";

<RemoteCode
  src="https://raw.githubusercontent.com/algorandfoundation/algokit-utils-py/main/examples/concepts/algorand_client.py"
  snippet="INSTANTIATE_ALGORAND_CLIENT"
  lang="python"
/>
```
