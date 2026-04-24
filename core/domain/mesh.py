import numpy as np

from core.domain.profiles import eval_profile_1d
from core.domain.shapes import capsule_rho, minor_span, oval_mask, oval_metrics, shape_params


def _require_params(params, keys):
    missing = [k for k in keys if k not in params or params[k] is None]
    if missing:
        raise ValueError(f"Отсутствует параметр(ы): {', '.join(missing)}")


def build_surface(params, x_grid, y_grid):
    _require_params(
        params,
        [
            "shape",
            "profile",
            "is_modified",
            "W",
            "L",
            "Re",
            "Rs",
            "Land",
            "Dc",
            "R_min_maj",
            "R_min_min",
        ],
    )
    shape, is_modified, w_val, l_val, land, re, rs = shape_params(params)
    dc = max(0.0, params["Dc"])
    x_arr, y_arr = np.meshgrid(x_grid, y_grid)

    # === КРУГ ===
    if shape == "round":
        rc = max(0.001, w_val / 2 - land)
        rho = np.sqrt(x_arr**2 + y_arr**2)
        mask_cup = rho <= rc
        z = np.zeros_like(x_arr)
        z[mask_cup] = eval_profile_1d(rho[mask_cup], params, rc, dc)
        perimeter = np.pi * w_val
        die_hole_sa = np.pi * (w_val / 2) ** 2
        return x_arr, y_arr, z, rho, mask_cup, perimeter, die_hole_sa

    # === СТАНДАРТНАЯ КАПСУЛА ===
    if shape == "capsule" and not is_modified:
        l_flat = max(0.0, l_val - w_val)
        rc = max(0.001, w_val / 2 - land)
        rho = capsule_rho(x_arr, y_arr, l_flat)
        mask_cup = rho <= rc
        z = np.zeros_like(x_arr)
        z[mask_cup] = eval_profile_1d(rho[mask_cup], params, rc, dc)
        perimeter = np.pi * w_val + 2 * l_flat
        die_hole_sa = np.pi * (w_val / 2) ** 2 + w_val * l_flat
        return x_arr, y_arr, z, rho, mask_cup, perimeter, die_hole_sa

    # === МОДИФИЦИРОВАННАЯ КАПСУЛА ===
    if shape == "capsule" and is_modified:
        l_flat = max(0.0, l_val - w_val)
        rc = max(0.001, w_val / 2 - land)
        base_mask = oval_mask(x_arr, y_arr, l_val, w_val, re, rs)
        if land > 0 and re > land + 1e-3 and rs > land + 1e-3:
            mask_cup = oval_mask(x_arr, y_arr, l_val - 2 * land, w_val - 2 * land, re - land, rs - land)
        else:
            mask_cup = base_mask

        rho = capsule_rho(x_arr, y_arr, l_flat)
        z = np.zeros_like(x_arr)
        z[mask_cup] = eval_profile_1d(rho[mask_cup], params, rc, dc)
        perimeter, die_hole_sa = oval_metrics(l_val, w_val, re, rs)
        return x_arr, y_arr, z, rho, mask_cup, perimeter, die_hole_sa

    # === ОВАЛ (Все профили: Concave, Compound, Flat, Bevel и т.д.) ===
    base_mask = oval_mask(x_arr, y_arr, l_val, w_val, re, rs)
    if land > 0 and re > land + 1e-3 and rs > land + 1e-3:
        mask_cup = oval_mask(x_arr, y_arr, l_val - 2 * land, w_val - 2 * land, re - land, rs - land)
    else:
        mask_cup = base_mask

    l_c = max(0.001, l_val / 2 - land)
    w_c = max(0.001, w_val / 2 - land)
    z = np.zeros_like(x_arr)
    profile = params["profile"]

    xi, yi = np.abs(x_arr), np.abs(y_arr)
    
    # === ВЫБОР ИДЕАЛЬНОЙ ГЕОМЕТРИЧЕСКОЙ МОДЕЛИ ===
    if profile == "concave":
        # 1. СТРОГАЯ СФЕРИЧЕСКАЯ ЧАШКА
        theta = np.arctan2(yi, np.maximum(1e-9, xi))
        r_curr = np.sqrt(xi**2 + yi**2)

        xe = max(0.0, l_val / 2 - re)
        ys_center = w_val / 2 - rs
        re_in = max(0.001, re - land)
        rs_in = max(0.001, rs - land)

        theta_tan_c = np.arctan2(np.abs(ys_center), max(1e-9, xe))
        x_tan = xe + re_in * np.cos(theta_tan_c)
        y_tan = re_in * np.sin(theta_tan_c)
        theta_tan = np.arctan2(y_tan, x_tan)

        r_max = np.zeros_like(theta)
        mask_end = theta <= theta_tan
        mask_side = ~mask_end

        rad_end = np.maximum(0.0, re_in**2 - (xe * np.sin(theta[mask_end]))**2)
        r_max[mask_end] = xe * np.cos(theta[mask_end]) + np.sqrt(rad_end)

        rad_side = np.maximum(0.0, rs_in**2 - (ys_center * np.cos(theta[mask_side]))**2)
        r_max[mask_side] = ys_center * np.sin(theta[mask_side]) + np.sqrt(rad_side)
        r_max = np.maximum(1e-6, r_max)

        dc_safe = max(1e-6, dc)
        r_local = (r_max**2 + dc_safe**2) / (2 * dc_safe)
        rho_clamped = np.minimum(r_curr, r_max)
        z_surf = np.sqrt(np.maximum(0.0, r_local**2 - rho_clamped**2)) - (r_local - dc_safe)
        z[mask_cup] = z_surf[mask_cup]
    
    elif profile == "compound":
        # 2. МЕТОД СВИПА / SPINE LOFTING (Пропорциональное масштабирование)
        xe_c = max(0.0, l_val / 2 - re)
        ys_c = w_val / 2 - rs
        
        re_in = max(0.001, re - land) if land > 0 else re
        rs_in = max(0.001, rs - land) if land > 0 else rs
        
        theta_tan_sweep = np.arctan2(np.abs(ys_c), max(1e-9, xe_c))
        x_tan_sweep = xe_c + re_in * np.cos(theta_tan_sweep)

        y_max = np.zeros_like(xi)
        mask_side_sw = xi <= x_tan_sweep
        mask_end_sw = ~mask_side_sw

        rad_side_sw = np.maximum(0.0, rs_in**2 - xi[mask_side_sw]**2)
        y_max[mask_side_sw] = ys_c + np.sqrt(rad_side_sw)

        rad_end_sw = np.maximum(0.0, re_in**2 - (xi[mask_end_sw] - xe_c)**2)
        y_max[mask_end_sw] = np.sqrt(rad_end_sw)

        y_max = np.maximum(1e-6, y_max)

        h_local = eval_profile_1d(xi, params, l_c, dc)
        
        y_norm = np.minimum(1.0, yi / y_max)
        y_eq = y_norm * w_c

        params_min = dict(params)
        params_min["profile"] = "compound"
        params_min["R_maj_maj"] = params["R_min_maj"]
        params_min["R_maj_min"] = params["R_min_min"]
        z_w_eq = eval_profile_1d(y_eq, params_min, w_c, dc)

        z_blend = z_w_eq * (h_local / max(1e-6, dc))
        z[mask_cup] = z_blend[mask_cup]

    elif profile == "cbe":
        # 3. ГИБРИДНЫЙ ПОДХОД (Distance Field для фаски + Radial Sweep для центральной сферы)
        # Это обеспечивает идеальную фаску постоянной ширины и плавную сферическую чашу внутри
        bev_d = params.get("Bev_D", 0.51)
        bev_a = params.get("Bev_A", 40.0)
        alpha = np.radians(bev_a)
        tan_a = np.tan(alpha)
        w_b = bev_d / tan_a if tan_a > 0 else 0.0
        
        xe_c = max(0.0, l_val / 2 - re)
        ys_c = w_val / 2 - rs
        re_in = max(0.001, re - land) if land > 0 else re
        rs_in = max(0.001, rs - land) if land > 0 else rs
        
        # Поле расстояний для точной фаски
        m = np.abs(ys_c) / max(1e-9, xe_c)
        is_end = yi < m * (xi - xe_c)
        dist_end = np.sqrt((xi - xe_c)**2 + yi**2)
        dist_side = np.sqrt(xi**2 + (yi - ys_c)**2)
        d_edge = np.where(is_end, re_in - dist_end, rs_in - dist_side)
        d_edge = np.maximum(0.0, d_edge)
        
        # Рассчитываем Z для фаски
        z_bevel = np.minimum(d_edge * tan_a, bev_d)
        
        # Рассчитываем Z для внутренней сферы (Radial Sweep)
        theta = np.arctan2(yi, np.maximum(1e-9, xi))
        r_curr = np.sqrt(xi**2 + yi**2)
        
        re_inner_cup = max(0.001, re_in - w_b)
        rs_inner_cup = max(0.001, rs_in - w_b)
        
        theta_tan_c = np.arctan2(np.abs(ys_c), max(1e-9, xe_c))
        x_tan = xe_c + re_inner_cup * np.cos(theta_tan_c)
        y_tan = re_inner_cup * np.sin(theta_tan_c)
        theta_tan = np.arctan2(y_tan, x_tan)
        
        r_max_inner = np.zeros_like(theta)
        mask_end_inner = theta <= theta_tan
        mask_side_inner = ~mask_end_inner
        
        rad_end = np.maximum(0.0, re_inner_cup**2 - (xe_c * np.sin(theta[mask_end_inner]))**2)
        r_max_inner[mask_end_inner] = xe_c * np.cos(theta[mask_end_inner]) + np.sqrt(rad_end)
        
        rad_side = np.maximum(0.0, rs_inner_cup**2 - (ys_c * np.cos(theta[mask_side_inner]))**2)
        r_max_inner[mask_side_inner] = ys_c * np.sin(theta[mask_side_inner]) + np.sqrt(rad_side)
        r_max_inner = np.maximum(1e-6, r_max_inner)
        
        hc = max(1e-6, dc - bev_d)
        r_local = (r_max_inner**2 + hc**2) / (2 * hc)
        rho_clamped = np.minimum(r_curr, r_max_inner)
        z_inner_cup = bev_d + np.sqrt(np.maximum(0.0, r_local**2 - rho_clamped**2)) - (r_local - hc)
        
        # Смешиваем фаску и сферу: если расстояние от края больше ширины фаски, то это сфера
        is_inner = d_edge > w_b
        z_hybrid = np.where(is_inner, z_inner_cup, z_bevel)
        z[mask_cup] = z_hybrid[mask_cup]

    else:
        # 4. ПОЛЕ РАССТОЯНИЙ / DISTANCE FIELD (Для Flat Radius, Flat Bevel и т.д.)
        # Гарантирует фаску строго постоянной ширины без искажений по диагоналям
        xe_c = max(0.0, l_val / 2 - re)
        ys_c = w_val / 2 - rs
        
        re_in = max(0.001, re - land) if land > 0 else re
        rs_in = max(0.001, rs - land) if land > 0 else rs
        
        # Линия водораздела (Voronoi edge) между торцевой и боковой дугой
        m = np.abs(ys_c) / max(1e-9, xe_c)
        is_end = yi < m * (xi - xe_c)
        
        # Точное математическое расстояние от пикселя до контура таблетки
        dist_end = np.sqrt((xi - xe_c)**2 + yi**2)
        dist_side = np.sqrt(xi**2 + (yi - ys_c)**2)
        
        d_edge = np.where(is_end, re_in - dist_end, rs_in - dist_side)
        d_edge = np.maximum(0.0, d_edge)
        
        # Переводим расстояние от края в эквивалентную координату Y малой оси
        y_eq = w_c - d_edge
        y_eq = np.clip(y_eq, 0.0, w_c)
        
        z_blend = eval_profile_1d(y_eq, params, w_c, dc)
        z[mask_cup] = z_blend[mask_cup]

    rho = np.sqrt((x_arr / l_c) ** 2 + (y_arr / w_c) ** 2) * w_c
    perimeter, die_hole_sa = oval_metrics(l_val, w_val, re, rs)
    return x_arr, y_arr, z, rho, mask_cup, perimeter, die_hole_sa


