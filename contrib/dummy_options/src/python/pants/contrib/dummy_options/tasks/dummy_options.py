# coding=utf-8
# Copyright 2015 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (absolute_import, division, generators, nested_scopes, print_function,
                        unicode_literals, with_statement)

from pants.task.task import Task


class DummyOptionsTask(Task):

  @classmethod
  def register_options(cls, register):
    super(DummyOptionsTask, cls).register_options(register)
    register('--dummy-crufty-expired', deprecated_version='0.0.1',
                deprecated_hint='blah')
    register('--dummy-crufty-deprecated-but-still-functioning', deprecated_version='999.99.9',
                deprecated_hint='blah')
