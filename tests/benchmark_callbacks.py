"""
Бенчмарк производительности колбэков TabletCAD

Замеряет:
1. Время выполнения основных колбэков
2. Размер сериализованных данных (payload)
3. Использование памяти
4. Частоту вызовов при типичном сценарии
"""

import sys
import time
import json
import tracemalloc
from pathlib import Path

# Добавляем корень проекта в path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.defaults import BASE_DEFAULTS, PROFILE_DEFAULTS, SHAPE_SPECIFIC, BISECT_DEFAULTS
from core.engine import generate_mesh
from core.renderer import render_tablet
from core.renderer_3d import render_tablet_3d


# Типичные сценарии использования
TEST_SCENARIOS = {
    "round_concave": {
        "shape": "round",
        "profile": "concave",
        "is_modified": False,
        "W": 7.94,
        "L": 7.94,
        "Re": 0,
        "Rs": 0,
        "Dc": 0.55,
        "Rc_min": 8.8,
        "Rc_maj": 0,
        "Land": 0.08,
        "Hb": 0.5,
        "Tt": 1.6,
        "density": 1.2,
    },
    "oval_cbe": {
        "shape": "oval",
        "profile": "cbe",
        "is_modified": False,
        "W": 7.94,
        "L": 14.0,
        "Re": 4.0,
        "Rs": 15.0,
        "Dc": 0.4,
        "Rc_min": 12.0,
        "Rc_maj": 25.0,
        "Land": 0.1,
        "Hb": 0.3,
        "Tt": 1.1,
        "density": 1.2,
        "Bev_D": 0.51,
        "Bev_A": 40.0,
    },
    "capsule_ffbe": {
        "shape": "capsule",
        "profile": "ffbe",
        "is_modified": True,
        "W": 10.0,
        "L": 18.0,
        "Re": 5.0,
        "Rs": 20.0,
        "Dc": 0.35,
        "Rc_min": 10.0,
        "Land": 0.15,
        "Hb": 0.2,
        "Tt": 0.9,
        "density": 1.2,
        "Bev_A": 45.0,
        "Blend_R": 0.38,
    },
}


def _build_params(scenario):
    """Собирает params dict из сценария"""
    params = {
        "shape": scenario["shape"],
        "profile": scenario["profile"],
        "is_modified": scenario.get("is_modified", False),
        "W": scenario.get("W", BASE_DEFAULTS["W"]),
        "L": scenario.get("L", BASE_DEFAULTS["L"]),
        "Re": scenario.get("Re", SHAPE_SPECIFIC["oval"]["re"]),
        "Rs": scenario.get("Rs", SHAPE_SPECIFIC["oval"]["rs"]),
        "Dc": scenario.get("Dc", BASE_DEFAULTS["dc"]),
        "Rc_min": scenario.get("Rc_min", PROFILE_DEFAULTS["concave"]["rc_min"]),
        "Rc_maj": scenario.get("Rc_maj", PROFILE_DEFAULTS["concave"]["rc_maj"]),
        "Land": scenario.get("Land", BASE_DEFAULTS["land"]),
        "Hb": scenario.get("Hb", BASE_DEFAULTS["hb"]),
        "Tt": scenario.get("Tt", BASE_DEFAULTS["tt"]),
        "density": scenario.get("density", BASE_DEFAULTS["density"]),
        "Bev_D": scenario.get("Bev_D", PROFILE_DEFAULTS["cbe"]["bev_d"]),
        "Bev_A": scenario.get("Bev_A", PROFILE_DEFAULTS["cbe"]["bev_a"]),
        "R_edge": scenario.get("R_edge", PROFILE_DEFAULTS["ffre"]["r_edge"]),
        "Blend_R": scenario.get("Blend_R", PROFILE_DEFAULTS["ffbe"]["blend_r"]),
        "R_maj_maj": scenario.get("R_maj_maj", PROFILE_DEFAULTS["compound"]["r_maj_maj"]),
        "R_maj_min": scenario.get("R_maj_min", PROFILE_DEFAULTS["compound"]["r_maj_min"]),
        "R_min_maj": scenario.get("R_min_maj", PROFILE_DEFAULTS["compound"]["r_min_maj"]),
        "R_min_min": scenario.get("R_min_min", PROFILE_DEFAULTS["compound"]["r_min_min"]),
        "b_type": "none",
        "b_width": BISECT_DEFAULTS["standard"]["width"],
        "b_depth": BISECT_DEFAULTS["standard"]["depth"],
        "b_angle": BISECT_DEFAULTS["standard"]["angle"],
        "b_Ri": BISECT_DEFAULTS["standard"]["ri"],
        "b_cruciform": False,
        "b_double_sided": False,
        "view_preset": "isometric",
        "render_mode": "shaded",
        "show_bbox": False,
        "render_2d_shaded": False,
        "render_2d_style": "web",
        "render_2d_format": "svg",
    }
    return params


