# coding=utf-8
# Copyright 2015 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (absolute_import, division, generators, nested_scopes, print_function,
                        unicode_literals, with_statement)

import os

from pants.backend.jvm.tasks.classpath_util import ClasspathUtil
from pants.java.util import safe_classpath
from pants.task.task import Task
from pants.util.dirutil import rm_rf


class RuntimeClasspathPublisher(Task):
  """Create stable symlinks for runtime classpath entries for JVM targets."""

  @classmethod
  def register_options(cls, register):
    super(Task, cls).register_options(register)
    register('--synthetic-only', type=bool, default=False,
             help='Only export classpath in a synthetic jar.')

  @classmethod
  def prepare(cls, options, round_manager):
    round_manager.require_data('runtime_classpath')

  @property
  def _output_folder(self):
    return self.options_scope.replace('.', os.sep)

  def execute(self):
    basedir = os.path.join(self.get_options().pants_distdir, self._output_folder)
    runtime_classpath = self.context.products.get_data('runtime_classpath')
    targets = self.context.targets()
    if self.get_options().synthetic_only:
      synthetic_jar_path = os.path.join(basedir, "current.jar")
      classpath = ClasspathUtil.classpath(targets, runtime_classpath)
      synthetic_jar = safe_classpath(classpath, basedir)
      rm_rf(synthetic_jar_path)
      os.rename(synthetic_jar[0], synthetic_jar_path)
    else:
      ClasspathUtil.create_canonical_classpath(runtime_classpath,
                                               targets,
                                               basedir,
                                               save_classpath_file=True)
