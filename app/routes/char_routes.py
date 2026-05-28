from datetime import datetime
from hashlib import sha256
from platform import node
from bson import ObjectId  
from fastapi import APIRouter, Header, Depends, UploadFile , Form , File, UploadFile
from fastapi.responses import JSONResponse , StreamingResponse
from app.database import get_db
from app.utils.jwt import verify_access_token, verify_share_token
from app.models.chart import ChartModel
from app.schema.chart_schema import ChartRequest ,ChartUpdateRequest ,ChartRequestFile
from bson import ObjectId
from fastapi.responses import JSONResponse ,FileResponse
from typing import  Optional
from app.schema.user_schema import verify_BEARER_TOKEN
import hashlib
from typing import Optional, Literal
import base64
from io import BytesIO
from app.config import settings
import os
import json

# from fastapi import FastAPI, File, UploadFile

# Initialize the router
router = APIRouter()


# ----------------------------------------get all charts----------------------------------------------------------

# Serialize MongoDB data, handling ObjectId and datetime
def get_all_serialize_mongo_data(data):
    if isinstance(data, list):
        return [get_all_serialize_mongo_data(item) for item in data]
    elif isinstance(data, dict):
        serialized = {}
        for key, value in data.items():
            if isinstance(value, ObjectId):
                serialized[key] = str(value)  # Serialize ObjectId to string
            elif isinstance(value, datetime):
                serialized[key] = value.isoformat()  # Serialize datetime to ISO format
            elif isinstance(value, dict) or isinstance(value, list):
                serialized[key] = get_all_serialize_mongo_data(value)  # Recursively serialize
            else:
                serialized[key] = value
        return serialized
    return data

# Function to calculate totals of employees and departments recursively
def calculate_totals(node):
    total_employees = 0
    total_departments = 0

    # Skip main parent node for department count
    if node.get("node_type") == "department" and node.get("parent_hashid") is not None:
        total_departments += 1
    elif node.get("node_type") == "employee" and node.get("parent_hashid") is not None:
        total_employees += 1

    for child in node.get("children", []):
        child_employees, child_departments = calculate_totals(child)
        total_employees += child_employees
        total_departments += child_departments

    return total_employees, total_departments


# Function to extract departments and employees from the chart recursively
def extract_lists(node, parent_node):
    if node.get("node_type") == "department" and node.get("parent_hashid") is not None:
        parent_node["department"].append({
            "hashid": node["hashid"],
            "name": node["name"],
        })
    elif node.get("node_type") == "employee" and node.get("parent_hashid") is not None:
        # Check if the 'role' exists in the 'person' field before adding it
        employee_data = {
            "hashid": node["hashid"],
            "name": node["name"]
        }
        if "img" in node.get("person", {}): 
            employee_data["img"] = node["person"]["img"]
        parent_node["employees"].append(employee_data)

    for child in node.get("children", []):
        extract_lists(child, parent_node)


@router.get("/", dependencies=[Depends(verify_BEARER_TOKEN)])
async def get_user_charts(
    page: int,
    limit: int,
    User_Token: str = Header(None),
    db=Depends(get_db)
):
    """
    API endpoint to retrieve paginated charts created by a specific user with pagination sent as query parameters.
    """
    # Verify the access token
    payload_response = verify_access_token(User_Token)  # Ensure this is awaited
    if isinstance(payload_response, JSONResponse):
        return payload_response

    user_id = payload_response.get("id")
    try:
        user_id = ObjectId(user_id)
    except Exception:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "message": "Invalid user ID format.",
                "data": {"error": "Invalid user ID format."},
            },
        )

    try:
        # Calculate pagination offsets
        skip = (page - 1) * limit
        total_count = db["charts"].count_documents({"user_id": str(user_id)})

        # If no charts exist for the user
        if total_count == 0:
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "message": "No charts found for the user.",
                    "data": {
                        "nodes": [],
                        "total_count": total_count,
                        "page": page,
                        "limit": limit,
                    },
                },
            )

        # Fetch paginated charts
        charts_cursor = db["charts"].find({"user_id": str(user_id)}).skip(skip).limit(limit)
        charts = await charts_cursor.to_list(length=limit)
        nodes = []  # List to store the required fields for response

        if charts:
            # Process each chart to calculate additional data and convert fields
            for chart in charts:
                # Serialize the chart data
                chart = get_all_serialize_mongo_data(chart)

                # Calculate totals recursively for employees and departments
                total_employees, total_departments = calculate_totals(chart)

                # Extract required fields and create the desired node structure
                node = {
                    "uid": chart.get("uid", ""),
                    "name": chart.get("name", ""),
                    "hashid": chart.get("hashid", ""),
                    "departments_count": total_departments,
                    "employees_count": total_employees,
                    "department": [],
                    "employees": []
                }

                # Extract departments and employees recursively
                extract_lists(chart, node)

                # Append node to nodes list
                nodes.append(node)
                print(f"Processed node: {node}")

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Charts retrieved successfully.",
                "data": {
                    "nodes": nodes,
                    "page": page,
                    "limit": limit,
                },
            },
        )

    except Exception as e:
        print(f"Error during processing: {str(e)}")  # Log the error for debugging
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"An error occurred: {str(e)}",
                "data": {"error": str(e)},
            },
        )


