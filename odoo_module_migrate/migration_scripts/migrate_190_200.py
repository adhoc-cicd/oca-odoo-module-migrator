# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import csv
import io
import os
import re

from odoo_module_migrate.base_migration_script import BaseMigrationScript

_OLD_ACCESS_FILE = "ir.model.access.csv"
_NEW_ACCESS_FILE = "ir.access.csv"
_NEW_ACCESS_HEADER = ["id", "name", "model_id", "group_id/id", "operation", "domain"]
# Odoo 20 spells the operations in this fixed order.
_PERM_COLUMNS = [
    ("c", "perm_create"),
    ("r", "perm_read"),
    ("u", "perm_write"),
    ("d", "perm_unlink"),
]
_MODEL_NAME_RE = re.compile(r"""^\s*_name\s*=\s*(['"])([\w.]+)\1""", re.MULTILINE)


def _models_by_table(module_path, tools):
    """Map table name -> model name for the models defined in the module."""
    res = {}
    for file in tools.get_files(module_path, (".py",)):
        for _quote, model in _MODEL_NAME_RE.findall(tools._read_content(file)):
            res[model.replace(".", "_")] = model
    return res


def _model_from_xmlid(xmlid, models_by_table, logger, file):
    """'module.model_res_partner' -> 'res.partner'.

    Without a database the table name is ambiguous when the model name has
    underscores, so models defined in the module are resolved first and the
    rest falls back to replacing '_' by '.' with a warning.
    """
    ref = xmlid.split(".")[-1]
    table = ref[len("model_") :] if ref.startswith("model_") else ref
    if table in models_by_table:
        return models_by_table[table]
    model = table.replace("_", ".")
    logger.warning(
        "[20] '%s' resolved to model '%s' by name only: check it in %s"
        % (xmlid, model, file)
    )
    return model


def migrate_ir_model_access_to_ir_access(
    logger, module_path, module_name, manifest_path, migration_steps, tools
):
    """Convert security/ir.model.access.csv to the ir.access.csv of Odoo 20.

    Odoo ships odoo/upgrade_code/19.4-00-ir-access.py, which also folds the
    ir.rule records into the domain column, but it needs a database. This
    conversion only covers the CSV; ir.rule records are reported by text_errors.
    """
    models_by_table = _models_by_table(module_path, tools)
    for old_file in tools.get_files(module_path, (".csv",)):
        if old_file.name != _OLD_ACCESS_FILE:
            continue
        reader = csv.DictReader(io.StringIO(tools._read_content(old_file)))
        output = io.StringIO()
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow(_NEW_ACCESS_HEADER)
        for row in reader:
            model_xmlid = row.get("model_id:id") or row.get("model_id/id") or ""
            group_xmlid = row.get("group_id:id") or row.get("group_id/id") or ""
            operation = "".join(
                letter
                for letter, column in _PERM_COLUMNS
                if (row.get(column) or "0").strip() not in ("0", "", "False")
            )
            if not operation:
                logger.warning(
                    "[20] access '%s' grants no operation and will be dropped by"
                    " Odoo: check %s" % (row.get("id"), old_file)
                )
            writer.writerow(
                [
                    row.get("id", ""),
                    row.get("name", ""),
                    _model_from_xmlid(model_xmlid, models_by_table, logger, old_file),
                    group_xmlid,
                    operation,
                    "",
                ]
            )
        new_file = old_file.with_name(_NEW_ACCESS_FILE)
        tools._write_content(new_file, output.getvalue())
        os.remove(old_file)
        logger.info("Converted %s to %s" % (old_file, new_file))

    tools._replace_in_file(
        manifest_path,
        {re.escape(_OLD_ACCESS_FILE): _NEW_ACCESS_FILE},
        "Replace %s by %s in manifest" % (_OLD_ACCESS_FILE, _NEW_ACCESS_FILE),
    )


# ---------------------------------------------------------------------------
# Font Awesome -> Material Symbols
# ---------------------------------------------------------------------------

