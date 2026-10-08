# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
"""Port of Font Awesome icons to Material Symbols, in migrate_190_200."""

import unittest

from odoo_module_migrate.migration_scripts.migrate_190_200 import (
    FA_TO_ICON,
    OI_TO_ICON,
    port_content,
)


def port(text):
    reports = []
    content, changed = port_content(text, reports.append)
    return content, changed, reports


class TestIcons(unittest.TestCase):
    def assertPorted(self, before, after):
        content, changed, reports = port(before)
        self.assertEqual(content, after)
        self.assertTrue(changed)
        self.assertFalse(reports, "should not have reported anything")

    def assertReported(self, before, needle):
        content, changed, reports = port(before)
        self.assertEqual(content, before, "a reported case must be left untouched")
        self.assertFalse(changed)
        self.assertTrue(
            any(needle in r for r in reports),
            "expected a report about %r, got %r" % (needle, reports),
        )

    # --- migrated automatically ------------------------------------------------

    def test_filled_icon(self):
        # fa-pencil is one of the 71 entries Odoo's map marks as filled
        self.assertPorted(
            '<i class="fa fa-pencil"/>',
            '<i class="oi oi-filled" data-icon="edit"/>',
        )

    def test_outline_variant_keeps_the_glyph_and_drops_the_fill(self):
        self.assertPorted(
            '<span class="fa fa-fw fa-star-o text-muted"/>',
            '<span class="oi oi-fw text-muted" data-icon="star"/>',
        )
        self.assertPorted(
            '<span class="fa fa-star"/>',
            '<span class="oi oi-filled" data-icon="star"/>',
        )

    def test_brand_goes_to_the_odoo_ui_icons_font(self):
        self.assertPorted(
            '<i class="fa fa-facebook fa-2x"/>',
            '<i class="oi oi-2x" data-icon="oi_facebook"/>',
        )

    def test_legacy_oi_class(self):
        self.assertPorted(
            '<i class="oi oi-arrow-left"/>',
            '<i class="oi" data-icon="west"/>',
        )

    def test_icon_attribute_splits_into_icon_and_icon_class(self):
        self.assertPorted(
            '<button icon="fa-check text-success"/>',
            '<button icon="check" icon_class="text-success"/>',
        )

    def test_plain_icon_attribute(self):
        self.assertPorted('<button icon="fa-bars"/>', '<button icon="menu"/>')

    # --- left alone ------------------------------------------------------------

    def test_modifier_only_element_is_not_an_icon(self):
        content, changed, reports = port('<i class="oi oi-fw"/>')
        self.assertEqual(content, '<i class="oi oi-fw"/>')
        self.assertFalse(changed)
        self.assertFalse(reports, "a surviving modifier is not something to report")

    def test_dynamic_class_is_reported(self):
        self.assertReported(
            '<i t-attf-class="fa fa-{{ rec.icon }}"/>', "built at render time"
        )

    def test_unknown_icon_is_reported(self):
        # fa-solid belongs to Font Awesome 5: it never rendered under Odoo 19 either
        self.assertReported('<i class="fa fa-solid"/>', "no known Odoo 20 icon")

    def test_two_icons_on_one_element_are_reported(self):
        self.assertReported('<i class="fa fa-star fa-trash"/>', "no known Odoo 20 icon")

    def test_report_carries_the_line_number(self):
        _, _, reports = port('<odoo>\n\n<i t-attf-class="fa fa-{{ x }}"/>\n</odoo>')
        self.assertTrue(any(r.startswith("line 3:") for r in reports), reports)

    def test_xpath_selecting_on_an_icon_class_is_reported(self):
        # the view it inherits no longer has that class, so the module would not install
        self.assertReported(
            '<xpath expr="//div[i[hasclass(\'fa-clock-o\')]]/span" position="replace"/>',
            "fa-clock-o left in place",
        )

    def test_the_report_tells_which_icon_it_would_have_been(self):
        _, _, reports = port(
            '<xpath expr="//i[hasclass(\'fa-video-camera\')]" position="replace"/>'
        )
        self.assertTrue(any("it is videocam in Odoo 20" in r for r in reports), reports)

    def test_widget_options_icon(self):
        self.assertPorted(
            '<field name="x" widget="boolean_icon" options="{\'icon\': \'fa-repeat\'}"/>',
            '<field name="x" widget="boolean_icon" options="{\'icon\': \'redo\'}"/>',
        )

    def test_widget_options_icon_carries_the_fill(self):
        content, _, _ = port(
            "<field widget=\"boolean_icon\" options=\"{'icon': 'fa-star'}\"/>"
        )
        self.assertIn("'icon': 'star'", content)
        self.assertIn("'icon_class': 'oi-filled'", content)

    # --- safety ----------------------------------------------------------------

    def test_file_without_icons_is_untouched(self):
        text = "<odoo>\n  <record id='x'><field name='y'>hi</field></record>\n</odoo>\n"
        content, changed, reports = port(text)
        self.assertEqual(content, text)
        self.assertFalse(changed)
        self.assertFalse(reports)

    def test_already_migrated_file_is_untouched(self):
        text = (
            '<i class="oi oi-filled oi-fw" data-icon="delete"/>'
            '<i class="oi oi-2x oi-spin" data-icon="autorenew"/>'
            '<button icon="menu" icon_class="oi-filled"/>'
        )
        content, changed, reports = port(text)
        self.assertEqual(content, text)
        self.assertFalse(changed)
        self.assertFalse(reports, "a ported file must stay quiet, not report itself")

    def test_is_idempotent(self):
        before = '<i class="fa fa-pencil"/><button icon="fa-bars"/>'
        once, _, _ = port(before)
        twice, changed, _ = port(once)
        self.assertEqual(twice, once)
        self.assertFalse(changed, "a second run must be a no-op")

    # --- the tables themselves -------------------------------------------------

    def test_tables_are_not_empty_and_well_formed(self):
        self.assertGreater(len(FA_TO_ICON), 700)
        self.assertTrue(OI_TO_ICON)
        for table in (FA_TO_ICON, OI_TO_ICON):
            for key, value in table.items():
                self.assertTrue(key.startswith(("fa-", "oi-")), key)
                self.assertEqual(len(value), 2, key)
                self.assertIsInstance(value[0], str)
                self.assertIsInstance(value[1], bool)


if __name__ == "__main__":
    unittest.main()