# ------------------Create charts ---------------------------------------------------------------

# Define the folder to store images
UPLOAD_FOLDER = 'images'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
    

async def save_image(file: UploadFile, uid: str, hashid: str, name: str) -> str:
    user_folder = os.path.join(UPLOAD_FOLDER, uid)
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)

    original_filename = file.filename or ""
    image_filename = f"{hashid}{name}{os.path.splitext(original_filename)[-1]}.enc"
    # image_filename = f"{hashid}_{name}.enc"
    file_path = os.path.join(user_folder, image_filename)
    img_content = await file.read()
    with open(file_path, "wb") as f:
        f.write(img_content)
    relative_path = os.path.join(uid,image_filename)
    return relative_path

# Endpoint for creating a chart node with the image
@router.post("/create", dependencies=[Depends(verify_BEARER_TOKEN)])
async def create_chart_node(
    name: str = Form(...),
    node_type: Literal["employee", "department"] = Form("employee"),
    parent_hashid: Optional[str] = Form(None),
    person: Optional[str] = Form(None),
    uid: Optional[str] = Form(None),
    User_Token: str = Header(None),
    db=Depends(get_db),
    person_img: Optional[UploadFile] = File(None),
):
    """API endpoint to create a node in the chart with support for dynamic nested children and image upload."""
    # Verify access token
    payload_response = verify_access_token(User_Token)
    if isinstance(payload_response, JSONResponse):
        return payload_response

    user_id = payload_response.get("id")

    try:
        user_id = str(ObjectId(user_id))
    except Exception:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "Invalid user ID format."},
        )

    # Ensure person details for employee nodes
    if node_type == "employee" and not person:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "Person details must be provided for employee nodes."},
        )

    if person:
        try:
            person = json.loads(person)
        except json.JSONDecodeError:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Invalid format for person details. Must be a valid JSON string."},
            )

    try:
        # Generate hashid for the new node
        hashid = hashlib.sha256(f"{name}{datetime.utcnow()}".encode()).hexdigest()[:10]
        image_path = None
        new_uid = None

        # Check for existing `uid` associated with the `user_id`
        if uid:
            existing_chart = await db["charts"].find_one({"uid": uid, "user_id": str(user_id)})
            if not existing_chart:
                raise ValueError("No chart with the given UID exists for this user.")

            # Create the new child node
            new_child = {
                "name": name,
                "node_type": node_type,
                "user_id": user_id,
                "hashid": hashid,
                "parent_hashid": parent_hashid,
                "person": person,
                "children": [],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }

            if person_img:
                try:
                    image_path = await save_image(person_img, uid, hashid, name)
                    print(image_path)
                    image_path = os.path.normpath(image_path).replace("\\", "/")
                    person["img"] = image_path
                except Exception as e:
                    return JSONResponse(
                        status_code=500,
                        content={"status": "error", "message": f"Error saving image: {str(e)}"},
                    )

            if parent_hashid:
                success = await add_child_to_parent_recursive(uid, parent_hashid, new_child, db)
                if not success:
                    raise ValueError("Parent node not found or could not update children.")
            else:
                raise ValueError("Parent hashid must be provided when UID is given.")
        else:
            # Create a new chart with a unique UID
            new_uid = hashlib.sha256(f"{user_id}{datetime.utcnow()}".encode()).hexdigest()[:10]
            chart_data = {
                "name": name,
                "uid": new_uid,
                "node_type": node_type,
                "user_id": str(user_id),
                "hashid": hashid,
                "parent_hashid": None,
                "person": person,
                "children": [],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }

            if person_img:
                try:
                    image_path = await save_image(person_img, new_uid, hashid, name)
                    image_path = os.path.normpath(image_path).replace("\\", "/")
                    person["img"] = image_path
                except Exception as e:
                    return JSONResponse(
                        status_code=500,
                        content={"status": "error", "message": f"Error saving image: {str(e)}"},
                    )

            result = await db["charts"].insert_one(chart_data)
            if not result.acknowledged:
                raise ValueError("Failed to create chart node.")

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Chart node created successfully.",
                "data": {
                    "name": name,
                    "node_type": node_type,
                    "user_id": str(user_id),
                    "hashid": hashid,
                    "uid": new_uid if not uid else uid,
                    "parent_hashid": parent_hashid,
                    "person": person,
                    "children": [],
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                },
            },
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"An error occurred: {str(e)}",
                "data": {"error": str(e)},
            },
        )


