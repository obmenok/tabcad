import numpy as np
import plotly.graph_objects as go

from core.domain.shapes import shape_params


def _get_circle_contour(radius, density=220):
    t = np.linspace(0, 2 * np.pi, density)
    return radius * np.cos(t), radius * np.sin(t)


def _get_capsule_contour(l_val, w_val, density=150):
    r = w_val / 2
    l_flat = max(0, l_val - w_val)
    
    # 1. Правая дуга
    t_right = np.linspace(0, np.pi, density)
    x_right = l_flat / 2 + r * np.sin(t_right)
    y_right = r * np.cos(t_right)
    
    # 2. Нижняя прямая (плоская грань)
    x_bottom = np.linspace(l_flat / 2, -l_flat / 2, density)
    y_bottom = np.full_like(x_bottom, -r)
    
    # 3. Левая дуга
    t_left = np.linspace(np.pi, 2 * np.pi, density)
    x_left = -l_flat / 2 + r * np.sin(t_left)
    y_left = r * np.cos(t_left)
    
    # 4. Верхняя прямая (плоская грань)
    x_top = np.linspace(-l_flat / 2, l_flat / 2, density)
    y_top = np.full_like(x_top, r)
    
    x = np.concatenate([x_right, x_bottom, x_left, x_top])
    y = np.concatenate([y_right, y_bottom, y_left, y_top])
    return x, y


def _get_oval_contour(l_val, w_val, re, rs, density=120):
    xe = l_val / 2 - re
    ys = w_val / 2 - rs
    gamma = np.arctan2(abs(ys), max(1e-6, xe))
    t1 = np.linspace(-gamma, gamma, density)
    t2 = np.linspace(gamma, np.pi - gamma, density)
    t3 = np.linspace(np.pi - gamma, np.pi + gamma, density)
    t4 = np.linspace(np.pi + gamma, 2 * np.pi - gamma, density)
    c1_x, c1_y = xe + re * np.cos(t1), re * np.sin(t1)
    c2_x, c2_y = rs * np.cos(t2), ys + rs * np.sin(t2)
    c3_x, c3_y = -xe + re * np.cos(t3), re * np.sin(t3)
    c4_x, c4_y = rs * np.cos(t4), -ys + rs * np.sin(t4)
    x = np.concatenate([c1_x, c2_x, c3_x, c4_x, [c1_x[0]]])
    y = np.concatenate([c1_y, c2_y, c3_y, c4_y, [c1_y[0]]])
    return x, y


def _shape_contour(params):
    shape, is_modified, w_val, l_val, _, re, rs = shape_params(params)
    if shape == "round":
        return _get_circle_contour(w_val / 2)
    if shape == "capsule" and not is_modified:
        return _get_capsule_contour(l_val, w_val)
    return _get_oval_contour(l_val, w_val, re, rs)


def _boundary_radius_from_contour(x_c, y_c, theta_query):
    theta_c = np.mod(np.arctan2(y_c, x_c), 2 * np.pi)
    r_c = np.hypot(x_c, y_c)
    order = np.argsort(theta_c)
    theta_s = theta_c[order]
    r_s = r_c[order]

    theta_u, idx = np.unique(theta_s, return_index=True)
    r_u = r_s[idx]

    theta_ext = np.concatenate(([theta_u[-1] - 2 * np.pi], theta_u, [theta_u[0] + 2 * np.pi]))
    r_ext = np.concatenate(([r_u[-1]], r_u, [r_u[0]]))
    return np.interp(theta_query, theta_ext, r_ext)


def _interp_bilinear(z_arr, x_grid, y_grid, xq, yq):
    ix = np.searchsorted(x_grid, xq) - 1
    iy = np.searchsorted(y_grid, yq) - 1
    ix = np.clip(ix, 0, len(x_grid) - 2)
    iy = np.clip(iy, 0, len(y_grid) - 2)

    x1 = x_grid[ix]
    x2 = x_grid[ix + 1]
    y1 = y_grid[iy]
    y2 = y_grid[iy + 1]

    tx = np.where(np.abs(x2 - x1) > 1e-12, (xq - x1) / (x2 - x1), 0.0)
    ty = np.where(np.abs(y2 - y1) > 1e-12, (yq - y1) / (y2 - y1), 0.0)

    z11 = z_arr[iy, ix]
    z12 = z_arr[iy + 1, ix]
    z21 = z_arr[iy, ix + 1]
    z22 = z_arr[iy + 1, ix + 1]

    return (
        (1 - tx) * (1 - ty) * z11
        + tx * (1 - ty) * z21
        + (1 - tx) * ty * z12
        + tx * ty * z22
    )


