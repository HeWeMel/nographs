"""
The types and classes of this module are regarded as implementation secret.
They are not documented as part of the API documentation.

In the API documentation, the type aliases are replaced by their respective
definition. And the classes are only used internally by other classes, and
not in the API.
"""

from collections.abc import Iterable, Hashable, Iterator, MutableSet, MutableMapping
from typing import Protocol, TypeVar, Generic, Callable, Union, Optional, cast
from itertools import repeat
from abc import ABC, abstractmethod


T_hashable_key = TypeVar("T_hashable_key", bound=Hashable)
T_hashable_key_contra = TypeVar(
    "T_hashable_key_contra", bound=Hashable, contravariant=True
)

T_value = TypeVar("T_value")
T_value_contra = TypeVar("T_value_contra", contravariant=True)
T_value_co = TypeVar("T_value_co", covariant=True)

T_default_value = TypeVar("T_default_value")


# --- General gear collection types ---
# Intention: Declare type bounds and document details that hold for all places
# where the type aliases are used.

VertexSet = MutableSet[T_hashable_key]
"""ABC for a collection that is intended to be used by NoGraphs for storing sets
of vertices, e.g., represented by some form of hashable id. A VertexSet is not allowed
to raise an IndexError in any circumstance (but, of cause, it might raise a KeyError).

Instances of VertexSet created by NoGraphs always completely fulfil this interface.

For the case that application code creates a VertexSet, e.g., with an
implementation that is optimized for specific data types or use cases, NoGraphs
gives the following guarantees:

- NoGraphs only calls the methods __contains__ and __add__
- NoGraphs calls __contains__ only with keys of T_hashable_keys

Apart from this, a VertexSet created by application code needs to fulfil all
parts of the interface that the application code itself requires from a VertexSet,
since NoGraphs might return the object it has been called with.
"""


VertexMapping = MutableMapping[T_hashable_key, T_value]
"""ABC for a collection that is intended to be used by NoGraphs for storing mappings
from vertices, e.g., represented by some form of hashable id, to some values.
A VertexMapping is not allowed to raise an IndexError in any circumstance (but of
cause it might raise a KeyError).

Instances of VertexSet created by NoGraphs always completely fulfil this interface.

For the case that application code creates a VertexSet, e.g., with an
implementation that is optimized for specific data types or use cases, NoGraphs
gives the following guarantees:

- NoGraphs only calls the methods __getitem__, __setitem__,
  __contains__,  __iter__ and updatedefault

- NoGraphs calls __contains__ only with keys of T_hashable_keys.

Apart from this, a VertexMapping created by application code needs to fulfil all
parts of the interface that the application code itself requires from a VertexMapping,
since NoGraphs might return the object it has been called with.
"""


# --- Gear collections for dense integer keys ---
# Here, sets and mappings are implemented based on a wrapped sequence.


# NoGraphs provides special implementations of VertexSet and VertexMapping for vertex
# ids that are non-negative dense integers (some of these implementations are further
# specialized for the case, that also the vertices themselves are non-negative dense
# integers). Application code can provide additional implementations.
#
# Each such implementation offered by NoGraphs is a wrapper around a sequence that is
# used internally to store the data, e.g., a list or an array. If key / value pairs
# with non-consecutive keys are to be stored, the gaps are marked by using an
# implementation specific default value ("no value marker", e.g. None in case of a
# list, and some special value within the value type in case of an array).
#
# It exposes the underlying sequence to the traversal algorithms of NoGraphs,
# and they use the direct access to the sequence for getting a better performance
# when setting and getting values for keys. When the sequence needs to be extended to
# store a value for a key that exceeds the current length of the sequence, this is
# handled by the wrapper.
#
# The used mechanism is generic, type save, fast, transparent for application code
# that get such a VertexSet or VertexMapping, and it allows NoGraphs for an
# implementation that can also handle VertexSet and VertexMapping without underlying
# sequences (both if given by NoGraphs itself or if given by application code).
# The drawback: Especially for typing reasons, the implementation is extremely
# long for a seemingly easy job.


# --- Protocols for the used kind of sequences (external and internal view)


class GettableSettableForGearProto(
    Protocol[T_hashable_key_contra, T_value_contra, T_value_co]
):
    """
    Protocol for a mutable subscriptable container with separate types
    for values that are to be stored and values that are retrieved.

    NoGraphs uses this to specify the case that the creator of the container
    might generate own entries of some key/value, and the value can be of a
    type that can not be stored by using __setitem__, but could be returned
    by __getitem__.
    """

    @abstractmethod
    def __getitem__(self, item: T_hashable_key_contra) -> T_value_co:
        """Get the value that is stored for key *item*. If *item* exceeds the
        internal size of the container, an IndexError is raised.
        """
        raise NotImplementedError

    def __setitem__(self, item: T_hashable_key_contra, value: T_value_contra) -> None:
        """Store *value* for key *item* in the container. If *item* exceeds the
        internal size of the container, an IndexError is raised.
        """
        raise NotImplementedError


