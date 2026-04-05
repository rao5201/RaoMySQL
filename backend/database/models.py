"""数据库模型"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, BigInteger, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    role = Column(String(32), default="developer")
    email = Column(String(128), nullable=True)
    status = Column(String(16), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DbConnection(Base):
    __tablename__ = "db_connections"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(128), nullable=False)
    host = Column(String(255), nullable=False)
    port = Column(Integer, default=3306)
    username = Column(String(128), nullable=True)
    password_enc = Column(String(512), nullable=True)
    database_name = Column(String(128), nullable=True)
    tags = Column(String(256), nullable=True)
    ssl_enabled = Column(Boolean, default=False)
    max_connections = Column(Integer, default=100)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SqlHistory(Base):
    __tablename__ = "sql_history"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    connection_id = Column(Integer, ForeignKey("db_connections.id"), nullable=False)
    sql_text = Column(Text, nullable=False)
    sql_type = Column(String(16), nullable=True)
    duration_ms = Column(Integer, nullable=True)
    rows_affected = Column(Integer, nullable=True)
    status = Column(String(16), nullable=True)
    error_msg = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class SqlSnippet(Base):
    __tablename__ = "sql_snippets"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(128), nullable=True)
    sql_text = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Backup(Base):
    __tablename__ = "backups"
    id = Column(Integer, primary_key=True, autoincrement=True)
    connection_id = Column(Integer, ForeignKey("db_connections.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_path = Column(String(512), nullable=True)
    file_size = Column(BigInteger, nullable=True)
    status = Column(String(16), default="pending")
    backup_type = Column(String(16), default="manual")
    checksum = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ScheduledTask(Base):
    __tablename__ = "scheduled_tasks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(128), nullable=False)
    task_type = Column(String(64), nullable=False)
    cron_expr = Column(String(64), nullable=True)
    config = Column(Text, nullable=True)
    enabled = Column(Boolean, default=True)
    last_run_at = Column(DateTime, nullable=True)
    last_status = Column(String(16), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class TaskRun(Base):
    __tablename__ = "task_runs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("scheduled_tasks.id"), nullable=False)
    status = Column(String(16), nullable=True)
    output = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    connection_id = Column(Integer, ForeignKey("db_connections.id"), nullable=True)
    level = Column(String(16), default="info")
    title = Column(String(256), nullable=True)
    content = Column(Text, nullable=True)
    status = Column(String(16), default="unread")
    created_at = Column(DateTime, default=datetime.utcnow)
