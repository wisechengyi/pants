# coding=utf-8
# Copyright 2015 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (absolute_import, division, generators, nested_scopes, print_function,
                        unicode_literals, with_statement)

import xml.etree.ElementTree as ET

from pants.util.contextutil import open_tar, open_zip, temporary_dir
from pants_test.backend.jvm.tasks.jvm_compile.base_compile_integration_test import BaseCompileIT


SHAPELESS_CLSFILE = 'org/pantsbuild/testproject/unicode/shapeless/ShapelessExample.class'
SHAPELESS_TARGET = 'testprojects/src/scala/org/pantsbuild/testproject/unicode/shapeless'


class ZincCompileIntegrationTest(BaseCompileIT):

  def test_scala_compile_jar(self):
    jar_suffix = 'z.jar'
    with self.do_test_compile(SHAPELESS_TARGET,
                              expected_files=[jar_suffix]) as found:
      with open_zip(self.get_only(found, jar_suffix), 'r') as jar:
        self.assertTrue(jar.getinfo(SHAPELESS_CLSFILE),
                        'Expected a jar containing the expected class.')

  def test_scala_empty_compile(self):
    with self.do_test_compile('testprojects/src/scala/org/pantsbuild/testproject/emptyscala',
                              expected_files=[]) as found:
      # no classes generated by this target
      pass

  def test_scala_shared_sources(self):
    clsname = 'SharedSources.class'

    with self.do_test_compile('testprojects/src/scala/org/pantsbuild/testproject/sharedsources::',
                              expected_files=[clsname]) as found:
      classes = found[clsname]
      self.assertEqual(2, len(classes))
      for cls in classes:
        self.assertTrue(cls.endswith(
          'org/pantsbuild/testproject/sharedsources/SharedSources.class'))

  def test_scala_failure(self):
    """With no initial analysis, a failed compilation shouldn't leave anything behind."""
    analysis_file = 'testprojects.src.scala.' \
        'org.pantsbuild.testproject.compilation_failure.compilation_failure.analysis'
    with self.do_test_compile('testprojects/src/scala/org/pantsbuild/testprojects/compilation_failure',
                              expected_files=[analysis_file],
                              expect_failure=True) as found:
      self.assertEqual(0, len(found[analysis_file]))

  def test_scala_with_java_sources_compile(self):
    with self.do_test_compile('testprojects/src/scala/org/pantsbuild/testproject/javasources',
                              expected_files=['ScalaWithJavaSources.class',
                                              'JavaSource.class']) as found:

      self.assertTrue(
          self.get_only(found, 'ScalaWithJavaSources.class').endswith(
              'org/pantsbuild/testproject/javasources/ScalaWithJavaSources.class'))

      self.assertTrue(
          self.get_only(found, 'JavaSource.class').endswith(
              'org/pantsbuild/testproject/javasources/JavaSource.class'))

  def test_scalac_plugin_compile(self):
    with self.do_test_compile('testprojects/src/scala/org/pantsbuild/testproject/scalac/plugin',
                              expected_files=['HelloScalac.class', 'scalac-plugin.xml']) as found:

      self.assertTrue(
          self.get_only(found, 'HelloScalac.class').endswith(
              'org/pantsbuild/testproject/scalac/plugin/HelloScalac.class'))

      tree = ET.parse(self.get_only(found, 'scalac-plugin.xml'))
      root = tree.getroot()
      self.assertEqual('plugin', root.tag)
      self.assertEqual('hello_scalac', root.find('name').text)
      self.assertEqual('org.pantsbuild.testproject.scalac.plugin.HelloScalac',
                       root.find('classname').text)

  def test_scalac_debug_symbol(self):
    with self.do_test_compile('testprojects/src/scala/org/pantsbuild/testproject/scalac/plugin',
                         expected_files=['HelloScalac.class', 'scalac-plugin.xml'],
                         extra_args=['--compile-zinc-debug-symbol']) as found:
      pass

  def test_zinc_unsupported_option(self):
    with temporary_dir(root_dir=self.workdir_root()) as workdir:
      with temporary_dir(root_dir=self.workdir_root()) as cachedir:
        # compile with an unsupported flag
        pants_run = self.run_test_compile(
            workdir,
            cachedir,
            'testprojects/src/scala/org/pantsbuild/testproject/emptyscala',
            extra_args=[
              '--compile-zinc-args=-recompile-all-fraction',
              '--compile-zinc-args=0.5',
            ])
        self.assert_success(pants_run)

        # confirm that we were warned
        self.assertIn('is not supported, and is subject to change/removal', pants_run.stdout_data)
