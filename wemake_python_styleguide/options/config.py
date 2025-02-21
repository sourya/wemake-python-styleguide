# -*- coding: utf-8 -*-

from typing import ClassVar, Mapping, Optional, Sequence, Union

import attr
from flake8.options.manager import OptionManager
from typing_extensions import final

from wemake_python_styleguide.options import defaults

#: Immutable config values passed from `flake8`.
ConfigValues = Mapping[str, Union[str, int, bool]]


@final
@attr.dataclass(frozen=True, slots=True)
class _Option(object):
    """Represents ``flake8`` option object."""

    long_option_name: str
    default: int  # noqa: E704
    help: str
    type: Optional[str] = 'int'  # noqa: A003
    parse_from_config: bool = True
    action: str = 'store'

    def __attrs_post_init__(self):
        """Is called after regular init is done."""
        object.__setattr__(  # noqa: WPS609
            self, 'help', self.help + ' Defaults to: %default',
        )


@final
class Configuration(object):
    """
    Provides configuration options for our plugin.

    We do not like our linter to be configurable.
    Since people may take the wrong path or make wrong decisions.
    We try to make all defaults as reasonable as possible.

    However, you can currently adjust some complexity options. Why?
    Because we are not quite sure about the ideal values yet. We are still
    researching them, and providing a way for developers to help us out is
    a good thing at the moment.

    Options for general checks:

    - ``min-name-length`` - minimum number of chars to define a valid
      variable and module name, defaults to
      :str:`wemake_python_styleguide.options.defaults.MIN_NAME_LENGTH`
    - ``max-name-length`` - maximum number of chars to define a valid
      variable and module name, defaults to
      :str:`wemake_python_styleguide.options.defaults.MAX_NAME_LENGTH`
    - ``i-control-code`` - whether you control ones who use your code,
      more rules are enforced when you do control it, defaults to
      :str:`wemake_python_styleguide.options.defaults.I_CONTROL_CODE`

    Options for complexity related checks:

    - ``max-returns`` - maximum allowed number of ``return``
      statements in one function, defaults to
      :str:`wemake_python_styleguide.options.defaults.MAX_RETURNS`
    - ``max-local-variables`` - maximum allowed number of local
      variables in one function, defaults to
      :str:`wemake_python_styleguide.options.defaults.MAX_LOCAL_VARIABLES`
    - ``max-expressions`` - maximum allowed number of expressions
      in one function, defaults to
      :str:`wemake_python_styleguide.options.defaults.MAX_EXPRESSIONS`
    - ``max-arguments`` - maximum allowed number of arguments in one function,
      defaults to
      :str:`wemake_python_styleguide.options.defaults.MAX_ARGUMENTS`
    - ``max-module-members`` - maximum number of classes and functions
      in a single module, defaults to
      :str:`wemake_python_styleguide.options.defaults.MAX_MODULE_MEMBERS`
    - ``max-methods`` - maximum number of methods in a single class,
      defaults to
      :str:`wemake_python_styleguide.options.defaults.MAX_METHODS`
    - ``max-line-complexity`` - maximum line complexity measured in number of
      ``ast`` nodes per line, defaults to
      :str:`wemake_python_styleguide.options.defaults.MAX_LINE_COMPLEXITY`
    - ``max-jones-score`` - maximum Jones score for a module, which is equal
      to the median of all lines complexity sum, defaults to
      :str:`wemake_python_styleguide.options.defaults.MAX_JONES_SCORE`
    - ``max-imports`` - maximum number of imports in a single module,
      defaults to
      :str:`wemake_python_styleguide.options.defaults.MAX_IMPORTS`
    - ``max-imported-names`` - maximum number of imported names
      in a single module, defaults to
      :str:`wemake_python_styleguide.options.defaults.MAX_IMPORTED_NAMES`
    - ``max-base-classes`` - maximum number of parent classes inside a class
      definition, defaults to
      :str:`wemake_python_styleguide.options.defaults.MAX_BASE_CLASSES`
    - ``max-decorators`` - maximum number of decorators for single function
      or class definition, defaults to
      :str:`wemake_python_styleguide.options.defaults.MAX_DECORATORS`
    - ``max-string-usages`` - maximum number of repeated string constants
      in your modules, defaults to
      :str:`wemake_python_styleguide.options.defaults.MAX_DECORATORS`
    - ``max-awaits`` - maximum allowed number of ``await``
      expressions in one function, defaults to
      :str:`wemake_python_styleguide.options.defaults.MAX_AWAITS`
    - ``max-try-body-length`` - maximum amount of ``try`` node body length,
      defaults to
      :str:`wemake_python_styleguide.options.defaults.MAX_TRY_BODY_LENGTH`

    All options are configurable via ``flake8`` CLI.

    Example::

        flake8 --max-returns=2 --max-arguments=4

    Or you can provide options in ``tox.ini`` or ``setup.cfg``.

    Example::

        [flake8]
        max-returns = 2
        max-arguments = 4

    We use ``setup.cfg`` as a default way to provide configuration.

    """

    options: ClassVar[Sequence[_Option]] = [
        # Complexity:

        _Option(
            '--max-returns',
            defaults.MAX_RETURNS,
            'Maximum allowed number of return statements in one function.',
        ),

        _Option(
            '--max-local-variables',
            defaults.MAX_LOCAL_VARIABLES,
            'Maximum allowed number of local variables in one function.',
        ),

        _Option(
            '--max-expressions',
            defaults.MAX_EXPRESSIONS,
            'Maximum allowed number of expressions in one function.',
        ),

        _Option(
            '--max-arguments',
            defaults.MAX_ARGUMENTS,
            'Maximum allowed number of arguments in one function.',
        ),

        _Option(
            '--max-module-members',
            defaults.MAX_MODULE_MEMBERS,
            'Maximum number of classes and functions in a single module.',
        ),

        _Option(
            '--max-methods',
            defaults.MAX_METHODS,
            'Maximum number of methods in a single class.',
        ),

        _Option(
            '--max-line-complexity',
            defaults.MAX_LINE_COMPLEXITY,
            'Maximum line complexity, measured in `ast` nodes.',
        ),

        _Option(
            '--max-jones-score',
            defaults.MAX_JONES_SCORE,
            'Maximum median module complexity, based on sum of lines.',
        ),

        _Option(
            '--max-imports',
            defaults.MAX_IMPORTS,
            'Maximum number of imports in a single module.',
        ),

        _Option(
            '--max-imported-names',
            defaults.MAX_IMPORTED_NAMES,
            'Maximum number of imported names in a single module.',
        ),

        _Option(
            '--max-base-classes',
            defaults.MAX_BASE_CLASSES,
            'Maximum number of base classes.',
        ),

        _Option(
            '--max-decorators',
            defaults.MAX_DECORATORS,
            'Maximum number of decorators.',
        ),

        _Option(
            '--max-string-usages',
            defaults.MAX_STRING_USAGES,
            'Maximum number of string constant usages.',
        ),

        _Option(
            '--max-awaits',
            defaults.MAX_AWAITS,
            'Maximum allowed number of await statements in one function.',
        ),

        _Option(
            '--max-try-body-length',
            defaults.MAX_TRY_BODY_LENGTH,
            'Maximum amount of try block node body length.',
        ),

        # General:

        _Option(
            '--min-name-length',
            defaults.MIN_NAME_LENGTH,
            'Minimum required length of variable and module names.',
        ),

        _Option(
            '--max-name-length',
            defaults.MAX_NAME_LENGTH,
            'Maximum possible length of the variable and module names.',
        ),

        _Option(
            '--i-control-code',
            defaults.I_CONTROL_CODE,
            'Whether you control ones who use your code.',
            action='store_true',
            type=None,
        ),
    ]

    def register_options(self, parser: OptionManager) -> None:
        """Registers options for our plugin."""
        for option in self.options:
            parser.add_option(**attr.asdict(option))
