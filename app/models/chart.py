from typing import List, Optional
from pydantic import BaseModel, Field, root_validator
from datetime import datetime
from bson import ObjectId

# --------------------------
# Custom ObjectId for Pydantic
# --------------------------
class PyObjectId(ObjectId):
    """
    A custom ObjectId type for Pydantic models to support BSON ObjectIds
    from MongoDB and ensure correct schema generation and validation.
    """

    @classmethod
    def __get_pydantic_json_schema__(cls, schema: dict):
        """
        Override to define how ObjectId should appear in OpenAPI schema.

        Args:
            schema (dict): The original schema.

        Returns:
            dict: Updated schema treating ObjectId as a string.
        """
        schema.update({
            "type": "string",
            "description": "A custom object ID type",
        })
        return schema

    @classmethod
    def __get_validators__(cls):
        """
        Provide validators for Pydantic model usage.

        Yields:
            Callable: The validate method.
        """
        yield cls.validate

    @classmethod
    def validate(cls, v):
        """
        Validate that the input value is a valid ObjectId.

        Args:
            v (Any): The input to validate.

        Returns:
            ObjectId: The validated ObjectId.

        Raises:
            ValueError: If the value is not a valid ObjectId.
        """
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        """
        Update schema field to treat ObjectId as a string type in docs.

        Args:
            field_schema (dict): The schema field to modify.
        """
        field_schema.update(type="string")


# --------------------------
# Chart Node Model
# --------------------------
class ChartModel(BaseModel):
    """
    Represents a node in an organizational chart. Nodes can be either 
    departments or employees, and can have child nodes for hierarchy.
    """

    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")  # MongoDB document ID
    name: str = Field(...)  # Name of the department or employee
    user_id: str = Field(..., description="User ID who created the chart")
    uid: Optional[str] = Field(None)  # Optional unique ID (used in some logic layers)
    node_type: str = Field(..., description="Type of node: 'department' or 'employee'")
    parent_hashid: Optional[str] = Field(None)  # Unique hash of the parent node
    hashid: str = Field(..., description="Unique hash for the node")
    person: Optional[dict] = Field(None, description="Person details if the node_type is 'employee'")
    children: Optional[List["ChartModel"]] = Field(default_factory=list, description="Child nodes of the current node")
    created_at: datetime = Field(default_factory=datetime.utcnow)  # Timestamp of creation
    updated_at: datetime = Field(default_factory=datetime.utcnow)  # Timestamp of last update

    @root_validator(pre=True)
    def check_person_field(cls, values):
        """
        Validator to ensure 'person' details are present if the node_type is 'employee'.

        Args:
            values (dict): The input data for validation.

        Returns:
            dict: Validated values.

        Raises:
            ValueError: If node_type is 'employee' and 'person' is not provided.
        """
        node_type = values.get('node_type')
        person = values.get('person')
        
        if node_type == 'employee' and not person:
            raise ValueError('Person details must be provided for "employee" nodes.')
        
        return values

    class Config:
        """
        Pydantic configuration for the model.
        """
        populate_by_name = True  # Allows setting fields by alias (e.g., _id)
        arbitrary_types_allowed = True  # Allow non-primitive types like ObjectId
        json_encoders = {ObjectId: str}  # Serialize ObjectId as string in responses
