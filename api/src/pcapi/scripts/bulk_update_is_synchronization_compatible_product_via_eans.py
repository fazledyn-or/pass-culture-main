import logging
from typing import Iterable

import pcapi.core.offers.models as offers_models
from pcapi.models import db


logger = logging.getLogger(__name__)


def process_batch(eans: list[str], is_synchronization_compatible: bool) -> None:
    logger.info(
        "Bulk-update products isSynchronizationCompatible=%s", is_synchronization_compatible, extra={"eans": eans}
    )
    products = offers_models.Product.query.filter(offers_models.Product.extraData["ean"].astext.in_(eans))
    updated_products_count = products.update(
        {"isSynchronizationCompatible": is_synchronization_compatible}, synchronize_session=False
    )
    db.session.commit()
    logger.info(
        "Finished bulk-update products isSynchronizationCompatible=%s",
        is_synchronization_compatible,
        extra={
            "eans": eans,
            "updated_products_count": updated_products_count,
        },
    )


def bulk_update_is_synchronization_compatible_via_eans(
    iterable: Iterable[str], is_synchronization_compatible: bool, batch_size: int
) -> None:
    total = 0
    batch = []

    for line in iterable:
        ean = line.strip()
        batch.append(ean)
        total += 1
        if len(batch) == batch_size:
            process_batch(batch, is_synchronization_compatible=is_synchronization_compatible)
            batch = []
    if batch:
        process_batch(batch, is_synchronization_compatible=is_synchronization_compatible)
    print("Count %i", total)


def bulk_mark_synchronization_compatible_product_from_path(path: str, batch_size: int) -> None:
    """Script à lancer en passant en premier paramètre le path d'un fichier csv avec une colonne contenant les eans
    à passer en synchronisable"""
    with open(path, encoding="utf-8") as fp:
        return bulk_update_is_synchronization_compatible_via_eans(
            fp, is_synchronization_compatible=True, batch_size=batch_size
        )


def bulk_mark_not_synchronization_compatible_product_from_path(path: str, batch_size: int) -> None:
    """Script à lancer en passant en premier paramètre le path d'un fichier csv avec une colonne contenant les eans
    à passer en non synchronisable"""
    with open(path, encoding="utf-8") as fp:
        return bulk_update_is_synchronization_compatible_via_eans(
            fp, is_synchronization_compatible=False, batch_size=batch_size
        )
