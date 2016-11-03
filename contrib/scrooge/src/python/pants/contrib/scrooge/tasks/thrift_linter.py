# coding=utf-8
# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (absolute_import, division, generators, nested_scopes, print_function,
                        unicode_literals, with_statement)

from multiprocessing import cpu_count

from pants.backend.jvm.tasks.nailgun_task import NailgunTask
from pants.base.exceptions import TaskError
from pants.base.worker_pool import Work, WorkerPool
from pants.base.workunit import WorkUnitLabel
from pants.option.ranked_value import RankedValue

from pants.contrib.scrooge.tasks.thrift_util import calculate_compile_sources


class ThriftLintError(Exception):
  """Raised on a lint failure."""


class ThriftLinter(NailgunTask):
  """Print linter warnings for thrift files."""

  @staticmethod
  def _is_thrift(target):
    return target.is_thrift

  @classmethod
  def register_options(cls, register):
    super(ThriftLinter, cls).register_options(register)
    register('--skip', type=bool, fingerprint=True, help='Skip thrift linting.')
    register('--strict', type=bool, fingerprint=True,
             help='Fail the goal if thrift linter errors are found. Overrides the '
                  '`strict-default` option.')
    register('--strict-default', default=False, advanced=True, type=bool,
             fingerprint=True,
             help='Sets the default strictness for targets. The `strict` option overrides '
                  'this value if it is set.')
    register('--linter-args', default=[], advanced=True, type=list, fingerprint=True,
             help='Additional options passed to the linter.')
    cls.register_jvm_tool(register, 'scrooge-linter')

  @classmethod
  def product_types(cls):
    # Declare the product of this goal. Gen depends on thrift-linter.
    return ['thrift-linter']

  @property
  def cache_target_dirs(self):
    return True

  @staticmethod
  def _to_bool(value):
    # Converts boolean and string values to boolean.
    return str(value) == 'True'

  def _is_strict(self, target):
    # The strict value is read from the following, in order:
    # 1. the option --[no-]strict, but only if explicitly set.
    # 2. java_thrift_library target in BUILD file, thrift_linter_strict = False,
    # 3. options, --[no-]strict-default
    options = self.get_options()
    if options.get_rank('strict') > RankedValue.HARDCODED:
      return self._to_bool(self.get_options().strict)

    if target.thrift_linter_strict is not None:
      return self._to_bool(target.thrift_linter_strict)

    return self._to_bool(self.get_options().strict_default)

  def _lint(self, target, classpath):
    self.context.log.debug('Linting {0}'.format(target.address.spec))

    config_args = []

    config_args.extend(self.get_options().linter_args)
    if not self._is_strict(target):
      config_args.append('--ignore-errors')

    include_paths , paths = calculate_compile_sources([target], self._is_thrift)
    for p in include_paths:
      config_args.extend(['--include-path', p])

    args = config_args + list(paths)


    # If runjava returns non-zero, this marks the workunit as a
    # FAILURE, and there is no way to wrap this here.
    returncode = self.runjava(classpath=classpath,
                              main='com.twitter.scrooge.linter.Main',
                              args=args,
                              jvm_options=self.get_options().jvm_options,
                              workunit_labels=[WorkUnitLabel.COMPILER])  # to let stdout/err through.

    if returncode != 0:
      raise ThriftLintError(
        'Lint errors in target {0} for {1}.'.format(target.address.spec, paths))

  def execute(self):
    if self.get_options().skip:
      return

    thrift_targets = self.context.targets(self._is_thrift)
    with self.invalidated(thrift_targets) as invalidation_check:
      if not invalidation_check.invalid_vts:
        return

      with self.context.new_workunit('parallel-thrift-linter') as workunit:
        results = set()
        worker_pool = WorkerPool(workunit.parent,
                                 self.context.run_tracker,
                                 cpu_count())
        for vt in invalidation_check.invalid_vts:
          r = worker_pool.submit_async_work(Work(self._lint, [(vt.target, self.tool_classpath('scrooge-linter'))]))
          results.add(r)

        for r in results:
          r.wait()

        success = all(r.successful() for r in results)
        if not success:
          raise TaskError("Thrift linter failed.")