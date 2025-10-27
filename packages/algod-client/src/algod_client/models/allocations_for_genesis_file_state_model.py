from __future__ import annotations

from dataclasses import dataclass, field

from algokit_common.serde import wire


@dataclass(slots=True)
class AllocationsForGenesisFileStateModel:
    algo: int = field(
        metadata=wire("algo"),
    )
    onl: int = field(
        metadata=wire("onl"),
    )
    sel: str | None = field(
        default=None,
        metadata=wire("sel"),
    )
    stprf: str | None = field(
        default=None,
        metadata=wire("stprf"),
    )
    vote: str | None = field(
        default=None,
        metadata=wire("vote"),
    )
    vote_fst: int | None = field(
        default=None,
        metadata=wire("voteFst"),
    )
    vote_kd: int | None = field(
        default=None,
        metadata=wire("voteKD"),
    )
    vote_lst: int | None = field(
        default=None,
        metadata=wire("voteLst"),
    )
