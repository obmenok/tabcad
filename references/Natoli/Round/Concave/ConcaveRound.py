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
style = {'description_width': '110px'}
layout = {'width': '200px'}            

# Входные параметры (Круглая таблетка)
ui_D = widgets.FloatText(value=8.0, step=0.01, description='Diameter:', style=style, layout=layout)
ui_Dc = widgets.FloatText(value=0.9213, step=0.01, description='Cup Depth:', style=style, layout=layout)
ui_Rc = widgets.FloatText(value=8.8, step=0.01, description='Cup Radius:', style=style, layout=layout)

ui_Land = widgets.FloatText(value=0.08, step=0.01, description='Land:', style=style, layout=layout)
ui_Hb = widgets.FloatText(value=2.5574, step=0.01, description='Belly Band:', style=style, layout=layout)
ui_Tt = widgets.FloatText(value=4.4, step=0.01, description='Tablet Thick:', style=style, layout=layout)

# Входные параметры (Риска)
ui_b_type = widgets.Dropdown(options=['None', 'Standard', 'Cut Through', 'Decreasing'], value='None', description='Bisect Type:', style=style, layout=layout)
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
# 3. МАТЕМАТИКА РИСКИ И ДВУСТОРОННИЙ СОЛВЕР
# =====================================================================
def compute_width_from_depth(depth, angle, ri, dc, rc):
    if depth <= 0: return 0.0
    half_angle = np.radians(angle / 2.0)
    if half_angle <= 0: return 0.0
    
    d_sharp = depth - ri + ri / np.sin(half_angle) if ri > 0 else depth
    
    a_quad = 1.0 / (np.sin(half_angle)**2)
    b_quad = 2.0 * (rc - d_sharp) / np.tan(half_angle)
    c_quad = d_sharp**2 - 2.0 * rc * d_sharp
    
    discriminant = b_quad**2 - 4 * a_quad * c_quad
    if discriminant >= 0:
        x_intersect = (-b_quad + np.sqrt(discriminant)) / (2 * a_quad)
        return round(2.0 * x_intersect, 4)
    return 0.0

def compute_depth_from_width(target_width, angle, ri, dc, rc):
    if target_width <= 0: return 0.0
    d_min, d_max = 0.0, dc * 2.0
    for _ in range(35):
        d_mid = (d_min + d_max) / 2
        w_mid = compute_width_from_depth(d_mid, angle, ri, dc, rc)
        if w_mid < target_width: d_min = d_mid
        else: d_max = d_mid
    return round((d_min + d_max) / 2, 4)

def apply_suggested(b):
    global updating
    updating = True
    try:
        current_type = ui_b_type.value
        if current_type == 'None':
            ui_b_type.value = 'Standard'
            current_type = 'Standard'
           
        ui_b_angle.value = 90.0
        ui_b_Ri.value = 0.061
       
        if current_type == 'Cut Through':
            suggested_depth = round(ui_Dc.value * 0.95, 4)
        else:
            suggested_depth = round(ui_Dc.value * 0.34 - 0.005, 4)
           
        ui_b_depth.value = suggested_depth
        ui_b_width.value = compute_width_from_depth(suggested_depth, 90.0, 0.061, ui_Dc.value, ui_Rc.value)
    finally:
        updating = False
        draw_views()

btn_suggest.on_click(apply_suggested)

# =====================================================================
# 4. ЛОГИКА ВАЛИДАЦИИ
# =====================================================================
updating = False

