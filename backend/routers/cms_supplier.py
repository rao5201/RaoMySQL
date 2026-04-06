"""
RaoCMS - 供应商和产品管理路由
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from backend.database.cms_models import Supplier, SupplierRecord, Product, ProductCategory, SalesRecord
from backend.routers.cms_auth import get_current_user, UserRole, Permission, require_permissions
from backend.database.init_db import get_db
from sqlalchemy import func

router = APIRouter(prefix="/api", tags=["供应商/产品管理"])


# ==================== Pydantic 模型 ====================

class SupplierCreate(BaseModel):
    name: str
    code: str
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    address: Optional[str] = None
    remark: Optional[str] = None


class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    address: Optional[str] = None
    status: Optional[str] = None
    rating: Optional[float] = None
    remark: Optional[str] = None


class SupplierRecordCreate(BaseModel):
    record_type: str  # contract/order/payment
    title: str
    amount: Optional[float] = None
    status: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    attachment: Optional[str] = None
    remark: Optional[str] = None


class ProductCreate(BaseModel):
    name: str
    code: str
    category_id: Optional[int] = None
    description: Optional[str] = None
    price: Optional[float] = None
    cost_price: Optional[float] = None
    stock: int = 0
    unit: Optional[str] = None
    images: Optional[str] = None


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    category_id: Optional[int] = None
    description: Optional[str] = None
    price: Optional[float] = None
    cost_price: Optional[float] = None
    stock: Optional[int] = None
    unit: Optional[str] = None
    images: Optional[str] = None
    status: Optional[str] = None


class CategoryCreate(BaseModel):
    name: str
    code: Optional[str] = None
    parent_id: int = 0


# ==================== 供应商管理 ====================

@router.get("/suppliers", response_model=List[dict])
async def get_suppliers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    current_user: dict = Depends(require_permissions([Permission.SUPPLIER_VIEW])),
    db: Session = Depends(get_db)
):
    """获取供应商列表"""
    query = db.query(Supplier)
    
    if status:
        query = query.filter(Supplier.status == status)
    if keyword:
        query = query.filter(Supplier.name.contains(keyword))
    
    total = query.count()
    suppliers = query.order_by(Supplier.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    
    # 转换为字典
    result = []
    for s in suppliers:
        result.append({
            "id": s.id,
            "name": s.name,
            "code": s.code,
            "contact_name": s.contact_name,
            "contact_phone": s.contact_phone,
            "contact_email": s.contact_email,
            "address": s.address,
            "status": s.status,
            "rating": float(s.rating) if s.rating else 5.0,
            "total_amount": float(s.total_amount) if s.total_amount else 0,
            "created_at": s.created_at
        })
    
    return result


@router.get("/suppliers/{supplier_id}")
async def get_supplier(
    supplier_id: int,
    current_user: dict = Depends(require_permissions([Permission.SUPPLIER_VIEW])),
    db: Session = Depends(get_db)
):
    """获取供应商详情"""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="供应商不存在")
    
    return {
        "id": supplier.id,
        "name": supplier.name,
        "code": supplier.code,
        "contact_name": supplier.contact_name,
        "contact_phone": supplier.contact_phone,
        "contact_email": supplier.contact_email,
        "address": supplier.address,
        "status": supplier.status,
        "rating": float(supplier.rating) if supplier.rating else 5.0,
        "total_amount": float(supplier.total_amount) if supplier.total_amount else 0,
        "remark": supplier.remark,
        "created_at": supplier.created_at
    }


@router.post("/suppliers")
async def create_supplier(
    supplier_data: SupplierCreate,
    current_user: dict = Depends(require_permissions([Permission.SUPPLIER_MANAGE])),
    db: Session = Depends(get_db)
):
    """创建供应商"""
    existing = db.query(Supplier).filter(Supplier.code == supplier_data.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="供应商编码已存在")
    
    supplier = Supplier(**supplier_data.dict())
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


@router.put("/suppliers/{supplier_id}")
async def update_supplier(
    supplier_id: int,
    supplier_data: SupplierUpdate,
    current_user: dict = Depends(require_permissions([Permission.SUPPLIER_MANAGE])),
    db: Session = Depends(get_db)
):
    """更新供应商"""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="供应商不存在")
    
    update_data = supplier_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(supplier, key, value)
    
    db.commit()
    db.refresh(supplier)
    return supplier


@router.delete("/suppliers/{supplier_id}")
async def delete_supplier(
    supplier_id: int,
    current_user: dict = Depends(require_permissions([Permission.SUPPLIER_MANAGE])),
    db: Session = Depends(get_db)
):
    """删除供应商"""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="供应商不存在")
    
    db.delete(supplier)
    db.commit()
    return {"message": "删除成功"}


@router.get("/suppliers/{supplier_id}/records")
async def get_supplier_records(
    supplier_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(require_permissions([Permission.SUPPLIER_VIEW])),
    db: Session = Depends(get_db)
):
    """获取供应商合作记录"""
    records = db.query(SupplierRecord).filter(
        SupplierRecord.supplier_id == supplier_id
    ).order_by(SupplierRecord.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    
    return records


@router.post("/suppliers/{supplier_id}/records")
async def add_supplier_record(
    supplier_id: int,
    record_data: SupplierRecordCreate,
    current_user: dict = Depends(require_permissions([Permission.SUPPLIER_MANAGE])),
    db: Session = Depends(get_db)
):
    """添加供应商合作记录"""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="供应商不存在")
    
    record = SupplierRecord(
        supplier_id=supplier_id,
        **record_data.dict()
    )
    db.add(record)
    
    # 更新累计合作金额
    if record_data.amount and record_data.record_type == "payment":
        supplier.total_amount = (supplier.total_amount or 0) + record_data.amount
    
    db.commit()
    db.refresh(record)
    return record


@router.get("/suppliers/stats")
async def get_supplier_stats(
    current_user: dict = Depends(require_permissions([Permission.SUPPLIER_VIEW])),
    db: Session = Depends(get_db)
):
    """获取供应商统计"""
    total = db.query(func.count(Supplier.id)).scalar()
    active = db.query(func.count(Supplier.id)).filter(Supplier.status == "active").scalar()
    total_amount = db.query(func.sum(Supplier.total_amount)).scalar() or 0
    
    return {
        "total": total,
        "active": active,
        "total_amount": float(total_amount)
    }


# ==================== 产品分类管理 ====================

@router.get("/product-categories")
async def get_product_categories(
    current_user: dict = Depends(require_permissions([Permission.PRODUCT_VIEW])),
    db: Session = Depends(get_db)
):
    """获取产品分类列表"""
    categories = db.query(ProductCategory).filter(
        ProductCategory.status == "active"
    ).order_by(ProductCategory.sort_order, ProductCategory.name).all()
    
    return categories


@router.post("/product-categories")
async def create_product_category(
    category_data: CategoryCreate,
    current_user: dict = Depends(require_permissions([Permission.PRODUCT_MANAGE])),
    db: Session = Depends(get_db)
):
    """创建产品分类"""
    category = ProductCategory(**category_data.dict())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


# ==================== 产品管理 ====================

@router.get("/products", response_model=List[dict])
async def get_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category_id: Optional[int] = None,
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    current_user: dict = Depends(require_permissions([Permission.PRODUCT_VIEW])),
    db: Session = Depends(get_db)
):
    """获取产品列表"""
    query = db.query(Product)
    
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if status:
        query = query.filter(Product.status == status)
    if keyword:
        query = query.filter(Product.name.contains(keyword))
    
    total = query.count()
    products = query.order_by(Product.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    
    result = []
    for p in products:
        result.append({
            "id": p.id,
            "name": p.name,
            "code": p.code,
            "category_id": p.category_id,
            "price": float(p.price) if p.price else 0,
            "stock": p.stock,
            "sales_count": p.sales_count,
            "status": p.status,
            "created_at": p.created_at
        })
    
    return result


@router.get("/products/{product_id}")
async def get_product(
    product_id: int,
    current_user: dict = Depends(require_permissions([Permission.PRODUCT_VIEW])),
    db: Session = Depends(get_db)
):
    """获取产品详情"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")
    
    return {
        "id": product.id,
        "name": product.name,
        "code": product.code,
        "category_id": product.category_id,
        "description": product.description,
        "price": float(product.price) if product.price else 0,
        "cost_price": float(product.cost_price) if product.cost_price else 0,
        "stock": product.stock,
        "unit": product.unit,
        "images": product.images,
        "status": product.status,
        "sales_count": product.sales_count,
        "created_at": product.created_at
    }


