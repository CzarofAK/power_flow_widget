# power_flow_widget

A reusable **`power_flow_box`** ESPHome/LVGL widget: one rounded panel
with a title, a large main value, an optional secondary state line, an
optional left/right sub-value row, and an optional horizontal fill bar
(e.g. a battery SOC gauge) — the "box" primitive a Victron/Venus-OS-style
power-flow overview page (Shore → Inverter/Charger → AC Loads / Solar →
Battery → DC Loads) is built out of.

> [!WARNING]
> **Safety & liability / Sicherheit & Haftung** – Private hobby project, provided "as is" and used **at your own risk**.
> Display widget, **v0.1, not yet tested on hardware**. Displayed power, battery and charge values can be wrong. Do not make decisions about batteries, chargers or electrical loads based on this display alone.
> See [DISCLAIMER.md](DISCLAIMER.md) (EN/DE).

## Where this came from

[`smartebl_display_esphome`](https://github.com/CzarofAK/smartebl_display_esphome)'s
`smart_ebl_pages/page_electric.yaml` hand-built exactly this box shape
with a YAML anchor + merge-key template (`&box_frame`, `&row_title`,
`&row_main`, `&row_state`, `&row_bottom_l`/`&row_bottom_r`) reused six
times for a 3×2 grid of Victron-style boxes. That layout was tuned by
hand against a real 800×1280 panel over several iterations (see that
repo's own file history) and, as of 2026-09-07, brought closer to
Victron's own [gui-v2](https://github.com/victronenergy/gui-v2) look —
blue-tinted panel chrome, a battery SOC fill bar, colored flow arrows —
researched against Victron's real color tokens and the community
[Venus-OS-Dashboard](https://github.com/skydarc/Venus-OS-Dashboard)
Home-Assistant reskin.

This repo turns that proven, already-approved layout into a real,
typed widget — same pixel positions, same design intent, now with a
declarative config schema (the ICD below) and a typed C++ API instead
of six copy-pasted YAML blocks. It does **not** change the layout; it
gives it a name and a schema.

**Status: v0.1, not yet compiled against real hardware.** This was
written in a session with no ESPHome toolchain available to verify it
against (`pip install esphome` failed in that sandbox for unrelated
packaging reasons). The Python codegen closely follows the proven,
working pattern in
[`m5dial_clock_sbb`](https://github.com/CzarofAK/m5dial_clock_sbb)'s
`sbb_clock` component (same `WidgetType`/`LvCompound`/`lv_expr`
machinery), and the layout constants are copied 1:1 from
`page_electric.yaml`'s own real, working YAML — but the LVGL C API call
names/signatures used inside `to_code()` (`lv.obj_align`,
`lv.obj_set_style_bg_opa`, etc.) have not been run through a real
`esphome config`/`esphome compile`. **Run both against
`examples/page_example.yaml`'s pattern before relying on this in a real
build**, and expect to fix small API-name mismatches (LVGL9 renames
things across versions occasionally).

## Why no canvas / dirty-rect tracking

`sbb_clock` uses a raw LVGL canvas with per-shape dirty-rect tracking
because it draws an analog clock face — arbitrary hand/tick shapes —
by hand, every `render_interval`. A power-flow box draws none of that:
its content is plain text labels and a plain bar, and LVGL's own object
model already repaints a changed label or bar efficiently on its own.
Building a custom canvas + dirty-rect scheme here would be adding
machinery a plain LVGL label/bar doesn't need — the resource-conscious
choice for *this* widget is the opposite of `sbb_clock`'s: use LVGL's
native objects directly, add nothing.

There is consequently no `render_interval` and no per-frame `loop()` —
`PowerFlowBox::setup()` is empty. A box only redraws when your own code
calls one of its setters, exactly like `lv_label_set_text()` on a plain
`label:` widget would.

## The ICD: config schema

One `power_flow_box:` entry under `lvgl: ... widgets:` is one box.
Every field below except `width`/`height` is optional.

| Key | Type | Default | Meaning |
|---|---|---|---|
| `width` | int | *required* | Box width, px |
| `height` | int | *required* | Box height, px |
| `title` | string | `""` | Static title text (top, y:16) |
| `title_font` | font id | `montserrat_20` | |
| `main_font` | font id | `montserrat_40` | Font for the large main value (y:48) |
| `sub_font` | font id | `montserrat_20` | Font for state line + sub-row |
| `radius` | int | `12` | Corner radius, px |
| `bg_color` | `color:` id | LVGL theme default | Panel background |
| `border_color` | `color:` id | LVGL theme default | Panel border (1px) |
| `title_color` | `color:` id | LVGL theme default | Title text color |
| `show_state` | bool | `true` | Secondary state line under the main value (y:132) |
| `show_sub_row` | bool | `false` | Left/right sub-value row (y:210, 24px inset) |
| `show_bar` | bool | `false` | Horizontal fill bar (y:100, between main value and state line) |
| `bar_min` / `bar_max` | int | `0` / `100` | Bar range |
| `bar_track_color` | `color:` id | LVGL theme default | Bar track (not indicator) color |

**Row positions (16 / 48 / 100 / 132 / 210) are fixed constants, not
config**, on purpose — see `power_flow_box.h`'s own comment. The whole
point of a shared template is that no individual box can quietly drift
from the others; exposing the offsets as per-instance config would
reopen exactly the problem the template exists to close. They assume a
box in roughly the proven ~300×290 size class, the same way
`sbb_clock` assumes a round ~240×240 class. A meaningfully different
box size is a new template, not a config knob on this one.

**Colors are `color:` id references, not hex literals in this
schema** — same pattern `sbb_clock` uses for `foreground`/`background`.
The widget doesn't invent its own palette; it takes whatever `color:`
block the consuming project already declares (see
`examples/page_example.yaml`, which reuses the exact Victron-tinted
values `page_electric.yaml` uses: `col_panel_bg` = `#142230`,
`col_panel_border` = `#27588A`).

## The ICD: runtime API (C++)

Called from your own page's drawing script — the widget only provides
the setters, it never decides when to call them or what the "right"
value is. It knows state, not the rule behind it, exactly like
`sbb_clock`'s `set_night_mode(bool)`.

```cpp
void set_title(const std::string &text);
void set_main(const std::string &text, Color color);
void set_state(const std::string &text, Color color);
void set_sub(const std::string &left, const std::string &right, Color color);
void set_bar(int value, Color color);
```

Any setter for a row the config left off (`show_state: false`, etc.)
is a silent no-op — safe to call unconditionally from a generic
drawing script without checking which optional rows a given box has.

```yaml
sensor:
  - platform: homeassistant
    id: s_battery_soc
    entity_id: sensor.smartshunt_ladestand
    on_value:
      - lambda: |-
          char buf[16];
          snprintf(buf, sizeof(buf), "%.0f%%", x);
          id(box_battery).set_main(buf, Color(0xFF, 0xFF, 0xFF));
          id(box_battery).set_bar((int) x, Color(0x2E, 0xCC, 0x71));
```

## Links (connector arrows) need no component of their own

`page_electric.yaml`'s flow arrows between boxes are a plain `label:`
inside a slim `obj:` wrapper (for centering in the gap between two
boxes) — see that file's `&arrow_wrap` anchor, or
`examples/page_example.yaml`'s `arrow_shore_battery`. There's no
drawing beyond a text glyph and a color, which a plain `label:` widget
already does for free; wrapping that in a dedicated component would be
solving a problem that doesn't exist. Set the glyph/color the same way
`page_electric.yaml`'s `draw_electric` script does:

```cpp
lv_label_set_text(id(arrow_shore_battery), active ? "→" : "-");
lv_obj_set_style_text_color(id(arrow_shore_battery),
    lv_color_hex(active ? 0x4A9EFF : 0x707070), 0);
```

No animation — `page_electric.yaml`'s own history already tried and
deliberately reverted a walking-dash flow animation on performance
grounds. A colored/static glyph, set once per value change, costs
nothing extra; keep it that way.

## Installation

```yaml
external_components:
  - source:
      type: git
      url: https://github.com/CzarofAK/power_flow_widget
      ref: main
    refresh: 1d
    components: [power_flow_box]

# Marker key - without it ESPHome never loads this component's Python
# side, so `power_flow_box:` widgets under `lvgl:` fail to validate.
power_flow_box:
```

See `examples/page_example.yaml` for a full two-box, one-link example
(Shore + Battery-with-bar), including the `color:` ids the schema
expects.

## Migration from `page_electric.yaml`

Not done as part of this repo, and not automatic. The plan (see the
`smartebl_display_esphome` session that produced this repo) is: once
this component has been validated against real hardware (`esphome
config`/`compile`, then a real flash), replace `page_electric.yaml`'s
six hand-rolled `&box_frame`-merged boxes with six `power_flow_box:`
entries one at a time, keeping the page's own sensor wiring and
`draw_electric` script exactly as-is except for swapping raw
`lv_label_set_text(id(lbl_electric_batt_main), ...)`-style calls for
`id(box_battery).set_main(...)`. `page_electric.yaml` is not touched by
this repo.

## License

MIT, see [LICENSE](LICENSE). Use at your own risk – see [DISCLAIMER.md](DISCLAIMER.md).