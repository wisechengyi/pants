# Copyright 2020 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).
from pants.backend.codegen.antlr4.python.python_antlr4_library import PythonAntlr4Library
from pants.build_graph.build_file_aliases import BuildFileAliases
from pants.goal.task_registrar import TaskRegistrar as task


def build_file_aliases():
    return BuildFileAliases(targets={"python_antlr4_library": PythonAntlr4Library})


def register_goals():

    from pants.backend.codegen.antlr4.python.antlr_py_gen import Antlr4PyGen

    task(name="antlr4-py", action=Antlr4PyGen).install("gen")
