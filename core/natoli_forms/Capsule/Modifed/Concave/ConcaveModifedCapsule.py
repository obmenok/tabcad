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

# Входные параметры (Modified Capsule Concave)
ui_W = widgets.FloatText(value=9.2, step=0.01, description='Minor Axis:', style=style, layout=layout)
ui_L = widgets.FloatText(value=18.3, step=0.01, description='Major Axis:', style=style, layout=layout)

# В Модифицированной капсуле радиусы разблокированы
ui_Re = widgets.FloatText(value=4.448, step=0.01, description='End Radius:', style=style, layout=layout)
ui_Rs = widgets.FloatText(value=77.2503, step=0.01, description='Side Radius:', style=style, layout=layout)

ui_Dc = widgets.FloatText(value=1.47, step=0.01, description='Cup Depth:', style=style, layout=layout)
ui_Rc = widgets.FloatText(value=7.6841, description='Cup Radius Minor:', disabled=True, style=style, layout=layout)

ui_Land = widgets.FloatText(value=0.08, step=0.01, description='Land:', style=style, layout=layout)
ui_Hb = widgets.FloatText(value=2.54, step=0.01, description='Belly Band:', style=style, layout=layout)
ui_Tt = widgets.FloatText(value=5.48, step=0.01, description='Tablet Thick:', style=style, layout=layout)

# Входные параметры (Риска) - Все 4 типа
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
# 3. МАТЕМАТИКА 3D СВОДА КАПСУЛЫ И РИСКИ
# =====================================================================
def get_capsule_concave_profile(rho_arr, Rc, Dc):
    """Возвращает профиль сферического купола по заданному радиусу rho от хребта капсулы"""
    z_prof = np.zeros_like(rho_arr)
    if Rc <= 0 or Dc <= 0: return z_prof
    mask = rho_arr <= np.sqrt(max(0, Rc**2 - (Rc - Dc)**2))
    z_prof[mask] = np.sqrt(np.maximum(0, Rc**2 - rho_arr[mask]**2)) - (Rc - Dc)
    return np.maximum(0, z_prof)

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
        ui_W.value = max(0.01, ui_W.value)
        ui_L.value = max(0.01, ui_L.value)
        if ui_W.value > ui_L.value: ui_W.value = ui_L.value

        ui_Re.value = max(0.01, ui_Re.value)
        ui_Rs.value = max(0.01, ui_Rs.value)
        ui_Dc.value = max(0.01, ui_Dc.value)
        ui_Land.value = max(0.0, ui_Land.value)
        ui_Hb.value = max(0.0, ui_Hb.value)
        ui_Tt.value = max(0.01, ui_Tt.value)
        
        ui_b_angle.value = max(1.0, min(179.0, ui_b_angle.value))
        ui_b_depth.value = max(0.0, ui_b_depth.value)
        ui_b_width.value = max(0.0, ui_b_width.value)
        ui_b_Ri.value = max(0.0, ui_b_Ri.value)

        W = ui_W.value
        L = ui_L.value
        Land = ui_Land.value
        Dc = ui_Dc.value
        Re = ui_Re.value
        
        if Land >= Re or Land >= W/2:
            ui_Land.value = 0; Land = 0
            
        r_c = W/2 - Land

        # Строгая геометрия сопряжения дуг Овала (Modified Capsule 2D)
        if sender in (ui_W, ui_L, ui_Re):
            if 2 * ui_Re.value >= W: ui_Re.value = round(W/2 - 0.01, 4)
            Re = ui_Re.value
            ui_Rs.value = round(((L/2 - Re)**2 + (W/2)**2 - Re**2) / (W - 2 * Re), 4)
        elif sender == ui_Rs:
            denom = 2 * ui_Rs.value - L
            new_Re = (ui_Rs.value * W - (W/2)**2 - (L/2)**2) / denom if denom > 0 else -1
            if new_Re <= 0:
                ui_Re.value = 0.01
                ui_Rs.value = round(((L/2 - 0.01)**2 + (W/2)**2 - 0.01**2) / (W - 2 * 0.01), 4)
            else: ui_Re.value = round(new_Re, 4)

        # Синхронизация эквивалентного сферического радиуса (на основе малой оси W)
        if sender in (ui_W, ui_L, ui_Dc, ui_Land, ui_Re, ui_Rs):
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
            calc_depth = compute_depth_from_width(ui_b_width.value, ui_b_angle.value, ui_b_Ri.value, ui_Dc.value, ui_Rc.value)
            if calc_depth > max_b_depth:
                ui_b_depth.value = max_b_depth
                ui_b_width.value = compute_width_from_depth(max_b_depth, ui_b_angle.value, ui_b_Ri.value, ui_Dc.value, ui_Rc.value)
            else:
                ui_b_depth.value = calc_depth
        elif sender in (ui_b_depth, ui_b_angle, ui_b_Ri, ui_b_type, ui_Dc, ui_W, ui_L, ui_Land):
            ui_b_width.value = compute_width_from_depth(ui_b_depth.value, ui_b_angle.value, ui_b_Ri.value, ui_Dc.value, ui_Rc.value)

        draw_views()
    finally:
        updating = False