class SequenceForGearProto(
    GettableSettableForGearProto[T_hashable_key_contra, T_value_contra, T_value_co],
    Protocol,
):
    """
    Protocol for a sequence-like collection that is intended to be used to implement
    a VertexSet or VertexMapping by wrapping the collection accordingly, and
    to expose the wrapped sequence for fast direct subscription access.

    The wrapper itself uses SequenceForGearProto as protocol to access the wrapped
    sequence, but only exposes GettableSettableForGearProto to traversal algorithms
    of NoGraphs and to application code.

    Not part of the protocol is, that the keys need to be non-negative integers
    (and in practice, they also need to start from 0 and to be dense), but all
    implementations given by NoGraphs require this and instantiate the protocol
    with accordingly restricted key type.

    Examples: A list and an array fulfil the protocol, if instantiated
    with suitable type restrictions.
    """

    def __len__(self) -> int:
        """Return the size of the collection."""
        raise NotImplementedError

    def append(self, value: T_value_contra) -> None:
        """Store *value* at the end of the collection. The size of the
        collection raises by 1."""
        raise NotImplementedError

    def extend(self, values: Iterable[T_value_contra]) -> None:
        """Store *values* at the end of the collection. The size of the
        collection raises accordingly."""
        raise NotImplementedError

    def __iter__(self) -> Iterator[T_value_co]:
        """Return an iterator that iterates the contained values."""
        raise NotImplementedError


# --- Protocols for the used kind of wrappers


class VertexSequenceWrapperProto(
    Protocol[T_hashable_key_contra, T_value_contra, T_value_co]
):
    """Protocol for a wrapper around a SequenceForGearProto. The wrapper
    can be used to implement a VertexSet or a VertexMapping based on the
    wrapped SequenceForGearProto.

    When creating a VertexSequenceWrapper, a factory method that is able
    to create the sequence has to be given. (When used to emulate a Set,
    the MutableSet mixin needs to be able to create new sets. Thus, a
    factory and not a collection is used here as parameter).

    If a special *default* value is stored in the sequence for some key, this
    is interpreted as having no assignment for the key. This allows
    for handling gaps between two keys that have regularly assigned values.

    The *default* is a value that can be stored in the sequence, but either
    will not occur as one of the regularly assigned values, or it is a
    value that can be interpreted as being assigned to all possible keys when
    the collection is empty or being assigned when a regular assignment is
    deleted. When the class is instantiated, a suitable default value has to
    be fixed.

    (Side note: A NoGraphs traversal object is generic in the key type and value type
    and uses its type variables for typing the VertexSequenceWrapperProto. Thus,
    VertexSequenceWrapperProto needs to be generic. Although, a concrete
    implementation of VertexSequenceWrapperProto is only possible for integer keys,
    since a sequence is used as the wrapped data structure, and because method
    extend_and_set does integer calculations in the key type. Thus,
    VertexSequenceWrapperProto and the concrete implementation had to be separated.)
    """

    def sequence(
        self,
    ) -> GettableSettableForGearProto[
        T_hashable_key_contra, T_value_contra, T_value_co
    ]:
        """Return the wrapped sequence. Allows NoGraphs' traversal algorithms
        to directly read from and write to the sequence.
        """
        raise NotImplementedError

    def default(self) -> T_value_co:
        """Return the default value. When NoGraphs' traversal algorithms
        retrieve this value for some key, they need to interpret this as if
        no value is assigned to the key.
        """
        raise NotImplementedError

    def extend_and_set(self, key: T_hashable_key_contra, value: T_value_contra) -> None:
        """Extend the underlying sequence in order to store *value* for *key*.
        For new keys "below" *key* and, for better overall performance, also
        for many keys "above" *key*, the *default* value is stored.

        The method is called by NoGraphs' traversal algorithms if writing to the
        underlying sequence raised an IndexError for some key. This allows to
        handle such cases correctly without knowing details. Since it is guaranteed
        that such cases occur rarely (due to the preloading described above),
        the call to the method is not as performance critical as the direct accesses
        to the underlying sequence.
        """
        raise NotImplementedError


