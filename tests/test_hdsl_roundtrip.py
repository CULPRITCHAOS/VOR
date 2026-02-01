"""H-DSL Round-trip Proofs."""
import pytest
from neuralogix.h_surface.parser import HParser
from neuralogix.h_surface.printer import HPrinter
from neuralogix.core.ir.graph import TypedGraph

@pytest.mark.parametrize("test_input", [
    "let n1 = 5",
    "let alice: Person = {'name': 'Alice'}",
    "let alice: Person = {'name': 'Alice'}\nlet bob: Person = {'name': 'Bob'}\nalice parent_of bob",
    "let n1 = 3\nlet n2 = 5\nn3 = add(n1, n2)",
    "let x = 1\nlet y = 2\nx add y -> z",
    "let x = 1\nlet y = 2\nlet z = 3\nx add y -> xy\nxy add z -> result",
    "# Comment line\nlet x = 10",
    "let x = 5",
    "let x = 1\nlet y = 2",
    "let n1: Number = 1.5",
    "let alice: Person = {'name': 'Alice'}\nbob = parent_of(alice)"
])
def test_hdsl_roundtrip(test_input):
    parser = HParser()
    printer = HPrinter()
    
    # 1. First parse
    g1 = parser.parse(test_input)
    
    # 2. Pretty print
    dsl_printed = printer.print_graph(g1)
    
    # 3. Second parse
    g2 = parser.parse(dsl_printed)
    
    # 4. Proof: parse(print(parse(x))) == parse(x)
    assert g1 == g2, f"Round-trip failed for: {test_input}\nPrinted:\n{dsl_printed}\nG1 Hash: {g1.state_hash()}\nG2 Hash: {g2.state_hash()}"

def test_roundtrip_stability():
    """Verify print(parse(print(parse(x)))) == print(parse(x))."""
    dsl = "let x = 1\nlet y = 2\nx add y -> z"
    parser = HParser()
    printer = HPrinter()
    
    g1 = parser.parse(dsl)
    dsl1 = printer.print_graph(g1)
    
    g2 = parser.parse(dsl1)
    dsl2 = printer.print_graph(g2)
    
    assert dsl1 == dsl2, "DSL output is not stable"