async def add_child_to_parent_recursive(uid, parent_hashid, new_child, db):
    """
    Recursively traverse the tree to add a child to the node with the given parent_hashid in the chart with the specified uid.
    """
    # Fetch the chart document using the provided uid
    document = await db["charts"].find_one({"uid": uid})
    if not document:
        return None  # Chart not found

    # Helper function to recursively add a child
    def add_child_recursive(node):
        if node.get("hashid") == parent_hashid:
            # Ensure 'children' exists before appending
            if "children" not in node:
                # print("yeess")
                node["children"] = []
            node["children"].append(new_child)
            return True

        # Recurse into the children
        for child in node.get("children", []):
            if add_child_recursive(child):
                return True

        return False

    # Attempt to add the child
    if add_child_recursive(document):
        # Update the document in the database with the new child added
        update_result = await db["charts"].replace_one({"_id": document["_id"]}, document)
        if update_result.modified_count > 0:
            return True

    return False

    
   
# ----------------------------Delete chart -----------------------------------------------------------------

from datetime import datetime
import os

async def delete_node_recursive(uid, node_hashid, db):
    """
    Recursively traverse the tree to delete the node and its children,
    returning the updated parent node or None.
    """
    # Fetch the chart document using the uid
    print(f"Fetching chart with UID: {uid}")
    document = await db["charts"].find_one({"uid": uid})
    if not document:
        print(f"Chart with UID: {uid} not found.")
        return None  # Return None if document is not found
    print(f"Found chart document with UID: {uid}")

    # Helper function to recursively find and delete a node
    def delete_node(node, parent_node=None):
        print(f"Checking node with hashid: {node.get('hashid')} against {node_hashid}")
        if node.get("hashid") == node_hashid:
            print(f"Found node with hashid: {node_hashid}")
            # If the node to delete is found, delete it
            if parent_node:
                # Remove the node from the parent's children list
                parent_node["children"] = [
                    child for child in parent_node.get("children", [])
                    if child.get("hashid") != node_hashid
                ]
                print(f"Removed node with hashid: {node_hashid} from parent")
            else:
                # If no parent node, it means we're deleting the root node (no parent)
                print(f"Deleting root node with hashid: {node_hashid}")
                return True, None  # Return True and None as there is no parent to update

            # Check if the 'img' key exists in the node and delete the associated image
            if "img" in node.get("person", {}):
                image_path = os.path.join(UPLOAD_FOLDER, node["person"]["img"])
                if os.path.exists(image_path):
                    os.remove(image_path)
                    print(f"Deleted image: {image_path}")
                else:
                    print(f"Image not found: {image_path}")
            else:
                print(f"No image associated with node hashid: {node_hashid}")

            # Recursively delete any child nodes of the node being deleted
            for child in node.get("children", []):
                delete_node(child, node)
            return True, parent_node  # Return True and the updated parent node

        # Recurse into the children if the node is not found yet
        for child in node.get("children", []):
            found, updated_parent = delete_node(child, node)
            if found:
                return found, updated_parent

        return False, None

    # Attempt to delete the node
    print(f"Attempting to delete node with hashid: {node_hashid}")
    found, parent_node = delete_node(document)
    if found:
        # Handle static fields deletion if the root node is being deleted
        if parent_node is None:  # Root node deletion
            print(f"Deleting static fields associated with chart UID: {uid}")
            
            # Debug: Check static fields before deletion
            static_fields_before = await db["charts_access"].find({"chart_uid": uid}).to_list(None)
            print(f"Static fields before deletion: {len(static_fields_before)} records")
            for static_field in static_fields_before:
                print(f"Static field found: {static_field}")  # Debug each static field

            static_deletion_result = await db["charts_access"].delete_many({"chart_uid": uid})
            print(f"Static fields deleted: {static_deletion_result.deleted_count}")

            # Debug: Check static fields after deletion
            static_fields_after = await db["charts_access"].find({"chart_uid": uid}).to_list(None)
            print(f"Static fields after deletion: {len(static_fields_after)} records")

            # Delete the chart itself
            chart_deletion_result = await db["charts"].delete_one({"_id": document["_id"]})
            if chart_deletion_result.deleted_count > 0:
                print(f"Chart with UID: {uid} deleted successfully")
                return {
                    "message": f"Chart and {static_deletion_result.deleted_count} static fields deleted successfully"
                }
            else:
                print(f"Failed to delete chart with UID: {uid}")
        else:
            # If it's not the root node, update the chart with the modified parent node
            print(f"Updating chart with UID: {uid} after node deletion")
            update_result = await db["charts"].replace_one({"_id": document["_id"]}, document)
            if update_result.modified_count > 0:
                print(f"Chart with UID: {uid} updated successfully after node deletion")
                return parent_node  # Return the updated parent node
    else:
        print(f"Node with hashid: {node_hashid} not found in chart UID: {uid}")
    return None

