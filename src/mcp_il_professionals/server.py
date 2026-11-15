"""mcp-il-professionals — verify licensed professionals in Israel: real-estate brokers, registered
contractors, real-estate appraisers, CPAs, vehicle appraisers, licensed surveyors and private investigators.
Live data from data.gov.il (Ministries of Justice, Construction & Housing, Transport, Survey of Israel, CPA Council)."""
from __future__ import annotations

import asyncio
import os

from fastmcp import FastMCP

from . import __version__
from .ckan import datastore_search, meta

R_BROKERS = "a0f56034-88db-4132-8803-854bcdb01ca1"  # מאגר מתווכים פעילים
R_CONTRACTORS = "4eb61bd6-18cf-4e7c-9f9c-e166dfa0a2d8"  # פנקס הקבלנים הרשומים
R_APPRAISERS = "8540534a-eccd-4568-a677-652d589ed172"  # מאגר שמאי מקרקעין
R_CPAS = "7e86def9-0899-45f4-8942-d6fe38482b1a"  # מאגר רואי החשבון
R_VEHICLE_APPRAISERS = "4a434d65-3ca2-45e5-8026-5d9819c3f95c"  # שמאי רכב
R_SURVEYORS = "096e5fba-420c-4822-8172-78be54767cef"  # רשימת המודדים (מפ"י)
R_INVESTIGATORS = "a9ddb445-825f-4635-a573-fe82d2a95bf0"  # חוקרים פרטיים
R_INVESTIGATION_FIRMS = "94722051-b0c7-4f73-b543-c558c6c2c660"  # תאגידי חוקרים פרטיים


def _broker(r):
    return {"name": r.get("שם המתווך"), "license_number": r.get("מס רשיון"), "city": r.get("עיר מגורים"),
            "status": "active (listed in the active brokers registry)"}


def _appraiser(r):
    return {"name": r.get("שם שמאי"), "license_number": r.get("מספר רשיון"), "file_number": r.get("מספר תיק"),
            "city": r.get("עיר")}


def _cpa(r):
    return {"first_name": r.get("שם פרטי"), "last_name": r.get("שם משפחה"), "license_number": r.get("מספר רישיון"),
            "licensed_since": r.get("תאריך קבלת רישיון"), "city": r.get("ישוב"), "status": r.get("סטטוס")}


def _vehicle_appraiser(r):
    return {"first_name": r.get("shem_prati"), "last_name": r.get("shem_mishpaha"),
            "license_number": r.get("mispar_rishayon"), "city": r.get("yishuv")}


def _surveyor(r):
    return {"first_name": r.get("name1"), "last_name": r.get("family_name"), "license_number": r.get("number"),
            "status": r.get("status"), "notes": r.get("information"), "certificate": r.get("cer_link")}


def _investigator(r):
    return {"first_name": r.get("שם פרטי"), "last_name": r.get("שם משפחה"), "license_number": r.get("מספר רישיון")}


def _investigation_firm(r):
    return {"firm": r.get("שם תאגיד"), "license_number": r.get("מספר רישיון")}


def _contractor(r):
    return {
        "name": r.get("SHEM_YESHUT"), "contractor_number": r.get("MISPAR_KABLAN"),
        "company_or_id_number": r.get("MISPAR_YESHUT"), "branch": " ".join((r.get("TEUR_ANAF") or "").split()) or None,
        "branch_code": r.get("KOD_ANAF"), "group": r.get("KVUTZA"), "classification": r.get("SIVUG"),
        "classification_since": r.get("TARICH_SUG"), "registered_since": (r.get("TAARICH_KABLAN") or "")[:10] or None,
        "recognized_for_government_work": r.get("KABLAN_MUKAR"), "city": r.get("SHEM_YISHUV"),
        "address": " ".join(x for x in (r.get("SHEM_REHOV"), r.get("MISPAR_BAIT")) if x) or None,
        "phone": r.get("MISPAR_TEL"), "email": r.get("EMAIL"), "qualified_manager": r.get("OVDIM"),
        "notes": r.get("HEARA"),
    }


