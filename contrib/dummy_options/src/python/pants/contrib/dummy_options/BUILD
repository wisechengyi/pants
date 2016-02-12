# Copyright 2015 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

contrib_plugin(
  name='plugin',
  dependencies=[
    'src/python/pants/goal:task_registrar',
    'contrib/dummy_options/src/python/pants/contrib/dummy_options/tasks',
  ],
  distribution_name='pantsbuild.pants.contrib.dummy_options',
  build_file_aliases=True,
  register_goals=True,
  global_subsystems=True,
)
