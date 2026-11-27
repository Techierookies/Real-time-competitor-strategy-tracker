"""Store catalogue management (admin only)."""

from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..db import Database
from ..deps import get_db
from ..schemas import StoreProductIn, StoreProductUpdate
from ..security import require_admin

router = APIRouter(prefix="/api/products", tags=["catalogue"])


@router.get("")
def list_products(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    status_filter: str | None = Query(default=None, alias="status"),
    db: Database = Depends(get_db),
) -> dict:
    """Paginated catalogue listing.

    The previous endpoint returned every row with no limit, which is fine with
    one product and a problem with ten thousand.
    """
    clauses, params = [], []
    if status_filter:
        clauses.append("status = ?")
        params.append(status_filter)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    with db.connect() as connection:
        total = connection.execute(
            f"SELECT COUNT(*) AS n FROM store_products {where}", params
        ).fetchone()["n"]
        rows = connection.execute(
            f"""
            SELECT id, name, sku, category, price, cost, stock, status
            FROM store_products {where}
            ORDER BY id DESC LIMIT ? OFFSET ?
            """,
            (*params, limit, offset),
        ).fetchall()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "products": [dict(row) for row in rows],
    }


@router.post("", status_code=201, dependencies=[Depends(require_admin)])
def create_product(payload: StoreProductIn, db: Database = Depends(get_db)) -> dict:
    try:
        with db.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO store_products
                    (name, sku, category, price, cost, stock, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload.name, payload.sku, payload.category, payload.price,
                    payload.cost, payload.stock, payload.status,
                ),
            )
            return {"id": cursor.lastrowid, "message": "Product created."}
    except sqlite3.IntegrityError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"SKU '{payload.sku}' already exists.",
        ) from error


@router.patch("/{product_id}", dependencies=[Depends(require_admin)])
def update_product(
    product_id: int, payload: StoreProductUpdate, db: Database = Depends(get_db)
) -> dict:
    """Update a product.

    Columns are taken from the validated schema rather than interpolated from
    arbitrary request keys, so the SQL cannot be shaped by the caller.
    """
    changes = payload.model_dump(exclude_none=True)
    if not changes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update."
        )

    assignments = ", ".join(f"{column} = ?" for column in changes)
    with db.connect() as connection:
        cursor = connection.execute(
            f"UPDATE store_products SET {assignments} WHERE id = ?",
            (*changes.values(), product_id),
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Product not found.")
    return {"message": "Product updated.", "updated_fields": list(changes)}


@router.delete("/{product_id}", dependencies=[Depends(require_admin)])
def delete_product(product_id: int, db: Database = Depends(get_db)) -> dict:
    with db.connect() as connection:
        cursor = connection.execute(
            "DELETE FROM store_products WHERE id = ?", (product_id,)
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Product not found.")
    return {"message": "Product deleted."}
