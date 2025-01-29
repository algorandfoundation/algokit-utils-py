from algokit_utils import (
    replace_template_variables,
)
from algokit_utils._legacy_v2.deploy import strip_comments
from legacy_v2_tests.conftest import check_output_stability


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
test "TMPL_STR" // not replaced
test "TMPL_STRING" // not replaced
test TMPL_STRING // not replaced
test TMPL_STRI // not replaced
test TMPL_STR TMPL_INT TMPL_INT TMPL_STR // TMPL_STR TMPL_INT TMPL_INT TMPL_STR
test TMPL_INT TMPL_STR TMPL_STRING "TMPL_INT TMPL_STR TMPL_STRING" //TMPL_INT TMPL_STR TMPL_STRING
test TMPL_INT TMPL_INT TMPL_STRING TMPL_STRING TMPL_STRING TMPL_INT TMPL_STRING //keep
TMPL_STR TMPL_STR TMPL_STR
TMPL_STRING
test NOTTMPL_STR // not replaced
NOTTMPL_STR // not replaced
TMPL_STR // replaced
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
pushbytes base64(//8=)
pushbytes b64(//8=)

pushbytes base64(//8=)  // pushbytes base64(//8=)
pushbytes b64(//8=)     // pushbytes b64(//8=)
pushbytes "base64(//8=)"  // pushbytes "base64(//8=)"
pushbytes "b64(//8=)"     // pushbytes "b64(//8=)"

pushbytes base64 //8=
pushbytes b64 //8=

pushbytes base64 //8=  // pushbytes base64 //8=
pushbytes b64 //8=     // pushbytes b64 //8=
pushbytes "base64 //8="  // pushbytes "base64 //8="
pushbytes "b64 //8="     // pushbytes "b64 //8="

"""
    result = strip_comments(program)
    check_output_stability(result)
