import nographs as nog  # noqa: F401 (used in doctests, undetected by flake 8)

# noinspection PyProtectedMember
import nographs._gear_collections as gear_collections  # noqa: F401 (used by doctests)


class CallToPrivateDummyFunctionality:
    """
    The following classes are library private. Only NoGraphs is expected the
    see and use them. And NoGraphs is expected to never call their methods. Thus,
    if a call ever happens, this would be unexpected and probly due to an error
    in NoGraphs. An assertion error is to be raised to signal this.

    >>> gettable_settable_for_gear_assert_no_call = (
    ...     # noinspection PyProtectedMember
    ...     gear_collections._GettableSettableForGearAssertNoCall[int, int, int]()
    ... )

    >>> gettable_settable_for_gear_assert_no_call.__getitem__(0)
    Traceback (most recent call last):
    AssertionError: Call to a method of this object is not expected to ever happen

    >>> gettable_settable_for_gear_assert_no_call.__setitem__(0, 0)
    Traceback (most recent call last):
    AssertionError: Call to a method of this object is not expected to ever happen

    >>> # noinspection PyProtectedMember
    >>> _vertex_sequence_wrapper_assert_no_call = (
    ...     # noinspection PyProtectedMember
    ...     gear_collections._VertexSequenceWrapperAssertNoCall[int, int, int]()
    ... )

    >>> _vertex_sequence_wrapper_assert_no_call.sequence()
    Traceback (most recent call last):
    AssertionError: Call to a method of this object is not expected to ever happen

    >>> _vertex_sequence_wrapper_assert_no_call.default()
    Traceback (most recent call last):
    AssertionError: Call to a method of this object is not expected to ever happen

    >>> _vertex_sequence_wrapper_assert_no_call.extend_and_set(0, 0)
    Traceback (most recent call last):
    AssertionError: Call to a method of this object is not expected to ever happen

    >>> _vertex_sequence_wrapper_assert_no_call.update_from_keys(0)
    Traceback (most recent call last):
    AssertionError: Call to a method of this object is not expected to ever happen

    >>> _vertex_sequence_wrapper_assert_no_call.index_and_bit_method()
    Traceback (most recent call last):
    AssertionError: Call to a method of this object is not expected to ever happen

    >>> _vertex_sequence_wrapper_assert_no_call.update_from_keys_values(0)
    Traceback (most recent call last):
    AssertionError: Call to a method of this object is not expected to ever happen

    >>> _vertex_sequence_wrapper_assert_no_call.update_default(0)
    Traceback (most recent call last):
    AssertionError: Call to a method of this object is not expected to ever happen

    >>> # noinspection PyProtectedMember
    >>> _vertex_sequence_wrapper_assert_no_call._from_iterable(0)
    Traceback (most recent call last):
    AssertionError: Call to a method of this object is not expected to ever happen
    """


# --------- edge cases of the functionality -----------


