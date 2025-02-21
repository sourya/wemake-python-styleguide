# -*- coding: utf-8 -*-

import ast
from collections import Counter, Hashable, defaultdict
from contextlib import suppress
from typing import (
    ClassVar,
    DefaultDict,
    Iterable,
    List,
    Mapping,
    Sequence,
    Union,
)

import astor
from typing_extensions import final

from wemake_python_styleguide import constants
from wemake_python_styleguide.compat.aliases import FunctionNodes
from wemake_python_styleguide.logic import nodes, safe_eval
from wemake_python_styleguide.logic.naming.name_nodes import extract_name
from wemake_python_styleguide.logic.operators import (
    count_unary_operator,
    get_parent_ignoring_unary,
    unwrap_starred_node,
    unwrap_unary_node,
)
from wemake_python_styleguide.types import (
    AnyFor,
    AnyNodes,
    AnyUnaryOp,
    AnyWith,
)
from wemake_python_styleguide.violations import complexity, consistency
from wemake_python_styleguide.violations.best_practices import (
    MagicNumberViolation,
    MultipleAssignmentsViolation,
    NonUniqueItemsInHashViolation,
    UnhashableTypeInHashViolation,
    WrongUnpackingViolation,
)
from wemake_python_styleguide.visitors import base, decorators


@final
class WrongStringVisitor(base.BaseNodeVisitor):
    """Restricts several string usages."""

    def __init__(self, *args, **kwargs) -> None:
        """Inits the counter for constants."""
        super().__init__(*args, **kwargs)
        self._string_constants: DefaultDict[str, int] = defaultdict(int)

    def visit_Str(self, node: ast.Str) -> None:
        """
        Restricts to over-use string constants.

        Raises:
            OverusedStringViolation

        """
        self._check_string_constant(node)
        self.generic_visit(node)

    def visit_JoinedStr(self, node: ast.JoinedStr) -> None:
        """
        Restricts to use ``f`` strings.

        Raises:
            FormattedStringViolation

        """
        self.add_violation(consistency.FormattedStringViolation(node))
        self.generic_visit(node)

    def _check_string_constant(self, node: ast.Str) -> None:
        annotations = (
            ast.arg,
            ast.AnnAssign,
        )

        parent = nodes.get_parent(node)
        if isinstance(parent, annotations) and parent.annotation == node:
            return  # it is argument or variable annotation

        if isinstance(parent, FunctionNodes) and parent.returns == node:
            return  # it is return annotation

        self._string_constants[node.s] += 1

    def _post_visit(self) -> None:
        for string, usage_count in self._string_constants.items():
            if usage_count > self.options.max_string_usages:
                self.add_violation(
                    complexity.OverusedStringViolation(text=string or "''"),
                )


@final
class MagicNumberVisitor(base.BaseNodeVisitor):
    """Checks magic numbers used in the code."""

    _allowed_parents: ClassVar[AnyNodes] = (
        ast.Assign,
        ast.AnnAssign,

        # Constructor usages:
        *FunctionNodes,
        ast.arguments,

        # Primitives:
        ast.List,
        ast.Dict,
        ast.Set,
        ast.Tuple,
    )

    def visit_Num(self, node: ast.Num) -> None:
        """
        Checks numbers not to be magic constants inside the code.

        Raises:
            MagicNumberViolation

        """
        self._check_is_magic(node)
        self.generic_visit(node)

    def _check_is_magic(self, node: ast.Num) -> None:
        parent = get_parent_ignoring_unary(node)
        if isinstance(parent, self._allowed_parents):
            return

        if node.n in constants.MAGIC_NUMBERS_WHITELIST:
            return

        if isinstance(node.n, int) and node.n <= constants.NON_MAGIC_MODULO:
            return

        self.add_violation(MagicNumberViolation(node, text=str(node.n)))


@final
class UselessOperatorsVisitor(base.BaseNodeVisitor):
    """Checks operators used in the code."""

    _limits: ClassVar[Mapping[AnyUnaryOp, int]] = {
        ast.UAdd: 0,
        ast.Invert: 1,
        ast.Not: 1,
        ast.USub: 1,
    }

    def visit_Num(self, node: ast.Num) -> None:
        """
        Checks numbers unnecessary operators inside the code.

        Raises:
            UselessOperatorsViolation

        """
        self._check_operator_count(node)
        self.generic_visit(node)

    def _check_operator_count(self, node: ast.Num) -> None:
        for node_type, limit in self._limits.items():
            if count_unary_operator(node, node_type) > limit:
                self.add_violation(
                    consistency.UselessOperatorsViolation(
                        node, text=str(node.n),
                    ),
                )