class VertexSequenceWrapperForSetProto(
    VertexSequenceWrapperProto[T_hashable_key, T_value_contra, T_value_co], Protocol
):
    """VertexSequenceWrapperProto for a wrapper that emulates a VertexSet"""

    def update_from_keys(self, elements: Iterable[T_hashable_key]) -> None:
        """Store the elements."""
        raise NotImplementedError

    def index_and_bit_method(
        self,
    ) -> Optional[Callable[[T_hashable_key, int], tuple[T_hashable_key, int]]]:
        """Return a function that computes the integer index and the bit number for
        the given *key* and the given number of bits that each integer can handle.
        """
        raise NotImplementedError

    def _from_iterable(
        self, elements: Iterable[T_hashable_key]
    ) -> "VertexSequenceWrapperForSetProto":
        """Return a new VertexSequenceWrapperForSetProto with the *elements*
        as content."""
        raise NotImplementedError


class VertexSequenceWrapperForMappingProto(
    VertexSequenceWrapperProto[T_hashable_key_contra, T_value_contra, T_value_co],
    Protocol,
):
    """VertexSequenceWrapperProto for a wrapper that emulates a VertexMapping"""

    def update_from_keys_values(
        self, elements: Iterable[tuple[T_hashable_key_contra, T_value_contra]]
    ) -> None:
        """For each pair of key and value given by *elements*, assign
        the value to the key.
        """
        raise NotImplementedError

    def update_default(
        self, elements: Iterable[tuple[T_hashable_key_contra, T_value_contra]]
    ) -> None:
        """For each pair of key and value given by *elements*, assign
        the value to the key if the collection does not already store a value (other
        than the default value) for the key.
        """
        raise NotImplementedError


# --- ABCs and helper functions to allow for type-save down casts
# (From VertexSet and VertexMapping to an underlying
# VertexSequenceWrapperForSetProto or VertexSequenceWrapperForMappingProto, with
# guaranteed correct typing of the generic variables of VertexSequenceWrapperProto.)


# - Dummy implementations

called_by_mistake = "Call to a method of this object is not expected to ever happen"


class _GettableSettableForGearAssertNoCall(
    GettableSettableForGearProto[T_hashable_key_contra, T_value_contra, T_value_co]
):
    """An implementation of GettableSettableForGearProto that implements nothing,
    but raises AssertionError on all method calls.

    Used in traversal strategies instead of the combination of an optional object
    and statements *assert not None* in a cases where the type
    checker cannot fully correctly track all execution paths. The AssertionError,
    that were being raised by the assert statements in case of implementation
    errors are now raised when a method of _GettableSettableForGearAssertNoCall
    is really called by mistake.
    """

    def __getitem__(self, item):
        raise AssertionError(called_by_mistake)

    def __setitem__(self, item, value):
        raise AssertionError(called_by_mistake)


class _VertexSequenceWrapperAssertNoCall(
    VertexSequenceWrapperForSetProto[T_hashable_key, T_value_contra, T_value_co],
    VertexSequenceWrapperForMappingProto[
        T_hashable_key, T_value_contra, T_value_co
    ],
):
    """An implementation of the protocols that implements nothing,
    but raises AssertionError on all method calls.

    Used in traversal strategies instead of combination of an optional object
    together with statements *assert not None* in a cases where the type
    checker cannot fully correctly track all execution paths. The AssertionError,
    that were being raised by the assert statements in case of implementation
    errors are now raised when a method of _VertexSequenceWrapperAssertNoCall
    is really called by mistake.
    """

    def sequence(self):
        raise AssertionError(called_by_mistake)

    def default(self):
        raise AssertionError(called_by_mistake)

    def extend_and_set(self, key, value):
        raise AssertionError(called_by_mistake)

    def update_from_keys(self, elements):
        raise AssertionError(called_by_mistake)

    def index_and_bit_method(self):
        raise AssertionError(called_by_mistake)

    def update_from_keys_values(self, elements):
        raise AssertionError(called_by_mistake)

    def update_default(self, elements):
        raise AssertionError(called_by_mistake)

    def _from_iterable(self, elements):
        raise AssertionError(called_by_mistake)

# - Set


class VertexSetByWrapper(
    VertexSequenceWrapperForSetProto[T_hashable_key, int, int],
    VertexSet[T_hashable_key],
    ABC,
):
    """
    A VertexSet that is implemented based on a sequence-like internal container
    needs to subclass this class in order to allow NoGraphs' traversal algorithms to
    cast the VertexSet to a VertexSequenceWrapperProto with the defined generic
    parameters in a type-save way.
    """

    pass


