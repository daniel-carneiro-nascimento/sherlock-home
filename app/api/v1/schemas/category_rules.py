import re

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from app.rules.categories import (
    CategoryRuleField,
    ExpenseCategory,
)


class CategoryRuleCreate(BaseModel):
    category: ExpenseCategory
    field: CategoryRuleField
    pattern: str = Field(
        min_length=1,
        max_length=2000,
    )
    priority: int = Field(gt=0)
    enabled: bool = True

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


class CategoryRuleUpdate(CategoryRuleCreate):
    pass


class CategoryRuleEnabledUpdate(BaseModel):
    enabled: bool


class CategoryRuleResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    public_id: str
    category: str
    field: str
    pattern: str
    priority: int
    enabled: bool
