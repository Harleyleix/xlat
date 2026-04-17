#ifndef XLAT_UI_PALETTE_H
#define XLAT_UI_PALETTE_H

#include "lvgl/lvgl.h"

/*
 * Central UI palette.
 * Current theme: dark cyan / teal.
 * Change these values to recolor the whole UI from one place.
 */
#define XLAT_UI_COLOR_BG             LV_COLOR_MAKE(0x0D, 0x14, 0x1F)
#define XLAT_UI_COLOR_PANEL          LV_COLOR_MAKE(0x16, 0x22, 0x30)
#define XLAT_UI_COLOR_PANEL_ALT      LV_COLOR_MAKE(0x1B, 0x2B, 0x3B)
#define XLAT_UI_COLOR_BORDER         LV_COLOR_MAKE(0x2E, 0x4A, 0x5E)
#define XLAT_UI_COLOR_TEXT           LV_COLOR_MAKE(0xF2, 0xF7, 0xFA)
#define XLAT_UI_COLOR_TEXT_MUTED     LV_COLOR_MAKE(0x9B, 0xAE, 0xBD)
#define XLAT_UI_COLOR_ACCENT         LV_COLOR_MAKE(0x36, 0xC2, 0xC9)
#define XLAT_UI_COLOR_ACCENT_SOFT    LV_COLOR_MAKE(0x22, 0x89, 0x95)
#define XLAT_UI_COLOR_SUCCESS        LV_COLOR_MAKE(0x45, 0xD4, 0x83)
#define XLAT_UI_COLOR_WARNING        LV_COLOR_MAKE(0xF4, 0xB4, 0x00)
#define XLAT_UI_COLOR_DANGER         LV_COLOR_MAKE(0xF1, 0x5B, 0x5B)

static inline void xlat_ui_style_screen(lv_obj_t * obj)
{
    lv_obj_set_style_bg_color(obj, XLAT_UI_COLOR_BG, 0);
    lv_obj_set_style_bg_opa(obj, LV_OPA_COVER, 0);
    lv_obj_set_style_text_color(obj, XLAT_UI_COLOR_TEXT, 0);
}

static inline void xlat_ui_style_panel(lv_obj_t * obj)
{
    lv_obj_set_style_bg_color(obj, XLAT_UI_COLOR_PANEL, 0);
    lv_obj_set_style_bg_opa(obj, LV_OPA_COVER, 0);
    lv_obj_set_style_border_color(obj, XLAT_UI_COLOR_BORDER, 0);
    lv_obj_set_style_border_width(obj, 1, 0);
    lv_obj_set_style_border_opa(obj, LV_OPA_80, 0);
    lv_obj_set_style_radius(obj, 8, 0);
    lv_obj_set_style_text_color(obj, XLAT_UI_COLOR_TEXT, 0);
}

static inline void xlat_ui_style_label_muted(lv_obj_t * obj)
{
    lv_obj_set_style_text_color(obj, XLAT_UI_COLOR_TEXT_MUTED, 0);
}

static inline void xlat_ui_style_button(lv_obj_t * btn, lv_color_t bg, lv_color_t border)
{
    lv_obj_set_style_radius(btn, 10, 0);
    lv_obj_set_style_bg_color(btn, bg, LV_PART_MAIN);
    lv_obj_set_style_bg_grad_color(btn, lv_color_mix(bg, XLAT_UI_COLOR_BG, LV_OPA_20), LV_PART_MAIN);
    lv_obj_set_style_bg_grad_dir(btn, LV_GRAD_DIR_VER, LV_PART_MAIN);
    lv_obj_set_style_bg_opa(btn, LV_OPA_COVER, LV_PART_MAIN);
    lv_obj_set_style_border_color(btn, border, LV_PART_MAIN);
    lv_obj_set_style_border_width(btn, 1, LV_PART_MAIN);
    lv_obj_set_style_border_opa(btn, LV_OPA_90, LV_PART_MAIN);
    lv_obj_set_style_shadow_width(btn, 10, LV_PART_MAIN);
    lv_obj_set_style_shadow_color(btn, border, LV_PART_MAIN);
    lv_obj_set_style_shadow_opa(btn, LV_OPA_20, LV_PART_MAIN);
    lv_obj_set_style_text_color(btn, XLAT_UI_COLOR_TEXT, LV_PART_MAIN);

    lv_obj_set_style_bg_color(btn, lv_color_mix(border, bg, LV_OPA_60), LV_PART_MAIN | LV_STATE_PRESSED);
    lv_obj_set_style_bg_grad_color(btn, bg, LV_PART_MAIN | LV_STATE_PRESSED);
    lv_obj_set_style_border_color(btn, border, LV_PART_MAIN | LV_STATE_PRESSED);
}