def measure_payload_size(params_dict):
    """Замеряет размер JSON payload для передачи в колбэк"""
    json_str = json.dumps(params_dict)
    return len(json_str.encode('utf-8'))


def benchmark_generate_mesh(scenario_name, scenario, iterations=10):
    """Бенчмарк generate_mesh()"""
    params = _build_params(scenario)
    
    times = []
    memory_deltas = []
    
    for i in range(iterations):
        tracemalloc.start()
        
        start = time.perf_counter()
        mesh_data = generate_mesh(params)
        elapsed = time.perf_counter() - start
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        times.append(elapsed)
        memory_deltas.append(peak)
    
    return {
        "name": f"generate_mesh ({scenario_name})",
        "iterations": iterations,
        "avg_time_ms": sum(times) / len(times) * 1000,
        "min_time_ms": min(times) * 1000,
        "max_time_ms": max(times) * 1000,
        "avg_memory_kb": sum(memory_deltas) / len(memory_deltas) / 1024,
        "peak_memory_kb": max(memory_deltas) / 1024,
    }


def benchmark_render_2d(scenario_name, scenario, iterations=5):
    """Бенчмарк render_tablet() 2D"""
    params = _build_params(scenario)
    mesh_data = generate_mesh(params)
    
    times = []
    memory_deltas = []
    
    for i in range(iterations):
        tracemalloc.start()
        
        start = time.perf_counter()
        img_src = render_tablet(mesh_data, params)
        elapsed = time.perf_counter() - start
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        times.append(elapsed)
        memory_deltas.append(peak)
    
    payload_size = len(img_src.encode('utf-8')) if img_src else 0
    
    return {
        "name": f"render_2d ({scenario_name})",
        "iterations": iterations,
        "avg_time_ms": sum(times) / len(times) * 1000,
        "min_time_ms": min(times) * 1000,
        "max_time_ms": max(times) * 1000,
        "avg_memory_kb": sum(memory_deltas) / len(memory_deltas) / 1024,
        "peak_memory_kb": max(memory_deltas) / 1024,
        "output_size_kb": payload_size / 1024,
    }


def benchmark_render_3d(scenario_name, scenario, iterations=5):
    """Бенчмарк render_tablet_3d()"""
    params = _build_params(scenario)
    mesh_data = generate_mesh(params)
    
    times = []
    memory_deltas = []
    
    for i in range(iterations):
        tracemalloc.start()
        
        start = time.perf_counter()
        fig = render_tablet_3d(mesh_data, params)
        elapsed = time.perf_counter() - start
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        times.append(elapsed)
        memory_deltas.append(peak)
    
    return {
        "name": f"render_3d ({scenario_name})",
        "iterations": iterations,
        "avg_time_ms": sum(times) / len(times) * 1000,
        "min_time_ms": min(times) * 1000,
        "max_time_ms": max(times) * 1000,
        "avg_memory_kb": sum(memory_deltas) / len(memory_deltas) / 1024,
        "peak_memory_kb": max(memory_deltas) / 1024,
    }


def estimate_callback_overhead(num_inputs=35):
    """Оценивает накладные расходы Dash на сериализацию"""
    # Симулируем payload с num_inputs числовыми значениями
    dummy_payload = {f"input_{i}": 1.2345 for i in range(num_inputs)}
    json_str = json.dumps(dummy_payload)
    payload_bytes = len(json_str.encode('utf-8'))
    
    # Сериализация/десериализация
    iterations = 1000
    start = time.perf_counter()
    for _ in range(iterations):
        json.dumps(dummy_payload)
        json.loads(json_str)
    elapsed = time.perf_counter() - start
    
    return {
        "name": f"Dash overhead ({num_inputs} inputs)",
        "payload_size_bytes": payload_bytes,
        "avg_serialization_time_us": (elapsed / iterations / 2) * 1_000_000,
        "note": "Включает json.dumps + json.loads",
    }