for widget in (ui_W, ui_L, ui_Re, ui_Rs, ui_Hb, ui_Tt, ui_Dc, ui_Land, ui_b_type, ui_b_width, ui_b_depth, ui_b_angle, ui_b_Ri):
    widget.observe(on_value_change, names='value')

# =====================================================================
# 5. ИНСТРУМЕНТЫ РИСОВАНИЯ ОВАЛА В 2D
# =====================================================================
def get_oval_contour(L, W, Re, Rs):
    xe, ys = L/2 - Re, W/2 - Rs
    gamma = np.arctan2(abs(ys), xe)
    t1 = np.linspace(-gamma, gamma, 50)
    t2 = np.linspace(gamma, np.pi-gamma, 50)
    t3 = np.linspace(np.pi-gamma, np.pi+gamma, 50)
    t4 = np.linspace(np.pi+gamma, 2*np.pi-gamma, 50)
    c1_x, c1_y = xe + Re*np.cos(t1), Re*np.sin(t1)
    c2_x, c2_y = Rs*np.cos(t2), ys + Rs*np.sin(t2)
    c3_x, c3_y = -xe + Re*np.cos(t3), Re*np.sin(t3)
    c4_x, c4_y = Rs*np.cos(t4), -ys + Rs*np.sin(t4)
    return np.concatenate([c1_x, c2_x, c3_x, c4_x, [c1_x[0]]]), np.concatenate([c1_y, c2_y, c3_y, c4_y, [c1_y[0]]])

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
        Re, Rs, Land = ui_Re.value, ui_Rs.value, ui_Land.value
        Dc, Rc = ui_Dc.value, ui_Rc.value
        b_type, b_depth, b_angle, b_Ri = ui_b_type.value, ui_b_depth.value, ui_b_angle.value, ui_b_Ri.value

        if W >= L or 2 * Re >= W or 2 * Rs <= L: return

        # Вычисление площади для Овала (Модифицированной капсулы)
        xe, ys = L / 2 - Re, W / 2 - Rs
        gamma = np.arctan2(abs(ys), xe)
        Perimeter = 4 * gamma * Re + 2 * (np.pi - 2 * gamma) * Rs
        x_tan = xe + Re * np.cos(gamma)

        def arc_area(x, R, cy): return cy * x + 0.5 * x * np.sqrt(max(0, R**2 - x**2)) + 0.5 * R**2 * np.arcsin(x/R)
        def end_arc_area(u, R): return 0.5 * u * np.sqrt(max(0, R**2 - u**2)) + 0.5 * R**2 * np.arcsin(u/R)
        Die_Hole_SA = 4 * ((arc_area(x_tan, Rs, ys) - arc_area(0, Rs, ys)) + (end_arc_area(Re, Re) - end_arc_area(x_tan - xe, Re)))

        # Для 3D-свода: Капсульный хребет (ровный участок по длине L - W)
        l_flat = max(0, L - W)
        r_c = W/2 - Land

        x_grid, y_grid = np.linspace(-L/2, L/2, 300), np.linspace(-W/2, W/2, 300)
        X, Y = np.meshgrid(x_grid, y_grid)
        dx, dy = x_grid[1] - x_grid[0], y_grid[1] - y_grid[0]
        dA = dx * dy

        # 2D Контур: обрезаем 3D-массив Овалом
        theta_grid = np.arctan2(np.abs(Y), np.abs(X))
        r_max = np.zeros_like(theta_grid)
        
        # Вычисляем полярный угол точки сопряжения (от центра координат), 
        # а не угол нормали (gamma)
        theta_t = np.arctan2(Re * np.sin(gamma), xe + Re * np.cos(gamma))
        
        mask_end = theta_grid <= theta_t
        mask_side = theta_grid > theta_t
        
        r_max[mask_end] = xe * np.cos(theta_grid[mask_end]) + np.sqrt(np.maximum(0, Re**2 - (xe * np.sin(theta_grid[mask_end]))**2))
        r_max[mask_side] = ys * np.sin(theta_grid[mask_side]) + np.sqrt(np.maximum(0, Rs**2 - (ys * np.cos(theta_grid[mask_side]))**2))
        r_max_land = np.maximum(0.001, r_max - Land)
        
        rho_2d = np.sqrt(X**2 + Y**2)
        mask_cup = rho_2d <= r_max_land

        # 3D Контур: Вытянутый капсульный свод (Гарантирует прямое ребро на Side View)
        rho_3d = np.zeros_like(X)
        mask_center = np.abs(X) <= l_flat/2
        mask_top = X > l_flat/2
        mask_bot = X < -l_flat/2
        
        rho_3d[mask_center] = np.abs(Y[mask_center])
        rho_3d[mask_top] = np.sqrt((X[mask_top] - l_flat/2)**2 + Y[mask_top]**2)
        rho_3d[mask_bot] = np.sqrt((X[mask_bot] + l_flat/2)**2 + Y[mask_bot]**2)

        Z = np.zeros_like(X)
        Z[mask_cup] = get_capsule_concave_profile(rho_3d[mask_cup], Rc, Dc)

        Z_cup_top = Z.copy()
        Z_groove = np.full_like(X, Dc * 5.0)
       
        if b_type != 'None' and b_depth > 0:
            alpha = np.radians(b_angle / 2.0)
            d_sharp = b_Ri / np.sin(alpha) - b_Ri if b_Ri > 0 and alpha > 0 else 0
            x_ti = b_Ri * np.sin(alpha)
           
            Z_centerline = np.zeros_like(X)
            m_in = np.abs(X) <= r_c 
            Z_centerline[m_in] = get_capsule_concave_profile(np.abs(Y[m_in]), Rc, Dc)
            
            if b_type == 'Standard':
                z_bottom = Z_centerline - b_depth
            elif b_type == 'Cut Through':
                z_bottom = np.full_like(X, Dc - b_depth)
            elif b_type == 'Decreasing':
                edge_rad = r_c if r_c > 0 else W/2
                z_bottom = Z_centerline - b_depth * np.maximum(0, 1 - (np.abs(Y) / edge_rad)**2)

            X_abs = np.abs(X)
            Z_v = z_bottom - d_sharp + X_abs / np.tan(alpha)
            Z_inner = z_bottom + b_Ri - np.sqrt(np.maximum(0, b_Ri**2 - X_abs**2))
            Z_groove = np.where(X_abs <= x_ti, Z_inner, Z_v)
            Z_cup_top = np.maximum(0, np.minimum(Z, Z_groove))

        # Численное интегрирование и исправление ошибки NameError (Land_SA)
        Cup_Volume_Final = np.sum(Z_cup_top) * dA
        dZdx, dZdy = np.gradient(Z_cup_top, dx, axis=1), np.gradient(Z_cup_top, dy, axis=0)
        Cup_SA_Final = np.sum(np.sqrt(1 + dZdx**2 + dZdy**2)[mask_cup]) * dA

        Land_SA = max(0, Die_Hole_SA - np.sum(mask_cup) * dA)

        ui_calc_die.value = round(Die_Hole_SA, 4)
        ui_calc_cvol.value = round(Cup_Volume_Final, 4)
        ui_calc_csa.value = round(Cup_SA_Final + Land_SA, 4)
        ui_calc_perim.value = round(Perimeter, 4)
        ui_calc_tsa.value = round(Perimeter * Hb + 2 * (Cup_SA_Final + Land_SA), 4)
        ui_calc_tvol.value = round(Die_Hole_SA * Hb + 2 * Cup_Volume_Final, 4)

        # -----------------------------------------------------------
        # ОТРИСОВКА ВИДОВ
        # -----------------------------------------------------------
        fig, ax = plt.subplots(figsize=(11, 11))
        fig.patch.set_facecolor('#f4f4f9')
        ax.set_aspect('equal')
        ax.axis('off')

        cx_top, cy_top = 0, 0
        cx_side, cy_side = -(W/2 + Tt/2 + 15), 0
        cx_front, cy_front = 0, -(L/2 + Tt/2 + 15)

        # --- 1. TOP VIEW (Вид сверху: Овал) ---
        x_out, y_out = get_oval_contour(L, W, Re, Rs)
        # Отрисовка: y_out горизонтально (ширина), x_out вертикально (длина)
        ax.plot(y_out + cx_top, x_out + cy_top, 'k-', linewidth=1.2)
        if Land > 0:
            x_in, y_in = get_oval_contour(L - 2*Land, W - 2*Land, Re - Land, Rs - Land)
            ax.plot(y_in + cx_top, x_in + cy_top, 'k-', linewidth=0.6)

        if b_type != 'None' and b_depth > 0:
            Z_diff_masked = np.where(mask_cup, Z - Z_groove, np.nan)
            Z_groove_masked = np.where(mask_cup, Z_groove, np.nan)
            
            ax.contour(Y + cx_top, X + cy_top, Z_diff_masked, levels=[0], colors='k', linewidths=0.8)
            ax.contour(Y + cx_top, X + cy_top, Z_groove_masked, levels=[0], colors='k', linewidths=0.6)
            
            x_ti_val = b_Ri * np.sin(np.radians(b_angle / 2.0))
            if x_ti_val > 0.005:
                idx_x = np.argmin(np.abs(x_grid - x_ti_val))
                cond = (Z - Z_groove)[:, idx_x]
                if b_type in ['Standard', 'Decreasing']: cond = np.minimum(cond, Z_groove[:, idx_x])
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
        
        # Выноски радиусов на Top View
        draw_pointer(ax, (cx_top + W/2, cy_top), (cx_top + W/2 + 5, cy_top - L/4), f"{Rs:g}\nSide Radius")
        pt_x = Re * np.sin(np.pi/4)
        pt_y = -(L/2 - Re) - Re * np.cos(np.pi/4)
        draw_pointer(ax, (cx_top + pt_x, cy_top + pt_y), (cx_top + pt_x + 4, cy_top + pt_y - 4), f"{Re:g}\nEnd Radius")

        # --- 2. SIDE VIEW (Разрез вдоль длины L - С ИДЕАЛЬНЫМ ПРЯМЫМ РЕБРОМ) ---
        yc_up_maj = Hb/2
        l_c = L/2 - Land
        x_maj_cup = np.linspace(-l_c, l_c, 400)
        
        rho_maj = np.maximum(0, np.abs(x_maj_cup) - l_flat/2)
        z_up_maj_surf = get_capsule_concave_profile(rho_maj, Rc, Dc) + yc_up_maj
       
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

        l_prof = np.concatenate([[-L/2, -L/2], [-L/2, -l_c], x_maj_cup, [l_c, L/2], [L/2, L/2], [L/2, l_c], x_maj_cup[::-1], [-l_c, -L/2], [-L/2]])
        
        z_down_maj_surf = get_capsule_concave_profile(rho_maj, Rc, Dc) + yc_up_maj

        t_prof = np.concatenate([[-Hb/2, Hb/2], [Hb/2, Hb/2], z_up_maj_surf, [Hb/2, Hb/2], [Hb/2, -Hb/2], [-Hb/2, -Hb/2], -z_down_maj_surf[::-1], [-Hb/2, -Hb/2], [-Hb/2]])

        ax.plot(t_prof + cx_side, l_prof + cy_side, 'k-', linewidth=1.2)
        ax.plot([-Hb/2 + cx_side, -Hb/2 + cx_side], [-L/2 + cy_side, L/2 + cy_side], 'k-', linewidth=1.2)
        ax.plot([Hb/2 + cx_side, Hb/2 + cx_side], [-L/2 + cy_side, L/2 + cy_side], 'k-', linewidth=1.2)

        draw_ext_outside(ax, cx_side + Hb/2, cy_side + L/2, cx_side + Hb/2 + Dc, cy_side + L/2, 0, 4, f"{Dc:g}\nCup Depth")
        draw_ext_outside(ax, cx_side - Hb/2, cy_side - L/2, cx_side + Hb/2, cy_side - L/2, 0, -4, f"{Hb:g}\nBelly Band")

        if l_flat > 0:
            draw_ext(ax, cx_side + Hb/2 + Dc, cy_side + l_flat/2, cx_side + Hb/2 + Dc, cy_side - l_flat/2, 4.5, 0, f"{l_flat:g}\nRef. Flat")

        # --- 3. FRONT VIEW (Разрез поперек ширины W) ---
        yc_up_min = Hb/2
        y_min_cup = np.linspace(-r_c, r_c, 200)
        
        z_up_min = yc_up_min + get_capsule_concave_profile(np.abs(y_min_cup), Rc, Dc)

        w_prof = np.concatenate([[-W/2, -W/2], [-W/2, -r_c], y_min_cup, [r_c, W/2], [W/2, W/2], [W/2, r_c], y_min_cup[::-1], [-r_c, -W/2], [-W/2]])
        th_prof = np.concatenate([[-Hb/2, Hb/2], [Hb/2, Hb/2], z_up_min, [Hb/2, Hb/2], [Hb/2, -Hb/2], [-Hb/2, -Hb/2], -z_up_min[::-1], [-Hb/2, -Hb/2], [-Hb/2]])

        ax.plot(w_prof + cx_front, th_prof + cy_front, 'k-', linewidth=1.2)
        ax.plot([-W/2 + cx_front, W/2 + cx_front], [Hb/2 + cy_front, Hb/2 + cy_front], 'k-', linewidth=1.2)
        ax.plot([-W/2 + cx_front, W/2 + cx_front], [-Hb/2 + cy_front, -Hb/2 + cy_front], 'k-', linewidth=1.2)
       
        # Если есть риска, на фронтальном виде мы видим дно риски
        if b_type != 'None' and b_depth > 0:
            Z_centerline_front = get_capsule_concave_profile(np.abs(y_min_cup), Rc, Dc)
            
            if b_type == 'Standard': z_bottom_line = Z_centerline_front - b_depth
            elif b_type == 'Cut Through': z_bottom_line = np.full_like(y_min_cup, Dc - b_depth)
            elif b_type == 'Decreasing':
                edge_rad = r_c if r_c > 0 else W/2
                z_bottom_line = Z_centerline_front - b_depth * np.maximum(0, 1 - (np.abs(y_min_cup) / edge_rad)**2)
           
            valid = (z_bottom_line > 0) & ((z_bottom_line + Hb/2) < z_up_min)
            ax.plot(y_min_cup[valid] + cx_front, z_bottom_line[valid] + Hb/2 + cy_front, 'k--', lw=0.8)

        draw_ext(ax, cx_front - W/2, cy_front - Tt/2, cx_front - W/2, cy_front + Tt/2, -4.5, 0, f"{Tt:g}\nTablet Thickness")
        
        # Выноска Cup Radius Minor
        draw_pointer(ax, (cx_front, cy_front + Hb/2 + Dc), (cx_front - W/4, cy_front + Hb/2 + Dc + 4), f"{Rc:g}\nCup Radius\nMinor")

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
col4 = widgets.VBox([ui_Land, ui_Hb, ui_Tt])
col5 = widgets.VBox([ui_b_type, btn_suggest, ui_b_width, ui_b_depth, ui_b_angle, ui_b_Ri])
input_box = widgets.HBox([col1, col2, col3, col4, col5])

calc_col1 = widgets.VBox([ui_calc_die, ui_calc_cvol, ui_calc_csa])
calc_col2 = widgets.VBox([ui_calc_perim, ui_calc_tsa, ui_calc_tvol])
calc_box = widgets.HBox([calc_col1, calc_col2], layout=widgets.Layout(margin='10px 0 0 0'))

display(input_box)
display(widgets.HTML(value="<b>Approximated Calculations:</b>"))
display(calc_box)
display(out)