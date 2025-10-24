from __future__ import annotations

from typing_extensions import NotRequired, TypedDict


class StateSchemaDto(TypedDict):
    nui: int
    nbs: int


class AssetParamsDto(TypedDict, total=False):
    t: int
    dc: int
    df: bool
    un: str
    an: str
    au: str
    am: bytes
    m: bytes
    f: bytes
    c: bytes
    r: bytes


class HashFactoryDto(TypedDict, total=False):
    t: int


class MerkleArrayProofDto(TypedDict, total=False):
    pth: list[bytes]
    hsh: HashFactoryDto
    td: int


class MerkleSignatureVerifierDto(TypedDict, total=False):
    cmt: bytes
    lf: int


class ParticipantDto(TypedDict, total=False):
    p: MerkleSignatureVerifierDto
    w: int


class FalconVerifierDto(TypedDict, total=False):
    k: bytes


class FalconSignatureStructDto(TypedDict, total=False):
    sig: bytes
    idx: int
    prf: MerkleArrayProofDto
    vkey: FalconVerifierDto


class SigslotCommitDto(TypedDict, total=False):
    s: FalconSignatureStructDto
    l: int  # noqa: E741


class RevealEntryDto(TypedDict, total=False):
    s: SigslotCommitDto
    p: ParticipantDto


RevealMapDto = dict[int, RevealEntryDto]


class StateProofDto(TypedDict, total=False):
    c: bytes
    w: int
    S: MerkleArrayProofDto
    P: MerkleArrayProofDto
    v: int
    pr: list[int]
    r: RevealMapDto


class StateProofMessageDto(TypedDict, total=False):
    b: bytes
    v: bytes
    P: int
    f: int
    l: int  # noqa: E741


class HeartbeatProofDto(TypedDict, total=False):
    s: bytes
    p: bytes
    p2: bytes
    p1s: bytes
    p2s: bytes


class HeartbeatDto(TypedDict, total=False):
    a: bytes
    prf: HeartbeatProofDto
    sd: bytes
    vid: bytes
    kd: int


class MultisigSubsigDto(TypedDict):
    pk: bytes
    s: NotRequired[bytes]


class MultisigDto(TypedDict):
    thr: int
    v: int
    subsig: NotRequired[list[MultisigSubsigDto]]


class LogicSignatureDto(TypedDict):
    l: bytes  # noqa: E741
    arg: NotRequired[list[bytes]]
    sig: NotRequired[bytes]
    msig: NotRequired[MultisigDto]


class TransactionDtoBase(TypedDict):
    type: str
    snd: bytes
    fv: int
    lv: int


class TransactionDto(TransactionDtoBase, total=False):
    fee: int
    gen: str
    gh: bytes
    note: bytes
    lx: bytes
    rekey: bytes
    grp: bytes
    amt: int
    rcv: bytes
    close: bytes
    xaid: int
    aamt: int
    arcv: bytes
    aclose: bytes
    asnd: bytes
    caid: int
    apar: AssetParamsDto
    faid: int
    fadd: bytes
    afrz: bool
    apid: int
    apan: int
    apap: bytes
    apsu: bytes
    apgs: StateSchemaDto
    apls: StateSchemaDto
    apaa: list[bytes]
    apat: list[bytes]
    apfa: list[int]
    apas: list[int]
    apep: int
    votekey: bytes
    selkey: bytes
    votefst: int
    votelst: int
    votekd: int
    sprfkey: bytes
    nonpart: bool
    hb: HeartbeatDto
    sptype: int
    sp: StateProofDto
    spmsg: StateProofMessageDto