def get_wrapper_from_vertex_set(
    vertex_set: VertexSet[T_hashable_key],
) -> Optional[VertexSequenceWrapperForSetProto[T_hashable_key, int, int]]:
    """If *vertex_set* is implemented by a VertexSetByWrapper,
    return its wrapper, otherwise return None. The class encapsulates the
    down cast and the argumentation for its correctness.
    """
    if isinstance(vertex_set, VertexSetByWrapper):
        # VertexSet is invariant in T_hashable_key. So,
        # having a VertexSet[T_hashable_key] also means having a
        # VertexSetByWrapper[T_hashable_key], and thus a
        # VertexSequenceWrapperForSetProto[T_hashable_key, int, int].
        return cast(
            VertexSequenceWrapperForSetProto[T_hashable_key, int, int], vertex_set
        )
    return None


def access_to_vertex_set(
    vertex_set: VertexSet[T_hashable_key],
) -> tuple[
    bool,
    GettableSettableForGearProto[T_hashable_key, int, int],
    VertexSequenceWrapperForSetProto[T_hashable_key, int, int],
    bool,
    Callable[[T_hashable_key, int], tuple[T_hashable_key, int]],
]:
    """
    If *vertex_set* is implemented by a VertexSetByWrapper,
    return True, the wrapper, the wrapped sequence,
    and either True and the index_and_bit_method of the wrapper, if available,
    or False and a dummy function. It the returned sequence raises an IndexError
    on access, the wrapper can be used to extend the sequence in order to solve
    the problem.

    Otherwise, return False ("no wrapper, no underlying sequence") and dummy
    implementations, that are not intended to be accessed.
    """

    wrapper = get_wrapper_from_vertex_set(vertex_set)

    def do_not_call(
        key: T_hashable_key, bits_per_integer: int
    ) -> tuple[T_hashable_key, int]:
        raise AssertionError(called_by_mistake)

    if wrapper is None:
        return (
            False,
            _GettableSettableForGearAssertNoCall[T_hashable_key, int, int](),
            _VertexSequenceWrapperAssertNoCall[T_hashable_key, int, int](),
            False,
            do_not_call,
        )
    else:
        index_and_bit_method = wrapper.index_and_bit_method()
        if index_and_bit_method is None:
            return (True, wrapper.sequence(), wrapper, False, do_not_call)
        else:
            return (True, wrapper.sequence(), wrapper, True, index_and_bit_method)


# - Mapping (without None)


class VertexMappingByWrapper(
    VertexSequenceWrapperForMappingProto[T_hashable_key, T_value, T_value],
    VertexMapping[T_hashable_key, T_value],
    ABC,
):
    """
    A VertexMapping that is implemented based on a sequence-like internal container
    needs to subclass this class in order to allow NoGraphs' traversal algorithms to
    cast the VertexMapping to a VertexSequenceWrapperForMappingProto with the defined
    generic parameters in a type-save way.
    """

    pass


def get_wrapper_from_vertex_mapping(
    vertex_mapping: VertexMapping[T_hashable_key, T_value]
) -> Optional[VertexSequenceWrapperForMappingProto[T_hashable_key, T_value, T_value]]:
    """If *vertex_mapping* is implemented by a VertexMappingByWrapper,
    return its wrapper, otherwise return None. The class encapsulates the
    down cast and the argumentation for its correctness.
    """
    if isinstance(vertex_mapping, VertexMappingByWrapper):
        # VertexMapping is invariant in T_hashable_key and T_value. So,
        # having a VertexMapping[T_hashable_key, T_value] also means having a
        # VertexMappingByWrapper[T_hashable_key, T_value, T_value] , and thus a
        # VertexSequenceWrapperForMappingProto[T_hashable_key, T_value, T_value].
        return cast(
            VertexSequenceWrapperForMappingProto[T_hashable_key, T_value, T_value],
            vertex_mapping,
        )
    return None


def access_to_vertex_mapping(
    vertex_mapping: VertexMapping[T_hashable_key, T_value]
) -> tuple[
    bool,
    GettableSettableForGearProto[T_hashable_key, T_value, T_value],
    VertexSequenceWrapperForMappingProto[T_hashable_key, T_value, T_value],
]:
    """
    If *vertex_mapping* is implemented by a VertexMappingByWrapper,
    return True, the wrapped sequence for direct access,
    and the wrapper to extend to sequence if necessary.
    Otherwise, return False, the vertex_mapping itself, and a
    dummy implementation or a wrapper.

    Note: If the returned GettableSettableForGearProto raises an IndexError
    on access, it is guaranteed that the third returned value had been a
    VertexSequenceWrapperProto that can be used to extend the
    sequence in order solve the problem.
    """

    wrapper = get_wrapper_from_vertex_mapping(vertex_mapping)
    if wrapper is None:
        # The vertex_mapping returned here never raises an IndexError,
        # because it is a VertexMapping (see there) but is no
        # VertexMappingByWrapper.
        return (
            False,
            vertex_mapping,
            _VertexSequenceWrapperAssertNoCall[T_hashable_key, T_value, T_value](),
        )

    # The sequence returned here may raise an IndexError, but then a wrapper
    # is provided that can be used to handle this.
    return (
        True,
        wrapper.sequence(),
        wrapper,
    )


