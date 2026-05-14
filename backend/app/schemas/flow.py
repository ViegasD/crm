import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.enums import FlowExecStatus, FlowTriggerType


class FlowNodeModel(BaseModel):
    id: str
    type: str
    position: dict
    parameters: dict
    label: str | None = None


class FlowEdgeModel(BaseModel):
    id: str
    source: str
    source_handle: str
    target: str
    target_handle: str | None = None


class FlowGraphIn(BaseModel):
    version: int
    nodes: list[FlowNodeModel]
    edges: list[FlowEdgeModel]


class FlowCreate(BaseModel):
    name: str
    description: str | None = None
    trigger_type: FlowTriggerType
    channel_account_id: uuid.UUID | None = None
    nodes_data: FlowGraphIn


class FlowUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    nodes_data: FlowGraphIn | None = None


class FlowOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    description: str | None
    trigger_type: FlowTriggerType
    channel_account_id: uuid.UUID | None
    active: bool
    version: int
    created_at: datetime
    updated_at: datetime


class FlowExecutionOut(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    flow_id: uuid.UUID
    conversation_id: uuid.UUID
    status: FlowExecStatus
    current_node_id: str | None
    hop_count: int
    error_message: str | None
    created_at: datetime
