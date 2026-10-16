"""Datasets router: full CRUD.

Permission matrix:
  viewer  → GET /datasets, GET /datasets/{id}
  analyst → + POST, PUT /datasets/{id}
  admin   → + DELETE /datasets/{id}

Each endpoint declares its permission requirement via Depends(require_role(...)).
Integrated with Redis cache and cache invalidation on write.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from api.cache import cache_get, cache_set, invalidate_datasets_cache
from api.db.models import Dataset, Role, User
from api.db.session import get_db
from api.deps import require_role

router = APIRouter(prefix="/datasets", tags=["datasets"])


class DatasetIn(BaseModel):
    name: str
    description: str | None = None


class DatasetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    owner_id: int


# ── Read (viewer+) ────────────────────────────────────────────────────────────

_read_roles = (Role.viewer, Role.analyst, Role.admin)


@router.get("", response_model=list[DatasetOut])
def list_datasets(
    _: User = Depends(require_role(*_read_roles)),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> list[Dataset]:
    """Return all datasets (cached)."""
    cache_key = "dataset:list"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    datasets = db.query(Dataset).all()
    result = [DatasetOut.model_validate(ds).model_dump() for ds in datasets]
    cache_set(cache_key, result)
    return datasets


@router.get("/{dataset_id}", response_model=DatasetOut)
def get_dataset(
    dataset_id: int,
    _: User = Depends(require_role(*_read_roles)),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> Dataset:
    """Return a single dataset or 404 (cached)."""
    cache_key = f"dataset:{dataset_id}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    ds = db.get(Dataset, dataset_id)
    if ds is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")

    result = DatasetOut.model_validate(ds).model_dump()
    cache_set(cache_key, result)
    return ds


# ── Create / update (analyst+) ────────────────────────────────────────────────


@router.post("", response_model=DatasetOut, status_code=status.HTTP_201_CREATED)
def create_dataset(
    body: DatasetIn,
    current_user: User = Depends(require_role(Role.analyst, Role.admin)),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> Dataset:
    """Create a new dataset owned by the calling user. Invalidates cache."""
    ds = Dataset(name=body.name, description=body.description, owner_id=current_user.id)
    db.add(ds)
    db.commit()
    db.refresh(ds)
    invalidate_datasets_cache()
    return ds


@router.put("/{dataset_id}", response_model=DatasetOut)
def update_dataset(
    dataset_id: int,
    body: DatasetIn,
    _: User = Depends(require_role(Role.analyst, Role.admin)),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> Dataset:
    """Update an existing dataset's name and description. Invalidates cache."""
    ds = db.get(Dataset, dataset_id)
    if ds is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
    ds.name = body.name
    ds.description = body.description
    db.commit()
    db.refresh(ds)
    invalidate_datasets_cache()
    return ds


# ── Delete (admin only) ───────────────────────────────────────────────────────


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dataset(
    dataset_id: int,
    _: User = Depends(require_role(Role.admin)),  # noqa: B008
    db: Session = Depends(get_db),  # noqa: B008
) -> None:
    """Delete a dataset. Admin only. Invalidates cache."""
    ds = db.get(Dataset, dataset_id)
    if ds is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
    db.delete(ds)
    db.commit()
    invalidate_datasets_cache()
    return None
