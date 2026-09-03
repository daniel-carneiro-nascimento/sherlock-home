import re

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


class MerchantAliasCreate(BaseModel):
    canonical_name: str = Field(
        min_length=1,
        max_length=255,
    )
    pattern: str = Field(
        min_length=1,
        max_length=2000,
    )
    priority: int = Field(gt=0)
    enabled: bool = True

    @field_validator("canonical_name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = " ".join(value.split()).strip()

        if not normalized:
            raise ValueError(
                "Canonical name must not be empty."
            )

        return normalized.upper()

    @field_validator("pattern")
    @classmethod
    def validate_regex(cls, value: str) -> str:
        try:
            re.compile(value)
        except re.error as exc:
            raise ValueError(
                "Invalid regular expression."
            ) from exc

        return value


class MerchantAliasUpdate(MerchantAliasCreate):
    pass


class MerchantAliasEnabledUpdate(BaseModel):
    enabled: bool


class MerchantAliasResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    public_id: str
    canonical_name: str
    pattern: str
    priority: int
    enabled: bool
