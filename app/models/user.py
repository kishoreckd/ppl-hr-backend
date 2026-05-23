from typing import List, Optional
from pydantic import BaseModel, Field, root_validator
from datetime import datetime
from bson import ObjectId

# -------------------------
# Custom ObjectId Type
# -------------------------
class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic validation and serialization."""

    @classmethod
    def __get_pydantic_json_schema__(cls, schema: dict):
        """
        Modify the Pydantic schema for documentation.

        Args:
            schema (dict): Existing schema dictionary.

        Returns:
            dict: Updated schema with string type and description.
        """
        schema.update({
            "type": "string",
            "description": "A custom object ID type",
        })
        return schema

    @classmethod
    def __get_validators__(cls):
        """
        Yield validators for Pydantic to use.

        Returns:
            Callable: ObjectId validation method.
        """
        yield cls.validate

    @classmethod
    def validate(cls, v):
        """
        Validate ObjectId.

        Args:
            v (Any): The value to validate.

        Returns:
            ObjectId: Validated ObjectId instance.

        Raises:
            ValueError: If the input is not a valid ObjectId.
        """
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        """
        Modify the schema used in OpenAPI generation.

        Args:
            field_schema (dict): Field schema to update.
        """
        field_schema.update(type="string")

# -------------------------
# Chart Model
# -------------------------
class UserModel(BaseModel):
    """
    Data model for organization chart nodes.

    Attributes:
        id (Optional[PyObjectId]): Unique database identifier.
        name (str): Name of the chart node.
        user_id (str): ID of the user who created the chart.
        uid (Optional[str]): Optional unique user identifier.
        node_type (str): Type of the node (e.g., 'department', 'employee').
        parent_hashid (Optional[str]): Hash ID of the parent node.
        hashid (str): Unique identifier for this node.
        person (Optional[dict]): Details of the person (if node_type is 'employee').
        children (Optional[List[ChartModel]]): List of child nodes.
        created_at (datetime): Time of creation.
        updated_at (datetime): Last updated time.
    """

    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    name: str = Field(...)
    user_id: str = Field(..., description="User ID who created the chart")
    uid: Optional[str] = Field(None)
    node_type: str = Field(..., description="Type of node: 'department' or 'employee'")
    parent_hashid: Optional[str] = Field(None)
    hashid: str = Field(..., description="Unique hash for the node")
    person: Optional[dict] = Field(None, description="Person details if the node_type is 'employee'")
    children: Optional[List["ChartModel"]] = Field(default_factory=list, description="Child nodes of the current node")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @root_validator(pre=True)
    def check_person_field(cls, values):
        """
        Validator to ensure 'person' field is required if node_type is 'employee'.

        Args:
            values (dict): Field values.

        Returns:
            dict: Validated field values.

        Raises:
            ValueError: If node_type is 'employee' but 'person' is not provided.
        """
        node_type = values.get('node_type')
        person = values.get('person')

        if node_type == 'employee' and not person:
            raise ValueError('Person details must be provided for "employee" nodes.')

        return values

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}  # Ensure ObjectId is converted to str in JSON output
