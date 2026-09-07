#pragma once

#include "esphome/core/component.h"
#include "esphome/core/color.h"
#include "esphome/components/lvgl/lvgl_esphome.h"

#include <cstdint>
#include <string>

namespace esphome {
namespace power_flow_box {

// One "box" of a Victron/Venus-OS-style power-flow overview page: a
// rounded panel with a title, one large main value, an optional
// secondary state line, an optional left/right sub-value row, and an
// optional horizontal fill bar (e.g. battery SOC).
//
// This is the exact shape smartebl_display_esphome's page_electric.yaml
// hand-built with a YAML anchor + merge-key template (`&box_frame` /
// `&row_main` / etc.) before this component existed - see that repo's
// docs/design_rules.md §10 and the box's own comments for the original.
// Turning it into a real widget type doesn't change the layout that was
// already tuned by hand against a real device; it gives that same,
// already-approved layout a typed config schema (see this repo's
// README for the full field reference) and a typed C++ API instead of
// six copy-pasted YAML blocks merging in the same anchors.
//
// Row y-offsets (16 / 48 / 100 / 132 / 210) are FIXED CONSTANTS here,
// not exposed as config. That is deliberate, not a missing feature: the
// whole point of a shared box template - in the hand-written version
// and here - is that no single box can quietly drift from the others
// ("leg für die Boxen ein Template an, und nimm für jede Box DASSELBE
// Template... nur ich genehmige Abweichungen" - the repo-owner rule
// that produced the original template). Making these offsets
// per-instance config would reopen exactly the problem the template
// was built to close. They assume a box in roughly the proven ~300x290
// size class - like m5dial_clock_sbb's sbb_clock assuming a round
// 240x240 class (see that repo's design_rules.md §3: "tuned by looking
// at a physical device, not derived from a formula") - a meaningfully
// different box size is a new template, not a config knob on this one.
//
// No per-frame render loop: unlike sbb_clock (which redraws an analog
// face every render_interval because it draws arbitrary hand shapes by
// hand), a box's content only ever changes on a value update, and LVGL's
// own object model already repaints a changed label/bar efficiently on
// its own. Resource efficiency for THIS widget means not building a
// dirty-rect/canvas scheme a plain LVGL label/bar doesn't need - see
// the README's "Why no canvas" section for the reasoning in full.
class PowerFlowBox : public Component, public lvgl::LvCompound {
 public:
  void setup() override {}
  void dump_config() override;
  float get_setup_priority() const override { return setup_priority::PROCESSOR; }

  // ---- wiring, set once at codegen time (power_flow_box/__init__.py) ------
  // Any of these may be nullptr (an optional row/bar the config left
  // off) - every setter below checks before touching its label/bar, the
  // same has_state()-style guard pattern design_rules.md's invalid-value
  // rule already uses throughout smartebl_display_esphome.
  void set_title_label(lv_obj_t *l) { this->title_lbl_ = l; }
  void set_main_label(lv_obj_t *l) { this->main_lbl_ = l; }
  void set_state_label(lv_obj_t *l) { this->state_lbl_ = l; }
  void set_sub_labels(lv_obj_t *l, lv_obj_t *r) {
    this->sub_l_lbl_ = l;
    this->sub_r_lbl_ = r;
  }
  void set_bar_widget(lv_obj_t *b) { this->bar_ = b; }

  // ---- runtime API, called from a page's own draw_<page> script -----------
  // Same "one script redraws the page, called from every contributing
  // sensor's own on_value plus esphome: on_boot:" pattern
  // design_rules.md documents for the page itself (inherited from
  // m5dial_fram's design_rules.md §9) - this widget only provides the
  // setters, it never decides when to call them or what the "right"
  // value is. It knows state, not the rule behind it - same principle
  // sbb_clock's set_night_mode() already established for this fleet.
  void set_title(const std::string &text) {
    if (this->title_lbl_ != nullptr)
      lv_label_set_text(this->title_lbl_, text.c_str());
  }
  void set_main(const std::string &text, Color color) {
    if (this->main_lbl_ == nullptr)
      return;
    lv_label_set_text(this->main_lbl_, text.c_str());
    lv_obj_set_style_text_color(this->main_lbl_, lv_color_make(color.r, color.g, color.b), 0);
  }
  void set_state(const std::string &text, Color color) {
    if (this->state_lbl_ == nullptr)
      return;
    lv_label_set_text(this->state_lbl_, text.c_str());
    lv_obj_set_style_text_color(this->state_lbl_, lv_color_make(color.r, color.g, color.b), 0);
  }
  // Both sides share one color - matches every box in page_electric.yaml
  // today (the bottom V/A/W-style row is always one uniform secondary
  // color, never independently colored left vs. right). Call set_sub()
  // twice with different colors if a future box genuinely needs that;
  // not worth a 4-argument signature for a case that hasn't come up yet.
  void set_sub(const std::string &left, const std::string &right, Color color) {
    if (this->sub_l_lbl_ != nullptr) {
      lv_label_set_text(this->sub_l_lbl_, left.c_str());
      lv_obj_set_style_text_color(this->sub_l_lbl_, lv_color_make(color.r, color.g, color.b), 0);
    }
    if (this->sub_r_lbl_ != nullptr) {
      lv_label_set_text(this->sub_r_lbl_, right.c_str());
      lv_obj_set_style_text_color(this->sub_r_lbl_, lv_color_make(color.r, color.g, color.b), 0);
    }
  }
  void set_bar(int value, Color color) {
    if (this->bar_ == nullptr)
      return;
    lv_bar_set_value(this->bar_, value, LV_ANIM_OFF);
    lv_obj_set_style_bg_color(this->bar_, lv_color_make(color.r, color.g, color.b), LV_PART_INDICATOR);
  }

 protected:
  lv_obj_t *title_lbl_{nullptr};
  lv_obj_t *main_lbl_{nullptr};
  lv_obj_t *state_lbl_{nullptr};
  lv_obj_t *sub_l_lbl_{nullptr};
  lv_obj_t *sub_r_lbl_{nullptr};
  lv_obj_t *bar_{nullptr};
};

}  // namespace power_flow_box
}  // namespace esphome
