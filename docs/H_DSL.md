# NeuraLogix-H DSL Reference

NeuraLogix-H is a high-level surface language for interacting with the Neuralogix Reasoning Engine. It provides a human-writable syntax for defining nodes (embeddings), relationships, and reasoning operations.

## EBNF Grammar (Simplified)

```ebnf
program      = { statement } ;
statement    = node_def | edge_def | op_assign | comment ;

node_def     = "let" identifier [ ":" type ] "=" value ;
edge_def     = identifier edge_type identifier [ "->" identifier ] ;
op_assign    = identifier "=" op_name "(" arguments ")" ;

identifier   = [a-zA-Z_][a-zA-Z0-9_]* ;
type         = "Number" | "Person" | "Relation" | "Operation" | "Boolean" ;
edge_type    = identifier ;
op_name      = identifier ;
arguments    = identifier { "," identifier } ;
value        = number | string | dict ;
comment      = "#" { any_character } ;
```

## Core Principles

1.  **Implicit Node Creation**: Operations and edges will automatically create "placeholder" nodes if the referenced IDs have not been defined via `let`.
2.  **Type Defaulting**: `let x = 5` defaults to `NodeType.NUMBER`. `let alice = {"name": "Alice"}` defaults to `NodeType.PERSON`.
3.  **Round-trip Parity**: `parse(pretty_print(parse(text)))` is guaranteed to be isomorphic to `parse(text)`.
4.  **Linting**: The `HLinter` checks for disconnected nodes, improper type usage, and unreachable reasoning chains.

## Examples

### 1. Basic Arithmetic
```h-dsl
let n1 = 10
let n2 = 20
let n3: Number = 30
sum = add(n1, n2)
# sum now holds a reference node for the addition of n1 and n2
```

### 2. Family Relations
```h-dsl
let alice: Person = {"name": "Alice", "age": 30}
let bob: Person = {"name": "Bob", "age": 5}
alice parent_of bob
```

### 3. Mixed Reasoning
```h-dsl
let budget = 1000
let cost = 1200
is_over = greater_than(cost, budget)
# is_over will trigger a boolean node
```

### 4. Direct Edge with Result
```h-dsl
n1 add n2 -> sum
```

## Verification

Compliance is verified by `tests/test_hdsl_roundtrip.py` covering:
- Comments and whitespace stability.
- Nested type literals.
- Op-shorthand vs Explicit edge definitions.
