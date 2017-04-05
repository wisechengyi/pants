# coding=utf-8
# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (absolute_import, division, generators, nested_scopes, print_function,
                        unicode_literals, with_statement)

from pex.interpreter import PythonIdentity
from twitter.common.collections import maybe_list

from pants.backend.python.python_artifact import PythonArtifact
from pants.base.deprecated import deprecated_conditional
from pants.base.exceptions import TargetDefinitionException
from pants.base.payload import Payload
from pants.base.payload_field import PrimitiveField
from pants.build_graph.address import Address
from pants.build_graph.resources import Resources
from pants.build_graph.target import Target
from pants.util.memo import memoized_property


class PythonTarget(Target):
  """Base class for all Python targets.

  :API: public
  """

  def __init__(self,
               address=None,
               payload=None,
               sources=None,
               resources=None,  # Old-style resources (file list, Fileset).
               resource_targets=None,  # New-style resources (Resources target specs).
               provides=None,
               compatibility=None,
               **kwargs):
    """
    :param dependencies: The addresses of targets that this target depends on.
      These dependencies may
      be ``python_library``-like targets (``python_library``,
      ``python_thrift_library``, ``python_antlr_library`` and so forth) or
      ``python_requirement_library`` targets.
    :type dependencies: list of strings
    :param sources: Files to "include". Paths are relative to the
      BUILD file's directory.
    :type sources: ``Fileset`` or list of strings
    :param resources: non-Python resources, e.g. templates, keys, other data
      (it is
      recommended that your application uses the pkgutil package to access these
      resources in a .zip-module friendly way.) Paths are relative to the BUILD
      file's directory.
    :type sources: ``Fileset`` or list of strings
    :param resource_targets: The addresses of ``resources`` targets this target
      depends on.
    :type resource_targets: list of strings
    :param provides:
      The `setup_py <#setup_py>`_ to publish that represents this
      target outside the repo.
    :param compatibility: either a string or list of strings that represents
      interpreter compatibility for this target, using the Requirement-style
      format, e.g. ``'CPython>=3', or just ['>=2.7','<3']`` for requirements
      agnostic to interpreter class.
    """
    deprecated_conditional(lambda: resources is not None, '1.5.0.dev0',
                           'The `resources=` Python target argument', 'Depend on resources targets instead.')
    deprecated_conditional(lambda: resource_targets is not None, '1.5.0.dev0',
                           'The `resource_targets=` Python target argument', 'Use `dependencies=` instead.')
    self.address = address
    payload = payload or Payload()
    payload.add_fields({
      'sources': self.create_sources_field(sources, address.spec_path, key_arg='sources'),
      'resources': self.create_sources_field(resources, address.spec_path, key_arg='resources'),
      'provides': provides,
      'compatibility': PrimitiveField(maybe_list(compatibility or ())),
    })
    super(PythonTarget, self).__init__(address=address, payload=payload, **kwargs)
    self._resource_target_specs = resource_targets
    self.add_labels('python')

    if provides and not isinstance(provides, PythonArtifact):
      raise TargetDefinitionException(self,
        "Target must provide a valid pants setup_py object. Received a '{}' object instead.".format(
          provides.__class__.__name__))

    self._provides = provides

    # Check that the compatibility requirements are well-formed.
    for req in self.payload.compatibility:
      try:
        PythonIdentity.parse_requirement(req)
      except ValueError as e:
        raise TargetDefinitionException(self, str(e))

  @property
  def traversable_specs(self):
    for spec in super(PythonTarget, self).traversable_specs:
      yield spec
    if self._provides:
      for spec in list(self._provides._binaries.values()):
        address = Address.parse(spec, relative_to=self.address.spec_path)
        yield address.spec

  @property
  def traversable_dependency_specs(self):
    for spec in super(PythonTarget, self).traversable_dependency_specs:
      yield spec
    if self._resource_target_specs:
      for spec in self._resource_target_specs:
        yield spec
    if self._synthetic_resources_target:
      yield self._synthetic_resources_target.address.spec

  @property
  def provides(self):
    return self.payload.provides

  @property
  def provided_binaries(self):
    def binary_iter():
      if self.payload.provides:
        for key, binary_spec in list(self.payload.provides.binaries.items()):
          address = Address.parse(binary_spec, relative_to=self.address.spec_path)
          yield (key, self._build_graph.get_target(address))
    return dict(binary_iter())

  @property
  def compatibility(self):
    return self.payload.compatibility

  @property
  def resources(self):
    # Note: Will correctly find:
    #   - Regular dependencies on Resources targets.
    #   - Resources targets specified via resource_targets=.
    #   - The synthetic Resources target created from the resources= fileset.
    # Because these are all in the traversable_dependency_specs.
    return [dep for dep in self.dependencies if isinstance(dep, Resources)]

  def walk(self, work, predicate=None):
    super(PythonTarget, self).walk(work, predicate)
    for binary in list(self.provided_binaries.values()):
      binary.walk(work, predicate)

  @memoized_property
  def _synthetic_resources_target(self):
    if not self.payload.resources.source_paths:
      return None

    # Create an address for the synthetic target.
    spec = self.address.spec + '_synthetic_resources'
    resource_address = Address.parse(spec=spec)
    # For safety, ensure an address that's not used already, even though that's highly unlikely.
    while self._build_graph.contains_address(resource_address):
      spec += '_'
      resource_address = Address.parse(spec=spec)

    self._build_graph.inject_synthetic_target(resource_address, Resources,
                                              sources=self.payload.resources.source_paths,
                                              derived_from=self)
    return self._build_graph.get_target(resource_address)
