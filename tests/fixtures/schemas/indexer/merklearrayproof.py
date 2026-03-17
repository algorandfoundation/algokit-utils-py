from pydantic import BaseModel, ConfigDict, Field


class MerkleArrayProofSchema(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)

    path: list[str] | None = Field(default=None, alias="path")
    hash_factory: "HashFactorySchema | None" = Field(default=None, alias="hash-factory")
    tree_depth: int | None = Field(default=None, alias="tree-depth")
