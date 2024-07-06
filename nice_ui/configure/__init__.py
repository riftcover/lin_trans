from typing import Dict, TypedDict


class ModelInfo(TypedDict):
    status: int
    model_name: str


ModelDict = Dict[str, ModelInfo]
