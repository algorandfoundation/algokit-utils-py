from algokit_utils import (
    replace_template_variables,
)
from algokit_utils.deploy import strip_comments

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


def test_comment_stripping() -> None:
    program = r"""
//comment
op arg //comment
op "arg" //comment
op "//" //comment
op "  //comment  " //comment
op "\" //" //comment
op "// \" //" //comment
op "" //comment
//
op 123
op 123 // something
op "" // more comments
op "//" //op "//"
op "//"
"""
    result = strip_comments(program)
    check_output_stability(result)
