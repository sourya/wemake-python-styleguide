# -*- coding: utf-8 -*-

from wemake_python_styleguide.violations.naming import TooShortNameViolation
from wemake_python_styleguide.visitors.ast.naming import WrongNameVisitor


def test_short_variable_name(
    assert_errors,
    assert_error_text,
    parse_ast_tree,
    naming_template,
    default_options,
    mode,
):
    """Ensures that short names are not allowed."""
    short_name = 'y'
    tree = parse_ast_tree(mode(naming_template.format(short_name)))

    visitor = WrongNameVisitor(default_options, tree=tree)
    visitor.run()

    assert_errors(visitor, [TooShortNameViolation])
    assert_error_text(visitor, short_name)


def test_naming_length_settings(
    assert_errors,
    assert_error_text,
    parse_ast_tree,
    naming_template,
    options,
    mode,
):
    """Ensures that correct names are allowed."""
    short_name = 'xy'
    tree = parse_ast_tree(mode(naming_template.format(short_name)))

    option_values = options(min_name_length=3)
    visitor = WrongNameVisitor(option_values, tree=tree)
    visitor.run()

    assert_errors(visitor, [TooShortNameViolation])
    assert_error_text(visitor, short_name)