# Odoo's own Font Awesome 4.7 -> Material Symbols map, taken verbatim from
# addons/web/static/src/webclient/icons_mappings/fa_to_ms.scss at
# odoo/odoo@aefaec8 -- the commit before odoo/odoo@6883d73 deleted it, once the
# codebase had been ported and the table had no further use upstream. Nothing
# here is inferred: every entry is the icon Odoo itself chose as the equivalent.
# {"class": (data-icon, whether it needs the oi-filled class)}.
# Entries whose glyph is absent from the fonts Odoo ships are left out on
# purpose, so they are reported instead of silently rendering nothing: the Font
# Awesome logos, and fa-ils / fa-krw / fa-registered, which the map sent to a
# literal character rather than to an icon.
FA_TO_ICON = {
    "fa-500px": ("oi_500px", False),
    "fa-address-book": ("contact_page", True),
    "fa-address-book-o": ("contact_page", False),
    "fa-address-card": ("contact_mail", True),
    "fa-address-card-o": ("contact_mail", False),
    "fa-adjust": ("contrast", False),
    "fa-adn": ("oi_adn", False),
    "fa-align-center": ("format_align_center", False),
    "fa-align-justify": ("format_align_justify", False),
    "fa-align-left": ("format_align_left", False),
    "fa-align-right": ("format_align_right", False),
    "fa-amazon": ("oi_amazon", False),
    "fa-ambulance": ("emergency", False),
    "fa-american-sign-language-interpreting": ("sign_language", False),
    "fa-anchor": ("anchor", False),
    "fa-android": ("oi_android", False),
    "fa-angellist": ("oi_angellist", False),
    "fa-angle-double-down": ("keyboard_double_arrow_down", False),
    "fa-angle-double-left": ("keyboard_double_arrow_left", False),
    "fa-angle-double-right": ("keyboard_double_arrow_right", False),
    "fa-angle-double-up": ("keyboard_double_arrow_up", False),
    "fa-angle-down": ("keyboard_arrow_down", False),
    "fa-angle-left": ("keyboard_arrow_left", False),
    "fa-angle-right": ("keyboard_arrow_right", False),
    "fa-angle-up": ("keyboard_arrow_up", False),
    "fa-apple": ("oi_apple", False),
    "fa-archive": ("archive", False),
    "fa-area-chart": ("area_chart", False),
    "fa-arrow-circle-down": ("arrow_circle_down", True),
    "fa-arrow-circle-left": ("arrow_circle_left", True),
    "fa-arrow-circle-o-down": ("arrow_circle_down", False),
    "fa-arrow-circle-o-left": ("arrow_circle_left", False),
    "fa-arrow-circle-o-right": ("arrow_circle_right", False),
    "fa-arrow-circle-o-up": ("arrow_circle_up", False),
    "fa-arrow-circle-right": ("arrow_circle_right", True),
    "fa-arrow-circle-up": ("arrow_circle_up", True),
    "fa-arrow-down": ("arrow_downward", False),
    "fa-arrow-left": ("arrow_back", False),
    "fa-arrow-right": ("arrow_forward", False),
    "fa-arrow-up": ("arrow_upward", False),
    "fa-arrows": ("open_with", False),
    "fa-arrows-alt": ("open_with", False),
    "fa-arrows-h": ("swap_horiz", False),
    "fa-arrows-v": ("swap_vert", False),
    "fa-asl-interpreting": ("sign_language", False),
    "fa-assistive-listening-systems": ("hearing", False),
    "fa-asterisk": ("emergency", False),
    "fa-at": ("alternate_email", False),
    "fa-audio-description": ("audio_description", False),
    "fa-automobile": ("directions_car", False),
    "fa-backward": ("fast_rewind", False),
    "fa-balance-scale": ("balance", False),
    "fa-ban": ("block", False),
    "fa-bandcamp": ("oi_bandcamp", False),
    "fa-bank": ("account_balance", False),
    "fa-bar-chart": ("bar_chart", False),
    "fa-bar-chart-o": ("bar_chart", False),
    "fa-barcode": ("barcode", False),
    "fa-bars": ("menu", False),
    "fa-bath": ("bathtub", False),
    "fa-bathtub": ("bathtub", False),
    "fa-battery": ("battery_full", False),
    "fa-battery-0": ("battery_0_bar", False),
    "fa-battery-1": ("battery_2_bar", False),
    "fa-battery-2": ("battery_3_bar", False),
    "fa-battery-3": ("battery_5_bar", False),
    "fa-battery-4": ("battery_full", False),
    "fa-battery-empty": ("battery_0_bar", False),
    "fa-battery-full": ("battery_full", False),
    "fa-battery-half": ("battery_3_bar", False),
    "fa-battery-quarter": ("battery_2_bar", False),
    "fa-battery-three-quarters": ("battery_5_bar", False),
    "fa-bed": ("bed", False),
    "fa-beer": ("sports_bar", False),
    "fa-behance": ("oi_behance", False),
    "fa-behance-square": ("oi_behance-square", False),
    "fa-bell": ("notifications", True),
    "fa-bell-o": ("notifications", False),
    "fa-bell-slash": ("notifications_off", True),
    "fa-bell-slash-o": ("notifications_off", False),
    "fa-bicycle": ("directions_bike", False),
    "fa-binoculars": ("oi_binoculars", False),
    "fa-birthday-cake": ("cake", False),
    "fa-bitbucket": ("oi_bitbucket", False),
    "fa-bitbucket-square": ("oi_bitbucket-square", False),
    "fa-bitcoin": ("currency_bitcoin", False),
    "fa-black-tie": ("oi_black-tie", False),
    "fa-blind": ("blind", False),
    "fa-bluesky": ("oi_bluesky", False),
    "fa-bluetooth": ("bluetooth", False),
    "fa-bluetooth-b": ("bluetooth", False),
    "fa-bold": ("format_bold", False),
    "fa-bolt": ("flash_on", False),
    "fa-bomb": ("oi_bomb", False),
    "fa-book": ("book", False),
    "fa-bookmark": ("bookmark", True),
    "fa-bookmark-o": ("bookmark", False),
    "fa-braille": ("grain", False),
    "fa-briefcase": ("work", False),
    "fa-btc": ("currency_bitcoin", False),
    "fa-bug": ("bug_report", False),
    "fa-building": ("business", False),
    "fa-building-o": ("business", False),
    "fa-bullhorn": ("campaign", False),
    "fa-bullseye": ("crisis_alert", False),
    "fa-bus": ("directions_bus", False),
    "fa-buysellads": ("oi_buysellads", False),
    "fa-cab": ("local_taxi", False),
    "fa-calculator": ("calculate", False),
    "fa-calendar": ("calendar_today", True),
    "fa-calendar-check-o": ("event_available", False),
    "fa-calendar-minus-o": ("event_busy", False),
    "fa-calendar-o": ("calendar_today", False),
    "fa-calendar-plus-o": ("calendar_add_on", False),
    "fa-calendar-times-o": ("event_busy", False),
    "fa-camera": ("photo_camera", False),
    "fa-camera-retro": ("photo_camera", False),
    "fa-car": ("directions_car", False),
    "fa-caret-down": ("arrow_drop_down", False),
    "fa-caret-left": ("arrow_left", False),
    "fa-caret-right": ("arrow_right", False),
    "fa-caret-square-o-down": ("arrow_drop_down_circle", False),
    "fa-caret-square-o-left": ("arrow_circle_left", False),
    "fa-caret-square-o-right": ("arrow_circle_right", False),
    "fa-caret-square-o-up": ("arrow_circle_up", False),
    "fa-caret-up": ("arrow_drop_up", False),
    "fa-cart-arrow-down": ("shopping_cart_checkout", False),
    "fa-cart-plus": ("add_shopping_cart", False),
    "fa-cc": ("closed_caption", False),
    "fa-cc-amex": ("oi_cc-amex", False),
    "fa-cc-diners-club": ("oi_cc-diners-club", False),
    "fa-cc-discover": ("oi_cc-discover", False),
    "fa-cc-jcb": ("oi_cc-jcb", False),
    "fa-cc-mastercard": ("oi_cc-mastercard", False),
    "fa-cc-paypal": ("oi_cc-paypal", False),
    "fa-cc-stripe": ("oi_cc-stripe", False),
    "fa-cc-visa": ("oi_cc-visa", False),
    "fa-certificate": ("verified", False),
    "fa-chain": ("link", False),
    "fa-chain-broken": ("link_off", False),
    "fa-check": ("check", False),
    "fa-check-circle": ("check_circle", True),
    "fa-check-circle-o": ("check_circle", False),
    "fa-check-square": ("check_box", True),
    "fa-check-square-o": ("check_box", False),
    "fa-chevron-circle-down": ("expand_circle_down", True),
    "fa-chevron-circle-left": ("arrow_circle_left", True),
    "fa-chevron-circle-right": ("arrow_circle_right", True),
    "fa-chevron-circle-up": ("expand_circle_up", True),
    "fa-chevron-down": ("expand_more", False),
    "fa-chevron-left": ("chevron_left", False),
    "fa-chevron-right": ("chevron_right", False),
    "fa-chevron-up": ("expand_less", False),
    "fa-child": ("child_care", False),
    "fa-chrome": ("oi_chrome", False),
    "fa-circle": ("circle", True),
    "fa-circle-o": ("circle", False),
    "fa-circle-o-notch": ("autorenew", False),
    "fa-circle-thin": ("radio_button_unchecked", False),
    "fa-clipboard": ("assignment", False),
    "fa-clock-o": ("schedule", False),
    "fa-clone": ("content_copy", False),
    "fa-close": ("close", False),
    "fa-cloud": ("cloud", False),
    "fa-cloud-download": ("cloud_download", False),
    "fa-cloud-upload": ("cloud_upload", False),
    "fa-cny": ("currency_yen", False),
    "fa-code": ("code", False),
    "fa-code-fork": ("fork_right", False),
    "fa-codepen": ("oi_codepen", False),
    "fa-codiepie": ("oi_codiepie", False),
    "fa-coffee": ("coffee", False),
    "fa-cog": ("settings", True),
    "fa-cogs": ("settings_applications", False),
    "fa-columns": ("view_column", False),
    "fa-comment": ("chat_bubble", True),
    "fa-comment-o": ("chat_bubble", False),
    "fa-commenting": ("mode_comment", True),
    "fa-commenting-o": ("mode_comment", False),
    "fa-comments": ("forum", True),
    "fa-comments-o": ("forum", False),
    "fa-compass": ("explore", False),
    "fa-compress": ("close_fullscreen", False),
    "fa-connectdevelop": ("oi_connectdevelop", False),
    "fa-contao": ("oi_contao", False),
    "fa-copy": ("content_copy", False),
    "fa-copyright": ("copyright", False),
    "fa-creative-commons": ("oi_creative-commons", False),
    "fa-credit-card": ("credit_card", False),
    "fa-credit-card-alt": ("credit_card", False),
    "fa-crop": ("crop", False),
    "fa-crosshairs": ("my_location", False),
    "fa-css3": ("oi_css3", False),
    "fa-cube": ("deployed_code", False),
    "fa-cubes": ("inventory_2", False),
    "fa-cut": ("content_cut", False),
    "fa-cutlery": ("restaurant", False),
    "fa-dashboard": ("speed", False),
    "fa-dashcube": ("oi_dashcube", False),
    "fa-database": ("database", False),
    "fa-deaf": ("hearing_disabled", False),
    "fa-deafness": ("hearing_disabled", False),
    "fa-dedent": ("format_indent_decrease", False),
    "fa-delicious": ("oi_delicious", False),
    "fa-desktop": ("desktop_windows", False),
    "fa-deviantart": ("oi_deviantart", False),
    "fa-diamond": ("diamond", False),
    "fa-digg": ("oi_digg", False),
    "fa-discord": ("oi_discord", False),
    "fa-dollar": ("attach_money", False),
    "fa-dot-circle-o": ("radio_button_checked", False),
    "fa-download": ("download", False),
    "fa-dribbble": ("oi_dribbble", False),
    "fa-drivers-license": ("badge", True),
    "fa-drivers-license-o": ("badge", False),
    "fa-dropbox": ("oi_dropbox", False),
    "fa-drupal": ("oi_drupal", False),
    "fa-edge": ("oi_edge", False),
    "fa-edit": ("edit", True),
    "fa-eercast": ("oi_eercast", False),
    "fa-eject": ("eject", False),
    "fa-ellipsis-h": ("more_horiz", False),
    "fa-ellipsis-v": ("more_vert", False),
    "fa-empire": ("oi_empire", False),
    "fa-envelope": ("mail", True),
    "fa-envelope-o": ("mail", False),
    "fa-envelope-open": ("drafts", True),
    "fa-envelope-open-o": ("drafts", False),
    "fa-envelope-square": ("mail", True),
    "fa-envira": ("oi_envira", False),
    "fa-eraser": ("ink_eraser", False),
    "fa-etsy": ("oi_etsy", False),
    "fa-eur": ("euro", False),
    "fa-euro": ("euro", False),
    "fa-exchange": ("swap_horiz", False),
    "fa-exclamation": ("priority_high", False),
    "fa-exclamation-circle": ("error", True),
    "fa-exclamation-triangle": ("warning", False),
    "fa-expand": ("expand_content", False),
    "fa-expeditedssl": ("oi_expeditedssl", False),
    "fa-external-link": ("open_in_new", False),
    "fa-external-link-square": ("open_in_new", False),
    "fa-eye": ("visibility", False),
    "fa-eye-slash": ("visibility_off", False),
    "fa-eyedropper": ("colorize", False),
    "fa-facebook": ("oi_facebook", False),
    "fa-facebook-f": ("oi_facebook", False),
    "fa-facebook-official": ("oi_facebook-official", False),
    "fa-facebook-square": ("oi_facebook-square", False),
    "fa-fast-backward": ("fast_rewind", False),
    "fa-fast-forward": ("fast_forward", False),
    "fa-fax": ("fax", False),
    "fa-feed": ("rss_feed", False),
    "fa-female": ("female", False),
    "fa-fighter-jet": ("flight", False),
    "fa-file": ("description", True),
    "fa-file-archive-o": ("folder_zip", False),
    "fa-file-audio-o": ("audio_file", False),
    "fa-file-code-o": ("code", False),
    "fa-file-excel-o": ("table_chart", False),
    "fa-file-image-o": ("image", False),
    "fa-file-movie-o": ("video_file", False),
    "fa-file-o": ("description", False),
    "fa-file-pdf-o": ("picture_as_pdf", False),
    "fa-file-photo-o": ("image", False),
    "fa-file-picture-o": ("image", False),
    "fa-file-powerpoint-o": ("slideshow", False),
    "fa-file-sound-o": ("audio_file", False),
    "fa-file-text": ("article", True),
    "fa-file-text-o": ("article", False),
    "fa-file-video-o": ("video_file", False),
    "fa-file-word-o": ("description", False),
    "fa-file-zip-o": ("folder_zip", False),
    "fa-files-o": ("content_copy", False),
    "fa-film": ("movie", False),
    "fa-filter": ("filter_alt", True),
    "fa-fire": ("whatshot", False),
    "fa-fire-extinguisher": ("fire_extinguisher", False),
    "fa-firefox": ("oi_firefox", False),
    "fa-first-order": ("oi_first-order", False),
    "fa-flag": ("flag", True),
    "fa-flag-checkered": ("sports_score", False),
    "fa-flag-o": ("flag", False),
    "fa-flash": ("flash_on", False),
    "fa-flask": ("science", False),
    "fa-flickr": ("oi_flickr", False),
    "fa-floppy-o": ("save", False),
    "fa-folder": ("folder", True),
    "fa-folder-o": ("folder", False),
    "fa-folder-open": ("folder_open", True),
    "fa-folder-open-o": ("folder_open", False),
    "fa-font": ("font_download", False),
    "fa-fonticons": ("oi_fonticons", False),
    "fa-forumbee": ("oi_forumbee", False),
    "fa-forward": ("fast_forward", False),
    "fa-foursquare": ("oi_foursquare", False),
    "fa-free-code-camp": ("oi_free-code-camp", False),
    "fa-frown-o": ("sentiment_sad", False),
    "fa-futbol-o": ("sports_soccer", False),
    "fa-gamepad": ("stadia_controller", False),
    "fa-gavel": ("gavel", False),
    "fa-gbp": ("currency_pound", False),
    "fa-ge": ("oi_empire", False),
    "fa-gear": ("settings", True),
    "fa-gears": ("settings_applications", False),
    "fa-genderless": ("radio_button_unchecked", False),
    "fa-get-pocket": ("oi_get-pocket", False),
    "fa-gg": ("oi_gg", False),
    "fa-gg-circle": ("oi_gg-circle", False),
    "fa-gift": ("card_giftcard", False),
    "fa-git": ("oi_git", False),
    "fa-git-square": ("oi_git-square", False),
    "fa-github": ("oi_github", False),
    "fa-github-alt": ("oi_github-alt", False),
    "fa-github-square": ("oi_github-square", False),
    "fa-gitlab": ("oi_gitlab", False),
    "fa-gittip": ("oi_gittip", False),
    "fa-glass": ("local_bar", False),
    "fa-glide": ("oi_glide", False),
    "fa-glide-g": ("oi_glide-g", False),
    "fa-globe": ("public", False),
    "fa-google": ("oi_google", False),
    "fa-google-play": ("oi_google-play", False),
    "fa-google-plus": ("oi_google-plus", False),
    "fa-google-plus-circle": ("oi_google-plus-circle", False),
    "fa-google-plus-official": ("oi_google-plus-circle", False),
    "fa-google-plus-square": ("oi_google-plus-square", False),
    "fa-google-wallet": ("oi_google-wallet", False),
    "fa-graduation-cap": ("school", False),
    "fa-gratipay": ("oi_gittip", False),
    "fa-grav": ("oi_grav", False),
    "fa-group": ("group", True),
    "fa-h-square": ("local_hospital", False),
    "fa-hacker-news": ("oi_hacker-news", False),
    "fa-hand-grab-o": ("back_hand", False),
    "fa-hand-lizard-o": ("oi_hand-lizard-o", False),
    "fa-hand-o-down": ("arrow_downward", False),
    "fa-hand-o-left": ("arrow_back", False),
    "fa-hand-o-right": ("arrow_forward", False),
    "fa-hand-o-up": ("arrow_upward", False),
    "fa-hand-paper-o": ("back_hand", False),
    "fa-hand-peace-o": ("oi_hand-peace-o", False),
    "fa-hand-pointer-o": ("pan_tool_alt", False),
    "fa-hand-rock-o": ("back_hand", False),
    "fa-hand-scissors-o": ("oi_hand-scissors-o", False),
    "fa-hand-spock-o": ("oi_hand-spock-o", False),
    "fa-hand-stop-o": ("back_hand", False),
    "fa-handshake-o": ("handshake", False),
    "fa-hard-of-hearing": ("hearing_disabled", False),
    "fa-hashtag": ("tag", False),
    "fa-hdd-o": ("storage", False),
    "fa-header": ("title", False),
    "fa-headphones": ("headphones", False),
    "fa-heart": ("favorite", True),
    "fa-heart-o": ("favorite", False),
    "fa-heartbeat": ("cardiology", False),
    "fa-history": ("history", False),
    "fa-home": ("home", False),
    "fa-hospital-o": ("local_hospital", False),
    "fa-hotel": ("bed", False),
    "fa-hourglass": ("hourglass_empty", False),
    "fa-hourglass-1": ("hourglass_top", False),
    "fa-hourglass-2": ("hourglass_bottom", False),
    "fa-hourglass-3": ("hourglass_disabled", False),
    "fa-hourglass-end": ("hourglass_disabled", False),
    "fa-hourglass-half": ("hourglass_bottom", False),
    "fa-hourglass-o": ("hourglass_empty", False),
    "fa-hourglass-start": ("hourglass_top", False),
    "fa-houzz": ("oi_houzz", False),
    "fa-html5": ("oi_html5", False),
    "fa-i-cursor": ("text_fields", False),
    "fa-id-badge": ("badge", False),
    "fa-id-card": ("badge", True),
    "fa-id-card-o": ("badge", False),
    "fa-image": ("image", False),
    "fa-imdb": ("oi_imdb", False),
    "fa-inbox": ("inbox", False),
    "fa-indent": ("format_indent_increase", False),
    "fa-industry": ("factory", False),
    "fa-info": ("info", False),
    "fa-info-circle": ("info", True),
    "fa-inr": ("currency_rupee", False),
    "fa-instagram": ("oi_instagram", False),
    "fa-institution": ("account_balance", False),
    "fa-internet-explorer": ("oi_internet-explorer", False),
    "fa-intersex": ("transgender", False),
    "fa-ioxhost": ("oi_ioxhost", False),
    "fa-italic": ("format_italic", False),
    "fa-joomla": ("oi_joomla", False),
    "fa-jpy": ("currency_yen", False),
    "fa-jsfiddle": ("oi_jsfiddle", False),
    "fa-key": ("key", False),
    "fa-keyboard-o": ("keyboard", False),
    "fa-kickstarter": ("oi_kickstarter", False),
    "fa-language": ("translate", False),
    "fa-laptop": ("laptop", False),
    "fa-lastfm": ("oi_lastfm", False),
    "fa-lastfm-square": ("oi_lastfm-square", False),
    "fa-leaf": ("eco", False),
    "fa-leanpub": ("oi_leanpub", False),
    "fa-legal": ("gavel", False),
    "fa-lemon-o": ("oi_lemon-o", False),
    "fa-level-down": ("subdirectory_arrow_right", False),
    "fa-level-up": ("subdirectory_arrow_left", False),
    "fa-life-bouy": ("support", False),
    "fa-life-buoy": ("support", False),
    "fa-life-ring": ("support", False),
    "fa-life-saver": ("support", False),
    "fa-lightbulb-o": ("lightbulb", False),
    "fa-line-chart": ("show_chart", False),
    "fa-link": ("link", False),
    "fa-linkedin": ("oi_linkedin", False),
    "fa-linkedin-square": ("oi_linkedin-square", False),
    "fa-linode": ("oi_linode", False),
    "fa-linux": ("oi_linux", False),
    "fa-list": ("format_list_bulleted", False),
    "fa-list-alt": ("list_alt", False),
    "fa-list-ol": ("format_list_numbered", False),
    "fa-list-ul": ("format_list_bulleted", False),
    "fa-location-arrow": ("near_me", False),
    "fa-lock": ("lock", False),
    "fa-long-arrow-down": ("south", False),
    "fa-long-arrow-left": ("west", False),
    "fa-long-arrow-right": ("east", False),
    "fa-long-arrow-up": ("north", False),
    "fa-low-vision": ("visibility_off", False),
    "fa-magic": ("wand_stars", False),
    "fa-magnet": ("oi_magnet", False),
    "fa-mail-forward": ("share", False),
    "fa-mail-reply": ("reply", False),
    "fa-mail-reply-all": ("reply_all", False),
    "fa-male": ("male", False),
    "fa-map": ("map", False),
    "fa-map-marker": ("location_on", False),
    "fa-map-o": ("map", False),
    "fa-map-pin": ("push_pin", False),
    "fa-map-signs": ("signpost", False),
    "fa-mars": ("male", False),
    "fa-mars-double": ("oi_mars-double", False),
    "fa-mars-stroke": ("oi_mars-stroke", False),
    "fa-mars-stroke-h": ("oi_mars-stroke-h", False),
    "fa-mars-stroke-v": ("oi_mars-stroke-v", False),
    "fa-maxcdn": ("oi_maxcdn", False),
    "fa-meanpath": ("oi_meanpath", False),
    "fa-medium": ("oi_medium", False),
    "fa-medkit": ("medical_services", False),
    "fa-meetup": ("oi_meetup", False),
    "fa-meh-o": ("sentiment_neutral", False),
    "fa-mercury": ("oi_mercury", False),
    "fa-microchip": ("memory", False),
    "fa-microphone": ("mic", False),
    "fa-microphone-slash": ("mic_off", False),
    "fa-minus": ("remove", False),
    "fa-minus-circle": ("remove_circle", True),
    "fa-minus-square": ("indeterminate_check_box", True),
    "fa-minus-square-o": ("indeterminate_check_box", False),
    "fa-mixcloud": ("oi_mixcloud", False),
    "fa-mobile": ("smartphone", False),
    "fa-mobile-phone": ("smartphone", False),
    "fa-modx": ("oi_modx", False),
    "fa-money": ("payments", False),
    "fa-moon-o": ("dark_mode", False),
    "fa-mortar-board": ("school", False),
    "fa-motorcycle": ("two_wheeler", False),
    "fa-mouse-pointer": ("arrow_selector_tool", True),
    "fa-music": ("music_note", False),
    "fa-navicon": ("menu", False),
    "fa-neuter": ("oi_neuter", False),
    "fa-newspaper-o": ("newspaper", False),
    "fa-object-group": ("select_all", False),
    "fa-object-ungroup": ("deselect", False),
    "fa-odnoklassniki": ("oi_odnoklassniki", False),
    "fa-odnoklassniki-square": ("oi_odnoklassniki-square", False),
    "fa-opencart": ("oi_opencart", False),
    "fa-openid": ("oi_openid", False),
    "fa-opera": ("oi_opera", False),
    "fa-optin-monster": ("oi_optin-monster", False),
    "fa-outdent": ("format_indent_decrease", False),
    "fa-pagelines": ("oi_pagelines", False),
    "fa-paint-brush": ("brush", False),
    "fa-paper-plane": ("send", True),
    "fa-paper-plane-o": ("send", False),
    "fa-paperclip": ("attach_file", False),
    "fa-paragraph": ("format_paragraph", False),
    "fa-paste": ("content_paste", False),
    "fa-pause": ("pause", False),
    "fa-pause-circle": ("pause_circle", True),
    "fa-pause-circle-o": ("pause_circle", False),
    "fa-paw": ("pets", False),
    "fa-paypal": ("oi_paypal", False),
    "fa-pencil": ("edit", True),
    "fa-pencil-square": ("edit_square", True),
    "fa-pencil-square-o": ("edit_square", False),
    "fa-percent": ("percent", False),
    "fa-phone": ("phone", True),
    "fa-phone-square": ("phone", True),
    "fa-photo": ("image", False),
    "fa-picture-o": ("image", False),
    "fa-pie-chart": ("pie_chart", False),
    "fa-pied-piper": ("oi_pied-piper", False),
    "fa-pied-piper-alt": ("oi_pied-piper-alt", False),
    "fa-pied-piper-pp": ("oi_pied-piper-pp", False),
    "fa-pinterest": ("oi_pinterest", False),
    "fa-pinterest-p": ("oi_pinterest-p", False),
    "fa-pinterest-square": ("oi_pinterest-square", False),
    "fa-plane": ("travel", False),
    "fa-play": ("play_arrow", False),
    "fa-play-circle": ("play_circle", True),
    "fa-play-circle-o": ("play_circle", False),
    "fa-plug": ("power", False),
    "fa-plus": ("add", False),
    "fa-plus-circle": ("add_circle", True),
    "fa-plus-square": ("add_box", True),
    "fa-plus-square-o": ("add_box", False),
    "fa-podcast": ("podcasts", False),
    "fa-power-off": ("power_settings_new", False),
    "fa-print": ("print", False),
    "fa-product-hunt": ("oi_product-hunt", False),
    "fa-puzzle-piece": ("extension", False),
    "fa-qq": ("oi_qq", False),
    "fa-qrcode": ("qr_code", False),
    "fa-question": ("question_mark", False),
    "fa-question-circle": ("help", True),
    "fa-question-circle-o": ("help_outline", False),
    "fa-quora": ("oi_quora", False),
    "fa-quote-left": ("format_quote", False),
    "fa-quote-right": ("format_quote", False),
    "fa-ra": ("oi_ra", False),
    "fa-random": ("shuffle", False),
    "fa-ravelry": ("oi_ravelry", False),
    "fa-rebel": ("oi_ra", False),
    "fa-recycle": ("recycling", False),
    "fa-reddit": ("oi_reddit", False),
    "fa-reddit-alien": ("oi_reddit-alien", False),
    "fa-reddit-square": ("oi_reddit-square", False),
    "fa-refresh": ("refresh", False),
    "fa-remove": ("close", False),
    "fa-renren": ("oi_renren", False),
    "fa-reorder": ("menu", False),
    "fa-repeat": ("redo", False),
    "fa-reply": ("reply", False),
    "fa-reply-all": ("reply_all", False),
    "fa-resistance": ("oi_ra", False),
    "fa-retweet": ("repeat", False),
    "fa-rmb": ("currency_yen", False),
    "fa-road": ("road", False),
    "fa-rocket": ("rocket_launch", False),
    "fa-rotate-left": ("undo", False),
    "fa-rotate-right": ("redo", False),
    "fa-rouble": ("currency_ruble", False),
    "fa-rss": ("rss_feed", False),
    "fa-rss-square": ("rss_feed", False),
    "fa-rub": ("currency_ruble", False),
    "fa-ruble": ("currency_ruble", False),
    "fa-rupee": ("currency_rupee", False),
    "fa-s15": ("bathtub", False),
    "fa-safari": ("oi_safari", False),
    "fa-save": ("save", False),
    "fa-scissors": ("content_cut", False),
    "fa-scribd": ("oi_scribd", False),
    "fa-search": ("search", False),
    "fa-search-minus": ("zoom_out", False),
    "fa-search-plus": ("zoom_in", False),
    "fa-sellsy": ("oi_sellsy", False),
    "fa-send": ("send", True),
    "fa-send-o": ("send", False),
    "fa-server": ("dns", False),
    "fa-share": ("share", False),
    "fa-share-alt": ("share", True),
    "fa-share-alt-square": ("share", False),
    "fa-share-square": ("share", False),
    "fa-share-square-o": ("share", False),
    "fa-shield": ("security", False),
    "fa-ship": ("directions_boat", False),
    "fa-shirtsinbulk": ("oi_shirtsinbulk", False),
    "fa-shopping-bag": ("shopping_bag", False),
    "fa-shopping-basket": ("shopping_basket", False),
    "fa-shopping-cart": ("shopping_cart", False),
    "fa-shower": ("shower", False),
    "fa-sign-in": ("login", False),
    "fa-sign-language": ("sign_language", False),
    "fa-sign-out": ("logout", False),
    "fa-signal": ("signal_cellular_4_bar", False),
    "fa-signing": ("sign_language", False),
    "fa-simplybuilt": ("oi_simplybuilt", False),
    "fa-sitemap": ("account_tree", False),
    "fa-skyatlas": ("oi_skyatlas", False),
    "fa-skype": ("oi_skype", False),
    "fa-slack": ("oi_slack", False),
    "fa-sliders": ("tune", False),
    "fa-slideshare": ("oi_slideshare", False),
    "fa-smile-o": ("sentiment_satisfied", False),
    "fa-snapchat": ("oi_snapchat", False),
    "fa-snapchat-ghost": ("oi_snapchat-ghost", False),
    "fa-snapchat-square": ("oi_snapchat-square", False),
    "fa-snowflake-o": ("ac_unit", False),
    "fa-soccer-ball-o": ("sports_soccer", False),
    "fa-sort": ("swap_vert", False),
    "fa-sort-alpha-asc": ("sort_by_alpha", False),
    "fa-sort-alpha-desc": ("sort_by_alpha", False),
    "fa-sort-amount-asc": ("sort", False),
    "fa-sort-amount-desc": ("sort", False),
    "fa-sort-asc": ("arrow_upward", False),
    "fa-sort-desc": ("arrow_downward", False),
    "fa-sort-down": ("arrow_downward", False),
    "fa-sort-numeric-asc": ("sort", False),
    "fa-sort-numeric-desc": ("sort", False),
    "fa-sort-up": ("arrow_upward", False),
    "fa-soundcloud": ("oi_soundcloud", False),
    "fa-space-shuttle": ("rocket", False),
    "fa-spinner": ("progress_activity", False),
    "fa-spoon": ("restaurant", False),
    "fa-spotify": ("oi_spotify", False),
    "fa-square": ("square", True),
    "fa-square-o": ("square", False),
    "fa-stack-exchange": ("oi_stack-exchange", False),
    "fa-stack-overflow": ("oi_stack-overflow", False),
    "fa-star": ("star", True),
    "fa-star-half": ("star_half", False),
    "fa-star-half-empty": ("star_half", False),
    "fa-star-half-full": ("star_half", False),
    "fa-star-half-o": ("star_half", False),
    "fa-star-o": ("star", False),
    "fa-steam": ("oi_steam", False),
    "fa-steam-square": ("oi_steam-square", False),
    "fa-step-backward": ("skip_previous", False),
    "fa-step-forward": ("skip_next", False),
    "fa-stethoscope": ("stethoscope", False),
    "fa-sticky-note": ("sticky_note_2", True),
    "fa-sticky-note-o": ("sticky_note_2", False),
    "fa-stop": ("stop", False),
    "fa-stop-circle": ("stop_circle", True),
    "fa-stop-circle-o": ("stop_circle", False),
    "fa-strava": ("oi_strava", False),
    "fa-street-view": ("streetview", False),
    "fa-strikethrough": ("strikethrough_s", False),
    "fa-stumbleupon": ("oi_stumbleupon", False),
    "fa-stumbleupon-circle": ("oi_stumbleupon-circle", False),
    "fa-subscript": ("subscript", False),
    "fa-subway": ("subway", False),
    "fa-suitcase": ("luggage", False),
    "fa-sun-o": ("light_mode", False),
    "fa-superpowers": ("oi_superpowers", False),
    "fa-superscript": ("superscript", False),
    "fa-support": ("support", False),
    "fa-table": ("table_chart", False),
    "fa-tablet": ("tablet", False),
    "fa-tachometer": ("speed", False),
    "fa-tag": ("label", False),
    "fa-tags": ("sell", False),
    "fa-tasks": ("checklist", False),
    "fa-taxi": ("local_taxi", False),
    "fa-telegram": ("oi_telegram", False),
    "fa-television": ("tv", False),
    "fa-tencent-weibo": ("oi_tencent-weibo", False),
    "fa-terminal": ("terminal", False),
    "fa-text-height": ("height", False),
    "fa-text-width": ("width", False),
    "fa-th": ("grid_view", False),
    "fa-th-large": ("view_module", False),
    "fa-th-list": ("view_list", False),
    "fa-themeisle": ("oi_themeisle", False),
    "fa-thermometer": ("device_thermostat", False),
    "fa-thermometer-0": ("device_thermostat", False),
    "fa-thermometer-1": ("device_thermostat", False),
    "fa-thermometer-2": ("device_thermostat", False),
    "fa-thermometer-3": ("device_thermostat", False),
    "fa-thermometer-4": ("device_thermostat", False),
    "fa-thermometer-empty": ("device_thermostat", False),
    "fa-thermometer-full": ("device_thermostat", False),
    "fa-thermometer-half": ("device_thermostat", False),
    "fa-thermometer-quarter": ("device_thermostat", False),
    "fa-thermometer-three-quarters": ("device_thermostat", False),
    "fa-threads": ("oi_threads", False),
    "fa-thumb-tack": ("push_pin", False),
    "fa-thumbs-down": ("thumb_down", True),
    "fa-thumbs-o-down": ("thumb_down", False),
    "fa-thumbs-o-up": ("thumb_up", False),
    "fa-thumbs-up": ("thumb_up", True),
    "fa-ticket": ("confirmation_number", False),
    "fa-tiktok": ("oi_tiktok", False),
    "fa-times": ("close", False),
    "fa-times-circle": ("cancel", True),
    "fa-times-circle-o": ("cancel", False),
    "fa-times-rectangle": ("cancel", True),
    "fa-times-rectangle-o": ("cancel", False),
    "fa-tint": ("water_drop", False),
    "fa-toggle-down": ("arrow_drop_down_circle", False),
    "fa-toggle-left": ("arrow_circle_left", False),
    "fa-toggle-off": ("toggle_off", False),
    "fa-toggle-on": ("toggle_on", False),
    "fa-toggle-right": ("arrow_circle_right", False),
    "fa-toggle-up": ("arrow_circle_up", False),
    "fa-trademark": ("oi_trademark", False),
    "fa-train": ("train", False),
    "fa-transgender": ("transgender", False),
    "fa-transgender-alt": ("transgender", False),
    "fa-trash": ("delete", True),
    "fa-trash-o": ("delete", False),
    "fa-tree": ("park", False),
    "fa-trello": ("oi_trello", False),
    "fa-tripadvisor": ("oi_tripadvisor", False),
    "fa-trophy": ("trophy", True),
    "fa-truck": ("local_shipping", False),
    "fa-try": ("currency_lira", False),
    "fa-tty": ("tty", False),
    "fa-tumblr": ("oi_tumblr", False),
    "fa-tumblr-square": ("oi_tumblr-square", False),
    "fa-turkish-lira": ("currency_lira", False),
    "fa-tv": ("tv", False),
    "fa-twitch": ("oi_twitch", False),
    "fa-twitter": ("oi_twitter", False),
    "fa-twitter-square": ("oi_twitter-square", False),
    "fa-umbrella": ("umbrella", False),
    "fa-underline": ("format_underlined", False),
    "fa-undo": ("undo", False),
    "fa-universal-access": ("accessibility", False),
    "fa-university": ("account_balance", False),
    "fa-unlink": ("link_off", False),
    "fa-unlock": ("lock_open", False),
    "fa-unlock-alt": ("no_encryption", False),
    "fa-unsorted": ("swap_vert", False),
    "fa-upload": ("upload", False),
    "fa-usb": ("usb", False),
    "fa-usd": ("attach_money", False),
    "fa-user": ("person", True),
    "fa-user-circle": ("account_circle", True),
    "fa-user-circle-o": ("account_circle", False),
    "fa-user-md": ("medical_services", False),
    "fa-user-o": ("person", False),
    "fa-user-plus": ("person_add", True),
    "fa-user-secret": ("oi_user-secret", False),
    "fa-user-times": ("person_remove", True),
    "fa-users": ("group", True),
    "fa-vcard": ("contact_mail", True),
    "fa-vcard-o": ("contact_mail", False),
    "fa-venus": ("female", False),
    "fa-venus-double": ("oi_venus-double", False),
    "fa-venus-mars": ("oi_venus-mars", False),
    "fa-viacoin": ("oi_viacoin", False),
    "fa-viadeo": ("oi_viadeo", False),
    "fa-viadeo-square": ("oi_viadeo-square", False),
    "fa-video-camera": ("videocam", True),
    "fa-vimeo": ("oi_vimeo", False),
    "fa-vimeo-square": ("oi_vimeo-square", False),
    "fa-vine": ("oi_vine", False),
    "fa-vk": ("oi_vk", False),
    "fa-volume-control-phone": ("phone_in_talk", False),
    "fa-volume-down": ("volume_down", False),
    "fa-volume-off": ("volume_off", False),
    "fa-volume-up": ("volume_up", False),
    "fa-warning": ("warning", False),
    "fa-wechat": ("oi_wechat", False),
    "fa-weibo": ("oi_weibo", False),
    "fa-weixin": ("oi_wechat", False),
    "fa-whatsapp": ("oi_whatsapp", False),
    "fa-wheelchair": ("accessible", False),
    "fa-wheelchair-alt": ("accessible_forward", False),
    "fa-wifi": ("wifi", False),
    "fa-wikipedia-w": ("oi_wikipedia-w", False),
    "fa-window-close": ("cancel", True),
    "fa-window-close-o": ("cancel", False),
    "fa-window-maximize": ("fullscreen", False),
    "fa-window-minimize": ("minimize", False),
    "fa-window-restore": ("fullscreen_exit", False),
    "fa-windows": ("oi_windows", False),
    "fa-wordpress": ("oi_wordpress", False),
    "fa-wpbeginner": ("oi_wpbeginner", False),
    "fa-wpexplorer": ("oi_wpexplorer", False),
    "fa-wpforms": ("oi_wpforms", False),
    "fa-wrench": ("build", False),
    "fa-xing": ("oi_xing", False),
    "fa-xing-square": ("oi_xing-square", False),
    "fa-y-combinator": ("oi_y-combinator", False),
    "fa-y-combinator-square": ("oi_hacker-news", False),
    "fa-yahoo": ("oi_yahoo", False),
    "fa-yc": ("oi_y-combinator", False),
    "fa-yc-square": ("oi_hacker-news", False),
    "fa-yelp": ("oi_yelp", False),
    "fa-yen": ("currency_yen", False),
    "fa-youtube": ("oi_youtube", False),
    "fa-youtube-play": ("oi_youtube-play", False),
    "fa-youtube-square": ("oi_youtube-square", False),
}

