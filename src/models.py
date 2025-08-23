from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from pydantic import BaseModel, Field
from enum import Enum


class DocumentMetadata(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    author: Optional[str] = None
    created: Optional[datetime] = None
    modified: Optional[datetime] = None
    version: Optional[str] = None
    custom_fields: Dict[str, Any] = Field(default_factory=dict)


class DocumentContext(BaseModel):
    id: str
    title: str
    content: str
    path: str
    relative_path: str
    last_modified: datetime
    size: int
    tags: List[str] = Field(default_factory=list)
    metadata: DocumentMetadata = Field(default_factory=DocumentMetadata)
    excerpt: Optional[str] = None
    word_count: int = 0
    file_type: str = ""


class ProjectStatistics(BaseModel):
    total_files: int = 0
    total_size: int = 0
    total_words: int = 0
    file_types: Dict[str, int] = Field(default_factory=dict)
    last_activity: datetime = Field(default_factory=datetime.now)


class ProjectContext(BaseModel):
    id: str
    name: str
    description: str
    root_path: str
    documents: List[DocumentContext] = Field(default_factory=list)
    total_documents: int = 0
    last_updated: datetime = Field(default_factory=datetime.now)
    statistics: ProjectStatistics = Field(default_factory=ProjectStatistics)


class SortBy(str, Enum):
    RELEVANCE = "relevance"
    MODIFIED = "modified"
    CREATED = "created"
    TITLE = "title"


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


class ContextQuery(BaseModel):
    query: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    path: Optional[str] = None
    file_type: Optional[str] = None
    limit: int = 10
    offset: int = 0
    since: Optional[datetime] = None
    sort_by: SortBy = SortBy.RELEVANCE
    sort_order: SortOrder = SortOrder.DESC


class SearchMatch(BaseModel):
    line: int
    text: str
    start_index: int
    end_index: int


class SearchResult(BaseModel):
    document: DocumentContext
    score: float
    matches: List[SearchMatch] = Field(default_factory=list)


class ContextResponse(BaseModel):
    results: List[SearchResult] = Field(default_factory=list)
    total: int = 0
    query: ContextQuery
    timestamp: datetime = Field(default_factory=datetime.now)
    execution_time: float = 0.0


class FileWatchEvent(BaseModel):
    type: str  # 'created', 'modified', 'deleted'
    path: str
    timestamp: datetime = Field(default_factory=datetime.now)


class MCPToolResult(BaseModel):
    content: List[Dict[str, str]]


class UploadedFile(BaseModel):
    filename: str
    content: str
    size: int
    upload_time: datetime = Field(default_factory=datetime.now)
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AdminAction(BaseModel):
    action: str
    target: str
    user: str
    timestamp: datetime = Field(default_factory=datetime.now)
    details: Dict[str, Any] = Field(default_factory=dict)


class ServerStatus(BaseModel):
    status: str
    uptime: float
    documents_loaded: int
    memory_usage: float
    last_activity: datetime
    version: str = "1.0.0"