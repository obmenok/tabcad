import numpy as np
import matplotlib.pyplot as plt
import ipywidgets as widgets
from IPython.display import display, clear_output
import matplotlib.gridspec as gridspec

# =====================================================================
# 1. ГЛОБАЛЬНЫЕ НАСТРОЙКИ (Константы чертежа)
# =====================================================================
DIM_LINE_WIDTH = 0.6  
C_TEXT = '#9467bd'    
ARROW_LENGTH = 10.0  
ARR_STYLE_DOUBLE = "<|-|>,head_length=1,head_width=0.175"
ARR_STYLE_SINGLE = "-|>,head_length=1,head_width=0.175"

# =====================================================================
# 2. НАСТРОЙКА ИНТЕРФЕЙСА (Виджеты)
# =====================================================================
style = {'description_width': '125px'}
layout = {'width': '210px'}            

# Входные параметры (Капсула FFBE)
ui_W = widgets.FloatText(value=9.2, step=0.01, description='Minor Axis:', style=style, layout=layout)
ui_L = widgets.FloatText(value=18.3, step=0.01, description='Major Axis:', style=style, layout=layout)

# Для строгой капсулы радиусы концов жестко привязаны к ширине
ui_Re = widgets.FloatText(value=4.6, description='End Radius:', disabled=True, style=style, layout=layout)
ui_Rs = widgets.FloatText(value=0.0, description='Side Radius:', disabled=True, style=style, layout=layout)

ui_Dc = widgets.FloatText(value=1.47, step=0.01, description='Cup Depth:', style=style, layout=layout)
ui_Rc = widgets.FloatText(value=7.6841, description='Cup Radius Minor:', disabled=True, style=style, layout=layout)

ui_Land = widgets.FloatText(value=0.08, step=0.01, description='Land:', style=style, layout=layout)
ui_Hb = widgets.FloatText(value=2.54, step=0.01, description='Belly Band:', style=style, layout=layout)
ui_Tt = widgets.FloatText(value=5.48, step=0.01, description='Tablet Thick:', style=style, layout=layout)

# Параметры фаски и скругления
ui_Bev_A = widgets.FloatText(value=30.0, step=0.1, description='Bevel Angle:', style=style, layout=layout)
ui_Blend_R = widgets.FloatText(value=0.38, step=0.01, description='Blend Radius:', style=style, layout=layout)

# Входные параметры (Риска) - Только None и Cut Through
ui_b_type = widgets.Dropdown(options=['None', 'Cut Through'], value='None', description='Bisect Type:', style=style, layout=layout)
ui_b_width = widgets.FloatText(value=2.2566, step=0.01, description='Width:', style=style, layout=layout)
ui_b_depth = widgets.FloatText(value=1.121, step=0.01, description='Depth:', style=style, layout=layout)
ui_b_angle = widgets.FloatText(value=90.0, step=0.01, description='Angle:', style=style, layout=layout)
ui_b_Ri = widgets.FloatText(value=0.061, step=0.01, description='Radius Inner:', style=style, layout=layout)

btn_suggest = widgets.Button(description="Suggested Bisect", button_style='info', layout=layout)

# Выходные параметры
calc_style = {'description_width': '130px'}
calc_layout = {'width': '220px'}
ui_calc_die = widgets.FloatText(description='Die Hole SA:', disabled=True, style=calc_style, layout=calc_layout)
ui_calc_cvol = widgets.FloatText(description='Cup Volume:', disabled=True, style=calc_style, layout=calc_layout)
ui_calc_csa = widgets.FloatText(description='Cup SA:', disabled=True, style=calc_style, layout=calc_layout)
ui_calc_perim = widgets.FloatText(description='Perimeter:', disabled=True, style=calc_style, layout=calc_layout)
ui_calc_tsa = widgets.FloatText(description='Tablet SA:', disabled=True, style=calc_style, layout=calc_layout)
ui_calc_tvol = widgets.FloatText(description='Tablet Vol:', disabled=True, style=calc_style, layout=calc_layout)

out = widgets.Output()

