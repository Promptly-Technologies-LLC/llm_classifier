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

# --- EAV Models for Dynamic User-Defined Input Models ---

class DynamicModel(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(..., unique=True, index=True)
    description: Optional[str] = None
    fields: List["DynamicField"] = Relationship(back_populates="model")
    values: List["DynamicValue"] = Relationship(back_populates="model")
    prompts: List["DynamicPrompt"] = Relationship(back_populates="model", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

class DynamicField(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    model_id: int = Field(foreign_key="dynamicmodel.id")
    field_name: str
    field_type: str  # e.g., 'string', 'integer', etc.
    model: DynamicModel = Relationship(back_populates="fields")
    values: List["DynamicValue"] = Relationship(back_populates="field")

class DynamicValue(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    model_id: int = Field(foreign_key="dynamicmodel.id")
    field_id: int = Field(foreign_key="dynamicfield.id")
    value: str  # Store as string, cast as needed in code
    user_id: Optional[int] = None
    model: DynamicModel = Relationship(back_populates="values")
    field: DynamicField = Relationship(back_populates="values")

class DynamicPrompt(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    model_id: int = Field(foreign_key="dynamicmodel.id")
    name: str = Field(..., index=True)
    template: str  # The prompt template string
    description: Optional[str] = None
    model: DynamicModel = Relationship(back_populates="prompts")

# --- Helper methods for dynamic models ---

def get_dynamic_model_fields(session, model_id):
    """Fetch fields for a given DynamicModel."""
    return session.exec(
        select(DynamicField).where(DynamicField.model_id == model_id)
    ).all()

def collect_dynamic_input(fields):
    """Prompt user for input for each field (console input for demo)."""
    input_data = {}
    for field in fields:
        value = input(f"Enter value for {field.field_name} ({field.field_type}): ")
        input_data[field.field_name] = value
    return input_data

def store_dynamic_input(session, model_id, user_id, input_data):
    """Store user input as DynamicValue entries."""
    fields = get_dynamic_model_fields(session, model_id)
    field_map = {f.field_name: f for f in fields}
    for name, value in input_data.items():
        field = field_map.get(name)
        if field:
            dv = DynamicValue(
                model_id=model_id,
                field_id=field.id,
                value=str(value),
                user_id=user_id
            )
            session.add(dv)
    session.commit()

def build_dynamic_prompt(model, fields, values):
    """Build a prompt template dynamically from fields and values."""
    prompt = f"Input for model: {model.name}\n"
    for field in fields:
        val = values.get(field.field_name, "")
        prompt += f"{field.field_name}: {val}\n"
    return prompt

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