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
    register('--classpath-manifest-only', type=bool, default=False,
             help='Only export classpath in a manifest jar.')

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
    if self.get_options().classpath_manifest_only:
      classpath_manifest_jar = os.path.join(basedir, "classpath_manifest.jar")
      classpath = ClasspathUtil.classpath(targets, runtime_classpath)
      # Safely create e.g. dist/export-classpath/tmp2oLDYp.jar
      temp_jar = safe_classpath(classpath, basedir)[0]
      # Clean up any old "classpath_manifest_jar",
      # and rename `temp_jar` to "classpath_manifest.jar".
      if os.path.exists(classpath_manifest_jar):
        rm_rf(classpath_manifest_jar)
      os.rename(temp_jar, classpath_manifest_jar)
    else:
      ClasspathUtil.create_canonical_classpath(runtime_classpath,
                                               targets,
                                               basedir,
                                               save_classpath_file=True)
