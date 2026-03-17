from pydantic import BaseModel, ConfigDict, Field


class StateProofFieldsSchema(BaseModel):
    """\[sp\] represents a state proof.

    Definition:
    crypto/stateproof/structs.go : StateProof"""

    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    sig_commit: str | None = Field(default=None, alias="sig-commit")
    signed_weight: int | None = Field(default=None, alias="signed-weight")
    sig_proofs: "MerkleArrayProofSchema | None" = Field(default=None, alias="sig-proofs")
    part_proofs: "MerkleArrayProofSchema | None" = Field(default=None, alias="part-proofs")
    salt_version: int | None = Field(default=None, alias="salt-version")
    reveals: "list[StateProofRevealSchema] | None" = Field(default=None, alias="reveals")
    positions_to_reveal: list[int] | None = Field(default=None, alias="positions-to-reveal")