# - Mapping with None


class VertexMappingByWrapperWithNone(
    VertexSequenceWrapperForMappingProto[T_hashable_key, T_value, Optional[T_value]],
    VertexMapping[T_hashable_key, T_value],
    ABC,
):
    """
    A VertexMapping that is implemented based on a sequence-like internal container
    needs to subclass this class in order to allow NoGraphs' traversal algorithms to
    cast the VertexMapping to a VertexSequenceWrapperForMappingProto with the defined
    generic parameters (including None as no-value marker) in a type-save way.
    """

    pass


def get_wrapper_from_vertex_mapping_with_none(
    vertex_mapping: VertexMapping[T_hashable_key, T_value]
) -> Optional[
    VertexSequenceWrapperForMappingProto[T_hashable_key, T_value, Optional[T_value]]
]:
    """If *vertex_mapping* is implemented by a VertexMappingByWrapper,
    return its wrapper, otherwise return None. The class encapsulates the
    down cast and the argumentation for its correctness.
    """
    if isinstance(vertex_mapping, VertexMappingByWrapperWithNone):
        # VertexMapping is invariant in T_hashable_key and T_value. So,
        # having a VertexMapping[T_hashable_key, T_value] also means having a
        # VertexMappingByWrapperWithNone[T_hashable_key, T_value], and thus a
        # VertexSequenceWrapperForMappingProto[T_hashable_key, T_value, T_value].
        return cast(
            VertexSequenceWrapperForMappingProto[
                T_hashable_key, T_value, Optional[T_value]
            ],
            vertex_mapping,
        )
    return None


def access_to_vertex_mapping_expect_none(
    vertex_mapping: VertexMapping[T_hashable_key, T_value]
) -> tuple[
    bool,
    GettableSettableForGearProto[T_hashable_key, T_value, Optional[T_value]],
    VertexSequenceWrapperForMappingProto[T_hashable_key, T_value, Optional[T_value]],
]:
    """
    If *vertex_mapping* is implemented by a VertexMappingByWrapper or a
    VertexMappingByWrapperWithNone,
    return True, the wrapped sequence for direct access, and the wrapper to
    extend to sequence if necessary.
    Otherwise, return False, the vertex_mapping itself, and a
    dummy implementation or a wrapper.

    If the returned container ever raises an IndexError on access, it
    is guaranteed that the second returned value had been a
    VertexSequenceWrapperProto that can be used to extend the
    sequence in order solve the problem.
    """

    wrapper = get_wrapper_from_vertex_mapping_with_none(vertex_mapping)
    if wrapper is None:
        wrapper = get_wrapper_from_vertex_mapping(vertex_mapping)
    if wrapper is not None:
        # The sequence returned here may raise an IndexError, but then a wrapper
        # is provided that can be used to handle this.
        return True, wrapper.sequence(), wrapper

    # The vertex_mapping returned here never raises an IndexError.
    return (
        False,
        vertex_mapping,
        _VertexSequenceWrapperAssertNoCall[
            T_hashable_key, T_value, Optional[T_value]
        ](),
    )


# --- General implementations for sequence wrappers


# Non-negative (for typing) and dense (for performance) cannot be specified
NonNegativeDenseInt = int


