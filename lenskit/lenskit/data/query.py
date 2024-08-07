"""
Recommendation queries.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

from lenskit.data.items import ItemList

from .types import EntityId


@dataclass
class RecQuery:
    """
    Representation of a the data available for a recommendation query.  This is
    generally the available inputs for a recommendation request *except* the set
    of candidate items.

    .. todo::
        Document and test methods for extending the recommendation query with arbitrary
        data to be used by client-provided pipeline components.

    .. todo::
        When LensKit supports context-aware recommendation, this should be extended
        to include context cues.
    """

    user_id: EntityId | None = None
    """
    The user's identifier.
    """
    user_items: ItemList | None = None
    """
    The items from the user's interaction history, with ratings if available.  This
    list is *deduplicated*, like :meth:`~lenskit.data.Dataset.interaction_matrix`,
    rather than a full interaction log.
    """

    @classmethod
    def create(cls, data: QueryInput) -> RecQuery:
        """
        Create a recommenadtion query from an input, filling in available
        components based on the data type.

        Args:
            data:
                Input data to turn into a recommendation query.  If the input is
                already a query, it is returned *as-is* (not copied).

        Returns:
            The recommendation query.
        """
        if data is None:
            return RecQuery()
        elif isinstance(data, RecQuery):
            return data
        elif isinstance(data, ItemList):
            return cls(user_items=data)
        elif isinstance(data, EntityId):
            return cls(user_id=data)
        else:
            raise TypeError(f"invalid input of type {type(data)}")


QueryInput: TypeAlias = RecQuery | EntityId | ItemList | None
"""
Types that can be converted to a query by :meth:`RecQuery.create`.
"""