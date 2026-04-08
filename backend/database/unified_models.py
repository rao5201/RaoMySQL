"""
Unified User Model - Shared across RaoMySQL, RaoCMS, RaoFileManager
All systems use the same user table and authentication.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.orm import declarative_base
import enum

Base = declarative_base()

class UserRole(str, enum.Enum):
    """Unified role system across all platforms"""
    ADMIN = "admin"           # Full access to all systems
    FINANCE = "finance"       # Finance/audit - view sales, expenses, reports
    SUPPORT = "support"       # Customer service - view + add, no delete, needs review
    SUPPLIER = "supplier"     # Supplier - manage own products
    MERCHANT = "merchant"     # Merchant backend
    USER = "user"             # Regular user - blocked from CMS, file access only
    GUEST = "guest"           # Guest - read-only public content

class User(Base):
    """Unified user table - shared by all Rao* systems"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Role & Permissions
    role = Column(String(20), default="user", nullable=False)  # UserRole enum
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Profile
    display_name = Column(String(100), nullable=True)
    avatar_url = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    
    # System-specific permissions (JSON for flexibility)
    # {"raomysql": ["read", "write"], "raocms": ["read"], "raofm": ["read", "write", "delete"]}
    permissions = Column(String(500), nullable=True)  # JSON string
    
    # Ownership (for suppliers/merchants)
    organization_id = Column(Integer, nullable=True)  # Link to organization/supplier
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)
    
    def has_permission(self, system: str, action: str) -> bool:
        """Check if user has specific permission for a system"""
        import json
        if self.role == "admin":
            return True
        
        perms = json.loads(self.permissions or "{}")
        system_perms = perms.get(system, [])
        return action in system_perms
    
    def can_access_system(self, system: str) -> bool:
        """Check if user can access a system at all"""
        # Admin: all systems
        if self.role == "admin":
            return True
        
        # Finance: only RaoCMS finance modules
        if self.role == "finance":
            return system in ["raocms"]
        
        # Support: RaoCMS (limited) + RaoFileManager
        if self.role == "support":
            return system in ["raocms", "raofm"]
        
        # Supplier: RaoCMS supplier modules
        if self.role == "supplier":
            return system in ["raocms"]
        
        # Merchant: RaoCMS merchant modules
        if self.role == "merchant":
            return system in ["raocms"]
        
        # User: only RaoFileManager (their own files)
        if self.role == "user":
            return system in ["raofm"]
        
        # Guest: read-only public content
        if self.role == "guest":
            return system in ["raocms"]  # Public articles only
        
        return False

class Organization(Base):
    """Organization/Supplier/Merchant - for B2B scenarios"""
    __tablename__ = "organizations"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    org_type = Column(String(20))  # "supplier", "merchant", "company"
    contact_person = Column(String(50))
    contact_email = Column(String(100))
    contact_phone = Column(String(20))
    
    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)  # Admin verification required
    
    # Metadata
    description = Column(String(500), nullable=True)
    website = Column(String(255), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UserSession(Base):
    """Session tracking for unified auth"""
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    token_hash = Column(String(64), unique=True, nullable=False)  # SHA256 of JWT
    system = Column(String(20))  # Which system they logged in from
    
    # Device info
    user_agent = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)  # For logout/revocation