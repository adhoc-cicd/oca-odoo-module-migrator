# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo_module_migrate.base_migration_script import BaseMigrationScript

_TEXT_REPLACES = {
    ".py": {
        r"\.get_xml_id\(": ".get_external_id(",
        r"\.fields_get_keys\(\)": "._fields",
    },
}

_RENAMED_MODELS = [
    ("stock.production.lot", "stock.lot", None),
]

_REMOVED_MODELS = [
    ("account.account.type",
        "Commit https://github.com/odoo/odoo/commit/26b2472f4977ccedbb0b5ed5f")
]


class MigrationScript(BaseMigrationScript):
    _TEXT_REPLACES = _TEXT_REPLACES
    _RENAMED_MODELS = _RENAMED_MODELS
    _REMOVED_MODELS = _REMOVED_MODELS