# profession -> (resource, mapper, license field, dataset label)
REGISTRIES = {
    "real_estate_broker": (R_BROKERS, _broker, "מס רשיון", "Ministry of Justice — licensed real-estate brokers"),
    "real_estate_appraiser": (R_APPRAISERS, _appraiser, "מספר רשיון", "Ministry of Justice — real-estate appraisers"),
    "cpa": (R_CPAS, _cpa, "מספר רישיון", "CPA Council — certified public accountants"),
    "vehicle_appraiser": (R_VEHICLE_APPRAISERS, _vehicle_appraiser, "mispar_rishayon",
                          "Ministry of Transport — vehicle appraisers"),
    "surveyor": (R_SURVEYORS, _surveyor, "number", "Survey of Israel — licensed surveyors"),
    "private_investigator": (R_INVESTIGATORS, _investigator, "מספר רישיון",
                             "Ministry of Justice — private investigators"),
    "investigation_firm": (R_INVESTIGATION_FIRMS, _investigation_firm, "מספר רישיון",
                           "Ministry of Justice — private investigation firms"),
    "contractor": (R_CONTRACTORS, _contractor, "MISPAR_KABLAN", "Registrar of Contractors — registered contractors"),
}
STRING_LICENSE = {"contractor"}  # stored as text in the dataset

NOT_OPEN = {
    "electrician": {
        "regulator": "Ministry of Labor — Electricians Licensing Unit (המחלקה לרישוי חשמלאים)",
        "how_to_verify": "Ask for the licence number and ID; check it in the Ministry of Labor online electrician "
                         "licence search. Licence grade matters (e.g. מוסמך / ראשי / בודק).",
        "info_page": "https://www.gov.il/he/departments/units/electricity-licensing-unit",
    },
    "engineer_or_architect": {
        "regulator": "Ministry of Labor — Registrar of Engineers and Architects (פנקס המהנדסים והאדריכלים)",
        "how_to_verify": "Use the Registrar's online search on gov.il; registration and licence are separate steps.",
    },
    "lawyer": {
        "regulator": "Israel Bar Association",
        "how_to_verify": "Use the Bar Association's public lawyer search.",
    },
}

mcp = FastMCP(
    "mcp-il-professionals",
    version=__version__,
    instructions=(
        "Verify Israeli licensed professionals before hiring. Professions: " + ", ".join(REGISTRIES)
        + ". Use find_contractors for registered building contractors by city/branch. Electricians, engineers and "
        "lawyers are not in open data — call list_professions for how to verify them. Names are Hebrew."
    ),
)


@mcp.tool
async def list_professions() -> dict:
    """Which professions can be verified here, and how to verify those that are not open data
    (electricians, engineers/architects, lawyers)."""
    return {
        "available": {k: v[3] for k, v in REGISTRIES.items()},
        "not_in_open_data": NOT_OPEN,
        **meta("data.gov.il catalogue"),
    }


@mcp.tool
async def verify_professional(profession: str, name: str = "", license_number: str = "", city: str = "",
                              limit: int = 20) -> dict:
    """Check that a person or firm holds a licence in an Israeli professional registry.

    Args:
        profession: one of real_estate_broker, real_estate_appraiser, cpa, vehicle_appraiser, surveyor,
            private_investigator, investigation_firm, contractor (or electrician / engineer_or_architect /
            lawyer — returns how to verify, these are not open data).
        name: full or partial name in Hebrew (e.g. "גריצר דורית").
        license_number: licence / registration number (exact match).
        city: optional city text to narrow name searches.
    """
    if profession in NOT_OPEN:
        return {"profession": profession, "open_data": False, **NOT_OPEN[profession]}
    if profession not in REGISTRIES:
        raise ValueError(f"Unknown profession. Choose from: {', '.join(list(REGISTRIES) + list(NOT_OPEN))}")
    rid, mapper, lic_field, label = REGISTRIES[profession]
    if license_number:
        digits = "".join(ch for ch in license_number if ch.isdigit())
        value = digits if profession in STRING_LICENSE else int(digits)
        res = await datastore_search(rid, filters={lic_field: value}, limit=20)
    elif name:
        q = " ".join(x for x in (name, city) if x)
        res = await datastore_search(rid, q=q, limit=max(1, min(limit, 100)))
    else:
        raise ValueError("Provide name or license_number")
    rows = [mapper(r) for r in res["records"]]
    return {
        "profession": profession,
        "found": bool(rows),
        "total": res["total"],
        "results": rows,
        "note": None if rows else "Not found. Check spelling (Hebrew), try the licence number, or the person may be "
        "unlicensed / inactive.",
        **meta(label),
    }