def compute_bisect_width(params, depth, angle, ri):
    if depth <= 0:
        return 0.0
    _require_params(params, ["Dc"])
    dc = max(0.0, params["Dc"])
    span = minor_span(params)
    x_test = np.linspace(0, span, 2000)
    z_bottom = dc - depth
    alpha = np.radians(angle / 2.0)
    if alpha <= 0:
        return 0.0
    d_sharp = ri / np.sin(alpha) - ri if ri > 0 else 0
    x_ti = ri * np.sin(alpha)
    z_v = z_bottom - d_sharp + x_test / np.tan(alpha)
    z_inner = z_bottom + ri - np.sqrt(np.maximum(0, ri**2 - x_test**2))
    z_g = np.where(x_test <= x_ti, z_inner, z_v)
    z_cup = eval_profile_1d(x_test, params, span, dc)
    diff = z_cup - z_g
    crossings = np.where(np.diff(np.sign(diff)))[0]
    if len(crossings) > 0:
        idx = crossings[0]
        x1, x2 = x_test[idx], x_test[idx + 1]
        y1, y2 = diff[idx], diff[idx + 1]
        if y2 != y1:
            return round(2 * (x1 - y1 * (x2 - x1) / (y2 - y1)), 4)
    return 0.0


def compute_bisect_depth(params, target_width, angle, ri):
    if target_width <= 0:
        return 0.0
    _require_params(params, ["Dc"])
    dc = max(0.0, params["Dc"])
    d_min, d_max = 0.0, dc * 2.0
    for _ in range(35):
        d_mid = (d_min + d_max) / 2
        w_mid = compute_bisect_width(params, d_mid, angle, ri)
        if w_mid < target_width:
            d_min = d_mid
        else:
            d_max = d_mid
    return round((d_min + d_max) / 2, 4)


