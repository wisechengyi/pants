# Copyright 2014 Pants project contributors (see CONTRIBUTORS.md).
# Licensed under the Apache License, Version 2.0 (see LICENSE).

import copy
from typing import Dict, Iterator, List, Optional

from pants.option.ranked_value import Rank, RankedValue, Value

Key = str


class OptionValueContainer:
    """A container for option values.

    Implements "value ranking":

       Attribute values can be ranked, so that a given attribute's value can only be changed if
       the new value has at least as high a rank as the old value. This allows an option value in
       an outer scope to override that option's value in an inner scope, when the outer scope's
       value comes from a higher ranked source (e.g., the outer value comes from an env var and
       the inner one from config).

       See ranked_value.py for more details.
    """

    def __init__(self) -> None:
        self._value_map: Dict[Key, RankedValue] = {}

    def get_explicit_keys(self) -> List[Key]:
        """Returns the keys for any values that were set explicitly (via flag, config, or env
        var)."""
        ret = []
        for k, v in self._value_map.items():
            if v.rank > RankedValue.CONFIG_DEFAULT:
                ret.append(k)
        return ret

    def get_rank(self, key: Key) -> Rank:
        """Returns the rank of the value at the specified key.

        Returns one of the constants in RankedValue.
        """
        ranked_value = self._value_map.get(key)
        if ranked_value is None:
            raise AttributeError(key)
        return ranked_value.rank

    def is_flagged(self, key: Key) -> bool:
        """Returns `True` if the value for the specified key was supplied via a flag.

        A convenience equivalent to `get_rank(key) == RankedValue.FLAG`.

        This check can be useful to determine whether or not a user explicitly set an option for this
        run.  Although a user might also set an option explicitly via an environment variable, ie via:
        `ENV_VAR=value ./pants ...`, this is an ambiguous case since the environment variable could also
        be permanently set in the user's environment.

        :param string key: The name of the option to check.
        :returns: `True` if the option was explicitly flagged by the user from the command line.
        :rtype: bool
        """
        return self.get_rank(key) == RankedValue.FLAG

    def is_default(self, key: Key) -> bool:
        """Returns `True` if the value for the specified key was not supplied by the user.

        I.e. the option was NOT specified config files, on the cli, or in environment variables.

        :param string key: The name of the option to check.
        :returns: `True` if the user did not set the value for this option.
        :rtype: bool
        """
        return self.get_rank(key) in (RankedValue.NONE, RankedValue.HARDCODED)

    def get(self, key: Key, default: Optional[Value] = None):
        # Support dict-like dynamic access.  See also __getitem__ below.
        if key not in self._value_map:
            return default
        return self._get_underlying_value(key)

    def update(self, other: "OptionValueContainer") -> None:
        """Set other's values onto this object.

        For each key, highest ranked value wins. In a tie, other's value wins.
        """
        for k, v in other._value_map.items():
            self._set(k, v)

    def as_dict(self) -> Dict[Key, Value]:
        return {key: self.get(key) for key in self._value_map}

    def _get_underlying_value(self, key: Key):
        # Note that the key may exist with a value of None, so we can't just
        # test self._value_map.get() for None.
        if key not in self._value_map:
            raise AttributeError(key)
        ranked_val = self._value_map[key]
        return ranked_val.value

    def _set(self, key: Key, value: RankedValue) -> None:
        if key in self._value_map:
            existing_value = self._value_map[key]
            existing_rank = existing_value.rank
        else:
            existing_rank = RankedValue.NONE

        if not isinstance(value, RankedValue):
            raise AttributeError(f"Value must be of type RankedValue: {value}")

        new_rank = value.rank
        if new_rank >= existing_rank:
            # We set values from outer scopes before values from inner scopes, so
            # in case of equal rank we overwrite. That way that the inner scope value wins.
            self._value_map[key] = value

    # Support natural dynamic access, e.g., opts[foo] is more idiomatic than getattr(opts, 'foo').
    def __getitem__(self, key: Key):
        return self.__getattr__(key)

    # Support attribute setting, e.g., opts.foo = RankedValue(RankedValue.HARDCODED, 42).
    def __setattr__(self, key: Key, value: RankedValue) -> None:
        if key == "_value_map":
            return super().__setattr__(key, value)
        self._set(key, value)

    # Support attribute getting, e.g., foo = opts.foo.
    # Note: Called only if regular attribute lookup fails,
    # so method and member access will be handled the normal way.
    def __getattr__(self, key: Key):
        if key == "_value_map":
            # In case we get called in copy/deepcopy, which don't invoke the ctor.
            raise AttributeError(key)
        return self._get_underlying_value(key)

    def __iter__(self) -> Iterator[Key]:
        """Returns an iterator over all option names, in lexicographical order."""
        for name in sorted(self._value_map.keys()):
            yield name

    def __copy__(self) -> "OptionValueContainer":
        """Ensure that a shallow copy has its own value map."""
        ret = type(self)()
        ret._value_map = copy.copy(self._value_map)
        return ret