def on_value_change(change):
    global updating
    if updating: return
    updating = True

    try:
        sender = change['owner']
        ui_D.value = max(0.01, ui_D.value)
        ui_Dc.value = max(0.01, ui_Dc.value)
        ui_Rc.value = max(0.01, ui_Rc.value)
        ui_Land.value = max(0.0, ui_Land.value)
        ui_Hb.value = max(0.0, ui_Hb.value)
        ui_Tt.value = max(0.01, ui_Tt.value)

        ui_b_angle.value = max(1.0, min(179.0, ui_b_angle.value))
        ui_b_depth.value = max(0.0, ui_b_depth.value)
        ui_b_width.value = max(0.0, ui_b_width.value)
        ui_b_Ri.value = max(0.0, ui_b_Ri.value)

        D = ui_D.value
        Land = ui_Land.value
        if Land >= D/2:
            ui_Land.value = 0; Land = 0
        r_c = D/2 - Land

        # Синхронизация геометрии чаши
        if sender in (ui_D, ui_Dc, ui_Land):
            Dc = ui_Dc.value
            ui_Rc.value = round((r_c**2 + Dc**2) / (2 * Dc), 4)
            if sender == ui_Dc: ui_Tt.value = round(ui_Hb.value + 2 * Dc, 4)
        elif sender == ui_Rc:
            Rc = max(ui_Rc.value, r_c + 0.01)
            ui_Rc.value = round(Rc, 4)
            Dc = Rc - np.sqrt(max(0, Rc**2 - r_c**2))
            ui_Dc.value = round(Dc, 4)
            ui_Tt.value = round(ui_Hb.value + 2 * Dc, 4)

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
            calc_depth = compute_depth_from_width(ui_b_width.value, ui_b_angle.value, ui_b_Ri.value, ui_Dc.value, ui_Rc.value)
            if calc_depth > max_b_depth:
                ui_b_depth.value = max_b_depth
                ui_b_width.value = compute_width_from_depth(max_b_depth, ui_b_angle.value, ui_b_Ri.value, ui_Dc.value, ui_Rc.value)
            else:
                ui_b_depth.value = calc_depth
        elif sender in (ui_b_depth, ui_b_angle, ui_b_Ri, ui_b_type, ui_Dc, ui_Rc):
            ui_b_width.value = compute_width_from_depth(ui_b_depth.value, ui_b_angle.value, ui_b_Ri.value, ui_Dc.value, ui_Rc.value)

        draw_views()
    finally:
        updating = False

for widget in (ui_D, ui_Hb, ui_Tt, ui_Dc, ui_Rc, ui_Land, ui_b_type, ui_b_width, ui_b_depth, ui_b_angle, ui_b_Ri):
    widget.observe(on_value_change, names='value')

# =====================================================================
# 5. ИНСТРУМЕНТЫ РИСОВАНИЯ
# =====================================================================
def get_circle_contour(R, density=300):
    t = np.linspace(0, 2*np.pi, density)
    return R * np.cos(t), R * np.sin(t)

