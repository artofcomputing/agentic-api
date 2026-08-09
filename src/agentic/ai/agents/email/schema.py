from pydantic import BaseModel, Field


class EmailRubricUpdate(BaseModel):
    """Schema for updating an email's rubric score."""

    public_id: str = Field(..., alias="publicId")
    rubric: int = Field(
        ...,
        description="The score/rubric assigned to the email, representing its importance rank.",
    )

    model_config = {
        "populate_by_name": True,
    }