# The same, for the odoo_ui_icons names that became Material Symbols (oi_to_ms.scss).
OI_TO_ICON = {
    "oi-activity": ("schedule", False),
    "oi-activity-plus": ("alarm_add", False),
    "oi-apps": ("apps", False),
    "oi-archive": ("archive", False),
    "oi-arrow-down": ("south", False),
    "oi-arrow-down-left": ("south_west", False),
    "oi-arrow-down-right": ("south_east", False),
    "oi-arrow-left": ("west", False),
    "oi-arrow-right": ("east", False),
    "oi-arrow-up": ("north", False),
    "oi-arrow-up-left": ("north_west", False),
    "oi-arrow-up-right": ("north_east", False),
    "oi-arrows-h": ("arrow_range", False),
    "oi-arrows-v": ("height", False),
    "oi-backspace-o": ("backspace", False),
    "oi-bluesky": ("oi_bluesky", False),
    "oi-bring-front": ("flip_to_front", False),
    "oi-chevron-down": ("keyboard_arrow_down", False),
    "oi-chevron-left": ("chevron_backward", False),
    "oi-chevron-right": ("chevron_forward", False),
    "oi-chevron-up": ("keyboard_arrow_up", False),
    "oi-close": ("close_small", False),
    "oi-discord": ("oi_discord", False),
    "oi-draggable": ("drag_indicator", False),
    "oi-ellipsis-h": ("more_horiz", False),
    "oi-ellipsis-v": ("more_vert", False),
    "oi-food-delivery": ("shopping_bag_speed", False),
    "oi-gif-picker": ("gif_box", False),
    "oi-google-play": ("oi_google-play", False),
    "oi-group": ("stacks", False),
    "oi-kickstarter": ("oi_kickstarter", False),
    "oi-launch": ("open_in_browser", False),
    "oi-life-ring-plus": ("support", False),
    "oi-merge": ("call_merge", False),
    "oi-minus": ("remove", False),
    "oi-numpad": ("dialpad", False),
    "oi-odoo": ("oi_odoo", False),
    "oi-panel-right": ("dock_to_left", False),
    "oi-plus": ("add", False),
    "oi-record": ("graphic_eq", False),
    "oi-schedule-later": ("calendar_clock", False),
    "oi-schedule-today": ("early_on", False),
    "oi-schedule-tomorrow": ("event_upcoming", False),
    "oi-search": ("search", False),
    "oi-send-back": ("flip_to_back", False),
    "oi-settings-adjust": ("tune", False),
    "oi-smile-add": ("add_reaction", False),
    "oi-star-plus": ("star", False),
    "oi-strava": ("oi_strava", False),
    "oi-studio": ("oi_studio", False),
    "oi-subtitle": ("subtitles", False),
    "oi-suitcase": ("work", False),
    "oi-suitcase-plus": ("person_add", False),
    "oi-text-break": ("format_image_front", False),
    "oi-text-effect": ("stylus_laser_pointer", False),
    "oi-text-inline": ("format_image_inline_left", False),
    "oi-threads": ("oi_threads", False),
    "oi-tiktok": ("oi_tiktok", False),
    "oi-transfer": ("sync_alt", False),
    "oi-unarchive": ("unarchive", False),
    "oi-user": ("person", False),
    "oi-user-plus": ("person_add", False),
    "oi-users": ("group", False),
    "oi-view": ("toolbar", False),
    "oi-view-cohort": ("oi_view-cohort", False),
    "oi-view-kanban": ("view_kanban", False),
    "oi-view-list": ("view_list", False),
    "oi-view-pivot": ("oi_view-pivot", False),
    "oi-voip": ("tty", False),
    "oi-x": ("oi_twitter", False),
    "oi-x-square": ("oi_twitter-square", False),
}