def render_tablet_3d(mesh_data, params):
    hb = max(0.0, params.get("Hb", 2.54))
    x_grid = mesh_data["x_grid"]
    y_grid = mesh_data["y_grid"]
    z_top_grid = mesh_data["Z_cup_top"]
    z_bot_grid = mesh_data["Z"]

    theta = np.linspace(0, 2 * np.pi, 320)
    rr = np.linspace(0, 1, 160)
    rr_grid, tt_grid = np.meshgrid(rr, theta, indexing="ij")

    x_c, y_c = _shape_contour(params)
    r_boundary = _boundary_radius_from_contour(x_c, y_c, theta)
    r_grid = rr_grid * r_boundary[None, :]
    x_s = r_grid * np.cos(tt_grid)
    y_s = r_grid * np.sin(tt_grid)

    z_top_interp = _interp_bilinear(z_top_grid, x_grid, y_grid, x_s, y_s)
    z_bot_interp = _interp_bilinear(z_bot_grid, x_grid, y_grid, x_s, y_s)
    zt_s = z_top_interp + hb / 2
    zb_s = -z_bot_interp - hb / 2

    z_line = np.linspace(-hb / 2, hb / 2, 32)
    xb = np.tile(r_boundary * np.cos(theta), (len(z_line), 1))
    yb = np.tile(r_boundary * np.sin(theta), (len(z_line), 1))
    zb = np.tile(z_line[:, None], (1, len(theta)))

    # --- РАЗДЕЛЬНАЯ НАСТРОЙКА СВЕТА ---
    
    # 1. Для лицевой части (Верхняя чаша) оставляем тени контрастными
    lighting_top = dict(
        ambient=0.1,
        diffuse=0.2,
        specular=0.15,
        roughness=0.7,
        fresnel=0.1
    )
    
    # 2. Для борта и дна принудительно задираем базовую освещенность (ambient), 
    # чтобы они не проваливались в темноту, когда отвернуты от камеры
    lighting_sides_bottom = dict(
        ambient=0.8,     # Делаем "теневые" участки светлее
        diffuse=0.5,     # Чуть меньше реагируют на прямые лучи
        specular=0.1,    # Почти без бликов
        roughness=0.8,
        fresnel=0.2
    )
    
    # === НАСТРОЙКИ МАТЕРИАЛА ===
    # Базовый цвет делаем достаточно темным (матовый серый металл/пластик),
    # чтобы бликам от света было на чем контрастно выделяться
    cad_colorscale = [[0, "#db7b3b"], [1, "#db7b3b"]] 

    # Вектор света: бьет из левого верхнего угла вашего монитора
    # Чуть-чуть направлен вглубь экрана (z=0.2)
    vector_light = dict(x=-1, y=1, z=0.2)

    # 1. Свет для Лицевой чаши (Top)
    # Делаем контрастные тени, чтобы риска (Bisect) читалась идеально
    lighting_top = dict(
        ambient=0.4,     # Базовая освещенность (не слишком высоко, чтобы были тени)
        diffuse=0.8,     # Резкость теней от углублений
        specular=0.3,    # Умеренный матовый блик (без пересвета)
        roughness=0.6,   # Шероховатость прессованной таблетки
        fresnel=0.1      # Подсветка контуров
    )
    
    # 2. Свет для Дна и Борта (Bottom & Band)
    # Выкручиваем ambient, чтобы они не проваливались во мрак,
    # когда отвернуты от нашего левого-верхнего "прожектора"
    lighting_bot = dict(
        ambient=0.7,     # Делаем теневую сторону искусственно светлее
        diffuse=0.4,
        specular=0.1,
        roughness=0.8,
        fresnel=0.2
    )

    fig = go.Figure()
    fig.add_trace(
        go.Surface(
            x=x_s, y=y_s, z=zt_s,
            colorscale=cad_colorscale, showscale=False, hoverinfo="skip", name="Top",
            lighting=lighting_top, lightposition=vector_light # <--- ПРИМЕНЯЕМ ВЕКТОР
        )
    )
    fig.add_trace(
        go.Surface(
            x=x_s, y=y_s, z=zb_s,
            colorscale=cad_colorscale, showscale=False, hoverinfo="skip", name="Bottom",
            lighting=lighting_bot, lightposition=vector_light # <--- ПРИМЕНЯЕМ ВЕКТОР
        )
    )
    fig.add_trace(
        go.Surface(
            x=xb, y=yb, z=zb,
            colorscale=cad_colorscale, showscale=False, hoverinfo="skip", name="Band",
            lighting=lighting_bot, lightposition=vector_light # <--- ПРИМЕНЯЕМ ВЕКТОР
        )
    )

    shape, _, w_val, l_val, _, _, _ = shape_params(params)
    
    if shape == "round":
        r_lim = max(w_val, l_val) / 2 + 1.0
        z_lim = hb / 2 + max(float(np.nanmax(z_top_grid)), float(np.nanmax(z_bot_grid))) + 1.0
        scene_config = dict(
            xaxis=dict(title="X (mm)", range=[-r_lim, r_lim], showbackground=False),
            yaxis=dict(title="Y (mm)", range=[-r_lim, r_lim], showbackground=False),
            zaxis=dict(title="Z (mm)", range=[-z_lim, z_lim], showbackground=False),
            aspectmode="manual",
            aspectratio=dict(x=1, y=1, z=0.55),
            camera=dict(eye=dict(x=1.6, y=1.4, z=0.9)),
        )
    else:
        scene_config = dict(
            xaxis=dict(title="X (mm)", showbackground=False),
            yaxis=dict(title="Y (mm)", showbackground=False),
            zaxis=dict(title="Z (mm)", showbackground=False),
            aspectmode="data",
            camera=dict(eye=dict(x=1.6, y=1.4, z=0.9)),
        )

    fig.update_layout(
        margin=dict(l=0, r=0, b=0, t=10),
        scene=scene_config,
        paper_bgcolor="white",
        plot_bgcolor="white",
        showlegend=False,
    )
    return fig