@router.delete("/delete/{uid}/{node_hashid}", dependencies=[Depends(verify_BEARER_TOKEN)])
async def delete_chart_node(
    uid: str, 
    node_hashid: str, 
    User_Token: str = Header(None),
    db=Depends(get_db)
):
    """
    API endpoint to delete a chart node and its children from a specific chart and return the updated parent node or None.
    """
    # Verify the access token
    print(f"Verifying access token for User_Token: {User_Token}")
    payload_response = verify_access_token(User_Token)
    if isinstance(payload_response, JSONResponse):
        return payload_response

    try:
        # Attempt to delete the node and its children using the provided uid and node_hashid
        print(f"Attempting to delete chart node for UID: {uid}, hashid: {node_hashid}")
        result = await delete_node_recursive(uid, node_hashid, db)
        if result:
            # Serialize the result to handle ObjectId and datetime properly
            serialized_result = serialize_mongo_data(result)
            
            # Return success response with the updated parent node
            print(f"Chart node deletion successful for UID: {uid}, hashid: {node_hashid}")
            return JSONResponse(
                status_code=200,
                content={
                    "status": "success",
                    "message": result.get("message", "Chart node and its static fields deleted successfully."),
                    "parent": serialized_result if isinstance(serialized_result, dict) else None
                },
            )
        else:
            print(f"Chart node with hashid: {node_hashid} not found in chart UID: {uid}")
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "message": "Chart node not found.",
                    "data": {"error": "Chart node not found."},
                },
            )

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"An error occurred: {str(e)}",
                "data": {"error": str(e)}},
        )

# Helper function to convert ObjectId and datetime to serializable format
def serialize_mongo_data(data):
    if isinstance(data, dict):
        return {k: serialize_mongo_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [serialize_mongo_data(item) for item in data]
    elif isinstance(data, ObjectId):
        return str(data)  # Convert ObjectId to string
    elif isinstance(data, datetime):
        return data.isoformat()  # Convert datetime to ISO format
    else:
        return data
    
def calculate_counts(node):
    """
    Recursively calculate the departments_count and employees_count for each node,
    differentiated by node_type (either "employee" or "department").
    """
    departments_count = 0
    employees_count = 0

    # If this node is a department, count it as a department
    if node.get("node_type") == "department":
        departments_count += 1

    # If this node is an employee, count it as an employee
    if node.get("node_type") == "employee":
        employees_count += 1

    # Now, iterate through the children and calculate recursively
    for child in node.get("children", []):
        child_departments, child_employees =    calculate_counts(child)
        departments_count += child_departments  # Add departments count from child
        employees_count += child_employees  # Add employees count from child

    # Assign the counts to the node
    node["departments_count"] = departments_count
    node["employees_count"] = employees_count

    return departments_count, employees_count

    
#  -Gets one chart--------------------------------------------------------------------   


def calculate_and_assign_counts(node):
    if not node.get("children"):
        node["employees_count"] = 0
        node["departments_count"] = 0
        return (1, 0) if node["node_type"] == "employee" else (0, 1) if node["node_type"] == "department" else (0, 0)

    employees_count = 0
    departments_count = 0

    for child in node["children"]:
        child_employees, child_departments = calculate_and_assign_counts(child)
        employees_count += child_employees
        departments_count += child_departments

    node["employees_count"] = employees_count
    node["departments_count"] = departments_count

    return (employees_count + 1, departments_count) if node["node_type"] == "employee" else (employees_count, departments_count + 1) if node["node_type"] == "department" else (employees_count, departments_count)
    
@router.get("/get/{uid}" ,dependencies=[Depends(verify_BEARER_TOKEN)])
async def get_chart_with_counts(
    uid: str,
    User_Token: str = Header(None),
    db=Depends(get_db)
):
    """
    API endpoint to retrieve the chart details, including employee and department counts for all nodes.
    """
    payload_response = verify_access_token(User_Token)
    if isinstance(payload_response, JSONResponse):
        return payload_response

    user_id = payload_response.get("id")
    try:
        user_id = ObjectId(user_id)
    except Exception:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "message": "Invalid user ID format.",
                "data": {"error": "Invalid user ID format."},
            },
        )

    try:
        chart = await db["charts"].find_one({"uid": uid, "user_id": str(user_id)})
        if not chart:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "message": "Chart not found.",
                    "data": {"error": "Chart not found."},
                },
            )

        chart = serialize_mongo_data(chart)
        # Calculate and assign counts to all nodes
        calculate_and_assign_counts(chart)
        
        
        def add_image_urls(node):
            if "person" in node and "img" in node["person"]:
                # Domain_url = settings.DOMAIN_URL 
                Domain_url = settings.DOMAIN_URL if hasattr(settings, 'DOMAIN_URL') and settings.DOMAIN_URL else 'http://127.0.0.1:5002'

                node["person"]["img_url"] = f"{Domain_url}/chart/image/{node['person']['img']}"
            for child in node.get("children", []):
                add_image_urls(child)

        add_image_urls(chart)
        
        
        
            
        # If no hashid is provided, return the full chart with counts
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Chart details retrieved successfully.",
                "data": {"chart": chart},
            },
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"An error occurred: {str(e)}",
                "data": {"error": str(e)},
            },
        )
    