def generate_mesh(params):
    _require_params(
        params,
        [
            "shape",
            "profile",
            "is_modified",
            "W",
            "L",
            "Re",
            "Rs",
            "Land",
            "Dc",
            "Hb",
            "b_type",
            "b_depth",
            "b_angle",
            "b_Ri",
            "b_cruciform",
            "b_double_sided",
            "R_min_maj",
            "R_min_min",
        ],
    )
    shape, _, w_val, l_val, _, _, _ = shape_params(params)
    dc = max(0.0, params["Dc"])

    quality = params.get("pdf_3d_quality", "medium")
    if params.get("is_pdf_export"):
        if quality == "low":
            mesh_n = 150
        elif quality == "high":
            mesh_n = 450
        else:
            mesh_n = 300
    else:
        mesh_n = 300

    x_grid = np.linspace(-l_val / 2, l_val / 2, mesh_n)
    y_grid = np.linspace(-w_val / 2, w_val / 2, mesh_n)
    x_arr, y_arr, z, rho, mask_cup, perimeter, die_hole_sa = build_surface(params, x_grid, y_grid)

    dx, dy = x_grid[1] - x_grid[0], y_grid[1] - y_grid[0]
    d_a = dx * dy

    z_cup_top = z.copy()
    z_cup_bottom = z.copy()
    z_groove = np.full_like(z, dc * 5.0)

    b_type = params["b_type"]
    b_depth = params["b_depth"] or 0.0
    b_cruciform = bool(params["b_cruciform"])
    b_double_sided = bool(params["b_double_sided"])
    if b_type != "none" and b_depth > 0:
        b_angle = params["b_angle"]
        b_ri = params["b_Ri"]
        alpha = np.radians(b_angle / 2.0)
        d_sharp = b_ri / np.sin(alpha) - b_ri if (b_ri > 0 and alpha > 0) else 0.0
        x_ti = b_ri * np.sin(alpha)

        span = minor_span(params)
        profile = params["profile"]

        def _groove_from_axes(cut_axis, along_axis):
            if shape == "oval" and profile in ["compound", "compound_cup"]:
                params_along = dict(params)
                params_along["profile"] = "compound"
                params_along["R_maj_maj"] = params["R_min_maj"]
                params_along["R_maj_min"] = params["R_min_min"]
                z_centerline = eval_profile_1d(along_axis, params_along, span, dc)
            else:
                z_centerline = eval_profile_1d(along_axis, params, span, dc)

            if b_type == "standard":
                z_bottom = z_centerline - b_depth
            elif b_type == "cut_through":
                z_bottom = np.full_like(z, dc - b_depth)
            elif b_type == "decreasing":
                z_bottom = z_centerline - b_depth * np.maximum(0, 1 - (along_axis / max(1e-6, span)) ** 2)
            else:
                z_bottom = z_centerline - b_depth

            z_v = z_bottom - d_sharp + cut_axis / np.tan(alpha)
            z_inner = z_bottom + b_ri - np.sqrt(np.maximum(0, b_ri**2 - cut_axis**2))
            return np.where(cut_axis <= x_ti, z_inner, z_v)

        if shape == "round":
            z_groove_main = _groove_from_axes(np.abs(y_arr), np.abs(x_arr))
            if b_cruciform:
                z_groove_cross = _groove_from_axes(np.abs(x_arr), np.abs(y_arr))
                z_groove = np.minimum(z_groove_main, z_groove_cross)
            else:
                z_groove = z_groove_main
        else:
            z_groove = _groove_from_axes(np.abs(x_arr), np.abs(y_arr))

        z_cup_top = np.maximum(0, np.minimum(z, z_groove))
        if b_double_sided:
            z_cup_bottom = np.maximum(0, np.minimum(z, z_groove))

    cup_vol_top = np.sum(z_cup_top) * d_a
    dzdx_top = np.gradient(z_cup_top, dx, axis=1)
    dzdy_top = np.gradient(z_cup_top, dy, axis=0)
    cup_sa_top = np.sum(np.sqrt(1 + dzdx_top**2 + dzdy_top**2)[mask_cup]) * d_a

    cup_vol_bottom = np.sum(z_cup_bottom) * d_a
    dzdx_bot = np.gradient(z_cup_bottom, dx, axis=1)
    dzdy_bot = np.gradient(z_cup_bottom, dy, axis=0)
    cup_sa_bottom = np.sum(np.sqrt(1 + dzdx_bot**2 + dzdy_bot**2)[mask_cup]) * d_a

    land_sa = max(0.0, die_hole_sa - np.sum(mask_cup) * d_a)
    hb = params["Hb"]
    
    tablet_sa = perimeter * hb + (cup_sa_top + land_sa) + (cup_sa_bottom + land_sa)
    tablet_vol = die_hole_sa * hb + cup_vol_top + cup_vol_bottom

    return {
        "X": x_arr,
        "Y": y_arr,
        "Z": z,
        "Z_cup_bottom": z_cup_bottom,
        "Z_groove": z_groove,
        "Z_cup_top": z_cup_top,
        "mask_cup": mask_cup,
        "rho": rho,
        "x_grid": x_grid,
        "y_grid": y_grid,
        "metrics": {
            "Die_Hole_SA": round(die_hole_sa, 4),
            "Cup_Volume": round(cup_vol_top, 4),
            "Cup_SA": round(cup_sa_top + land_sa, 4),
            "Perimeter": round(perimeter, 4),
            "Tablet_SA": round(tablet_sa, 4),
            "Tablet_Vol": round(tablet_vol, 4),
        },
    }
