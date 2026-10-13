# GLOSSARY.md Format

## Structure

```md
# {Context Name}

{One or two sentences: what this context is and why it exists.}

## Language

**Order**:
{One or two sentences describing the term.}
_Avoid_: Purchase, transaction

**Invoice**:
A request for payment sent to a customer after delivery.
_Avoid_: Bill, payment request

**Customer**:
A person or organization that places orders.
_Avoid_: Client, buyer, account
```

## Rules

- **Be opinionated.** When several words exist for one concept, pick the best and list the others under `_Avoid_`. A spec that uses an `_Avoid_` word is a finding for `spec-consistency`.
- **Keep definitions tight.** One or two sentences. Define what it is, not what it does.
- **Only terms specific to this project's context.** General programming concepts (timeouts, error types, utility patterns) do not belong, however heavily the project uses them. Before adding a term, ask whether it is unique to this context.
- **Group terms under subheadings** when natural clusters emerge. A single cohesive area can stay a flat list.
- **No implementation detail.** No table names, routes or class names.

## Single and multiple contexts

**Single context (most projects):** one `GLOSSARY.md` in the vault, next to the product definition.

**Multiple contexts:** a `GLOSSARY-MAP.md` in the vault lists the contexts, where each glossary lives, and how they relate:

```md
# Glossary Map

## Contexts

- [[Ordering/GLOSSARY|Ordering]]: receives and tracks customer orders
- [[Billing/GLOSSARY|Billing]]: generates invoices and processes payments
- [[Fulfillment/GLOSSARY|Fulfillment]]: manages warehouse picking and shipping

## Relationships

- **Ordering -> Fulfillment**: Ordering emits `OrderPlaced`; Fulfillment consumes it to start picking
- **Fulfillment -> Billing**: Fulfillment emits `ShipmentDispatched`; Billing consumes it to generate invoices
- **Ordering <-> Billing**: shared types for `CustomerId` and `Money`
```

Write the links with the full path the vault resolves unambiguously.

Which structure applies is inferred:

- `GLOSSARY-MAP.md` exists: read it to find the contexts.
- Only `GLOSSARY.md` exists: single context.
- Neither exists: create `GLOSSARY.md` lazily when the first term is resolved.

With several contexts, infer which one the current topic belongs to. If unclear, ask.
