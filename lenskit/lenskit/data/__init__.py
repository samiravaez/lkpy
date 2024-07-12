# This file is part of LensKit.
# Copyright (C) 2018-2023 Boise State University
# Copyright (C) 2023-2024 Drexel University
# Licensed under the MIT license, see LICENSE.md for details.
# SPDX-License-Identifier: MIT

from typing import Literal, TypeAlias

FeedbackType: TypeAlias = Literal["explicit", "implicit"]
"Types of feedback supported."

EntityId: TypeAlias = int | str | bytes
"Allowable entity identifier types."

from .dataset import Dataset, from_interactions_df  # noqa: F401, E402
from .matrix import RatingMatrix, sparse_ratings  # noqa: F401, E402