class VertexSequenceWrapper(
    Generic[T_value, T_default_value],
    VertexSequenceWrapperProto[
        NonNegativeDenseInt, T_value, Union[T_value, T_default_value]
    ],
    ABC,
):
    """ABC for a wrapper around a SequenceForGearProto. It supports defining
    a VertexSet or a VertexMapping based on the wrapped sequence.

    See VertexSequenceWrapperProto for more details.

    (Side note: Even if Python allowed for defining a range of integers as
    type, it would not be possible to use this as application-defined
    variable key type for the wrapped sequence instead of just int:
    It stores data for keys that have and will never be given by application
    code, since it will fill key gaps, and these values could be outside the
    key type chosen by application code.)

    :param sequence_factory: A factory able to create a sequence of type
        SequenceForGearProto to be used as internal collection.

    :param default: The default value.

    :param extend_size: Number of pre-allocated item slots when the collection grows
    """

    def __init__(
        self,
        sequence_factory: Callable[
            [],
            SequenceForGearProto[
                NonNegativeDenseInt,
                Union[T_value, T_default_value],
                Union[T_value, T_default_value],
            ],
        ],
        default: T_default_value,
        extend_size: int,
    ) -> None:

        self._sequence_factory: Callable[
            [],
            SequenceForGearProto[
                NonNegativeDenseInt,
                Union[T_value, T_default_value],
                Union[T_value, T_default_value],
            ],
        ] = sequence_factory
        self._sequence: SequenceForGearProto[
            NonNegativeDenseInt,
            Union[T_value, T_default_value],
            Union[T_value, T_default_value],
        ] = self._sequence_factory()
        self._default = default
        self._extend_size = extend_size

    def sequence(
        self,
    ) -> GettableSettableForGearProto[
        NonNegativeDenseInt, T_value, Union[T_value, T_default_value]
    ]:
        """Return the wrapped sequence with restricted protocol and types. Allows
        NoGraphs' traversal algorithms to directly read from and write to the
        sequence.
        """
        return self._sequence

    def default(self) -> T_default_value:
        """Return the *default* value defined on initialization."""
        return self._default

    def extend_and_set(self, key: NonNegativeDenseInt, value: T_value) -> None:
        """Extend the underlying sequence in order to store *value* for *key*.
        For new keys "below" *key* and, for better overall performance, also
        for many keys "above" *key*, the *default* value is stored.

        The method is called by NoGraphs if writing to the underlying sequence
        raised an IndexError for some key. It allows NoGraphs to handle such
        cases correctly without knowing details. Since it is guaranteed that
        such cases occur rarely (due to the preloading described above), the
        call to the method is not as performance critical as the direct accesses
        to the underlying sequence.
        """
        default = self._default
        collection = self._sequence
        collection.extend(repeat(default, key - len(collection)))
        collection.append(value)
        collection.extend(repeat(default, self._extend_size))


# --- Implementations of VertexSet(...ByWrapper) and
# --- VertexMapping (...ByWrapperWithNone or ...ByWrapperWithoutNone)
# --- based on a VertexSequenceWrapper

# --  VertexSet


class VertexSetWrappingSequence(
    VertexSequenceWrapper[int, int], VertexSetByWrapper[NonNegativeDenseInt], ABC
):
    """A VertexSequenceWrapper that emulates a VertexSet for
    non-negative dense integer keys based on an underlying SequenceForGearProto.

    It must be initialized with a factory function for the SequenceForGearProto
    to be wrapped, the number of elements the sequence should be extended when
    more space is needed, and an iterable of keys with initial content.

    In performance critical cases, NoGraphs does not call the methods of this
    class (emulation of a set), but directly accesses the underlying sequence.
    """

    def __init__(
        self,
        sequence_factory: Callable[
            [], SequenceForGearProto[NonNegativeDenseInt, int, int]
        ],
        extend_size: int,
        keys: Iterable[NonNegativeDenseInt],
    ):
        super().__init__(sequence_factory, 0, extend_size)
        self.update_from_keys(keys)

    def __repr__(self) -> str:
        content = ", ".join(str(v) for v in self)
        return f"{{{content}}}"

    @abstractmethod
    def __iter__(self) -> Iterator[NonNegativeDenseInt]:
        """Return an iterator that iterates the "officially" contained keys.
        Keys with *default* as value are omitted and interpreted as key gap.
        """
        raise NotImplementedError()

    @abstractmethod
    def __len__(self) -> int:
        """Return number of keys stored in the collection. Time complexity of
        O(n), needs to iterate through the collection."""
        raise NotImplementedError()

    @abstractmethod
    def _from_iterable(
        self, elements: Iterable[NonNegativeDenseInt]
    ) -> "VertexSetWrappingSequence":
        """Create a new instance with the same sequence factory and default
        value, but a new content.

        See section "Examples and Recipes" of collections.abc about the Set mixin.
        """
        raise NotImplementedError()

    @abstractmethod
    def update_from_keys(self, keys: Iterable[NonNegativeDenseInt]) -> None:
        """Add all the keys to the collection"""
        raise NotImplementedError()

    @abstractmethod
    def index_and_bit_method(
        self,
    ) -> Optional[
        Callable[[NonNegativeDenseInt, int], tuple[NonNegativeDenseInt, int]]
    ]:
        """For cases where a sequence of bytes is used to emulate a bit array:
        return function that computes the byte index and the bit number for *key*
        """
        raise NotImplementedError()