@mcp.tool
async def find_contractors(city: str = "", branch: str = "", name: str = "", classification: str = "",
                           group: str = "", government_recognized_only: bool = False, limit: int = 20) -> dict:
    """Registered building contractors (פנקס הקבלנים) by city, branch keyword, name and classification.

    Args:
        city: city in Hebrew (e.g. "מודיעין", "בת ים").
        branch: work type keyword, e.g. "שיפוצים", "בניה", "חשמלאות", "אינסטלציה", "מיזוג", "איטום", "כבישים".
        classification: financial-scope class "1"-"5" ("ק" = small). Higher allows larger projects.
        group: registry group letter "א", "ב", "ג"...
        government_recognized_only: only contractors recognized for government tenders (קבלן מוכר).
    """
    filters: dict = {}
    if classification:
        filters["SIVUG"] = classification
    if group:
        filters["KVUTZA"] = group
    q = " ".join(x for x in (name, city, branch) if x) or None
    res = await datastore_search(R_CONTRACTORS, q=q, filters=filters or None, limit=max(1, min(limit, 200)))
    rows = [_contractor(r) for r in res["records"]]
    if government_recognized_only:
        rows = [r for r in rows if (r.get("recognized_for_government_work") or "").startswith("מוכר")]
    return {
        "total_matches": res["total"],
        "results": rows,
        "legend": {"classification": "1 = smallest scope … 5 = unlimited; ק = small works",
                   "group": "Registry group letter within the branch"},
        **meta(REGISTRIES["contractor"][3]),
    }


@mcp.tool
async def contractor_profile(contractor_number: str = "", company_number: str = "") -> dict:
    """All registered branches and classifications for one contractor (by contractor number or company/ID number)."""
    if contractor_number:
        filters = {"MISPAR_KABLAN": "".join(c for c in contractor_number if c.isdigit())}
    elif company_number:
        filters = {"MISPAR_YESHUT": "".join(c for c in company_number if c.isdigit())}
    else:
        raise ValueError("Provide contractor_number or company_number")
    res = await datastore_search(R_CONTRACTORS, filters=filters, limit=100)
    rows = [_contractor(r) for r in res["records"]]
    if not rows:
        return {"found": False, **meta(REGISTRIES["contractor"][3])}
    head = {k: rows[0][k] for k in ("name", "contractor_number", "company_or_id_number", "city", "address", "phone",
                                     "email", "registered_since")}
    branches = [{k: r[k] for k in ("branch", "group", "classification", "classification_since",
                                    "recognized_for_government_work", "qualified_manager")} for r in rows]
    return {"found": True, "contractor": head, "branches": branches, **meta(REGISTRIES["contractor"][3])}


@mcp.tool
async def search_all_registries(name: str, limit_per_registry: int = 5) -> dict:
    """Search a name across every professional registry at once — useful to see all licences a person holds."""
    lim = max(1, min(limit_per_registry, 20))
    keys = list(REGISTRIES)
    res = await asyncio.gather(*(datastore_search(REGISTRIES[k][0], q=name, limit=lim) for k in keys),
                               return_exceptions=True)
    out, errors = {}, {}
    for k, r in zip(keys, res, strict=True):
        if isinstance(r, Exception):
            errors[k] = str(r)
        elif r["records"]:
            out[k] = {"total": r["total"], "results": [REGISTRIES[k][1](x) for x in r["records"]]}
    body = {"query": name, "matches": out, **meta([v[3] for v in REGISTRIES.values()])}
    if errors:
        body["errors"] = errors
    return body


@mcp.tool
async def health() -> dict:
    """Check that the server can reach data.gov.il."""
    try:
        res = await datastore_search(R_CONTRACTORS, limit=1)
        return {"status": "ok", "registered_contractor_rows": res["total"], **meta(REGISTRIES["contractor"][3])}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "error": str(exc)}


def main() -> None:
    if os.environ.get("MCP_TRANSPORT", "stdio") == "stdio":
        mcp.run()
    else:
        mcp.run(transport="http", host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))


if __name__ == "__main__":
    main()
