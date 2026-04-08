"""
Cross-System Data Links
Connect RaoFileManager files to RaoCMS articles/products/suppliers
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from .unified_models import Base, User

class FileLink(Base):
    """Link files from RaoFileManager to entities in RaoCMS"""
    __tablename__ = "file_links"
    
    id = Column(Integer, primary_key=True)
    
    # File reference (from RaoFileManager)
    file_id = Column(Integer, nullable=False, index=True)  # FileRecord.id in RaoFM
    file_name = Column(String(255), nullable=False)  # Snapshot of filename
    
    # Target entity (in RaoCMS)
    entity_type = Column(String(50), nullable=False)  # "article", "product", "supplier", "user"
    entity_id = Column(Integer, nullable=False, index=True)
    
    # Link metadata
    link_type = Column(String(50))  # "attachment", "image", "document", "gallery"
    is_primary = Column(Boolean, default=False)  # Primary image/attachment
    sort_order = Column(Integer, default=0)
    
    # Ownership
    created_by = Column(Integer, ForeignKey("users.id"))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    @property
    def entity_ref(self):
        """Return entity reference string"""
        return f"{self.entity_type}:{self.entity_id}"

class DataSyncLog(Base):
    """Track data synchronization between systems"""
    __tablename__ = "data_sync_logs"
    
    id = Column(Integer, primary_key=True)
    
    source_system = Column(String(20))  # "raomysql", "raocms", "raofm"
    target_system = Column(String(20))
    
    sync_type = Column(String(50))  # "user", "permission", "file_link", "article"
    entity_id = Column(Integer)
    
    status = Column(String(20))  # "pending", "success", "failed"
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

class ArticleFile(Base):
    """Article attachments from RaoFileManager"""
    __tablename__ = "article_files"
    
    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, nullable=False, index=True)  # From RaoCMS
    file_id = Column(Integer, nullable=False, index=True)     # From RaoFM
    
    # File metadata snapshot
    filename = Column(String(255))
    file_size = Column(Integer)
    mime_type = Column(String(100))
    
    # Display options
    is_featured = Column(Boolean, default=False)  # Featured image
    show_in_gallery = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)

class ProductFile(Base):
    """Product images/documents from RaoFileManager"""
    __tablename__ = "product_files"
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, nullable=False, index=True)  # From RaoCMS
    file_id = Column(Integer, nullable=False, index=True)     # From RaoFM
    
    filename = Column(String(255))
    file_size = Column(Integer)
    mime_type = Column(String(100))
    
    # Product-specific
    image_type = Column(String(20))  # "main", "gallery", "spec", "manual"
    alt_text = Column(String(255), nullable=True)
    
    is_primary = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)

class SupplierDocument(Base):
    """Supplier documents from RaoFileManager"""
    __tablename__ = "supplier_documents"
    
    id = Column(Integer, primary_key=True)
    supplier_id = Column(Integer, nullable=False, index=True)  # From RaoCMS
    file_id = Column(Integer, nullable=False, index=True)      # From RaoFM
    
    filename = Column(String(255))
    file_size = Column(Integer)
    mime_type = Column(String(100))
    
    # Document type
    doc_type = Column(String(50))  # "contract", "license", "certificate", "invoice", "other"
    is_verified = Column(Boolean, default=False)  # Admin verification
    verified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    
    expires_at = Column(DateTime, nullable=True)  # For certificates/licenses
    
    created_at = Column(DateTime, default=datetime.utcnow)

class UserDocument(Base):
    """User documents (KYC, contracts, etc.) from RaoFileManager"""
    __tablename__ = "user_documents"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    file_id = Column(Integer, nullable=False, index=True)  # From RaoFM
    
    filename = Column(String(255))
    file_size = Column(Integer)
    mime_type = Column(String(100))
    
    # Document type
    doc_type = Column(String(50))  # "id_card", "contract", "avatar", "signature"
    is_verified = Column(Boolean, default=False)
    verified_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)