class VertexSetWrappingSequenceNoBitPacking(VertexSetWrappingSequence):
    """VertexSetWrappingSequence that does not use bit packing"""

    def __contains__(self, key: object) -> bool:
        if not isinstance(key, int) or key < 0:
            # A MutableMapping defines key as object. Thus, here, we have to
            # be able to handle keys outside the chosen key type.
            # Where NoGraphs inlines the method, this problem does not occur.
            return False
        try:
            return bool(self._sequence[key])
        except IndexError:
            return False

    def __iter__(self) -> Iterator[NonNegativeDenseInt]:
        for key, value in enumerate(self._sequence):
            if value:
                yield key

    def __len__(self) -> int:
        return sum(1 for value in iter(self._sequence) if value)

    def add(self, key: NonNegativeDenseInt) -> None:
        try:
            self._sequence[key] = True
        except IndexError:
            self.extend_and_set(key, True)

    def discard(self, key: NonNegativeDenseInt) -> None:
        try:
            self._sequence[key] = False
        except IndexError:
            return

    def update_from_keys(self, keys: Iterable[NonNegativeDenseInt]) -> None:
        for key in keys:
            try:
                self._sequence[key] = True
            except IndexError:
                self.extend_and_set(key, True)

    def _from_iterable(
        self, elements: Iterable[NonNegativeDenseInt]
    ) -> "VertexSetWrappingSequenceNoBitPacking":
        # Although the set mixin likely gives an iterable that is based
        # on the results of the __iter__ of our class, and thus, it yields
        # sorted values, but there is no guarantee. So, we do not assume this.
        # So, we create an empty sequence and add our values to it.
        new_collection = VertexSetWrappingSequenceNoBitPacking(
            self._sequence_factory, self._extend_size, ()
        )
        new_collection.update_from_keys(elements)
        return new_collection

    def index_and_bit_method(self) -> None:
        return None


class VertexSetWrappingSequenceBitPacking(VertexSetWrappingSequence):
    """VertexSetWrappingSequence that uses bit packing"""

    def __contains__(self, key: object) -> bool:
        if not isinstance(key, int) or key < 0:
            # A MutableMapping defines key as object. Thus, here, we have to
            # be able to handle keys outside the chosen key type.
            # Where NoGraphs inlines the method, this problem does not occur.
            return False
        sequence_key, bit_number = divmod(key, 8)
        try:
            value = self._sequence[sequence_key]
        except IndexError:
            return False
        return (value != 0) and (value & (1 << bit_number)) != 0

    def __iter__(self) -> Iterator[NonNegativeDenseInt]:
        value_high = 0
        for sequence_value in self._sequence:
            if sequence_value != 0:
                for (
                    value_low,
                    bit_mask,
                ) in enumerate((1, 2, 4, 8, 16, 32, 64, 128)):
                    if sequence_value & bit_mask:
                        yield value_high + value_low
            value_high += 8

    def __len__(self) -> int:
        return sum(value.bit_count() for value in self._sequence)

    def add(self, key: NonNegativeDenseInt) -> None:
        sequence = self._sequence
        sequence_key, bit_number = divmod(key, 8)
        bit_mask = 1 << bit_number
        try:
            sequence[sequence_key] = sequence[sequence_key] | bit_mask
        except IndexError:
            self.extend_and_set(sequence_key, bit_mask)

    def discard(self, key: NonNegativeDenseInt) -> None:
        sequence_key, bit_number = divmod(key, 8)
        bit_mask = 255 - (1 << bit_number)
        sequence = self._sequence
        try:
            sequence[sequence_key] = sequence[sequence_key] & bit_mask
        except IndexError:
            return

    def update_from_keys(self, keys: Iterable[NonNegativeDenseInt]) -> None:
        sequence = self._sequence
        for key in keys:
            sequence_key, bit_number = divmod(key, 8)
            bit_mask = 1 << bit_number
            try:
                sequence[sequence_key] = sequence[sequence_key] | bit_mask
            except IndexError:
                self.extend_and_set(sequence_key, bit_mask)

    def _from_iterable(
        self, elements: Iterable[NonNegativeDenseInt]
    ) -> "VertexSetWrappingSequenceBitPacking":
        # Although the set mixin likely gives an iterable that is based
        # on the results of the __iter__ of our class, and thus, it yields
        # sorted values, but there is no guarantee. So, we do not assume this.
        # So, we create an empty sequence and add our values to it.
        new_collection = VertexSetWrappingSequenceBitPacking(
            self._sequence_factory, self._extend_size, ()
        )
        new_collection.update_from_keys(elements)
        return new_collection

    def index_and_bit_method(
        self,
    ) -> Callable[[NonNegativeDenseInt, int], tuple[NonNegativeDenseInt, int]]:
        return divmod


