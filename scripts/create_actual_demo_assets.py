from __future__ import annotations

import importlib.util
import shutil
import sys
import time
import unicodedata
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageGrab

try:
    import imageio.v2 as imageio
except Exception:  # pragma: no cover
    imageio = None

try:
    import numpy as np
except Exception:  # pragma: no cover
    np = None


ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "hangul_filename_fixer.py"
OUTPUT_DIR = ROOT / "output" / "actual_demo"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR = ROOT / "tmp_actual_demo_workspace"

FONT_REGULAR = Path("C:/Windows/Fonts/malgun.ttf")
FONT_BOLD = Path("C:/Windows/Fonts/malgunbd.ttf")


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    font_path = FONT_BOLD if bold else FONT_REGULAR
    if font_path.exists():
        return ImageFont.truetype(str(font_path), size)
    return ImageFont.load_default()


def load_app_module():
    spec = importlib.util.spec_from_file_location("hangul_filename_fixer_demo", APP_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def create_demo_workspace() -> tuple[Path, list[Path]]:
    if TEMP_DIR.exists():
        shutil.rmtree(TEMP_DIR)
    TEMP_DIR.mkdir(parents=True)

    sample_names = [
        "코로나19로 인한 온라인 쇼핑 구매의 변화.pdf",
        "가상자산 시계열 데이터의 분석과 예측.pdf",
        "사이버 범죄 예측 모델 패턴 분석.pdf",
    ]

    paths: list[Path] = []
    for name in sample_names:
        broken = unicodedata.normalize("NFD", name)
        path = TEMP_DIR / broken
        path.write_text("demo", encoding="utf-8")
        paths.append(path)

    return TEMP_DIR, paths


def capture_window(root, caption: str, subcaption: str, out_name: str) -> Path:
    root.update_idletasks()
    root.update()
    root.lift()
    root.attributes("-topmost", True)
    root.update()
    time.sleep(0.5)

    x = root.winfo_rootx()
    y = root.winfo_rooty()
    w = root.winfo_width()
    h = root.winfo_height()
    image = ImageGrab.grab(bbox=(x, y, x + w, y + h), all_screens=True)
    root.attributes("-topmost", False)

    draw = ImageDraw.Draw(image)
    overlay_height = 92
    draw.rounded_rectangle((24, 18, image.width - 24, 18 + overlay_height), radius=26, fill=(255, 255, 255, 240))
    draw.text((46, 34), caption, font=load_font(34, bold=True), fill=(21, 47, 96))
    draw.text((48, 76), subcaption, font=load_font(18), fill=(86, 99, 123))

    out_path = OUTPUT_DIR / out_name
    image.save(out_path)
    return out_path


def build_demo_assets() -> dict[str, Path]:
    module = load_app_module()
    workspace, broken_files = create_demo_workspace()

    root = module.tk.Tk()
    root.geometry("1220x780+80+60")
    app = module.FixerApp(root)

    assets: dict[str, Path] = {}
    frames: list[Image.Image] = []

    try:
        app.folder_var.set(str(workspace))
        app.scan_folder()
        step1 = capture_window(
            root,
            "1. 실제 앱에서 깨진 파일명 스캔",
            "분해형(NFD) 한글 파일명을 자동으로 찾은 상태",
            "actual_scan.png",
        )
        assets["scan"] = step1
        frames.extend([Image.open(step1).copy()] * 4)

        app.load_targets(broken_files[:2], source="드래그앤드롭")
        step2 = capture_window(
            root,
            "2. 파일 여러 개 드래그앤드롭",
            "폴더 전체가 아니라 드롭한 파일만 따로 스캔 가능",
            "actual_drop_mode.png",
        )
        assets["drop"] = step2
        frames.extend([Image.open(step2).copy()] * 4)

        plan = module.build_plan_for_targets(broken_files, recursive=True, include_dirs=True)
        module.apply_plan(plan)
        app.folder_var.set(str(workspace))
        app.scan_folder()
        app.status_var.set("실제 데모: 이름 변경이 끝난 뒤 다시 스캔한 상태입니다.")
        step3 = capture_window(
            root,
            "3. 이름 변경 실행 후 다시 스캔",
            "더 이상 깨진 파일명이 없는 상태로 정리 완료",
            "actual_after.png",
        )
        assets["after"] = step3
        frames.extend([Image.open(step3).copy()] * 6)

        gif_path = OUTPUT_DIR / "actual_demo.gif"
        frames[0].save(
            gif_path,
            save_all=True,
            append_images=frames[1:],
            duration=[700] * len(frames),
            loop=0,
            optimize=False,
        )
        assets["gif"] = gif_path

        if imageio is not None and np is not None:
            mp4_path = OUTPUT_DIR / "actual_demo.mp4"
            with imageio.get_writer(mp4_path, fps=1.2) as writer:
                for frame in frames:
                    writer.append_data(np.array(frame))
            assets["mp4"] = mp4_path

        hero = Image.open(step2).copy()
        hero_path = OUTPUT_DIR / "actual_demo_hero.png"
        hero.save(hero_path)
        assets["hero"] = hero_path

        return assets
    finally:
        try:
            root.destroy()
        except Exception:
            pass
        if TEMP_DIR.exists():
            shutil.rmtree(TEMP_DIR)


def main() -> None:
    assets = build_demo_assets()
    for key, path in assets.items():
        print(f"{key}: {path}")


if __name__ == "__main__":
    main()