# The only ``oi-*`` classes that survive: they tweak rendering, not the glyph.
MODIFIERS = frozenset(
    {
        "fw",
        "filled",
        "stack",
        "stack-1x",
        "stack-2x",
        "pulse",
        "spin",
        "sm",
        "lg",
        "rotate-90",
        "rotate-180",
        "rotate-270",
        "flip-horizontal",
        "flip-vertical",
    }
)
SIZE_RE = re.compile(r"^\d{1,2}x$")

OPEN_TAG_RE = re.compile(r"<[a-zA-Z][^>]*?/?>", re.S)
CLASS_ATTR_RE = re.compile(r'([\w:-]*class)="([^"]*)"')
ICON_ATTR_RE = re.compile(r'(?<![-\w])icon="([^"]*)"')
ICON_CLASS_RE = re.compile(r'(?<![-\w])icon_class="')
# ``options="{'icon': 'fa-repeat'}"`` of the boolean_icon widget, which in Odoo 20
# takes the bare Material Symbols name and a separate 'icon_class'.
OPTIONS_ICON_RE = re.compile(r"('icon'\s*:\s*')(fa-[\w-]+|oi-[\w-]+)(')")
DATA_ICON_RE = re.compile(r'(?<![-\w])data-icon="')
INHERIT_CLASS_RE = re.compile(
    r'<attribute\s[^>]*name="[\w:-]*class"[^>]*>(?:[^<]*)</attribute>|'
    r'<attribute\s[^>]*name="[\w:-]*class"[^>]*/>',
    re.S,
)
# Anything that still names an icon the Odoo 19 way. The surviving ``oi-*``
# modifiers are NOT legacy: an already ported ``class="oi oi-fw"`` must not match,
# or every migrated file would report itself.
_LEGACY_PATTERN = (
    r"(?<![\w-])fa-[\w-]+(?![\w-])|"
    r"(?<![\w-])oi-(?!fw|filled|stack|pulse|spin|rotate|flip|sm|lg|\d{1,2}x)[\w-]+"
)
FA_OR_OI_RE = re.compile(r"(?<![\w-])fa(?![\w-])|" + _LEGACY_PATTERN)
# Same shape as odoo/addons/test_lint/tests/test_icons.py, minus the bare ``fa``
# which is too noisy outside xml.
LEGACY_RE = re.compile(_LEGACY_PATTERN)
# A value built at render time: we cannot know which icon comes out of it.
DYNAMIC_RE = re.compile(r"\{\{|#\{")


