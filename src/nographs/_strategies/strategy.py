from abc import ABC
from typing import Generic, Any, Optional, Iterable, ClassVar

from nographs._types import T_vertex, T_vertex_id, T_labels


class Strategy(ABC, Generic[T_vertex, T_vertex_id, T_labels]):
    """Base class of the traversal strategies and search strategies of NoGraphs."""

    _state_attrs: ClassVar = list[str]()
    # Public, writable attributes of the class. See _compute_state_attrs().

    _state_attrs_checked: ClassVar = False
    # Marks if results of _compute_state_attrs have already been checked
    # when not running under MyPyC.

    def _improve_state(
        self, state: dict[str, Any], vertices: Optional[Iterable[T_vertex]] = None
    ) -> None:
        """Improve the state description

        :param state: State in current form
        :param vertices: If the strategy can provide additional state data w.r.t. these
            vertices, it will do so.
        """
        pass

    def state_to_str(self, vertices: Optional[Iterable[T_vertex]] = None) -> str:
        """Return a human-readable description of the public state of the strategy as
        a string.

        If an attribute of the traversal is a containers that cannot iterate its
        content, or a collection that guarantees for the validity of stored
        results only for keys that are already visited vertices (see the API reference
        of the traversal classes), its content is only described for vertices given
        as parameter *vertices*.

        Implementation details, not covered by the semantic versioning:

        Currently, the method aims at providing a uniform behaviour over different
        platforms (*CPython*, *PyPy*, and *MyPyC*) and collection types (Gears with
        different *MutableSet* and *MutableMapping* implementations). It behaves
        roughly as follows:

        - A *MutableSet*, e.g. attribute *visited*, is described similar to a *set*,
          but items are sorted lexicographically in their string representations
          (this bridges differences between *CPython* and *PyPy*).

        - Attribute *Paths* is described similar to a *dict* (although keys can contain
          unhashable values, and only paths for the given *vertices* are described).

        - A *MutableMapping*, e.g. attribute *distance*, is described similarly to a
          *dict*, also in cases, where it is not a *dict*, and although the items
          for only the given *vertices* are described.

        :param vertices: If the strategy can provide additional state data w.r.t. these
            vertices, it will do so.
        """
        # Compute the state
        # When compiled with MyPyC, the following computes an empty
        # list even for subclasses with attributes.
        state = dict((k, v) for k, v in self.__dict__.items() if k[0] != "_")
        # print(">>>state_to_str", file=sys.stderr)
        if len(self.__dict__.keys()):  # pragma: no cover  # Not reachable on MyPy
            # __dict__ is filled. So, we are not on MyPyC compiled code.
            # Now, we check, whether _compute_state_attrs works correctly,
            # if not done before.
            if not self._state_attrs_checked:
                type(self)._state_attrs_checked = True
                state_attrs = self._state_attrs
                if list(state.keys()) != state_attrs:
                    raise RuntimeError(
                        "Internal error: attributes do not match"
                        + ".\nClass:"
                        + self.__class__.__name__
                        + ".\nManual list: "
                        + str(state_attrs)
                        + ".\nKeys from __dict__: "
                        + str(list(state.keys()))
                    )
        else:  # pragma: no cover  # Only reachable on MyPy
            # We rely on self._compute_state_attrs for getting the state.
            state = {k: getattr(self, k) for k in self._state_attrs}

        # Compute the optimal human-readable representation of the state attributes
        self._improve_state(state, vertices)
        return str(state)
