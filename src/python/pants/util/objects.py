# coding=utf-8
# Copyright 2016 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

from __future__ import (absolute_import, division, generators, nested_scopes, print_function,
                        unicode_literals, with_statement)

import sys
from collections import namedtuple

from pants.util.memo import memoized


def datatype(*args, **kwargs):
  """A wrapper for `namedtuple` that accounts for the type of the object in equality."""
  class DataType(namedtuple(*args, **kwargs)):
    def __eq__(self, other):
      if self is other:
        return True
      # Compare types and fields.
      return type(other) == type(self) and super(DataType, self).__eq__(other)

    def __ne__(self, other):
      return not (self == other)
  return DataType


class Collection(object):
  """
  Single Collection Type.
  """

  @classmethod
  @memoized
  def of(cls, ext):
    type_name = b'{}({!r})'.format(cls.__name__, ext)

    # 'dependencies' field is hardcoded here. If more flexibility is needed,
    # parameterize it as an argument.
    ext_type = type(type_name, (cls, datatype("{}s".format(ext.__name__), ('dependencies',))), {})

    # Expose the custom class type at the module level to be pickle compatible.
    setattr(sys.modules[cls.__module__], type_name, ext_type)

    return ext_type

  @classmethod
  def ext(cls):
    raise NotImplementedError()

  def __repr__(self):
    return '{}(of={!r})'.format(self.__class__.__name__, self.ext)
