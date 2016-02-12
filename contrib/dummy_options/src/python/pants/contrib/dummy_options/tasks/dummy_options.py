# coding=utf-8
# Copyright 2015 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (absolute_import, division, generators, nested_scopes, print_function,
                        unicode_literals, with_statement)

import os
import re
from collections import defaultdict

from pants.backend.jvm.targets.jar_dependency import JarDependency
from pants.backend.jvm.targets.java_library import JavaLibrary
from pants.backend.jvm.targets.scala_library import ScalaLibrary
from pants.backend.jvm.tasks.nailgun_task import NailgunTask
from pants.base.build_environment import get_buildroot
from pants.base.exceptions import TaskError
from pants.build_graph.address import Address
from pants.option.custom_types import list_option
from twitter.common.dirutil import safe_mkdir


class DummyOptionsTask(NailgunTask):
  @classmethod
  def product_types(cls):
    return [
      'dummy',
    ]

  @classmethod
  def register_options(cls, register):
    super(DummyOptionsTask, cls).register_options(register)
    # register(
    #   '--jvm-options',
    #   default=[],
    #   advanced=True,
    #   type=list_option,
    #   help='Use these jvm options when running Spindle.',
    # )
    # register(
    #   '--runtime-dependency',
    #   default=['3rdparty:spindle-runtime'],
    #   advanced=True,
    #   type=list_option,
    #   help='A list of targets that all spindle codegen depends on at runtime.',
    # )
    register('--dummy-crufty-expired', deprecated_version='0.0.1',
                deprecated_hint='use a less crufty global option')
    cls.register_jvm_tool(register, 'dummy_options')


  def execute(self):
    pass
