# database.py

from typing import Optional, List, Dict, Any
from sqlmodel import SQLModel, create_engine, Field, Relationship, Session
from sqlalchemy import Column
from sqlalchemy.engine import Engine
from sqlalchemy.dialects.sqlite import JSON

from datetime import datetime, UTC

class TaskDefinition(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(..., unique=True, index=True)
    input_schema: Dict[str, Any] = Field(sa_column=Column(JSON))
    response_schema: Dict[str, Any] = Field(sa_column=Column(JSON))
    prompt_template: str

    classification_inputs: List["ClassificationInput"] = Relationship(
        back_populates="task_definition"
    )

# Input data model
class ClassificationInput(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    custom_fields: Dict[str, Any] = Field(sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    
    task_definition_id: int = Field(foreign_key="taskdefinition.id")
    task_definition: TaskDefinition = Relationship(back_populates="classification_inputs")
    
    classification_response: Optional["ClassificationResponse"] = Relationship(
        back_populates="classification_input",
        cascade_delete=True
    )

# Output data model
class ClassificationResponse(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    custom_fields: Dict[str, Any] = Field(sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    
    input_id: int = Field(foreign_key="classificationinput.id")
    classification_input: ClassificationInput = Relationship(
        back_populates="classification_response"
    )

# --- Database initialization ---

def init_database(db_path: str) -> Engine:
    """Initialize SQLite database with the necessary tables."""
    engine = create_engine(f"sqlite:///{db_path}")
    SQLModel.metadata.create_all(engine)
    return engine
