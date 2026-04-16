"""Catalog taxonomy aliasing and canonical subtype helpers."""
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Set


@dataclass(frozen=True)
class CanonicalSubtype:
    """Canonical subtype contract metadata."""
    slug: str
    name: str


_CANONICAL_BY_SLUG: Dict[str, CanonicalSubtype] = {
    "crossbody": CanonicalSubtype(slug="crossbody", name="Crossbody"),
    "shoulder": CanonicalSubtype(slug="shoulder", name="Shoulder"),
    "top-handle": CanonicalSubtype(slug="top-handle", name="Top Handle"),
    "evening": CanonicalSubtype(slug="evening", name="Evening"),
}

# Forward aliases (raw slug -> canonical slug) for bags taxonomy.
_BAGS_ALIAS_TO_CANONICAL: Dict[str, str] = {
    "crossbody-bags": "crossbody",
    "crossbody": "crossbody",
    "sub-1": "crossbody",
    "shoulder-bags": "shoulder",
    "shoulder": "shoulder",
    "sub-2": "shoulder",
    "handbags": "top-handle",
    "top-handle": "top-handle",
    "top_handle": "top-handle",
    "sub-3": "top-handle",
    "sub-5": "top-handle",
    "clutches": "evening",
    "evening": "evening",
    "sub-4": "evening",
}

_CANONICAL_TO_ALIASES: Dict[str, Set[str]] = {}
for alias, canonical in _BAGS_ALIAS_TO_CANONICAL.items():
    _CANONICAL_TO_ALIASES.setdefault(canonical, set()).add(alias)
for canonical in _CANONICAL_BY_SLUG:
    _CANONICAL_TO_ALIASES.setdefault(canonical, set()).add(canonical)


def canonicalize_bags_subcategory(raw_slug: str) -> Optional[CanonicalSubtype]:
    """Map a bags subcategory slug to canonical subtype metadata."""
    canonical_slug = _BAGS_ALIAS_TO_CANONICAL.get(raw_slug)
    if not canonical_slug:
        return None
    return _CANONICAL_BY_SLUG[canonical_slug]


def bags_subcategory_aliases(raw_slug: str) -> List[str]:
    """Return stable aliases for a bags subcategory."""
    canonical = canonicalize_bags_subcategory(raw_slug)
    if not canonical:
        return [raw_slug]
    aliases = _CANONICAL_TO_ALIASES.get(canonical.slug, {canonical.slug})
    # Keep deterministic ordering for contract responses.
    return sorted(aliases)


def expand_bags_query_aliases(slugs: Iterable[str]) -> List[str]:
    """Expand canonical/alias slugs into all accepted raw slugs."""
    expanded: Set[str] = set()
    for slug in slugs:
        canonical = canonicalize_bags_subcategory(slug)
        if canonical:
            expanded.update(_CANONICAL_TO_ALIASES.get(canonical.slug, {canonical.slug}))
        expanded.add(slug)
    return sorted(expanded)
