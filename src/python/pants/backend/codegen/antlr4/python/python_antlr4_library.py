# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from pants.backend.python.targets.python_target import PythonTarget


class PythonAntlr4Library(PythonTarget):
    """A Python library generated from Antlr grammar files."""

    def __init__(self, module=None, antlr_version="4.8", *args, **kwargs):
        """
    :param module: everything beneath module is relative to this module name, None if root namespace
    :param antlr_version:
    """
        if antlr_version == "4.8":
            kwargs["compatibility"] = "CPython>=3.6,<4"
        super().__init__(*args, **kwargs)

        self.module = module
        self.antlr_version = antlr_version