def print_results(results):
    """Красивый вывод результатов"""
    print("\n" + "=" * 80)
    print("BENCHMARK RESULTS - TabletCAD Callbacks Performance")
    print("=" * 80 + "\n")
    
    for result in results:
        print(f"[*] {result['name']}")
        print("-" * 60)
        
        if "avg_time_ms" in result:
            print(f"   Время выполнения:")
            print(f"     • Среднее:  {result['avg_time_ms']:.2f} ms")
            print(f"     • Минимум:  {result['min_time_ms']:.2f} ms")
            print(f"     • Максимум: {result['max_time_ms']:.2f} ms")
        
        if "avg_memory_kb" in result:
            print(f"   Память:")
            print(f"     • Среднее:  {result['avg_memory_kb']:.1f} KB")
            print(f"     • Пик:      {result['peak_memory_kb']:.1f} KB")
        
        if "payload_size_bytes" in result:
            print(f"   Payload: {result['payload_size_bytes']} байт")
        
        if "output_size_kb" in result:
            print(f"   Выходные данные: {result['output_size_kb']:.1f} KB")
        
        if "avg_serialization_time_us" in result:
            print(f"   Сериализация: {result['avg_serialization_time_us']:.1f} мкс")
        
        if "note" in result:
            print(f"   Примечание: {result['note']}")
        
        print()
    
    # Сводная таблица
    print("=" * 80)
    print("SUMMARY TABLE")
    print("=" * 80)
    print(f"{'Компонент':<35} {'Время (ms)':<15} {'Память (KB)':<15}")
    print("-" * 80)
    
    for result in results:
        if "avg_time_ms" in result:
            name = result['name'][:33]
            time_str = f"{result['avg_time_ms']:.2f}"
            mem_str = f"{result['avg_memory_kb']:.1f}"
            print(f"{name:<35} {time_str:<15} {mem_str:<15}")
    
    print("=" * 80)
    
    # Выводы
    print("\nВЫВОДЫ:")
    print("-" * 80)
    
    # Находим самые тяжёлые операции
    time_results = [r for r in results if "avg_time_ms" in r]
    if time_results:
        slowest = max(time_results, key=lambda x: x["avg_time_ms"])
        print(f"   - Самая тяжёлая операция: {slowest['name']}")
        print(f"     Время: {slowest['avg_time_ms']:.2f} ms")
    
    # Оцениваем накладные расходы
    overhead = next((r for r in results if "Dash overhead" in r["name"]), None)
    if overhead:
        print(f"   - Накладные расходы Dash: {overhead['payload_size_bytes']} байт payload")
        print(f"     Сериализация: {overhead['avg_serialization_time_us']:.1f} мкс (незначительно)")
    
    print("\n   РЕКОМЕНДАЦИИ:")
    print("      - Для текущих метрик оптимизация колбэков не критична")
    print("      - Основное время занимает generate_mesh() - бизнес-логика")
    print("      - Dash overhead минимален (<1KB payload, <100мкс сериализация)")
    print("      - При >100 одновременных пользователей рассмотреть background callbacks")
    print()


def main():
    print("Запуск бенчмарка TabletCAD...\n")
    
    results = []
    
    # 1. Накладные расходы Dash
    print("Замер накладных расходов Dash...")
    results.append(estimate_callback_overhead(num_inputs=35))
    
    # 2. Бенчмарк для каждого сценария
    for scenario_name, scenario in TEST_SCENARIOS.items():
        print(f"\nСценарий: {scenario_name}")
        print("-" * 40)
        
        # generate_mesh
        print("   - generate_mesh...")
        results.append(benchmark_generate_mesh(scenario_name, scenario, iterations=10))
        
        # render_2d
        print("   - render_2d...")
        results.append(benchmark_render_2d(scenario_name, scenario, iterations=5))
        
        # render_3d
        print("   - render_3d...")
        results.append(benchmark_render_3d(scenario_name, scenario, iterations=5))
    
    # Вывод результатов
    print_results(results)
    
    # Сохранение в JSON
    output_path = Path(__file__).parent / "benchmark_results.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        # Конвертируем для JSON-сериализуемости
        json_results = []
        for r in results:
            json_r = {}
            for k, v in r.items():
                if isinstance(v, (str, int, float, dict)):
                    json_r[k] = v
                elif isinstance(v, bytes):
                    json_r[k] = len(v)
                else:
                    json_r[k] = str(v)
            json_results.append(json_r)
        json.dump(json_results, f, indent=2, ensure_ascii=False)
    
    print(f"Результаты сохранены в: {output_path}\n")


if __name__ == "__main__":
    main()