# =====================================================================
# 3. МАТЕМАТИКА КАПСУЛЫ (FFBE) И РИСКИ
# =====================================================================
def get_capsule_ffbe_profile(rho_arr, rc, Dc, R_blend, angle_deg):
    """Возвращает профиль Flat Face Bevel Edge по расстоянию rho от хребта капсулы"""
    z_prof = np.zeros_like(rho_arr)
    alpha = np.radians(angle_deg)
    if alpha <= 0 or alpha >= np.pi/2: return z_prof
    
    tan_a = np.tan(alpha)
    sin_a = np.sin(alpha)
    
    R_blend = min(R_blend, Dc)
    
    # Горизонтальное расстояние фаски и скругления
    D_inset = (Dc - R_blend) / tan_a + R_blend / sin_a if tan_a > 0 and sin_a > 0 else 0
    r_flat = max(0, rc - D_inset)
    
    Rt = r_flat + R_blend * sin_a if r_flat > 0 else rc - Dc / tan_a
    
    mask_flat = rho_arr <= r_flat
    mask_blend = (rho_arr > r_flat) & (rho_arr <= Rt)
    mask_bevel = (rho_arr > Rt) & (rho_arr <= rc)
    
    if np.any(mask_flat):
        z_prof[mask_flat] = Dc
    if np.any(mask_blend):
        z_prof[mask_blend] = (Dc - R_blend) + np.sqrt(np.maximum(0, R_blend**2 - (rho_arr[mask_blend] - r_flat)**2))
    if np.any(mask_bevel):
        z_prof[mask_bevel] = (rc - rho_arr[mask_bevel]) * tan_a
        
    return np.maximum(0, z_prof)

def compute_width_from_depth(depth, angle, ri, dc, R_blend, angle_deg, rc):
    if depth <= 0: return 0.0
    x_test = np.linspace(0, rc, 5000)
    z_bottom = dc - depth
    alpha = np.radians(angle / 2.0)
    d_sharp = ri / np.sin(alpha) - ri if ri > 0 and alpha > 0 else 0
    x_ti = ri * np.sin(alpha)
    
    z_v = z_bottom - d_sharp + x_test / np.tan(alpha)
    z_inner = z_bottom + ri - np.sqrt(np.maximum(0, ri**2 - x_test**2))
    z_g = np.where(x_test <= x_ti, z_inner, z_v)
    
    z_cup = get_capsule_ffbe_profile(x_test, rc, dc, R_blend, angle_deg)
    
    diff = z_cup - z_g
    crossings = np.where(np.diff(np.sign(diff)))[0]
    
    if len(crossings) > 0:
        idx = crossings[0]
        x1, x2 = x_test[idx], x_test[idx+1]
        y1, y2 = diff[idx], diff[idx+1]
        x_exact = x1 - y1 * (x2 - x1) / (y2 - y1)
        return round(2 * x_exact, 4)
    return 0.0

def compute_depth_from_width(target_width, angle, ri, dc, R_blend, angle_deg, rc):
    if target_width <= 0: return 0.0
    d_min, d_max = 0.0, dc * 2.0
    for _ in range(35):
        d_mid = (d_min + d_max) / 2
        w_mid = compute_width_from_depth(d_mid, angle, ri, dc, R_blend, angle_deg, rc)
        if w_mid < target_width: d_min = d_mid
        else: d_max = d_mid
    return round((d_min + d_max) / 2, 4)

def apply_suggested(b):
    global updating
    updating = True
    try:
        if ui_b_type.value == 'None':
            ui_b_type.value = 'Cut Through'
           
        ui_b_angle.value = 90.0
        ui_b_Ri.value = 0.061
       
        suggested_depth = round(ui_Dc.value * 0.95, 4)
        ui_b_depth.value = suggested_depth
        
        r_c = ui_W.value / 2 - ui_Land.value
        ui_b_width.value = compute_width_from_depth(suggested_depth, 90.0, 0.061, ui_Dc.value, ui_Blend_R.value, ui_Bev_A.value, r_c)
    finally:
        updating = False
        draw_views()

btn_suggest.on_click(apply_suggested)

# =====================================================================
# 4. ЛОГИКА ВАЛИДАЦИИ И ПРЕДОХРАНИТЕЛИ
# =====================================================================
updating = False