@router.post("/products")
async def create_product(
    product_data: ProductCreate,
    current_user: dict = Depends(require_permissions([Permission.PRODUCT_MANAGE])),
    db: Session = Depends(get_db)
):
    """创建产品"""
    existing = db.query(Product).filter(Product.code == product_data.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="产品编码已存在")
    
    product = Product(**product_data.dict())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.put("/products/{product_id}")
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    current_user: dict = Depends(require_permissions([Permission.PRODUCT_MANAGE])),
    db: Session = Depends(get_db)
):
    """更新产品"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")
    
    update_data = product_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(product, key, value)
    
    db.commit()
    db.refresh(product)
    return product


@router.delete("/products/{product_id}")
async def delete_product(
    product_id: int,
    current_user: dict = Depends(require_permissions([Permission.PRODUCT_MANAGE])),
    db: Session = Depends(get_db)
):
    """删除产品"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")
    
    db.delete(product)
    db.commit()
    return {"message": "删除成功"}


@router.get("/products/stats")
async def get_product_stats(
    current_user: dict = Depends(require_permissions([Permission.PRODUCT_VIEW])),
    db: Session = Depends(get_db)
):
    """获取产品统计"""
    total = db.query(func.count(Product.id)).scalar()
    active = db.query(func.count(Product.id)).filter(Product.status == "active").scalar()
    out_of_stock = db.query(func.count(Product.id)).filter(Product.status == "out_of_stock").scalar()
    
    # 热销产品 Top 10
    top_sales = db.query(Product).order_by(Product.sales_count.desc()).limit(10).all()
    
    return {
        "total": total,
        "active": active,
        "out_of_stock": out_of_stock,
        "top_sales": [{"id": p.id, "name": p.name, "sales_count": p.sales_count} for p in top_sales]
    }


@router.get("/products/sales")
async def get_sales_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    product_id: Optional[int] = None,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(require_permissions([Permission.PRODUCT_VIEW])),
    db: Session = Depends(get_db)
):
    """获取销售记录"""
    query = db.query(SalesRecord)
    
    if product_id:
        query = query.filter(SalesRecord.product_id == product_id)
    if status:
        query = query.filter(SalesRecord.status == status)
    if start_date:
        query = query.filter(SalesRecord.created_at >= start_date)
    if end_date:
        query = query.filter(SalesRecord.created_at <= end_date)
    
    total = query.count()
    records = query.order_by(SalesRecord.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    
    return records