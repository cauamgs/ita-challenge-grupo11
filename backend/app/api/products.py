from typing import Literal

from fastapi import APIRouter, Query

from app.api.deps import SessionDep
from app.schemas.common import Page
from app.schemas.products import ProductDetail, ProductListItem
from app.services import products as products_service

router = APIRouter(prefix="/products", tags=["Produtos"])


@router.get("", response_model=Page[ProductListItem], summary="Catálogo de produtos (do ERP)")
def list_products(
    session: SessionDep,
    q: str | None = Query(None, description="Busca por SKU ou nome"),
    category: str | None = None,
    abc_curve: Literal["A", "B", "C"] | None = None,
    status: str | None = None,
    sort: Literal["sku", "recentes"] = "sku",
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
) -> Page[ProductListItem]:
    return products_service.list_products(
        session,
        q=q,
        category=category,
        abc_curve=abc_curve,
        status=status,
        changed=sort,
        page=page,
        page_size=page_size,
    )


@router.get("/categories", response_model=list[str], summary="Categorias do catálogo")
def list_categories(session: SessionDep) -> list[str]:
    return products_service.categories(session)


@router.get(
    "/{sku}",
    response_model=ProductDetail,
    summary="Produto com preços por canal, estoque, histórico de preço e recomendações",
)
def get_product(sku: str, session: SessionDep) -> ProductDetail:
    return products_service.get_product(session, sku)