def is_modifier(name):
    return name in MODIFIERS or bool(SIZE_RE.match(name))


def resolve(token):
    """``(data-icon, filled)`` for an icon class, or ``None`` when unknown."""
    return FA_TO_ICON.get(token) or OI_TO_ICON.get(token)


def convert_class_value(value):
    """Rewrite an icon class list to the Odoo 20 form.

    Returns ``(new_value, icon_name)``, or ``None`` when the element carries a
    legacy icon class this script will not decide on its own.
    """
    tokens, kept, icon, filled, unresolved = value.split(), [], None, False, False
    for token in tokens:
        if token == "fa":
            continue
        if not token.startswith(("fa-", "oi-")):
            kept.append(token)
            continue
        name = token.split("-", 1)[1]
        if is_modifier(name):
            kept.append("oi-" + name)
            continue
        resolved = resolve(token)
        if resolved is None or icon is not None:
            unresolved = True  # unknown glyph, or two icons on one element
            break
        icon, filled = resolved
    if unresolved or icon is None:
        return None
    classes = ["oi"] + (["oi-filled"] if filled else [])
    return " ".join(classes + [t for t in kept if t not in ("oi", "oi-filled")]), icon


def port_tag(tag, report):
    """Rewrite the icon attributes of a single opening tag."""
    original = tag

    def class_repl(match):
        attr, value = match.group(1), match.group(2)
        if not FA_OR_OI_RE.search(value):
            return match.group(0)
        if attr.startswith("t-") or DYNAMIC_RE.search(value):
            report("icon class built at render time: " + value.strip())
            return match.group(0)
        if DATA_ICON_RE.search(tag):
            report("element already carries data-icon: " + value.strip())
            return match.group(0)
        converted = convert_class_value(value)
        if converted is None:
            report("no known Odoo 20 icon for: " + value.strip())
            return match.group(0)
        new_value, icon = converted
        return '%s="%s" data-icon="%s"' % (attr, new_value, icon)

    tag = CLASS_ATTR_RE.sub(class_repl, tag)

    def icon_repl(match):
        value = match.group(1)
        if not FA_OR_OI_RE.search(value):
            return match.group(0)
        if DYNAMIC_RE.search(value):
            report("icon attribute built at render time: " + value)
            return match.group(0)
        # ``icon="fa-check text-success"`` splits into the glyph and the classes
        # that styled it, which Odoo 20 moved to ``icon_class``.
        icon, extra = None, []
        for token in value.split():
            if token == "fa":
                continue
            if token.startswith(("fa-", "oi-")) and is_modifier(token.split("-", 1)[1]):
                extra.append("oi-" + token.split("-", 1)[1])
                continue
            resolved = resolve(token) if token.startswith(("fa-", "oi-")) else None
            if resolved and icon is None:
                icon, filled = resolved
                if filled:
                    extra.append("oi-filled")
            else:
                extra.append(token)
        if icon is None:
            report("no known Odoo 20 icon for: " + value)
            return match.group(0)
        if extra and ICON_CLASS_RE.search(tag):
            report(
                "icon classes to merge into the existing icon_class: " + " ".join(extra)
            )
            return 'icon="%s"' % icon
        if extra:
            return 'icon="%s" icon_class="%s"' % (icon, " ".join(extra))
        return 'icon="%s"' % icon

    tag = ICON_ATTR_RE.sub(icon_repl, tag)

    def options_repl(match):
        resolved = resolve(match.group(2))
        if resolved is None:
            report("no known Odoo 20 icon for: " + match.group(2))
            return match.group(0)
        icon, filled = resolved
        replacement = match.group(1) + icon + match.group(3)
        if filled and "'icon_class'" not in tag:
            replacement += ", 'icon_class': 'oi-filled'"
        return replacement

    tag = OPTIONS_ICON_RE.sub(options_repl, tag)
    return tag, tag != original