@router.get("/share/{uid}")
async def get_chart_with_counts(
    uid: str,
    User_Token: str = Header(None),
    Guest_token:str = Header(None),
    db=Depends(get_db)
):
    """
    API endpoint to retrieve the shared chart details.
    """
    print(f"{Guest_token}") 
    payload_response = verify_access_token(Guest_token)
    if isinstance(payload_response, JSONResponse):
        return payload_response
    
    if User_Token:
        payload_response = verify_share_token(User_Token)
        if isinstance(payload_response, JSONResponse):
            return payload_response
        user_id = None
    else:
        return JSONResponse(
            status_code=401,
            content={
                "status": "error",
                "message": "Authorization token is required.",
                "data": {"error": "Provide either User_Token or Share_Token."},
            },
        )

    try:
        query = {"uid": uid}
        if user_id:
            query["user_id"] = str(user_id)

        chart = await db["charts"].find_one(query)
        if not chart:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "message": "Chart not found.",
                    "data": {"error": "Chart not found."},
                },
            )

        chart = serialize_mongo_data(chart)
         # Calculate and assign counts to all nodes
        calculate_and_assign_counts(chart)

        def add_image_urls(node):
            if "person" in node and "img" in node["person"]:
                Domain_url = settings.DOMAIN_URL if hasattr(settings, 'DOMAIN_URL') else 'http://127.0.0.1:5002'
                node["person"]["img_url"] = f"{Domain_url}/chart/image/{node['person']['img']}"
            for child in node.get("children", []):
                add_image_urls(child)

        add_image_urls(chart)

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Chart details retrieved successfully.",
                "data": {"chart": chart},
            },
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"An error occurred: {str(e)}",
                "data": {"error": str(e)},
            },
        )

@router.get("/image/{uid}/{image_name}")
async def get_image(uid: str, image_name: str):
    try:
        # Define the path to the image
        file_path = os.path.join(UPLOAD_FOLDER, uid, image_name)
        print(file_path)
        
        if not os.path.exists(file_path):
            return JSONResponse(content={"message": "Image not found"}, status_code=404)
        # Serve the image file
        return FileResponse(file_path)
    
    except Exception as e:
        return JSONResponse(content={"message": f"Error fetching image: {str(e)}"}, status_code=500)


# --------------------------------edit chart----------------------------------------------