static inline void xlat_ui_style_dropdown(lv_obj_t * dd)
{
    lv_obj_set_style_bg_color(dd, XLAT_UI_COLOR_PANEL_ALT, LV_PART_MAIN);
    lv_obj_set_style_bg_opa(dd, LV_OPA_COVER, LV_PART_MAIN);
    lv_obj_set_style_border_color(dd, XLAT_UI_COLOR_BORDER, LV_PART_MAIN);
    lv_obj_set_style_border_width(dd, 1, LV_PART_MAIN);
    lv_obj_set_style_radius(dd, 8, LV_PART_MAIN);
    lv_obj_set_style_text_color(dd, XLAT_UI_COLOR_TEXT, LV_PART_MAIN);

    lv_obj_set_style_bg_color(dd, XLAT_UI_COLOR_PANEL, LV_PART_SELECTED);
    lv_obj_set_style_text_color(dd, XLAT_UI_COLOR_TEXT, LV_PART_SELECTED);

    lv_obj_set_style_bg_color(dd, XLAT_UI_COLOR_PANEL_ALT, LV_PART_ITEMS);
    lv_obj_set_style_text_color(dd, XLAT_UI_COLOR_TEXT, LV_PART_ITEMS);
    lv_obj_set_style_bg_color(dd, XLAT_UI_COLOR_ACCENT_SOFT, LV_PART_ITEMS | LV_STATE_CHECKED);
    lv_obj_set_style_text_color(dd, XLAT_UI_COLOR_TEXT, LV_PART_ITEMS | LV_STATE_CHECKED);
}

static inline void xlat_ui_style_tabview(lv_obj_t * tabview)
{
    lv_obj_t * tab_btns = lv_tabview_get_tab_btns(tabview);
    lv_obj_t * tab_content = lv_tabview_get_content(tabview);

    xlat_ui_style_panel(tabview);

    lv_obj_set_style_bg_color(tab_btns, XLAT_UI_COLOR_PANEL, LV_PART_MAIN);
    lv_obj_set_style_bg_opa(tab_btns, LV_OPA_COVER, LV_PART_MAIN);
    lv_obj_set_style_border_color(tab_btns, XLAT_UI_COLOR_BORDER, LV_PART_MAIN);
    lv_obj_set_style_border_width(tab_btns, 1, LV_PART_MAIN);
    lv_obj_set_style_text_color(tab_btns, XLAT_UI_COLOR_TEXT_MUTED, LV_PART_ITEMS);
    lv_obj_set_style_bg_color(tab_btns, XLAT_UI_COLOR_PANEL_ALT, LV_PART_ITEMS);
    lv_obj_set_style_bg_opa(tab_btns, LV_OPA_COVER, LV_PART_ITEMS);
    lv_obj_set_style_border_color(tab_btns, XLAT_UI_COLOR_BORDER, LV_PART_ITEMS);
    lv_obj_set_style_border_width(tab_btns, 1, LV_PART_ITEMS);
    lv_obj_set_style_bg_color(tab_btns, XLAT_UI_COLOR_ACCENT_SOFT, LV_PART_ITEMS | LV_STATE_CHECKED);
    lv_obj_set_style_text_color(tab_btns, XLAT_UI_COLOR_TEXT, LV_PART_ITEMS | LV_STATE_CHECKED);

    xlat_ui_style_panel(tab_content);
    lv_obj_set_style_pad_all(tab_content, 12, LV_PART_MAIN);
}

#endif
