from algokit_utils import (
    replace_template_variables,
)

from tests.conftest import check_output_stability


def test_template_substitution() -> None:
    program = """
test TMPL_INT // TMPL_INT
test TMPL_INT
no change
test TMPL_STR // TMPL_STR
TMPL_STR
TMPL_STR // TMPL_INT
TMPL_STR // foo //
TMPL_STR // bar
"""
    result = replace_template_variables(program, {"INT": 123, "STR": "ABC"})
    check_output_stability(result)