def port_content(content, report):
    """Rewrite every opening tag of an xml file. Returns the new content.

    Reports carry the line they came from: whatever this script leaves behind is
    meant to be opened and fixed by hand, so it has to say where.
    """
    source = content
    changed = [False]
    reported = set()

    def line_of(text, offset):
        return text.count("\n", 0, offset) + 1

    def tag_repl(match):
        line = line_of(source, match.start())

        def say(message):
            reported.add(line)
            report("line %d: %s" % (line, message))

        tag, did = port_tag(match.group(0), say)
        changed[0] = changed[0] or did
        return tag

    content = OPEN_TAG_RE.sub(tag_repl, content)
    for match in INHERIT_CLASS_RE.finditer(source):
        if FA_OR_OI_RE.search(match.group(0)):
            line = line_of(source, match.start())
            reported.add(line)
            report(
                "line %d: icon set through view inheritance, port by hand: %s"
                % (line, " ".join(match.group(0).split())[:90])
            )

    # Last sweep over the result. An icon name can sit somewhere this script does
    # not rewrite -- an xpath selecting on it (``hasclass('fa-clock-o')``), a dict
    # inside an attribute (``options="{'icon': 'fa-repeat'}"``), a class list built
    # in a template's javascript. Those are silent breakages, and an xpath is worse
    # than silent: the view no longer matches and the module fails to install. We
    # do not rewrite them -- what they select or feed is beyond this file -- but
    # none of them gets to pass unnoticed.
    for match in LEGACY_RE.finditer(content):
        line = line_of(content, match.start())
        if line in reported:
            continue
        reported.add(line)
        known = FA_TO_ICON.get(match.group(0)) or OI_TO_ICON.get(match.group(0))
        hint = " (it is %s in Odoo 20)" % known[0] if known else ""
        report(
            "line %d: %s left in place, port by hand%s" % (line, match.group(0), hint)
        )
    return content, changed[0]


