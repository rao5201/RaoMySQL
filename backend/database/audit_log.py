"""RaoMySQL Audit Log - Track all user operations"""
import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from backend.database.init_db import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, index=True)
    username = Column(String(50))
    action = Column(String(50), index=True)  # login/logout/query/backup/restore/write/delete/config
    resource = Column(String(100))  # connection_id / backup_id / sql_text
    detail = Column(Text)  # JSON string with extra info
    ip_address = Column(String(45))
    status = Column(String(20), default="success")  # success/failed/denied
    created_at = Column(DateTime, default=datetime.now, index=True)

    def to_dict(self):
        d = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        if d.get("detail"):
            try: d["detail"] = json.loads(d["detail"])
            except: pass
        return d
