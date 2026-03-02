import numpy as np
import plotly.graph_objects as go

# =====================================================================
# 1. ТОЧНЫЕ ПАРАМЕТРЫ ТАБЛЕТКИ (в мм)
# =====================================================================
W = 9.20           # Minor Axis
L = 18.30          # Major Axis
Re = 3.0           # End Radius
Rs = 15.61953      # Side Radius
Dc = 1.18          # Cup Depth
Hb = 2.95          # Belly Band

# =====================================================================
# 2. ПАРАМЕТРЫ РИСКИ (Standard Bisect)
# =====================================================================
b_depth = round(Dc * 0.34 - 0.005, 4) 
b_angle = 90.0     # Угол V-образного выреза
b_Ri = 0.061       # Внутренний радиус скругления на дне риски

# =====================================================================
# 3. РАСЧЕТ БАЗОВОЙ ГЕОМЕТРИИ (4-Arc Oval)
# =====================================================================
xe = L / 2 - Re
ys = W / 2 - Rs

theta_tan_c = np.arctan2(abs(ys), xe)
x_tan = xe + Re * np.cos(theta_tan_c)
y_tan = Re * np.sin(theta_tan_c)
theta_tan = np.arctan2(y_tan, x_tan)

def get_perimeter_radius(theta):
    t = np.abs(theta)
    t = np.where(t > np.pi, 2*np.pi - t, t)
    t = np.where(t > np.pi/2, np.pi - t, t)

    r_max = np.zeros_like(t)
    mask_end = t <= theta_tan
    mask_side = t > theta_tan

    r_max[mask_end] = xe * np.cos(t[mask_end]) + np.sqrt(Re**2 - (xe * np.sin(t[mask_end]))**2)
    ys_center = W / 2 - Rs
    r_max[mask_side] = ys_center * np.sin(t[mask_side]) + np.sqrt(Rs**2 - (ys_center * np.cos(t[mask_side]))**2)
    return r_max

# =====================================================================
# 4. ГЕНЕРАЦИЯ 3D СЕТКИ
# =====================================================================
r = np.linspace(0, 1, 150)
theta = np.linspace(0, 2*np.pi, 360)
R_grid, Theta_grid = np.meshgrid(r, theta)

Rmax_grid = get_perimeter_radius(Theta_grid)
X = R_grid * Rmax_grid * np.cos(Theta_grid)
Y = R_grid * Rmax_grid * np.sin(Theta_grid)

# =====================================================================
# 5. РАСЧЕТ ПОВЕРХНОСТИ ЧАШКИ (Cup Surface)
# =====================================================================
R_local = (Rmax_grid**2 + Dc**2) / (2 * Dc)
rho_grid = R_grid * Rmax_grid
Z_cup = np.sqrt(R_local**2 - rho_grid**2) - (R_local - Dc)

# =====================================================================
# 6. ВЫРЕЗАНИЕ РИСКИ (Верхняя чашка)
# =====================================================================
Rc_min = ((W/2)**2 + Dc**2) / (2 * Dc)
Z_centerline = np.sqrt(np.maximum(0, Rc_min**2 - Y**2)) - (Rc_min - Dc)
z_bottom = Z_centerline - b_depth

alpha = np.radians(b_angle / 2.0)
d_sharp = b_Ri / np.sin(alpha) - b_Ri if b_Ri > 0 else 0
x_ti = b_Ri * np.sin(alpha)

Z_v = z_bottom - d_sharp + np.abs(X) / np.tan(alpha)
Z_inner = z_bottom + b_Ri - np.sqrt(np.maximum(0, b_Ri**2 - np.clip(np.abs(X), 0, b_Ri)**2))

Z_groove = np.where(np.abs(X) <= x_ti, Z_inner, Z_v)

Z_upper_base = Z_cup + (Hb / 2)
# Срез на верхней чашке
Z_upper_cut = np.minimum(Z_upper_base, Z_groove + (Hb / 2))
Z_lower = -Z_cup - (Hb / 2)

# =====================================================================
# 7. ГЕНЕРАЦИЯ И ВЫРЕЗАНИЕ БОКОВОГО ПОЯСКА (Belly Band)
# =====================================================================
z_steps = np.linspace(-Hb/2, Hb/2, 10)
Theta_band, Z_band = np.meshgrid(theta, z_steps)
Rmax_band = get_perimeter_radius(Theta_band)

X_band = Rmax_band * np.cos(Theta_band)
Y_band = Rmax_band * np.sin(Theta_band)

# Рассчитываем профиль риски строго для координат бокового пояска
Z_centerline_band = np.sqrt(np.maximum(0, Rc_min**2 - Y_band**2)) - (Rc_min - Dc)
z_bottom_band = Z_centerline_band - b_depth

Z_v_band = z_bottom_band - d_sharp + np.abs(X_band) / np.tan(alpha)
Z_inner_band = z_bottom_band + b_Ri - np.sqrt(np.maximum(0, b_Ri**2 - np.clip(np.abs(X_band), 0, b_Ri)**2))
Z_groove_band = np.where(np.abs(X_band) <= x_ti, Z_inner_band, Z_v_band)

# КЛЮЧЕВОЙ ФИКС: Отрезаем нетронутую боковую стенку, чтобы закрыть дыру
Z_band = np.minimum(Z_band, Z_groove_band + (Hb / 2))

# =====================================================================
# 8. ОТРИСОВКА В PLOTLY
# =====================================================================
colorscale = [[0, '#e3f2fd'], [1, '#1565c0']]

fig = go.Figure()

# Верхняя чашка (с вырезом)
fig.add_trace(go.Surface(x=X, y=Y, z=Z_upper_cut, colorscale=colorscale, showscale=False))
# Нижняя чашка
fig.add_trace(go.Surface(x=X, y=Y, z=Z_lower, colorscale=colorscale, showscale=False))
# Боковой поясок (теперь с вырезанной засечкой)
fig.add_trace(go.Surface(x=X_band, y=Y_band, z=Z_band, colorscale=colorscale, showscale=False))

fig.update_layout(
    title=f'Таблетка 3D с риской (Gl. Depth: {b_depth:.4f}mm) - Исправлено',
    scene=dict(
        xaxis=dict(title='X (мм)', range=[-10, 10]),
        yaxis=dict(title='Y (мм)', range=[-10, 10]),
        zaxis=dict(title='Z (мм)', range=[-6, 6]),
        aspectmode='manual',
        aspectratio=dict(x=1, y=1, z=0.6)
    ),
    margin=dict(l=0, r=0, b=0, t=40)
)

fig.show()