def on_value_change(change):
    global updating
    if updating: return
    updating = True

    try:
        sender = change['owner']
        ui_W.value = max(0.01, ui_W.value)
        ui_L.value = max(0.01, ui_L.value)
        if ui_W.value > ui_L.value: ui_W.value = ui_L.value

        ui_Dc.value = max(0.01, ui_Dc.value)
        ui_Land.value = max(0.0, ui_Land.value)
        ui_Hb.value = max(0.0, ui_Hb.value)
        ui_Tt.value = max(0.01, ui_Tt.value)

        ui_Bev_A.value = max(1.0, min(89.0, ui_Bev_A.value))
        ui_Blend_R.value = max(0.0, ui_Blend_R.value)

        ui_b_angle.value = max(1.0, min(179.0, ui_b_angle.value))
        ui_b_depth.value = max(0.0, ui_b_depth.value)
        ui_b_width.value = max(0.0, ui_b_width.value)
        ui_b_Ri.value = max(0.0, ui_b_Ri.value)

        W = ui_W.value
        L = ui_L.value
        Land = ui_Land.value
        Dc = ui_Dc.value
        
        if Land >= W/2:
            ui_Land.value = 0; Land = 0
            
        r_c = W/2 - Land
        ui_Re.value = W / 2

        # === ИНТЕЛЛЕКТУАЛЬНЫЙ ПРЕДОХРАНИТЕЛЬ ДЛЯ ФАСКИ ===
        alpha = np.radians(ui_Bev_A.value)
        tan_a = np.tan(alpha)
        sin_a = np.sin(alpha)
        cos_a = np.cos(alpha)
        
        max_Dc = r_c * tan_a
        if Dc > max_Dc - 0.001:
            Dc = round(max_Dc - 0.001, 4)
            ui_Dc.value = Dc

        max_rb_num = r_c * sin_a - Dc * cos_a
        max_rb_den = 1.0 - cos_a
        
        if max_rb_den > 1e-5:
            max_rb = max_rb_num / max_rb_den
            if max_rb < 0: max_rb = 0.0
        else:
            max_rb = Dc 

        max_rb = min(Dc, max_rb)
        if ui_Blend_R.value > max_rb:
            ui_Blend_R.value = round(max_rb, 4)
        # =================================================

        # Синхронизация эквивалентного сферического радиуса
        if sender in (ui_W, ui_L, ui_Dc, ui_Land, ui_Bev_A, ui_Blend_R):
            ui_Rc.value = round((r_c**2 + Dc**2) / (2 * Dc), 4)
            if sender == ui_Dc: ui_Tt.value = round(ui_Hb.value + 2 * Dc, 4)

        # Синхронизация толщины
        if sender == ui_Hb: ui_Tt.value = round(ui_Hb.value + 2 * ui_Dc.value, 4)
        elif sender == ui_Tt:
            new_hb = ui_Tt.value - 2 * ui_Dc.value
            if new_hb >= 0: ui_Hb.value = round(new_hb, 4)
            else: ui_Hb.value = 0; ui_Tt.value = round(2 * ui_Dc.value, 4)

        max_b_depth = round(ui_Dc.value * 0.95, 4)
        if ui_b_depth.value > max_b_depth:
            ui_b_depth.value = max_b_depth

        # Синхронизация риски
        if sender == ui_b_width:
            calc_depth = compute_depth_from_width(ui_b_width.value, ui_b_angle.value, ui_b_Ri.value, ui_Dc.value, ui_Blend_R.value, ui_Bev_A.value, r_c)
            if calc_depth > max_b_depth:
                ui_b_depth.value = max_b_depth
                ui_b_width.value = compute_width_from_depth(max_b_depth, ui_b_angle.value, ui_b_Ri.value, ui_Dc.value, ui_Blend_R.value, ui_Bev_A.value, r_c)
            else:
                ui_b_depth.value = calc_depth
        elif sender in (ui_b_depth, ui_b_angle, ui_b_Ri, ui_b_type, ui_Dc, ui_W, ui_Land, ui_Blend_R, ui_Bev_A):
            ui_b_width.value = compute_width_from_depth(ui_b_depth.value, ui_b_angle.value, ui_b_Ri.value, ui_Dc.value, ui_Blend_R.value, ui_Bev_A.value, r_c)

        draw_views()
    finally:
        updating = False

for widget in (ui_W, ui_L, ui_Hb, ui_Tt, ui_Dc, ui_Blend_R, ui_Bev_A, ui_Land, ui_b_type, ui_b_width, ui_b_depth, ui_b_angle, ui_b_Ri):
    widget.observe(on_value_change, names='value')

# =====================================================================
# 5. ИНСТРУМЕНТЫ РИСОВАНИЯ
# =====================================================================
def get_capsule_contour(L, W, density=200):
    r = W / 2
    l_flat = max(0, L - W)
    t_top = np.linspace(0, np.pi, density)
    t_bot = np.linspace(np.pi, 2*np.pi, density)
    
    x_top = l_flat/2 + r * np.sin(t_top)
    y_top = r * np.cos(t_top)
    x_bot = -l_flat/2 + r * np.sin(t_bot)
    y_bot = r * np.cos(t_bot)
    
    return np.concatenate([x_top, x_bot, [x_top[0]]]), np.concatenate([y_top, y_bot, [y_top[0]]])

