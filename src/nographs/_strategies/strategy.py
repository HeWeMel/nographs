from __future__ import annotations

from abc import ABC
from typing import Generic, Any, Optional, Iterable

from nographs._types import T_vertex, T_vertex_id, T_labels


class Strategy(ABC, Generic[T_vertex, T_vertex_id, T_labels]):
    """Base class of the traversal strategies and search strategies of NoGraphs."""

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
        platforms (*CPython* and *PyPy*) and collection types (Gears with different
        *MutableSet* and *MutableMapping* implementations). It behaves roughly as
        follows:

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
        state = dict((k, v) for k, v in self.__dict__.items() if k[0] != "_")
        self._improve_state(state, vertices)
        return str(state)
