#include "power_flow_box.h"
#include "esphome/core/log.h"

namespace esphome {
namespace power_flow_box {

static const char *const TAG = "power_flow_box";

void PowerFlowBox::dump_config() {
  ESP_LOGCONFIG(TAG, "PowerFlowBox:");
  ESP_LOGCONFIG(TAG, "  Title label: %s", YESNO(this->title_lbl_ != nullptr));
  ESP_LOGCONFIG(TAG, "  Main label: %s", YESNO(this->main_lbl_ != nullptr));
  ESP_LOGCONFIG(TAG, "  State label: %s", YESNO(this->state_lbl_ != nullptr));
  ESP_LOGCONFIG(TAG, "  Sub-row: %s", YESNO(this->sub_l_lbl_ != nullptr));
  ESP_LOGCONFIG(TAG, "  Bar: %s", YESNO(this->bar_ != nullptr));
}

}  // namespace power_flow_box
}  // namespace esphome
