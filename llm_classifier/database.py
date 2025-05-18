# database.py

from typing import Optional, List
from sqlmodel import SQLModel, create_engine, Field, Relationship, Session, select
from sqlalchemy.engine import Engine
from datetime import datetime, UTC, date

from llm_classifier.prompt import Input, Response

class InputType(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(..., unique=True, index=True)

    classification_inputs: List["ClassificationInput"] = Relationship(
        back_populates="input_type"
    )

# Input data model
class ClassificationInput(Input, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    processed_date: date = Field(default_factory=lambda: datetime.now(UTC))

    input_type_id: Optional[int] = Field(default=None, foreign_key="inputtype.id")

    classification_response: Optional["ClassificationResponse"] = Relationship(
        back_populates="classification_input",
        cascade_delete=True
    )
    input_type: Optional[InputType] = Relationship(
        back_populates="classification_inputs"
    )

# Output data model
class ClassificationResponse(Response, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    input_id: Optional[int] = Field(default=None, foreign_key="classificationinput.id")
    classification_input: Optional[ClassificationInput] = Relationship(
        back_populates="classification_response"
    )

# --- Database initialization ---

def init_database(db_path: str) -> Engine:
    """Initialize SQLite database with the necessary table."""
    engine = create_engine(f"sqlite:///{db_path}")
    SQLModel.metadata.create_all(engine)
    return engine


def seed_input_types(
    session: Session,
    input_types: List[str]
) -> None:
    for itype in input_types:
        if not session.exec(select(InputType).where(InputType.name == itype)).first():
            session.add(InputType(name=itype))
    session.commit()