import esphome.codegen as cg
import esphome.config_validation as cv
from esphome.components.lvgl.defines import CONF_MAIN, literal
from esphome.components.lvgl.lv_validation import lv_font
from esphome.components.lvgl.lvcode import lv, lv_add, lv_expr
from esphome.components.lvgl.types import LvCompound, LvType
from esphome.components.lvgl.widgets import Widget, WidgetType
from esphome.const import CONF_HEIGHT, CONF_WIDTH

CODEOWNERS = ["@CzarofAK"]
# A bare marker key: this only exists so ESPHome imports this module (a
# component's Python only loads when its domain is a top-level YAML
# key), which registers the `power_flow_box` widget type below before
# `lvgl:` validates its `widgets:` list - same pattern m5dial_clock_sbb's
# `sbb_clock` marker key uses for the same reason.
DEPENDENCIES = ["lvgl"]

CONFIG_SCHEMA = cv.Schema({})


async def to_code(config):
    pass


power_flow_box_ns = cg.esphome_ns.namespace("power_flow_box")
PowerFlowBox = power_flow_box_ns.class_("PowerFlowBox", cg.Component, LvCompound)
# Same reasoning as sbb_clock's own lv_sbb_clock_t: cg.Component has to be
# listed alongside LvCompound so a declared `id:` of this type gets added
# to CORE.component_ids, which is what makes cg.register_component()
# below actually register it (WidgetType.create_to_code() only builds
# the compound widget, it never registers it as a component on its own -
# without this, PowerFlowBox would simply never be reachable via
# `id(my_box)` from another script).
lv_power_flow_box_t = LvType(str(PowerFlowBox), parents=(LvCompound, cg.Component))
ColorStruct = cg.esphome_ns.struct("Color")

CONF_TITLE = "title"
CONF_TITLE_FONT = "title_font"
CONF_MAIN_FONT = "main_font"
CONF_SUB_FONT = "sub_font"
CONF_RADIUS = "radius"
CONF_BG_COLOR = "bg_color"
CONF_BORDER_COLOR = "border_color"
CONF_TITLE_COLOR = "title_color"
CONF_SHOW_STATE = "show_state"
CONF_SHOW_SUB_ROW = "show_sub_row"
CONF_SHOW_BAR = "show_bar"
CONF_BAR_MIN = "bar_min"
CONF_BAR_MAX = "bar_max"
CONF_BAR_TRACK_COLOR = "bar_track_color"

# ESPHome's own built-in fonts (no `font:` block required in the
# consuming project) - a real project will almost always want to
# override these with its own declared type scale (smartebl_display_esphome
# uses font_ui_20/font_ui_40, see this repo's README), but a config that
# names nothing still compiles and looks reasonable out of the box, the
# same courtesy sbb_clock's date_font/temperature_font defaults extend.
_DEFAULT_TITLE_FONT = "montserrat_20"
_DEFAULT_MAIN_FONT = "montserrat_40"
_DEFAULT_SUB_FONT = "montserrat_20"

WIDGET_SCHEMA = cv.Schema(
    {
        cv.Required(CONF_WIDTH): cv.int_range(min=1),
        cv.Required(CONF_HEIGHT): cv.int_range(min=1),
        cv.Optional(CONF_TITLE, default=""): cv.string,
        cv.Optional(CONF_TITLE_FONT, default=_DEFAULT_TITLE_FONT): lv_font,
        cv.Optional(CONF_MAIN_FONT, default=_DEFAULT_MAIN_FONT): lv_font,
        cv.Optional(CONF_SUB_FONT, default=_DEFAULT_SUB_FONT): lv_font,
        cv.Optional(CONF_RADIUS, default=12): cv.int_range(min=0),
        cv.Optional(CONF_BG_COLOR): cv.use_id(ColorStruct),
        cv.Optional(CONF_BORDER_COLOR): cv.use_id(ColorStruct),
        cv.Optional(CONF_TITLE_COLOR): cv.use_id(ColorStruct),
        cv.Optional(CONF_SHOW_STATE, default=True): cv.boolean,
        cv.Optional(CONF_SHOW_SUB_ROW, default=False): cv.boolean,
        cv.Optional(CONF_SHOW_BAR, default=False): cv.boolean,
        cv.Optional(CONF_BAR_MIN, default=0): cv.int_,
        cv.Optional(CONF_BAR_MAX, default=100): cv.int_,
        cv.Optional(CONF_BAR_TRACK_COLOR): cv.use_id(ColorStruct),
    }
)


