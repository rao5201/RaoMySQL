"""
RaoCMS - 企业网站后台管理系统数据模型
支持多角色权限：admin(管理员), customer_service(客服), finance(财务)
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, DECIMAL, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import json

Base = declarative_base()

# ==================== 用户相关 ====================

class SysUser(Base):
    """后台用户表（管理员、客服、财务）"""
    __tablename__ = "sys_users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)  # bcrypt哈希
    real_name = Column(String(64))
    role = Column(String(32), default="customer_service")  # admin/customer_service/finance
    email = Column(String(128))
    phone = Column(String(32))
    avatar = Column(String(512))
    status = Column(String(16), default="active")  # active/disabled
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    articles = relationship("Article", back_populates="author")
    operation_logs = relationship("OperationLog", back_populates="user")


class PortalUser(Base):
    """前台注册用户表"""
    __tablename__ = "portal_users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    email = Column(String(128))
    phone = Column(String(32))
    nickname = Column(String(64))
    avatar = Column(String(512))
    status = Column(String(16), default="active")  # active/disabled
    user_tags = Column(String(256))  # 逗号分隔标签
    register_ip = Column(String(64))
    last_login = Column(DateTime)
    login_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class OperationLog(Base):
    """操作日志表"""
    __tablename__ = "operation_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("sys_users.id"))
    user_type = Column(String(16))  # sys/portal
    action = Column(String(64))  # 操作类型
    module = Column(String(64))  # 操作模块
    detail = Column(Text)  # 操作详情
    ip_address = Column(String(64))
    user_agent = Column(String(512))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("SysUser", back_populates="operation_logs")


# ==================== 内容相关 ====================

class Category(Base):
    """栏目分类表"""
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, default=0)
    name = Column(String(128), nullable=False)
    slug = Column(String(128), unique=True, index=True)
    description = Column(Text)
    sort_order = Column(Integer, default=0)
    status = Column(String(16), default="active")  # active/inactive
    created_at = Column(DateTime, default=datetime.utcnow)
    
    articles = relationship("Article", back_populates="category")


class Article(Base):
    """文章表"""
    __tablename__ = "articles"
    
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"))
    title = Column(String(256), nullable=False)
    slug = Column(String(256), index=True)
    summary = Column(Text)
    content = Column(Text)
    cover_image = Column(String(512))
    author_id = Column(Integer, ForeignKey("sys_users.id"))
    author_name = Column(String(64))
    status = Column(String(16), default="draft")  # draft/pending/approved/rejected/published/offline
    is_top = Column(Boolean, default=False)
    view_count = Column(Integer, default=0)
    seo_title = Column(String(256))
    seo_keywords = Column(String(256))
    seo_description = Column(Text)
    published_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    category = relationship("Category", back_populates="articles")
    author = relationship("SysUser", back_populates="articles")
    audits = relationship("ArticleAudit", back_populates="article")


class ArticleAudit(Base):
    """文章审核记录"""
    __tablename__ = "article_audits"
    
    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("articles.id"))
    operator_id = Column(Integer, ForeignKey("sys_users.id"))
    action = Column(String(32))  # submit/approve/reject/offline
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    article = relationship("Article", back_populates="audits")


class MediaFile(Base):
    """文件资源表"""
    __tablename__ = "media_files"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("sys_users.id"))
    filename = Column(String(256))
    original_name = Column(String(256))
    file_path = Column(String(512))
    file_url = Column(String(512))
    file_type = Column(String(64))  # image/document/video/audio/other
    file_size = Column(Integer)  # bytes
    mime_type = Column(String(128))
    tags = Column(String(256))
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


# ==================== 供应商相关 ====================

class Supplier(Base):
    """供应商表"""
    __tablename__ = "suppliers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(256), nullable=False)
    code = Column(String(64), unique=True, index=True)
    contact_name = Column(String(128))
    contact_phone = Column(String(32))
    contact_email = Column(String(128))
    address = Column(Text)
    status = Column(String(16), default="active")  # active/inactive/blacklisted
    rating = Column(DECIMAL(2, 1), default=5.0)  # 1-5分
    total_amount = Column(DECIMAL(15, 2), default=0)  # 累计合作金额
    remark = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    records = relationship("SupplierRecord", back_populates="supplier")


class SupplierRecord(Base):
    """供应商合作记录"""
    __tablename__ = "supplier_records"
    
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    record_type = Column(String(32))  # contract/order/payment
    title = Column(String(256))
    amount = Column(DECIMAL(15, 2))
    status = Column(String(32))
    start_date = Column(String(10))  # YYYY-MM-DD
    end_date = Column(String(10))
    attachment = Column(String(512))
    remark = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    supplier = relationship("Supplier", back_populates="records")


# ==================== 产品相关 ====================

class ProductCategory(Base):
    """产品分类表"""
    __tablename__ = "product_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, default=0)
    name = Column(String(128), nullable=False)
    code = Column(String(64))
    sort_order = Column(Integer, default=0)
    status = Column(String(16), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    products = relationship("Product", back_populates="category")


class Product(Base):
    """产品表"""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("product_categories.id"))
    name = Column(String(256), nullable=False)
    code = Column(String(64), unique=True, index=True)
    description = Column(Text)
    price = Column(DECIMAL(12, 2))
    cost_price = Column(DECIMAL(12, 2))
    stock = Column(Integer, default=0)
    unit = Column(String(32))
    images = Column(Text)  # JSON 数组
    status = Column(String(16), default="active")  # active/inactive/out_of_stock
    sales_count = Column(Integer, default=0)
    view_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    category = relationship("ProductCategory", back_populates="products")
    sales = relationship("SalesRecord", back_populates="product")


class SalesRecord(Base):
    """销售记录表"""
    __tablename__ = "sales_records"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    order_no = Column(String(64), index=True)
    quantity = Column(Integer)
    unit_price = Column(DECIMAL(12, 2))
    total_amount = Column(DECIMAL(12, 2))
    user_id = Column(Integer)  # 前台用户ID
    status = Column(String(32))  # pending/paid/shipped/completed/cancelled/refunded
    pay_method = Column(String(32))
    pay_time = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    product = relationship("Product", back_populates="sales")


# ==================== 财务相关 ====================

class FinanceRecord(Base):
    """收支记录表"""
    __tablename__ = "finance_records"
    
    id = Column(Integer, primary_key=True, index=True)
    record_type = Column(String(16))  # income/expense
    category = Column(String(64))  # 销售/退款/运营/营销/人力/供应商等
    amount = Column(DECIMAL(15, 2))
    title = Column(String(256))
    description = Column(Text)
    related_id = Column(Integer)  # 关联ID
    related_type = Column(String(64))  # 关联类型
    operator_id = Column(Integer, ForeignKey("sys_users.id"))
    record_date = Column(String(10))  # YYYY-MM-DD
    created_at = Column(DateTime, default=datetime.utcnow)


class FinanceDailyStat(Base):
    """财务报表缓存（日统计）"""
    __tablename__ = "finance_daily_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    stat_date = Column(String(10), unique=True, index=True)  # YYYY-MM-DD
    income = Column(DECIMAL(15, 2), default=0)
    expense = Column(DECIMAL(15, 2), default=0)
    order_count = Column(Integer, default=0)
    user_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


# ==================== 数据库初始化 ====================

def init_db(database_url: str = "sqlite:///raocms.db"):
    """初始化数据库"""
    engine = create_engine(database_url, echo=False)
    Base.metadata.create_all(bind=engine)
    return engine


def get_session_maker(engine):
    """获取会话工厂"""
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)