def draw_ext(ax, px1, py1, px2, py2, dx, dy, text, offset=(0,0)):
    ex1, ey1 = px1 + dx, py1 + dy; ex2, ey2 = px2 + dx, py2 + dy
    sgx, sgy = np.sign(dx) if dx != 0 else 0, np.sign(dy) if dy != 0 else 0
    ax.plot([px1, ex1 + sgx*0.5], [py1, ey1 + sgy*0.5], 'k-', lw=DIM_LINE_WIDTH)
    ax.plot([px2, ex2 + sgx*0.5], [py2, ey2 + sgy*0.5], 'k-', lw=DIM_LINE_WIDTH)
    ax.annotate('', xy=(ex1, ey1), xytext=(ex2, ey2), arrowprops=dict(arrowstyle=ARR_STYLE_DOUBLE, color='black', lw=DIM_LINE_WIDTH, mutation_scale=ARROW_LENGTH))
    tx, ty = (ex1+ex2)/2 + offset[0], (ey1+ey2)/2 + offset[1]
    ax.text(tx, ty, text, color=C_TEXT, ha='center', va='center', bbox=dict(facecolor='#f4f4f9', edgecolor='none', pad=1), fontsize=9)

def draw_ext_outside(ax, px1, py1, px2, py2, dx, dy, text):
    ex1, ey1 = px1 + dx, py1 + dy; ex2, ey2 = px2 + dx, py2 + dy
    sgx, sgy = np.sign(dx) if dx != 0 else 0, np.sign(dy) if dy != 0 else 0
    ax.plot([px1, ex1 + sgx*0.5], [py1, ey1 + sgy*0.5], 'k-', lw=DIM_LINE_WIDTH)
    ax.plot([px2, ex2 + sgx*0.5], [py2, ey2 + sgy*0.5], 'k-', lw=DIM_LINE_WIDTH)
    vec_x, vec_y = ex2 - ex1, ey2 - ey1
    length = np.sqrt(vec_x**2 + vec_y**2)
    if length == 0: return
    ux, uy = vec_x / length, vec_y / length
    ax.annotate('', xy=(ex1, ey1), xytext=(ex1 - ux*3, ey1 - uy*3), arrowprops=dict(arrowstyle=ARR_STYLE_SINGLE, color='black', lw=DIM_LINE_WIDTH, mutation_scale=ARROW_LENGTH))
    ax.annotate('', xy=(ex2, ey2), xytext=(ex2 + ux*3, ey2 + uy*3), arrowprops=dict(arrowstyle=ARR_STYLE_SINGLE, color='black', lw=DIM_LINE_WIDTH, mutation_scale=ARROW_LENGTH))
    tx, ty = ex2 + ux*5, ey2 + uy*5
    ax.text(tx, ty, text, color=C_TEXT, ha='center', va='center', bbox=dict(facecolor='#f4f4f9', edgecolor='none', pad=1), fontsize=9)

def draw_pointer(ax, p_target, p_text, text):
    ax.annotate(text, xy=p_target, xytext=p_text, arrowprops=dict(arrowstyle=ARR_STYLE_SINGLE, color='black', lw=DIM_LINE_WIDTH, mutation_scale=ARROW_LENGTH),
                color=C_TEXT, ha='center', va='center', fontsize=9, bbox=dict(facecolor='#f4f4f9', edgecolor='none', pad=0.5))

