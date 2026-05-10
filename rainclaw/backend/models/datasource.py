from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum
import uuid
import time


class DbType(str, Enum):
    MySQL = "MySQL"
    PostgreSQL = "PostgreSQL"
    Oracle = "Oracle"
    MongoDB = "MongoDB"
    SQLServer = "SQL Server"


class Datasource(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="数据源名称")
    code: str = Field(..., min_length=1, description="唯一编码标识")
    host: str = Field(..., description="主机地址/IP")
    port: int = Field(..., gt=0, lt=65536, description="端口号")
    database_name: str = Field(..., description="数据库名")
    username: str = Field(..., description="登录账号")
    password: str = Field(..., description="登录密码")
    db_type: DbType = Field(..., description="数据库类型")
    created_at: int = Field(default_factory=lambda: int(time.time()))
    updated_at: int = Field(default_factory=lambda: int(time.time()))


class DatasourceCreate(BaseModel):
    name: str
    code: str = Field(..., min_length=1)
    host: str
    port: int = Field(..., gt=0, lt=65536)
    database_name: str
    username: str
    password: str
    db_type: DbType


class DatasourceUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = Field(default=None, gt=0, lt=65536)
    database_name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    db_type: Optional[DbType] = None