@final
@decorators.alias('visit_any_for', (
    'visit_For',
    'visit_AsyncFor',
))
@decorators.alias('visit_any_with', (
    'visit_With',
    'visit_AsyncWith',
))
class WrongAssignmentVisitor(base.BaseNodeVisitor):
    """Visits all assign nodes."""

    def visit_any_with(self, node: AnyWith) -> None:
        """
        Checks assignments inside context managers to be correct.

        Raises:
            WrongUnpackingViolation

        """
        for withitem in node.items:
            if isinstance(withitem.optional_vars, ast.Tuple):
                self._check_unpacking_targets(
                    node, withitem.optional_vars.elts,
                )
        self.generic_visit(node)

    def visit_comprehension(self, node: ast.comprehension) -> None:
        """
        Checks comprehensions for the correct assignments.

        Raises:
            WrongUnpackingViolation

        """
        if isinstance(node.target, ast.Tuple):
            self._check_unpacking_targets(node.target, node.target.elts)
        self.generic_visit(node)

    def visit_any_for(self, node: AnyFor) -> None:
        """
        Checks assignments inside ``for`` loops to be correct.

        Raises:
            WrongUnpackingViolation

        """
        if isinstance(node.target, ast.Tuple):
            self._check_unpacking_targets(node, node.target.elts)
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        """
        Checks assignments to be correct.

        Raises:
            MultipleAssignmentsViolation
            WrongUnpackingViolation

        """
        self._check_assign_targets(node)
        if isinstance(node.targets[0], ast.Tuple):
            self._check_unpacking_targets(node, node.targets[0].elts)
        self.generic_visit(node)

    def _check_assign_targets(self, node: ast.Assign) -> None:
        if len(node.targets) > 1:
            self.add_violation(MultipleAssignmentsViolation(node))

    def _check_unpacking_targets(
        self,
        node: ast.AST,
        targets: Iterable[ast.AST],
    ) -> None:
        for target in targets:
            target_name = extract_name(target)
            if target_name is None:  # it means, that non name node was used
                self.add_violation(WrongUnpackingViolation(node))


@final
class WrongCollectionVisitor(base.BaseNodeVisitor):
    """Ensures that collection definitions are correct."""

    _elements_in_sets: ClassVar[AnyNodes] = (
        ast.Str,
        ast.Bytes,
        ast.Num,
        ast.NameConstant,
        ast.Name,
    )

    _unhashable_types: ClassVar[AnyNodes] = (
        ast.List,
        ast.ListComp,
        ast.Set,
        ast.SetComp,
        ast.Dict,
        ast.DictComp,
        ast.GeneratorExp,
    )

    _elements_to_eval: ClassVar[AnyNodes] = (
        ast.Num,
        ast.Str,
        ast.Bytes,
        ast.NameConstant,
        ast.Tuple,
        ast.List,
        ast.Set,
        ast.Dict,
        # Since python3.8 `BinOp` only works for complex numbers:
        # https://github.com/python/cpython/pull/4035/files
        # https://bugs.python.org/issue31778
        ast.BinOp,
        # Only our custom `eval` function can eval names safely:
        ast.Name,
    )

    def visit_Set(self, node: ast.Set) -> None:
        """
        Ensures that set literals do not have any duplicate items.

        Raises:
            NonUniqueItemsInHashViolation
            UnhashableTypeInHashViolation

        """
        self._check_set_elements(node, node.elts)
        self._check_unhashable_elements(node, node.elts)
        self.generic_visit(node)

    def visit_Dict(self, node: ast.Dict) -> None:
        """
        Ensures that dict literals do not have any duplicate keys.

        Raises:
            NonUniqueItemsInHashViolation
            UnhashableTypeInHashViolation

        """
        self._check_set_elements(node, node.keys)
        self._check_unhashable_elements(node, node.keys)
        self.generic_visit(node)

    def _check_unhashable_elements(
        self,
        node: ast.AST,
        keys_or_elts: Sequence[ast.AST],
    ) -> None:
        for set_item in keys_or_elts:
            if isinstance(set_item, self._unhashable_types):
                self.add_violation(UnhashableTypeInHashViolation(set_item))

    def _check_set_elements(
        self,
        node: Union[ast.Set, ast.Dict],
        keys_or_elts: Sequence[ast.AST],
    ) -> None:
        elements: List[str] = []
        element_values = []

        for set_item in keys_or_elts:
            real_item = unwrap_unary_node(set_item)
            if isinstance(real_item, self._elements_in_sets):
                # Similar look:
                source = astor.to_source(set_item)
                elements.append(source.strip().strip('(').strip(')'))

            real_item = unwrap_starred_node(real_item)

            # Non-constant nodes raise ValueError,
            # unhashables raise TypeError:
            with suppress(ValueError, TypeError):
                # Similar value:
                real_item = safe_eval.literal_eval_with_names(
                    real_item,
                ) if isinstance(
                    real_item, self._elements_to_eval,
                ) else set_item
                element_values.append(real_item)
        self._report_set_elements(node, elements, element_values)

    def _report_set_elements(
        self,
        node: Union[ast.Set, ast.Dict],
        elements: List[str],
        element_values,
    ) -> None:
        for look_element, look_count in Counter(elements).items():
            if look_count > 1:
                self.add_violation(
                    NonUniqueItemsInHashViolation(node, text=look_element),
                )
                return

        value_counts: DefaultDict[Hashable, int] = defaultdict(int)
        for value_element in element_values:
            real_value = value_element if isinstance(
                # Lists, sets, and dicst are not hashable:
                value_element, Hashable,
            ) else str(value_element)

            value_counts[real_value] += 1

            if value_counts[real_value] > 1:
                self.add_violation(
                    NonUniqueItemsInHashViolation(node, text=value_element),
                )