class GearCollectionFunctionalityMainlyOnlyForAppCode:
    """
    Test the functionality, that NoGraphs inlines, does not use itself,
    and that is mainly there for application code only.
    Exception: see documentation of VertexSequenceWrapperForSetAndMapping.

    >>> list_factory = lambda: list()
    >>> ws = nog.VertexSetWrappingSequenceNoBitPacking(
    ...     list_factory, 1024, False, [1, 3])
    >>> ws
    {1, 3}
    >>> len(ws.sequence())
    1026
    >>> "a" in ws  # Case "is not instance(key, int)"
    False
    >>> 1026 in ws  # Case "IndexError"
    False
    >>> 1 in ws  # Case "return True"
    True
    >>> 2 in ws  # Case "return False"
    False
    >>> len(ws)
    2
    >>> ws.add(2)
    >>> ws
    {1, 2, 3}
    >>> ws.discard(3)
    >>> ws
    {1, 2}
    >>> ws.discard(3)
    >>> ws.add(1026)  # Case "IndexError"
    >>> ws
    {1, 2, 1026}
    >>> len(ws.sequence())
    2051
    >>> ws.discard(2051)   # Case "IndexError"
    >>> ws2 = nog.VertexSetWrappingSequenceNoBitPacking(
    ...     list_factory, 1024, False, [4])
    >>> ws.__or__(ws2)  # Calls _from_iterable(iterable) to create new set
    {1, 2, 4, 1026}

    About the previous test:
    MyPyC: "ws | ws2" raises:
      TypeError: unsupported operand type(s) for |:
      'VertexSetWrappingSequenceBitPacking' and
      'VertexSetWrappingSequenceBitPacking'
    I expect this to work. Maybe an error in typeshed?

    >>> list_factory = lambda: list()
    >>> ws = nog.VertexSetWrappingSequenceBitPacking(
    ...     list_factory, 128, False, [1, 3])
    >>> ws
    {1, 3}
    >>> len(ws.sequence())
    129
    >>> "a" in ws  # Case "is not instance(key, int)"
    False
    >>> 129*8 in ws  # Case "IndexError"
    False
    >>> 1 in ws  # Case "return True"
    True
    >>> 2 in ws  # Case "return False"
    False
    >>> len(ws)
    2
    >>> ws.add(2)
    >>> ws
    {1, 2, 3}
    >>> ws.discard(3)
    >>> ws
    {1, 2}
    >>> ws.discard(3)
    >>> ws.add(129*8)  # Case "IndexError"
    >>> ws
    {1, 2, 1032}
    >>> len(ws.sequence())
    258
    >>> ws.discard(258*8)   # Case "IndexError"
    >>> ws2 = nog.VertexSetWrappingSequenceBitPacking(
    ...     list_factory, 128, False, [4])
    >>> ws.__or__(ws2)  # Calls _from_iterable(iterable) to create new set
    {1, 2, 4, 1032}

    About the previous test:
    MyPyC: "ws | ws2" raises:
      TypeError: unsupported operand type(s) for |:
      'VertexSetWrappingSequenceBitPacking' and
      'VertexSetWrappingSequenceBitPacking'
    I expect this to work. Maybe an error in typeshed?

    >>> list_factory = lambda: list[float]()
    >>> ws = nog.VertexMappingWrappingSequence(
    ...     list_factory, float("infinity"), 1024, False, [(0, 0), (2, 2)])
    >>> ws.default()  # Gap marker / default value of the mapping emulation
    inf
    >>> ws.sequence()[:5]  # Given values are set, others are gap-marker / default
    [0, inf, 2, inf, inf]
    >>> len(ws.sequence())
    1025
    >>> ws
    {0: 0, 2: 2}
    >>> ws.update_default([(1, 1), (2, 2.5), (3, 3)])  # key 2 has value ->ignore change
    >>> ws
    {0: 0, 1: 1, 2: 2, 3: 3}
    >>> ws.update_default([(1025, 1025)])  # Gives IndexError -> extend_and_set
    >>> ws
    {0: 0, 1: 1, 2: 2, 3: 3, 1025: 1025}
    >>> ws[0]
    0
    >>> ws[4]  # Gives KeyError because gap marker
    Traceback (most recent call last):
    KeyError
    >>> ws[2048]  # Gives KeyError because outside
    Traceback (most recent call last):
    KeyError
    >>> "hallo" in ws  # str is outside key type int
    False
    >>> len(ws)
    5
    >>> del ws[1]
    >>> ws
    {0: 0, 2: 2, 3: 3, 1025: 1025}
    >>> len(ws.sequence())
    2050
    >>> ws[2050] = 2050
    >>> ws
    {0: 0, 2: 2, 3: 3, 1025: 1025, 2050: 2050}
    """


class GearCollectionTestRemainingCasesForUseByLibrary:
    """
    An example that uses VertexMappingWrappingSequenceWithNone
    (and calls methods of VertexMappingWrappingSequenceWithNone) with distances is
    already given in the docs.
    Missing, and given here, is an example that uses VertexSetWrappingSequence
    (calls methods of VertexSetByWrapper)
    and VertexMappingWrappingSequenceWithoutNone
    (calls methods of VertexMappingByWrapper with case without None).

    Fehlt: Aufruf von access_paths_to_vertex_mapping_expect_none, wobei unter dem
    Mapping keine VertexMappingByWrapperWithNone sondern eine VertexMappingByWrapper
    liegt. Ich dachte, predecessor von Paths nutzt ...expect_none, und wenn ein
    Array darunter liegt, wird von GearArrays... dann VertexMappingByWrapper und nicht
    VertexMappingByWrapperWithNone genutzt...

    >>> def next_vertices(i, _):
    ...     yield i+1
    >>> t = nog.TraversalDepthFirstFlex(
    ...     nog.vertex_as_id, nog.GearForIntVerticesAndIDsAndCFloats(), next_vertices
    ... )
    >>> t.paths.debug = True
    >>> v = t.start_from(0, build_paths=True, compute_depth = True).go_to(5)
    >>> t.paths[5]
    (0, 1, 2, 3, 4, 5)
    >>> t.depth
    5
    """


class GearCollectionTestsForDoNotCallCases:
    """
    A "real" set has no wrapper. So, the index_and_bit_method returned by
    nog.access_to_vertex_set is not intended to be called.
    >>> c = set()
    >>> res = gear_collections.access_to_vertex_set(c)
    >>> is_wrapper, gettable_settable, wrapper, uses_bits, index_and_bit_method = res
    >>> index_and_bit_method(0, 0)
    Traceback (most recent call last):
    AssertionError: Call to a method of this object is not expected to ever happen
    """