@router.put("/edit", dependencies=[Depends(verify_BEARER_TOKEN)])
async def edit_chart(
    name: str = Form(...),
    node_type: Literal["employee", "department"] = Form("employee"),
    parent_hashid: Optional[str] = Form(None),
    person: Optional[str] = Form(None),
    uid: str = Form(...),
    hashid: str = Form(...),
    User_Token: str = Header(None),
    db=Depends(get_db),
    person_img: Optional[UploadFile] = File(None),
):
    """
    API endpoint to edit a specific node in the chart by providing the hashid.
    """
    # Verify the access token
    payload_response = verify_access_token(User_Token)
    if isinstance(payload_response, JSONResponse):
        return payload_response

    user_id = payload_response.get("id")
    try:
        user_id = ObjectId(user_id)
    except Exception:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "message": "Invalid user ID format.",
                "data": {"error": "Invalid user ID format."},
            },
        )

    try:
        # Fetch the chart document
        chart = await db["charts"].find_one({"uid": uid, "user_id": str(user_id)})
        if not chart:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "message": "Chart not found.",
                    "data": {"error": "Chart not found."},
                },
            )

        # Parse the person JSON if provided
        person_data = None
        if person:
            try:
                person_data = json.loads(person)
            except json.JSONDecodeError:
                return JSONResponse(
                    status_code=400,
                    content={
                        "status": "error",
                        "message": "Invalid format for person details. Must be a valid JSON string.",
                    },
                )

        # Recursive function to update the node
        async def find_and_update_node(node, hashid, name, node_type, parent_hashid, person_data, person_img):
            if node["hashid"] == hashid:
                # Update the node's fields
                if name:
                    node["name"] = name
                if node_type:
                    node["node_type"] = node_type
                if person_data:
                    node["person"] = person_data
                if parent_hashid:
                    node["parent_hashid"] = parent_hashid

                if person_img:
                    # Save the new image
                    img_path = await save_image(person_img, uid, hashid, name)
                    if "img" not in node["person"]:
                        node["person"] = node.get("person", {})
                    node["person"]["img"] = img_path.replace("\\", "/")

                node["updated_at"] = datetime.utcnow()

            # Process child nodes
            for child in node.get("children", []):
                await find_and_update_node(child, hashid, name, node_type, parent_hashid, person_data, person_img)

        # Update the specific node
        await find_and_update_node(chart, hashid, name, node_type, parent_hashid, person_data, person_img)

        # Update the chart's updated_at timestamp
        chart["updated_at"] = datetime.utcnow()

        # Remove the departments_count and employees_count before saving
        chart.pop("departments_count", None)
        chart.pop("employees_count", None)

        # Save back the updated chart document
        await db["charts"].replace_one({"uid": uid, "user_id": str(user_id)}, chart)

        # Dynamically calculate the counts for response
        def calculate_counts(node):
            departments_count = 0
            employees_count = 0

            if node["node_type"] == "department":
                departments_count += 1
            elif node["node_type"] == "employee":
                employees_count += 1

            # Process child nodes
            for child in node.get("children", []):
                child_counts = calculate_counts(child)
                departments_count += child_counts["departments_count"]
                employees_count += child_counts["employees_count"]

            return {"departments_count": departments_count, "employees_count": employees_count}

        # Calculate counts for the root node (chart)
        counts = calculate_counts(chart)

        # Add counts to the response
        chart["departments_count"] = counts["departments_count"]
        chart["employees_count"] = counts["employees_count"]

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": f"Chart {name} updated successfully.",
                "data": {"chart": serialize_mongo_data(chart)},
            },
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"An error occurred: {str(e)}",
                "data": {"error": str(e)},
            },
        )


@router.put("/move_node", dependencies=[Depends(verify_BEARER_TOKEN)])
async def reparent_node(
    uid: str = Form(...),
    hashid: str = Form(...),  # Node to be moved
    parent_hashid: str = Form(...),  # New parent node
    User_Token: str = Header(None),
    db=Depends(get_db),
):
    """
    API endpoint to move a node to a new parent.
    """
    # Verify the access token
    payload_response = verify_access_token(User_Token)
    if isinstance(payload_response, JSONResponse):
        return payload_response

    user_id = payload_response.get("id")
    try:
        user_id = ObjectId(user_id)
    except Exception:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "Invalid user ID format."},
        )

    try:
        # Fetch the chart document
        chart = await db["charts"].find_one({"uid": uid, "user_id": str(user_id)})
        if not chart:
            return JSONResponse(
                status_code=404,
                content={"status": "error", "message": "Chart not found."},
            )

        # Find and remove the node from its current parent
        def remove_node(node, hashid):
                """ Recursively search and remove the node from its parent's children list. """
                if "children" in node:
                    for i, child in enumerate(node["children"]):
                        print(f"Checking node: {child['hashid']}")  # Debug log
                        if child["hashid"] == hashid:
                            print(f"Found and removing node: {hashid}")  # Debug log
                            return node["children"].pop(i)
                        removed_node = remove_node(child, hashid)
                        if removed_node:
                            return removed_node
                return None

        # Find and add the node under the new parent
        def add_node(node, parent_hashid, moving_node):
            if node["hashid"] == parent_hashid:
                node["children"].append(moving_node)
                moving_node["parent_hashid"] = parent_hashid
                return True
            for child in node.get("children", []):
                if add_node(child, parent_hashid, moving_node):
                    return True
            return False

        # Remove the node
        moving_node = remove_node(chart, hashid)
        if not moving_node:
            return JSONResponse(
                status_code=404,
                content={"status": "error", "message": "Node to move not found."},
            )

        # Find and attach it to the new parent
        if not add_node(chart, parent_hashid, moving_node):
            return JSONResponse(
                status_code=404,
                content={"status": "error", "message": "New parent node not found."},
            )

        # Update timestamps
        chart["updated_at"] = datetime.utcnow()
        moving_node["updated_at"] = datetime.utcnow()

        # Save updated chart
        await db["charts"].replace_one({"uid": uid, "user_id": str(user_id)}, chart)

        return JSONResponse(
            status_code=200,
            content={"status": "success", "message": "Node reparented successfully."},
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"An error occurred: {str(e)}"},
        )


 