# --  VertexMapping


class VertexMappingWrappingSequence(VertexSequenceWrapper[T_value, T_default_value]):
    """A VertexSequenceSwapper that emulates a VertexMapping for
    non-negative dense integer keys based on an underlying SequenceForGearProto.

    It must be initialized with a factory function for the SequenceForGearProto
    to be wrapped, the number of elements the sequence should be extended when
    more space is needed,
    a default value of type T_value that is suitable for the use case,
    and an iterable of keys with initial content.

    In performance critical cases, NoGraphs does not call the methods of this
    class (emulation of a set), but directly accesses the underlying sequence.
    """

    def __init__(
        self,
        sequence_factory: Callable[
            [],
            SequenceForGearProto[
                NonNegativeDenseInt,
                Union[T_value, T_default_value],
                Union[T_value, T_default_value],
            ],
        ],
        default: T_default_value,
        extend_size: int,
        items: Iterable[tuple[NonNegativeDenseInt, T_value]],
    ):
        super().__init__(sequence_factory, default, extend_size)
        self.update_from_keys_values(items)

    def __getitem__(self, key: NonNegativeDenseInt) -> T_value:
        """Get the value that is stored for *key* by the collection.
        If no value is stored, return the *default* value."""
        if key in self:
            # We only store values of either T_value or the value self._default.
            # __contains(key) ensures that self._sequence[key] != self._default.
            value = cast(T_value, self._sequence[key])
            return value
        else:
            raise KeyError

    def __setitem__(self, key: NonNegativeDenseInt, value: T_value) -> None:
        """Store *value* as value for *key* in collection."""
        sequence = self._sequence
        try:
            sequence[key] = value
        except IndexError:
            self.extend_and_set(key, value)

    def __contains__(self, key: object) -> bool:
        """Check if *key* is a non-negative integer, within the range
        of keys in the collection, and not a gap (key without value)."""
        if not isinstance(key, int) or key < 0:
            # A MutableMapping defines key as object. Thus, here, we have to
            # be able to handle keys outside the chosen key type.
            # Where NoGraphs inlines the method, this problem does not occur.
            return False
        sequence = self._sequence
        return key < len(sequence) and sequence[key] != self._default

    def __iter__(self) -> Iterator[NonNegativeDenseInt]:
        """Return an iterator that iterates the "officially" contained keys.
        Keys with *default* as value are omitted and interpreted as key gap."""
        default = self._default
        sequence = self._sequence
        for key, value in enumerate(sequence):
            if value != default:
                yield key

    def __len__(self) -> int:
        """Return number of keys stored in the collection. Time complexity of
        O(n), needs to iterate through the collection."""
        default = self._default
        return sum(1 for value in iter(self._sequence) if value != default)

    def __delitem__(self, key: NonNegativeDenseInt) -> None:
        """Remove the assignment of some value to *key*"""
        if key in self:
            self._sequence[key] = self._default

    def __repr__(self) -> str:
        """Create string representation"""
        content = ", ".join(str(k) + ": " + str(self._sequence[k]) for k in self)
        return f"{{{content}}}"

    def update_from_keys_values(
        self, elements: Iterable[tuple[NonNegativeDenseInt, T_value]]
    ) -> None:
        """For each pair of key and value given by *elements*, assign
        value to key."""
        sequence = self._sequence
        for key, value in elements:
            try:
                sequence[key] = value
            except IndexError:
                # Key outside length of collection. Means no value stored so far.
                self.extend_and_set(key, value)

    def update_default(
        self, elements: Iterable[tuple[NonNegativeDenseInt, T_value]]
    ) -> None:
        """For each pair of key and value given by *elements*, assign
        value to key if the collection does not already store a value other
        than the default value for key."""
        default = self._default
        sequence = self._sequence
        for key, value in elements:
            try:
                if sequence[key] == default:  # A gap in the sequence: Assign only here
                    sequence[key] = value
            except IndexError:
                # Key outside length of collection -> no value stored so far -> store
                self.extend_and_set(key, value)


class VertexMappingWrappingSequenceWithNone(
    VertexMappingWrappingSequence[T_value, None],
    VertexMappingByWrapperWithNone[NonNegativeDenseInt, T_value],
):
    """Special case: sequence can/will store None as values"""

    pass


class VertexMappingWrappingSequenceWithoutNone(
    VertexMappingWrappingSequence[T_value, T_value],
    VertexMappingByWrapper[NonNegativeDenseInt, T_value],
):
    """Special case: sequence can/will not store None as values"""

    pass