def get_round_concave_profile(x_arr, span, Dc, Rc):
    z_prof = np.zeros_like(x_arr)
    if Rc <= 0 or Dc <= 0: return z_prof
    x_abs = np.abs(x_arr)
    mask = x_abs <= span
    z_prof[mask] = np.sqrt(np.maximum(0, Rc**2 - x_abs[mask]**2)) - (Rc - Dc)
    return np.maximum(0, z_prof)

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
        D, Hb, Tt = ui_D.value, ui_Hb.value, ui_Tt.value
        Dc, Rc, Land = ui_Dc.value, ui_Rc.value, ui_Land.value
        b_type, b_depth, b_angle, b_Ri = ui_b_type.value, ui_b_depth.value, ui_b_angle.value, ui_b_Ri.value

        r_c = D/2 - Land

        # Строгие аналитические вычисления для круглой таблетки
        Die_Hole_SA = np.pi * (D / 2)**2
        Perimeter = np.pi * D
        Cup_Volume = (np.pi * Dc / 6) * (3 * r_c**2 + Dc**2) if Dc > 0 else 0
        Cup_SA = 2 * np.pi * Rc * Dc if Dc > 0 else 0
        Land_SA = np.pi * ((D/2)**2 - r_c**2)

        # 3D сетка для визуализации риски
        x_grid, y_grid = np.linspace(-D/2, D/2, 300), np.linspace(-D/2, D/2, 300)
        X, Y = np.meshgrid(x_grid, y_grid)
        dx, dy = x_grid[1] - x_grid[0], y_grid[1] - y_grid[0]
        dA = dx * dy
        rho = np.sqrt(X**2 + Y**2)
        mask_cup = rho <= r_c

        Z = np.zeros_like(X)
        Z[mask_cup] = np.sqrt(np.maximum(0, Rc**2 - rho[mask_cup]**2)) - (Rc - Dc)

        Z_cup_top = Z.copy()
        Z_groove = np.full_like(X, Dc * 5.0)
       
        if b_type != 'None' and b_depth > 0:
            alpha = np.radians(b_angle / 2.0)
            d_sharp = b_Ri / np.sin(alpha) - b_Ri if b_Ri > 0 and alpha > 0 else 0
            x_ti = b_Ri * np.sin(alpha)
           
            # Риска проходит вдоль оси X (горизонтально на виде сверху).
            # Поэтому глубина выреза зависит от радиального профиля по оси X.
            Z_centerline = np.zeros_like(X)
            m_in = np.abs(X) <= r_c
            Z_centerline[m_in] = np.sqrt(np.maximum(0, Rc**2 - X[m_in]**2)) - (Rc - Dc)
            
            if b_type == 'Standard':
                z_bottom = Z_centerline - b_depth
            elif b_type == 'Cut Through':
                z_bottom = np.full_like(X, Dc - b_depth)
            elif b_type == 'Decreasing':
                edge_rad = r_c if r_c > 0 else D/2
                z_bottom = Z_centerline - b_depth * np.maximum(0, 1 - (X / edge_rad)**2)

            # Сечение риски формируется вдоль оси Y
            Y_abs = np.abs(Y)
            Z_v = z_bottom - d_sharp + Y_abs / np.tan(alpha)
            Z_inner = z_bottom + b_Ri - np.sqrt(np.maximum(0, b_Ri**2 - Y_abs**2))
            Z_groove = np.where(Y_abs <= x_ti, Z_inner, Z_v)
            Z_cup_top = np.maximum(0, np.minimum(Z, Z_groove))

        # Пересчет площади и объема с учетом выреза риски (численно)
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
        cx_side, cy_side = -(D/2 + Tt/2 + 15), 0
        cx_front, cy_front = 0, -(D/2 + Tt/2 + 15)

        # --- 1. TOP VIEW (Вид сверху) ---
        x_out, y_out = get_circle_contour(D/2)
        ax.plot(x_out + cx_top, y_out + cy_top, 'k-', linewidth=1.2)
        if Land > 0:
            x_in, y_in = get_circle_contour(r_c)
            ax.plot(x_in + cx_top, y_in + cy_top, 'k-', linewidth=0.6)

        if b_type != 'None' and b_depth > 0:
            Z_diff_masked = np.where(mask_cup, Z - Z_groove, np.nan)
            Z_groove_masked = np.where(mask_cup, Z_groove, np.nan)
            
            ax.contour(X + cx_top, Y + cy_top, Z_diff_masked, levels=[0], colors='k', linewidths=0.8)
            ax.contour(X + cx_top, Y + cy_top, Z_groove_masked, levels=[0], colors='k', linewidths=0.6)
            
            x_ti = b_Ri * np.sin(np.radians(b_angle / 2.0))
            if x_ti > 0.005:
                idx_y = np.argmin(np.abs(y_grid - x_ti))
                cond = (Z - Z_groove)[idx_y, :]
                if b_type == 'Standard': cond = np.minimum(cond, Z_groove[idx_y, :])
                cond = np.where(mask_cup[idx_y, :], cond, -1.0)
                
                valid_indices = np.where(cond >= 0)[0]
                if len(valid_indices) > 0:
                    i_min, i_max = valid_indices[0], valid_indices[-1]
                    x_start, x_end = x_grid[i_min], x_grid[i_max]
                    if i_min > 0:
                        c0, c1 = cond[i_min], cond[i_min-1]
                        if c0 != c1: x_start = x_grid[i_min] - c0 * (x_grid[i_min-1] - x_grid[i_min]) / (c1 - c0)
                    if i_max < len(x_grid) - 1:
                        c0, c1 = cond[i_max], cond[i_max+1]
                        if c0 != c1: x_end = x_grid[i_max] - c0 * (x_grid[i_max+1] - x_grid[i_max]) / (c1 - c0)
                    
                    ax.plot([x_start + cx_top, x_end + cx_top], [x_ti + cy_top, x_ti + cy_top], 'k-', lw=0.6)
                    ax.plot([x_start + cx_top, x_end + cx_top], [-x_ti + cy_top, -x_ti + cy_top], 'k-', lw=0.6)

        # Выноска Diameter слева
        draw_ext(ax, cx_top - D/2, cy_top + D/2, cx_top - D/2, cy_top - D/2, -4.5, 0, f"{D:g}\nDiameter")

        # --- 2. SIDE VIEW (Вертикальный вид слева - показывает сечение риски) ---
        yc_up = Hb/2
        y_cup = np.linspace(-r_c, r_c, 400)
        z_up_surf = yc_up + get_round_concave_profile(y_cup, r_c, Dc, Rc)
       
        if b_type != 'None' and b_depth > 0:
            Y_abs_1d = np.abs(y_cup)
            alpha_1d = np.radians(b_angle / 2.0)
            d_sharp_1d = b_Ri / np.sin(alpha_1d) - b_Ri if b_Ri > 0 else 0
            x_ti_1d = b_Ri * np.sin(alpha_1d)
            z_bottom_1d = Dc - b_depth 
            
            z_v_1d = z_bottom_1d - d_sharp_1d + Y_abs_1d / np.tan(alpha_1d)
            z_inner_1d = z_bottom_1d + b_Ri - np.sqrt(np.maximum(0, b_Ri**2 - Y_abs_1d**2))
            z_g_1d = np.where(Y_abs_1d <= x_ti_1d, z_inner_1d, z_v_1d)
            z_up_surf = np.minimum(z_up_surf, Hb/2 + z_g_1d)

        rad_prof = np.concatenate([[-D/2, -D/2], [-D/2, -r_c], y_cup, [r_c, D/2], [D/2, D/2], [D/2, r_c], y_cup[::-1], [-r_c, -D/2], [-D/2]])
        z_down_surf = yc_up + get_round_concave_profile(y_cup, r_c, Dc, Rc)
        t_prof = np.concatenate([[-Hb/2, Hb/2], [Hb/2, Hb/2], z_up_surf, [Hb/2, Hb/2], [Hb/2, -Hb/2], [-Hb/2, -Hb/2], -z_down_surf[::-1], [-Hb/2, -Hb/2], [-Hb/2]])

        ax.plot(t_prof + cx_side, rad_prof + cy_side, 'k-', linewidth=1.2)
        ax.plot([-Hb/2 + cx_side, -Hb/2 + cx_side], [-D/2 + cy_side, D/2 + cy_side], 'k-', linewidth=1.2)
        ax.plot([Hb/2 + cx_side, Hb/2 + cx_side], [-D/2 + cy_side, D/2 + cy_side], 'k-', linewidth=1.2)

        draw_ext_outside(ax, cx_side + Hb/2, cy_side + D/2, cx_side + Hb/2 + Dc, cy_side + D/2, 0, 4, f"{Dc:g}\nCup Depth")
        draw_ext_outside(ax, cx_side - Hb/2, cy_side - D/2, cx_side + Hb/2, cy_side - D/2, 0, -4, f"{Hb:g}\nBelly Band")

        # --- 3. FRONT VIEW (Горизонтальный вид снизу - показывает дно риски) ---
        xc_up = Hb/2
        x_cup = np.linspace(-r_c, r_c, 200)
        z_up_front = xc_up + get_round_concave_profile(x_cup, r_c, Dc, Rc)

        x_rad_prof = np.concatenate([[-D/2, -D/2], [-D/2, -r_c], x_cup, [r_c, D/2], [D/2, D/2], [D/2, r_c], x_cup[::-1], [-r_c, -D/2], [-D/2]])
        t_front_prof = np.concatenate([[-Hb/2, Hb/2], [Hb/2, Hb/2], z_up_front, [Hb/2, Hb/2], [Hb/2, -Hb/2], [-Hb/2, -Hb/2], -z_up_front[::-1], [-Hb/2, -Hb/2], [-Hb/2]])

        ax.plot(x_rad_prof + cx_front, t_front_prof + cy_front, 'k-', linewidth=1.2)
        ax.plot([-D/2 + cx_front, D/2 + cx_front], [Hb/2 + cy_front, Hb/2 + cy_front], 'k-', linewidth=1.2)
        ax.plot([-D/2 + cx_front, D/2 + cx_front], [-Hb/2 + cy_front, -Hb/2 + cy_front], 'k-', linewidth=1.2)
       
        if b_type != 'None' and b_depth > 0:
            Z_centerline_front = get_round_concave_profile(x_cup, r_c, Dc, Rc)
            if b_type == 'Standard': z_bottom_line = Z_centerline_front - b_depth
            elif b_type == 'Cut Through': z_bottom_line = np.full_like(x_cup, Dc - b_depth)
            elif b_type == 'Decreasing':
                edge_rad = r_c if r_c > 0 else D/2
                z_bottom_line = Z_centerline_front - b_depth * np.maximum(0, 1 - (x_cup / edge_rad)**2)
           
            valid = (z_bottom_line > 0) & ((z_bottom_line + Hb/2) < z_up_front)
            ax.plot(x_cup[valid] + cx_front, z_bottom_line[valid] + Hb/2 + cy_front, 'k--', lw=0.8)

        draw_ext(ax, cx_front - D/2, cy_front - Tt/2, cx_front - D/2, cy_front + Tt/2, -4.5, 0, f"{Tt:g}\nTablet Thickness")
        
        # Выноска Cup Radius (указывает на поверхность чаши)
        draw_pointer(ax, (cx_front, cy_front + Hb/2 + Dc), (cx_front - D/4, cy_front + Hb/2 + Dc + 4), f"{Rc:g}\nCup Radius")

        if Land > 0:
            ax.plot([cx_front + r_c, cx_front + r_c], [cy_front + Tt/2, cy_front + Tt/2 + 2.5], 'k-', lw=DIM_LINE_WIDTH)
            ax.plot([cx_front + D/2, cx_front + D/2], [cy_front + Tt/2, cy_front + Tt/2 + 2.5], 'k-', lw=DIM_LINE_WIDTH)
            ax.annotate('', xy=(cx_front + r_c, cy_front + Tt/2 + 2), xytext=(cx_front + r_c - 2.5, cy_front + Tt/2 + 2), arrowprops=dict(arrowstyle=ARR_STYLE_SINGLE, color='black', lw=DIM_LINE_WIDTH, mutation_scale=ARROW_LENGTH))
            ax.annotate('', xy=(cx_front + D/2, cy_front + Tt/2 + 2), xytext=(cx_front + D/2 + 2.5, cy_front + Tt/2 + 2), arrowprops=dict(arrowstyle=ARR_STYLE_SINGLE, color='black', lw=DIM_LINE_WIDTH, mutation_scale=ARROW_LENGTH))
            ax.text(cx_front + D/2 + 3, cy_front + Tt/2 + 2, f"{Land:g}\nBld. Land", color=C_TEXT, ha='center', va='center', fontsize=9, bbox=dict(facecolor='#f4f4f9', edgecolor='none', pad=0.5))

        x_min_val = cx_side - Tt/2 - 12
        x_max_val = cx_top + D/2 + 15
        y_min_val = cy_front - Tt/2 - 8
        y_max_val = cy_top + D/2 + 8

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
col1 = widgets.VBox([ui_D])
col2 = widgets.VBox([ui_Dc, ui_Rc])
col3 = widgets.VBox([ui_Land, ui_Hb, ui_Tt])
col4 = widgets.VBox([ui_b_type, btn_suggest, ui_b_width, ui_b_depth, ui_b_angle, ui_b_Ri])
input_box = widgets.HBox([col1, col2, col3, col4])

calc_col1 = widgets.VBox([ui_calc_die, ui_calc_cvol, ui_calc_csa])
calc_col2 = widgets.VBox([ui_calc_perim, ui_calc_tsa, ui_calc_tvol])
calc_box = widgets.HBox([calc_col1, calc_col2], layout=widgets.Layout(margin='10px 0 0 0'))

display(input_box)
display(widgets.HTML(value="<b>Approximated Calculations:</b>"))
display(calc_box)
display(out)