# --------------------------------------Static fields-----------------------------------------------------------

@router.post("/static", dependencies=[Depends(verify_BEARER_TOKEN)])
async def add_static_fields_endpoint(
    chart_uid: str = Form(...),
    static_fields: Optional[str] = Form(None),
    User_Token: str = Header(None),
    db=Depends(get_db),
):
    """
    API endpoint to add static fields to a specific chart.
    """
    # Verify access token
    payload_response = verify_access_token(User_Token)
    if isinstance(payload_response, JSONResponse):
        return payload_response

    user_id = payload_response.get("id")

    try:
        user_id = str(ObjectId(user_id))
    except Exception:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "Invalid user ID format."},
        )

    # Ensure `static_fields` is provided and valid JSON
    print(static_fields)
    if not static_fields:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "Static fields must be provided."},
        )

    try:
        static_fields_data = json.loads(static_fields)
    except json.JSONDecodeError:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "Invalid static fields format. Must be a valid JSON string."},
        )

    # Check if the chart exists
    existing_chart = await db["charts"].find_one({"uid": chart_uid, "user_id": user_id})
    if not existing_chart:
        return JSONResponse(
            status_code=404,
            content={"status": "error", "message": "No chart with the given UID exists for this user."},
        )

    try:
        # Convert each field into a separate object with its own hashid
        static_field_entries = []
        for field in static_fields_data:
            # Creating hashid from the field's name and value
            hashid = hashlib.sha256(f"{field['name']}{field['label']}{datetime.utcnow()}".encode()).hexdigest()[:10]
            static_field_entries.append({
                "hashid": hashid,
                "placeholder": field.get("placeholder"),
                "type": field.get("type"),
                "name": field.get("name"),
                "label": field.get("label")
            })

        # Append each entry separately to `static_fields`
        update_result = await db["charts_access"].update_one(
            {"uid": chart_uid, "user_id": user_id}, 
            {
                "$setOnInsert": {"user_id": user_id, "chart_uid": chart_uid},  
                "$push": {"static_fields": {"$each": static_field_entries}},  # Push multiple entries
            },
            upsert=True  # Create the document if it doesn't exist
        )

        if update_result.upserted_id:
            message = "Static fields added successfully and chart created."
        else:
            message = "Static fields updated successfully."

        return JSONResponse(
            status_code=200,
            content={"status": "success", "message": message, "static_fields": static_field_entries},
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"An error occurred: {str(e)}"},
        )

# -----------------------------------------Delete static fields------------------------------------------------------------------------------------

@router.delete("/static/{uid}", dependencies=[Depends(verify_BEARER_TOKEN)])
@router.delete("/static/{uid}/{hashid}", dependencies=[Depends(verify_BEARER_TOKEN)])
async def delete_static_fields(
    uid: str,
    hashid: str = None,
    User_Token: str = Header(None),
    db=Depends(get_db),
):
    """
    API endpoint to delete static fields for a specific chart.
    - If `hashid` is provided, delete the particular field.
    - If no `hashid` is provided, delete all static fields for the chart.
    """
    # Verify access token
    payload_response = verify_access_token(User_Token)
    if isinstance(payload_response, JSONResponse):
        return payload_response

    user_id = payload_response.get("id")

    try:
        user_id = str(ObjectId(user_id))
    except Exception:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "Invalid user ID format."},
        )

    try:
        # Find the chart to check if it exists
        # Case 1: Delete the entire chart and all static fields (if no hashid provided)
        if not hashid:
            # Delete the entire chart for the user (delete all static fields and the chart itself)
            delete_result = await db["charts_access"].delete_one(
                {"chart_uid": uid, "user_id": user_id}
            )

            if delete_result.deleted_count == 0:
                return JSONResponse(
                    status_code=404,
                    content={"status": "error", "message": "Chart not found to delete."},
                )

            return JSONResponse(
                status_code=200,
                content={"status": "success", "message": "Chart and all static fields deleted successfully."},
            )

        # Case 2: Delete the specific static field (if hashid is provided)
        update_result = await db["charts_access"].update_one(
            {"chart_uid": uid, "user_id": user_id},
            {"$pull": {"static_fields": {"hashid": hashid}}} 
        )

        if update_result.modified_count == 0:
            return JSONResponse(
                status_code=404,
                content={"status": "error", "message": "Static field not found with the given hashid."},
            )

        return JSONResponse(
            status_code=200,
            content={"status": "success", "message": "Static field deleted successfully."},
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"An error occurred: {str(e)}"},
        )