def migrate_icons(
    logger, module_path, module_name, manifest_path, migration_steps, tools
):
    """Port Font Awesome icon usages to the Material Symbols set of Odoo 20.

    Odoo 20 stopped shipping the Font Awesome stylesheet (see odoo/odoo#256840):
    an ``<i class="fa fa-trash"/>`` renders nothing. The icon name moved out of
    the class into a ``data-icon`` attribute, and ``odoo/addons/test_lint`` fails
    on any leftover ``fa*`` or obsolete ``oi-<name>`` class, our own modules
    included.

        <i class="fa fa-trash fa-fw"/>
            -> <i class="oi oi-filled oi-fw" data-icon="delete"/>
        <button icon="fa-bars"/>
            -> <button icon="menu"/>

    Material Symbols are outline by default, so ``oi-filled`` is added exactly
    where Odoo's map asks for it: that is how ``fa-star`` and ``fa-star-o`` reach
    the same glyph with a different weight.

    Whatever this script cannot resolve is left untouched and reported. An icon
    that did not migrate is visible and fixable; one that migrated to the wrong
    glyph is neither.
    """
    for file_path in tools.get_files(module_path, (".xml",)):
        pending = []
        try:
            content = tools._read_content(file_path)
            new_content, changed = port_content(content, pending.append)
            if changed:
                tools._write_content(file_path, new_content)
                logger.info("Ported icons to Material Symbols in: %s" % file_path)
        except Exception as error:
            logger.error("Error processing file %s: %s" % (file_path, error))
            continue
        for message in pending:
            logger.warning("%s: %s" % (file_path, message))

    # Icons set outside xml are left alone: only a human knows what they render.
    for file_path in tools.get_files(module_path, (".py", ".js", ".scss", ".css")):
        try:
            content = tools._read_content(file_path)
        except Exception:
            continue
        hits = sorted({m.group(0) for m in LEGACY_RE.finditer(content)})
        if hits:
            logger.warning(
                "%s: icon classes outside xml, port by hand: %s"
                % (file_path, ", ".join(hits[:8]))
            )


class MigrationScript(BaseMigrationScript):
    _GLOBAL_FUNCTIONS = [
        migrate_ir_model_access_to_ir_access,
        migrate_icons,
    ]
