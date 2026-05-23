from pydantic import BaseModel
from typing import Optional, Literal
from fastapi import UploadFile, Form, File

class ChartRequest(BaseModel):
    """
    Request model for creating a chart node via JSON body.

    Attributes:
        name (str): Name of the node (e.g., employee or department).
        node_type (Literal): Type of node, either "employee" or "department". Defaults to "employee".
        parent_hashid (Optional[str]): Hash ID of the parent node, if any.
        uid (Optional[str]): Unique identifier for the user.
        person (Optional[dict]): Additional person metadata (e.g., contact details).
    """
    name: str
    node_type: Literal["employee", "department"] = "employee"
    parent_hashid: Optional[str] = None
    uid: Optional[str] = None
    person: Optional[dict] = None


class ChartRequestFile(BaseModel):
    """
    Request model for creating a chart node via multipart/form-data.

    Attributes:
        name (str): Name of the node.
        node_type (Literal): Type of node ("employee" or "department").
        parent_hashid (Optional[str]): Hash ID of the parent node, if applicable.
        uid (Optional[str]): Unique identifier for the user.
        person (Optional[str]): JSON string representing person data.
    """
    name: str = Form(...)
    node_type: Literal["employee", "department"] = Form("employee")
    parent_hashid: Optional[str] = Form(None)
    uid: Optional[str] = Form(None)
    person: Optional[str] = Form(None)


class ChartUpdateRequest(BaseModel):
    """
    Request model for updating a chart node.

    Attributes:
        name (Optional[str]): New name of the node.
        node_type (Optional[Literal]): Updated node type, if applicable.
        parent_hashid (Optional[str]): Updated parent node reference.
        uid (Optional[str]): Unique identifier of the user.
        person (Optional[dict]): Updated person metadata.
        hashid (Optional[str]): Hash ID of the node being updated.
    """
    name: Optional[str] = None
    node_type: Optional[Literal["employee", "department"]] = None
    parent_hashid: Optional[str] = None
    uid: Optional[str]
    person: Optional[dict] = None
    hashid: Optional[str] = None