# --------------------------------Get static fields--------------------------------------------------------------------------\

@router.get("/static/{uid}", dependencies=[Depends(verify_BEARER_TOKEN)])
async def get_static_fields(
    uid: str ,
    User_Token: str = Header(None),
    db=Depends(get_db),
):
    """
    API endpoint to fetch static fields for a specific chart.
    """
    # Verify access token
    payload_response = verify_access_token(User_Token)
    if isinstance(payload_response, JSONResponse):
        return payload_response

    user_id = payload_response.get("id")
    print(f"uid: {uid}")
    print(f"id: {user_id}")
    try:
        user_id = str(ObjectId(user_id))
    except Exception:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "Invalid user ID format."},
        )

    try:
        # Find the chart based on uid and user_id
        chart = await db["charts_access"].find_one(
            {"chart_uid": uid, "user_id": user_id},
            {"static_fields": 1, "_id": 0}  # Only return static_fields
        )

        if not chart or "static_fields" not in chart:
            return JSONResponse(
                status_code=404,
                content={"status": "error", "message": "No static fields found for the specified chart."},
            )

        return JSONResponse(
            status_code=200,
            content={"status": "success", "data": chart["static_fields"]},
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"An error occurred: {str(e)}"},
        )



# ----------------------------------Edit Static fields------------------------------------------------------------------------


@router.put("/static/{uid}/{hashid}", dependencies=[Depends(verify_BEARER_TOKEN)])
async def edit_static_field(
    uid: str,
    hashid: str,
    static_fields: Optional[str] = Form(None),
    User_Token: str = Header(None),
    db=Depends(get_db),
):
    """
    API endpoint to edit static fields for a specific chart.
    - If `hashid` is provided, update the particular field.
    """
    # Verify access token
    payload_response = verify_access_token(User_Token)
    if isinstance(payload_response, JSONResponse):
        return payload_response

    user_id = payload_response.get("id")

    try:
        user_id = str(ObjectId(user_id))
    except Exception:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "Invalid user ID format."},
        )

    # Ensure `static_fields` is provided and valid JSON
    if not static_fields:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "Static fields must be provided."},
        )

    try:
        static_fields_data = json.loads(static_fields)
    except json.JSONDecodeError:
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "Invalid static fields format. Must be a valid JSON string."},
        )

    # Check if the chart exists
    existing_chart = await db["charts"].find_one({"uid": uid, "user_id": user_id})
    if not existing_chart:
        return JSONResponse(
            status_code=404,
            content={"status": "error", "message": "No chart with the given UID exists for this user."},
        )

    try:
        existing_chart_access = await db["charts_access"].find_one({"uid": uid, "user_id": user_id})
        print(f"existing_chart_access: {existing_chart_access}")  # Debugging line

        # Ensure static_fields is a list and contains dictionaries
        static_fields_list = existing_chart_access.get("static_fields", [])
        if not isinstance(static_fields_list, list):
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Static fields data is not in list format."},
            )

        # Debugging: Check the content of the list
        for field in static_fields_list:
            print(f"Static field item: {field}")

        # Check if static field exists
        static_field_to_edit = None
        for field in static_fields_list:
            if isinstance(field, dict):
                if "hashid" in field and field["hashid"] == hashid:
                    static_field_to_edit = field
                    break
            else:
                return JSONResponse(
                    status_code=400,
                    content={"status": "error", "message": "Invalid static field format. Expected a dictionary."},
                )

        if not static_field_to_edit:
            return JSONResponse(
                status_code=404,
                content={"status": "error", "message": "Static field with the given hashid not found."},
            )

        # Prepare updated field data with fallbacks
        updated_field = {
            "placeholder": static_fields_data.get("placeholder", static_field_to_edit.get("placeholder")),
            "type": static_fields_data.get("type", static_field_to_edit.get("type")),
            "name": static_fields_data.get("name", static_field_to_edit.get("name")),
            "label": static_fields_data.get("label", static_field_to_edit.get("label")),
        }

        # Perform the update in the database
        update_result = await db["charts_access"].update_one(
            {"uid": uid, "user_id": user_id, "static_fields.hashid": hashid},
            {
                "$set": {
                    "static_fields.$.placeholder": updated_field["placeholder"],
                    "static_fields.$.type": updated_field["type"],
                    "static_fields.$.name": updated_field["name"],
                    "static_fields.$.label": updated_field["label"]
                }
            }
        )

        if update_result.modified_count == 0:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Failed to update the static field."},
            )

        return JSONResponse(
            status_code=200,
            content={"status": "success", "message": "Static field updated successfully.", "updated_field": updated_field},
        )


    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"An error occurred: {str(e)}"},
        )
