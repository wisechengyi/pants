# coding=utf-8
# Copyright 2015 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (absolute_import, division, generators, nested_scopes, print_function,
                        unicode_literals, with_statement)

from pants.goal.task_registrar import TaskRegistrar as task

from pants.contrib.dummy_options.tasks.dummy_options import DummyOptionsTask


#
# def build_file_aliases():
#   return BuildFileAliases(
#     targets={
#       'spindle_thrift_library': SpindleThriftLibrary,
#     }
#   )
#

def register_goals():
  task(name='dummy-options', action=DummyOptionsTask).install()