# =====================================================================
# 6. ГЛАВНАЯ ФУНКЦИЯ (Математика и Рендер)
# =====================================================================
def draw_views():
    with out:
        clear_output(wait=True)
        W, L, Hb, Tt = ui_W.value, ui_L.value, ui_Hb.value, ui_Tt.value
        Dc, Land = ui_Dc.value, ui_Land.value
        R_blend, Bev_A = ui_Blend_R.value, ui_Bev_A.value
        b_type, b_depth, b_angle, b_Ri = ui_b_type.value, ui_b_depth.value, ui_b_angle.value, ui_b_Ri.value

        l_flat = max(0, L - W)
        r_c = W/2 - Land
        
        # Расчет границ плоской части капсулы
        alpha_rad = np.radians(Bev_A)
        tan_a = np.tan(alpha_rad)
        sin_a = np.sin(alpha_rad)
        D_inset = (Dc - R_blend) / tan_a + R_blend / sin_a if tan_a > 0 and sin_a > 0 else 0
        r_flat = max(0, r_c - D_inset)
        
        Die_Hole_SA = W * l_flat + np.pi * (W/2)**2
        Perimeter = 2 * l_flat + np.pi * W
        Land_SA = (W * l_flat + np.pi * (W/2)**2) - (2 * r_c * l_flat + np.pi * r_c**2)

        x_grid, y_grid = np.linspace(-L/2, L/2, 300), np.linspace(-W/2, W/2, 300)
        X, Y = np.meshgrid(x_grid, y_grid)
        dx, dy = x_grid[1] - x_grid[0], y_grid[1] - y_grid[0]
        dA = dx * dy

        # Расчет расстояния rho от центрального "хребта" капсулы
        rho = np.zeros_like(X)
        mask_center = np.abs(X) <= l_flat/2
        mask_top = X > l_flat/2
        mask_bot = X < -l_flat/2
        
        rho[mask_center] = np.abs(Y[mask_center])
        rho[mask_top] = np.sqrt((X[mask_top] - l_flat/2)**2 + Y[mask_top]**2)
        rho[mask_bot] = np.sqrt((X[mask_bot] + l_flat/2)**2 + Y[mask_bot]**2)

        mask_cup = rho <= r_c

        # 3D Генерация свода капсулы FFBE
        Z = np.zeros_like(X)
        Z[mask_cup] = get_capsule_ffbe_profile(rho[mask_cup], r_c, Dc, R_blend, Bev_A)
        
        # СТАБИЛИЗАТОР ПЛОСКОЙ ЧАСТИ ОТ МИКРОШУМОВ
        Z = np.where(np.abs(Z - Dc) < 1e-9, Dc, Z)

        Z_cup_top = Z.copy()
        Z_groove = np.full_like(X, Dc * 5.0)
       
        if b_type != 'None' and b_depth > 0:
            alpha_b = np.radians(b_angle / 2.0)
            d_sharp = b_Ri / np.sin(alpha_b) - b_Ri if b_Ri > 0 and alpha_b > 0 else 0
            x_ti = b_Ri * np.sin(alpha_b)
           
            Z_centerline = np.zeros_like(X)
            m_in = np.abs(X) <= r_c 
            Z_centerline[m_in] = get_capsule_ffbe_profile(np.abs(Y[m_in]), r_c, Dc, R_blend, Bev_A)
            Z_centerline = np.where(np.abs(Z_centerline - Dc) < 1e-9, Dc, Z_centerline)
            
            if b_type == 'Cut Through':
                z_bottom = np.full_like(X, Dc - b_depth)

            X_abs = np.abs(X)
            Z_v = z_bottom - d_sharp + X_abs / np.tan(alpha_b)
            Z_inner = z_bottom + b_Ri - np.sqrt(np.maximum(0, b_Ri**2 - X_abs**2))
            Z_groove = np.where(X_abs <= x_ti, Z_inner, Z_v)
            Z_cup_top = np.maximum(0, np.minimum(Z, Z_groove))

        Cup_Volume_Final = np.sum(Z_cup_top) * dA
        dZdx, dZdy = np.gradient(Z_cup_top, dx, axis=1), np.gradient(Z_cup_top, dy, axis=0)
        Cup_SA_Final = np.sum(np.sqrt(1 + dZdx**2 + dZdy**2)[mask_cup]) * dA

        ui_calc_die.value = round(Die_Hole_SA, 4)
        ui_calc_cvol.value = round(Cup_Volume_Final, 4)
        ui_calc_csa.value = round(Cup_SA_Final + Land_SA, 4)
        ui_calc_perim.value = round(Perimeter, 4)
        ui_calc_tsa.value = round(Perimeter * Hb + 2 * (Cup_SA_Final + Land_SA), 4)
        ui_calc_tvol.value = round(Die_Hole_SA * Hb + 2 * Cup_Volume_Final, 4)

        # -----------------------------------------------------------
        # ОТРИСОВКА ВИДОВ
        # -----------------------------------------------------------
        fig, ax = plt.subplots(figsize=(10, 10))
        fig.patch.set_facecolor('#f4f4f9')
        ax.set_aspect('equal')
        ax.axis('off')

        cx_top, cy_top = 0, 0
        cx_side, cy_side = -(W/2 + Tt/2 + 15), 0
        cx_front, cy_front = 0, -(L/2 + Tt/2 + 15)

        # --- 1. TOP VIEW (Вид сверху) ---
        x_out, y_out = get_capsule_contour(L, W)
        ax.plot(y_out + cx_top, x_out + cy_top, 'k-', linewidth=1.2)
        if Land > 0:
            x_in, y_in = get_capsule_contour(L - 2*Land, W - 2*Land)
            ax.plot(y_in + cx_top, x_in + cy_top, 'k-', linewidth=0.6)
            
        # Линия плоской части (пунктирная капсула)
        if r_flat > 0.05:
            flat_L = l_flat + 2 * r_flat
            flat_W = 2 * r_flat
            x_flat, y_flat = get_capsule_contour(flat_L, flat_W)
            ax.plot(y_flat + cx_top, x_flat + cy_top, 'k--', linewidth=0.6)

        if b_type != 'None' and b_depth > 0:
            Z_diff_masked = np.where(mask_cup, Z - Z_groove, np.nan)
            Z_groove_masked = np.where(mask_cup, Z_groove, np.nan)
            
            ax.contour(Y + cx_top, X + cy_top, Z_diff_masked, levels=[0], colors='k', linewidths=0.8)
            ax.contour(Y + cx_top, X + cy_top, Z_groove_masked, levels=[0], colors='k', linewidths=0.6)
            
            x_ti_val = b_Ri * np.sin(np.radians(b_angle / 2.0))
            if x_ti_val > 0.005:
                idx_x = np.argmin(np.abs(x_grid - x_ti_val))
                cond = (Z - Z_groove)[:, idx_x]
                
                cond = np.where(mask_cup[:, idx_x], cond, -1.0)
                
                valid_indices = np.where(cond >= 0)[0]
                if len(valid_indices) > 0:
                    i_min, i_max = valid_indices[0], valid_indices[-1]
                    y_start, y_end = y_grid[i_min], y_grid[i_max]
                    if i_min > 0:
                        c0, c1 = cond[i_min], cond[i_min-1]
                        if c0 != c1: y_start = y_grid[i_min] - c0 * (y_grid[i_min-1] - y_grid[i_min]) / (c1 - c0)
                    if i_max < len(y_grid) - 1:
                        c0, c1 = cond[i_max], cond[i_max+1]
                        if c0 != c1: y_end = y_grid[i_max] - c0 * (y_grid[i_max+1] - y_grid[i_max]) / (c1 - c0)
                    
                    ax.plot([y_start + cx_top, y_end + cx_top], [x_ti_val + cy_top, x_ti_val + cy_top], 'k-', lw=0.6)
                    ax.plot([y_start + cx_top, y_end + cx_top], [-x_ti_val + cy_top, -x_ti_val + cy_top], 'k-', lw=0.6)

        draw_ext(ax, cx_top - W/2, cy_top + L/2, cx_top + W/2, cy_top + L/2, 0, 4, f"{W:g}\nMinor Axis")
        draw_ext(ax, cx_top - W/2, cy_top - L/2, cx_top - W/2, cy_top + L/2, -4.5, 0, f"{L:g}\nMajor Axis")

        # --- 2. SIDE VIEW (Разрез вдоль длины L) ---
        yc_up_maj = Hb/2
        x_maj_cup = np.linspace(-L/2 + Land, L/2 - Land, 400)
        
        rho_maj = np.maximum(0, np.abs(x_maj_cup) - l_flat/2)
        z_up_maj_surf = get_capsule_ffbe_profile(rho_maj, r_c, Dc, R_blend, Bev_A) + yc_up_maj
       
        if b_type != 'None' and b_depth > 0:
            X_abs_1d = np.abs(x_maj_cup)
            alpha_1d = np.radians(b_angle / 2.0)
            d_sharp_1d = b_Ri / np.sin(alpha_1d) - b_Ri if b_Ri > 0 else 0
            x_ti_1d = b_Ri * np.sin(alpha_1d)
            z_bottom_1d = Dc - b_depth 
            
            z_v_1d = z_bottom_1d - d_sharp_1d + X_abs_1d / np.tan(alpha_1d)
            z_inner_1d = z_bottom_1d + b_Ri - np.sqrt(np.maximum(0, b_Ri**2 - X_abs_1d**2))
            z_g_1d = np.where(X_abs_1d <= x_ti_1d, z_inner_1d, z_v_1d)
            z_up_maj_surf = np.minimum(z_up_maj_surf, Hb/2 + z_g_1d)

        l_prof = np.concatenate([[-L/2, -L/2], [-L/2, -L/2 + Land], x_maj_cup, [L/2 - Land, L/2], [L/2, L/2], [L/2, L/2 - Land], x_maj_cup[::-1], [-L/2 + Land, -L/2], [-L/2]])
        
        z_down_maj_surf = get_capsule_ffbe_profile(rho_maj, r_c, Dc, R_blend, Bev_A) + yc_up_maj

        t_prof = np.concatenate([[-Hb/2, Hb/2], [Hb/2, Hb/2], z_up_maj_surf, [Hb/2, Hb/2], [Hb/2, -Hb/2], [-Hb/2, -Hb/2], -z_down_maj_surf[::-1], [-Hb/2, -Hb/2], [-Hb/2]])

        ax.plot(t_prof + cx_side, l_prof + cy_side, 'k-', linewidth=1.2)
        ax.plot([-Hb/2 + cx_side, -Hb/2 + cx_side], [-L/2 + cy_side, L/2 + cy_side], 'k-', linewidth=1.2)
        ax.plot([Hb/2 + cx_side, Hb/2 + cx_side], [-L/2 + cy_side, L/2 + cy_side], 'k-', linewidth=1.2)

        draw_ext_outside(ax, cx_side + Hb/2, cy_side + L/2, cx_side + Hb/2 + Dc, cy_side + L/2, 0, 4, f"{Dc:g}\nCup Depth")
        draw_ext_outside(ax, cx_side - Hb/2, cy_side - L/2, cx_side + Hb/2, cy_side - L/2, 0, -4, f"{Hb:g}\nBelly Band")

        if r_flat > 0:
            flat_L_val = l_flat + 2 * r_flat
            draw_ext(ax, cx_side + Hb/2 + Dc, cy_side + flat_L_val/2, cx_side + Hb/2 + Dc, cy_side - flat_L_val/2, 4.5, 0, f"{flat_L_val:.3f}\nRef. Flat")

        # --- 3. FRONT VIEW (Разрез поперек ширины W) ---
        yc_up_min = Hb/2
        y_min_cup = np.linspace(-r_c, r_c, 200)
        
        rho_min = np.abs(y_min_cup)
        z_up_min = yc_up_min + get_capsule_ffbe_profile(rho_min, r_c, Dc, R_blend, Bev_A)

        w_prof = np.concatenate([[-W/2, -W/2], [-W/2, -r_c], y_min_cup, [r_c, W/2], [W/2, W/2], [W/2, r_c], y_min_cup[::-1], [-r_c, -W/2], [-W/2]])
        th_prof = np.concatenate([[-Hb/2, Hb/2], [Hb/2, Hb/2], z_up_min, [Hb/2, Hb/2], [Hb/2, -Hb/2], [-Hb/2, -Hb/2], -z_up_min[::-1], [-Hb/2, -Hb/2], [-Hb/2]])

        ax.plot(w_prof + cx_front, th_prof + cy_front, 'k-', linewidth=1.2)
        ax.plot([-W/2 + cx_front, W/2 + cx_front], [Hb/2 + cy_front, Hb/2 + cy_front], 'k-', linewidth=1.2)
        ax.plot([-W/2 + cx_front, W/2 + cx_front], [-Hb/2 + cy_front, -Hb/2 + cy_front], 'k-', linewidth=1.2)
       
        if b_type != 'None' and b_depth > 0:
            Z_centerline_front = get_capsule_ffbe_profile(rho_min, r_c, Dc, R_blend, Bev_A)
            Z_centerline_front = np.where(np.abs(Z_centerline_front - Dc) < 1e-9, Dc, Z_centerline_front)
            
            if b_type == 'Cut Through': z_bottom_line = np.full_like(y_min_cup, Dc - b_depth)
           
            valid = (z_bottom_line > 0) & ((z_bottom_line + Hb/2) < z_up_min)
            ax.plot(y_min_cup[valid] + cx_front, z_bottom_line[valid] + Hb/2 + cy_front, 'k--', lw=0.8)

        draw_ext(ax, cx_front - W/2, cy_front - Tt/2, cx_front - W/2, cy_front + Tt/2, -4.5, 0, f"{Tt:g}\nTablet Thickness")
        
        # Выноска Ref. Flat (внизу по центру, на Front View это ширина плоской части)
        if r_flat > 0:
            flat_W_val = 2 * r_flat
            draw_ext_outside(ax, cx_front - r_flat, cy_front - Hb/2 - Dc, cx_front + r_flat, cy_front - Hb/2 - Dc, 0, -3, f"{flat_W_val:.3f}\nRef. Flat")

        # Отрисовка угла Bevel Angle на фронтальном виде (СПРАВА)
        if Bev_A > 0 and Bev_A < 90:
            pt_t = cx_front + W/2  # Правая граница (край Belly Band)
            pt_l = cy_front + Hb/2 # Верхняя граница Belly Band
            ext_len = W / 2.5 # Длина выносных линий
            
            alpha_rad = np.radians(Bev_A)
            
            # Горизонтальная выносная линия (вправо)
            ax.plot([pt_t, pt_t + ext_len], [pt_l, pt_l], 'k-', lw=DIM_LINE_WIDTH)
            
            # Наклонная выносная линия (продолжение фаски вниз-вправо)
            dx = ext_len * np.cos(alpha_rad)
            dy = -ext_len * np.sin(alpha_rad)
            ax.plot([pt_t, pt_t + dx], [pt_l, pt_l + dy], 'k-', lw=DIM_LINE_WIDTH)
            
            # Дуга
            arc_r = min(4.0, ext_len * 0.8)
            # Углы в полярных координатах: Горизонталь=0, Наклонная=-alpha_rad
            t_arc = np.linspace(-alpha_rad, 0, 30)
            ax.plot(pt_t + arc_r * np.cos(t_arc), pt_l + arc_r * np.sin(t_arc), 'k-', lw=DIM_LINE_WIDTH)
            
            # Текст угла
            mid_ang = -alpha_rad / 2
            text_offset = 1.5
            ax.text(pt_t + (arc_r + text_offset) * np.cos(mid_ang), pt_l + (arc_r + text_offset) * np.sin(mid_ang), 
                    f"{Bev_A:g}°", color=C_TEXT, ha='center', va='center', fontsize=9,
                    bbox=dict(facecolor='#f4f4f9', edgecolor='none', pad=0.5))

        # Выноска Blend Radius (указывает на скругление слева вверху)
        w_target_val = - (r_c - D_inset + (R_blend * sin_a)/2) 
        z_min_pt = get_capsule_ffbe_profile(np.array([np.abs(w_target_val)]), r_c, Dc, R_blend, Bev_A)[0]
        targ_front = (cx_front + w_target_val, cy_front + Hb/2 + z_min_pt)
        txt_front = (cx_front + w_target_val - W/4.5, cy_front + Hb/2 + z_min_pt + 4)
        draw_pointer(ax, targ_front, txt_front, f"{R_blend:g}\nBlend Radius")

        if Land > 0:
            ax.plot([cx_front + r_c, cx_front + r_c], [cy_front + Tt/2, cy_front + Tt/2 + 2.5], 'k-', lw=DIM_LINE_WIDTH)
            ax.plot([cx_front + W/2, cx_front + W/2], [cy_front + Tt/2, cy_front + Tt/2 + 2.5], 'k-', lw=DIM_LINE_WIDTH)
            ax.annotate('', xy=(cx_front + r_c, cy_front + Tt/2 + 2), xytext=(cx_front + r_c - 2.5, cy_front + Tt/2 + 2), arrowprops=dict(arrowstyle=ARR_STYLE_SINGLE, color='black', lw=DIM_LINE_WIDTH, mutation_scale=ARROW_LENGTH))
            ax.annotate('', xy=(cx_front + W/2, cy_front + Tt/2 + 2), xytext=(cx_front + W/2 + 2.5, cy_front + Tt/2 + 2), arrowprops=dict(arrowstyle=ARR_STYLE_SINGLE, color='black', lw=DIM_LINE_WIDTH, mutation_scale=ARROW_LENGTH))
            ax.text(cx_front + W/2 + 5, cy_front + Tt/2 + 2, f"{Land:g}\nBld. Land", color=C_TEXT, ha='center', va='center', fontsize=9, bbox=dict(facecolor='#f4f4f9', edgecolor='none', pad=0.5))

        x_min_val = cx_side - Tt/2 - 12
        x_max_val = cx_top + W/2 + 15
        y_min_val = cy_front - Tt/2 - 8
        y_max_val = cy_top + L/2 + 8

        center_x = (x_max_val + x_min_val) / 2
        center_y = (y_max_val + y_min_val) / 2
        max_range = max(x_max_val - x_min_val, y_max_val - y_min_val)
        padding = max_range * 0.02

        ax.set_xlim(center_x - max_range/2 - padding, center_x + max_range/2 + padding)
        ax.set_ylim(center_y - max_range/2 - padding, center_y + max_range/2 + padding)

        plt.tight_layout()
        plt.show()

draw_views()

# =====================================================================
# 7. КОМПОНОВКА ВЕРСТКИ
# =====================================================================
col1 = widgets.VBox([ui_W, ui_L])
col2 = widgets.VBox([ui_Re, ui_Rs])
col3 = widgets.VBox([ui_Dc, ui_Rc])
col4 = widgets.VBox([ui_Bev_A, ui_Blend_R])
col5 = widgets.VBox([ui_Land, ui_Hb, ui_Tt])
col6 = widgets.VBox([ui_b_type, btn_suggest, ui_b_width, ui_b_depth, ui_b_angle, ui_b_Ri])
input_box = widgets.HBox([col1, col2, col3, col4, col5, col6])

calc_col1 = widgets.VBox([ui_calc_die, ui_calc_cvol, ui_calc_csa])
calc_col2 = widgets.VBox([ui_calc_perim, ui_calc_tsa, ui_calc_tvol])
calc_box = widgets.HBox([calc_col1, calc_col2], layout=widgets.Layout(margin='10px 0 0 0'))

display(input_box)
display(widgets.HTML(value="<b>Approximated Calculations:</b>"))
display(calc_box)
display(out)