class PowerFlowBoxWidgetType(WidgetType):
    def __init__(self):
        super().__init__(
            "power_flow_box",
            lv_power_flow_box_t,
            (CONF_MAIN,),
            schema=WIDGET_SCHEMA,
            modify_schema={},
            lv_name="obj",
        )

    async def obj_creator(self, parent, config: dict):
        return lv_expr.call("obj_create", parent)

    def get_uses(self):
        return ("obj", "label", "bar")

    async def to_code(self, w: Widget, config):
        # Same reason sbb_clock registers itself: WidgetType.create_to_code()
        # only constructs the compound widget, it doesn't register it as
        # an ESPHome component on its own.
        await cg.register_component(w.var, config)

        width = config[CONF_WIDTH]

        # ---- box chrome -----------------------------------------------------
        lv.obj_set_style_pad_all(w.obj, 0, 0)
        lv.obj_set_style_radius(w.obj, config[CONF_RADIUS], 0)
        lv.obj_set_style_border_width(w.obj, 1, 0)
        lv.obj_set_style_bg_opa(w.obj, literal("LV_OPA_COVER"), 0)
        if (bg := config.get(CONF_BG_COLOR)) is not None:
            lv.obj_set_style_bg_color(w.obj, await cg.get_variable(bg), 0)
        if (bc := config.get(CONF_BORDER_COLOR)) is not None:
            lv.obj_set_style_border_color(w.obj, await cg.get_variable(bc), 0)

        title_font = await lv_font.process(config[CONF_TITLE_FONT])
        main_font = await lv_font.process(config[CONF_MAIN_FONT])
        sub_font = await lv_font.process(config[CONF_SUB_FONT])

        # ---- title (y:16, TOP_MID) - ported 1:1 from page_electric.yaml's
        # &row_title anchor. Static text, set once here; unlike main/state/
        # sub it has no runtime setter beyond set_title(), since a box's
        # title essentially never changes at runtime in the source layout.
        title_lbl = lv_expr.call("label_create", w.obj)
        lv.obj_align(title_lbl, literal("LV_ALIGN_TOP_MID"), 0, 16)
        lv.obj_set_style_text_font(title_lbl, title_font, 0)
        lv.label_set_text(title_lbl, config[CONF_TITLE])
        if (tc := config.get(CONF_TITLE_COLOR)) is not None:
            lv.obj_set_style_text_color(title_lbl, await cg.get_variable(tc), 0)
        lv_add(w.var.set_title_label(title_lbl))

        # ---- main value (y:48, TOP_MID) - ported from &row_main. Every box
        # gets one, unconditionally - a box with nothing to show here isn't
        # a box worth having.
        main_lbl = lv_expr.call("label_create", w.obj)
        lv.obj_align(main_lbl, literal("LV_ALIGN_TOP_MID"), 0, 48)
        lv.obj_set_style_text_font(main_lbl, main_font, 0)
        lv.label_set_text(main_lbl, "---")
        lv_add(w.var.set_main_label(main_lbl))

        # ---- optional SOC-style fill bar (y:100, ~36px gap below the main
        # value) - ported from page_electric.yaml's 2026-09-07 Battery-box
        # addition. That box's own comment explains why this sits ABOVE the
        # state line rather than as a full-height vertical bar on the edge
        # (RIGHT_MID like a Charger-style load bar): a box that also uses
        # show_sub_row has no room left on either edge without overlapping
        # its own V/A/W-style row, but the ~36px band between the main
        # value and the state line is free on every box regardless of
        # which other optional rows are enabled.
        if config[CONF_SHOW_BAR]:
            bar = lv_expr.call("bar_create", w.obj)
            lv.bar_set_range(bar, config[CONF_BAR_MIN], config[CONF_BAR_MAX])
            lv.obj_set_size(bar, width - 48, 10)
            lv.obj_align(bar, literal("LV_ALIGN_TOP_MID"), 0, 100)
            lv.obj_set_style_radius(bar, 4, 0)
            lv.obj_set_style_border_width(bar, 1, 0)
            if (btc := config.get(CONF_BAR_TRACK_COLOR)) is not None:
                lv.obj_set_style_bg_color(bar, await cg.get_variable(btc), 0)
            lv_add(w.var.set_bar_widget(bar))

        # ---- state / secondary line (y:132, TOP_MID) - ported from
        # &row_state. Optional: a box that's genuinely just "one number"
        # (no secondary status line) can turn this off rather than carry
        # a permanently-blank label, unlike page_electric.yaml's Shore box
        # which keeps its own row_state widget alive only because other
        # boxes' merges need the anchor to exist.
        if config[CONF_SHOW_STATE]:
            state_lbl = lv_expr.call("label_create", w.obj)
            lv.obj_align(state_lbl, literal("LV_ALIGN_TOP_MID"), 0, 132)
            lv.obj_set_style_text_font(state_lbl, sub_font, 0)
            lv.label_set_text(state_lbl, "")
            lv_add(w.var.set_state_label(state_lbl))

        # ---- left/right sub-value row (y:210, 24px inset) - ported from
        # &row_bottom_l/&row_bottom_r. The 24px inset matches Battery's own
        # V/A/W row in page_electric.yaml exactly (same repo-owner ask:
        # "alle Werte auf der untersten Ebene sind zu weit aussen").
        if config[CONF_SHOW_SUB_ROW]:
            sub_l = lv_expr.call("label_create", w.obj)
            lv.obj_align(sub_l, literal("LV_ALIGN_TOP_LEFT"), 24, 210)
            lv.obj_set_style_text_font(sub_l, sub_font, 0)
            lv.label_set_text(sub_l, "---")
            sub_r = lv_expr.call("label_create", w.obj)
            lv.obj_align(sub_r, literal("LV_ALIGN_TOP_RIGHT"), -24, 210)
            lv.obj_set_style_text_font(sub_r, sub_font, 0)
            lv.label_set_text(sub_r, "---")
            lv_add(w.var.set_sub_labels(sub_l, sub_r))


PowerFlowBoxWidgetType()
