from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "output" / "marketing"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FONT_REGULAR = Path("C:/Windows/Fonts/malgun.ttf")
FONT_BOLD = Path("C:/Windows/Fonts/malgunbd.ttf")


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    font_path = FONT_BOLD if bold else FONT_REGULAR
    if font_path.exists():
        return ImageFont.truetype(str(font_path), size)
    return ImageFont.load_default()


def draw_gradient(draw: ImageDraw.ImageDraw, width: int, height: int) -> None:
    top = (236, 243, 255)
    bottom = (249, 251, 255)
    for y in range(height):
        ratio = y / max(height - 1, 1)
        color = tuple(int(top[i] * (1 - ratio) + bottom[i] * ratio) for i in range(3))
        draw.line((0, y, width, y), fill=color)


def rounded_box(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fill, outline=None, radius: int = 28) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=2 if outline else 0)


def text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], value: str, font, fill, anchor: str | None = None) -> None:
    draw.text(xy, value, font=font, fill=fill, anchor=anchor)


def create_linkedin_cover() -> Path:
    width, height = 1200, 627
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    draw_gradient(draw, width, height)

    title_font = load_font(72, bold=True)
    subtitle_font = load_font(30)
    body_font = load_font(28)
    small_font = load_font(24)

    rounded_box(draw, (56, 52, width - 56, height - 52), fill=(255, 255, 255), outline=(212, 223, 240), radius=36)
    text(draw, (96, 92), "파일명구조대", title_font, (26, 48, 94))
    text(draw, (98, 176), "깨진 한글 파일명을 정상 이름으로 복구하는 Windows 도구", subtitle_font, (73, 90, 121))

    left_box = (96, 248, 716, 548)
    right_box = (756, 248, 1104, 548)
    rounded_box(draw, left_box, fill=(245, 248, 255), outline=(216, 226, 242), radius=28)
    rounded_box(draw, right_box, fill=(249, 251, 255), outline=(216, 226, 242), radius=28)

    text(draw, (130, 280), "Before", small_font, (104, 117, 143))
    text(draw, (130, 320), "코로나19로.pdf", body_font, (54, 72, 110))
    text(draw, (130, 376), "가상자산 시계열.pdf", body_font, (54, 72, 110))
    text(draw, (130, 432), "사이버 범죄 예측.pdf", body_font, (54, 72, 110))

    text(draw, (488, 472), "→", load_font(54, bold=True), (44, 124, 255), anchor="mm")

    text(draw, (528, 280), "After", small_font, (44, 124, 255))
    text(draw, (528, 320), "코로나19로.pdf", body_font, (22, 66, 37))
    text(draw, (528, 376), "가상자산 시계열.pdf", body_font, (22, 66, 37))
    text(draw, (528, 432), "사이버 범죄 예측.pdf", body_font, (22, 66, 37))

    pills = [
        "드래그앤드롭 지원",
        "미리보기 후 안전 변경",
        "파일/폴더 일괄 정리",
    ]
    y = 295
    for pill in pills:
        rounded_box(draw, (790, y, 1070, y + 62), fill=(232, 241, 255), radius=24)
        text(draw, (930, y + 31), pill, small_font, (26, 66, 133), anchor="mm")
        y += 84

    text(draw, (98, 570), "Drag files  •  Preview changes  •  Rename in batch", small_font, (90, 106, 136))

    output = OUTPUT_DIR / "linkedin_cover.png"
    image.save(output)
    return output


def create_blog_cover() -> Path:
    width, height = 1600, 900
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    draw_gradient(draw, width, height)

    title_font = load_font(92, bold=True)
    subtitle_font = load_font(38)
    body_font = load_font(30)
    label_font = load_font(26)

    rounded_box(draw, (70, 70, 1530, 830), fill=(255, 255, 255), outline=(214, 224, 241), radius=42)
    text(draw, (120, 126), "파일명구조대", title_font, (25, 48, 94))
    text(draw, (124, 236), "맥, OneDrive, 압축 파일 때문에 깨진 한글 파일명 복구", subtitle_font, (74, 89, 120))

    window = (120, 330, 1480, 760)
    rounded_box(draw, window, fill=(246, 249, 255), outline=(215, 226, 242), radius=28)
    rounded_box(draw, (150, 368, 1450, 720), fill=(255, 255, 255), outline=(227, 234, 244), radius=20)

    text(draw, (188, 392), "현재 이름", label_font, (109, 122, 147))
    text(draw, (760, 392), "변경될 이름", label_font, (44, 124, 255))
    rows = [
        ("코로나19로.pdf", "코로나19로.pdf"),
        ("가상자산 시계열.pdf", "가상자산 시계열.pdf"),
        ("사이버 범죄 예측.pdf", "사이버 범죄 예측.pdf"),
    ]
    y = 455
    for left, right in rows:
        draw.line((180, y - 20, 1420, y - 20), fill=(235, 240, 247), width=2)
        text(draw, (188, y), left, body_font, (55, 72, 108))
        text(draw, (760, y), right, body_font, (23, 71, 39))
        y += 95

    text(draw, (124, 790), "깨진 파일명 탐지 → 미리보기 → 안전한 일괄 변경", subtitle_font, (46, 74, 125))

    output = OUTPUT_DIR / "blog_cover.png"
    image.save(output)
    return output


def create_demo_gif() -> Path:
    width, height = 1280, 720
    title_font = load_font(64, bold=True)
    subtitle_font = load_font(34)
    body_font = load_font(28)
    small_font = load_font(22)
    frames = []
    durations = []

    def base_canvas() -> tuple[Image.Image, ImageDraw.ImageDraw]:
        image = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(image)
        draw_gradient(draw, width, height)
        rounded_box(draw, (48, 42, width - 48, height - 42), fill=(255, 255, 255), outline=(214, 224, 241), radius=38)
        return image, draw

    for step in range(6):
        image, draw = base_canvas()
        text(draw, (90, 84), "파일명구조대", title_font, (26, 48, 94))
        text(draw, (92, 152), "깨진 한글 파일명 복구 데모", subtitle_font, (74, 89, 120))
        rounded_box(draw, (90, 240, 560, 610), fill=(245, 248, 255), outline=(216, 226, 242), radius=28)
        rounded_box(draw, (620, 240, 1190, 610), fill=(249, 251, 255), outline=(216, 226, 242), radius=28)
        text(draw, (126, 278), "1. 파일 드래그", body_font, (52, 70, 109))
        text(draw, (656, 278), "2. 바뀔 이름 미리보기", body_font, (52, 70, 109))

        offset = step * 18
        rounded_box(draw, (142 + offset, 370, 388 + offset, 440), fill=(232, 241, 255), radius=22)
        text(draw, (265 + offset, 405), "코로나19로.pdf", small_font, (43, 72, 128), anchor="mm")
        text(draw, (470, 405), "→", load_font(54, bold=True), (44, 124, 255), anchor="mm")
        text(draw, (684, 366), "코로나19로.pdf", body_font, (55, 72, 108))
        text(draw, (684, 430), "코로나19로.pdf", body_font, (23, 71, 39))
        text(draw, (684, 494), "가상자산 시계열.pdf", body_font, (23, 71, 39))
        text(draw, (684, 558), "사이버 범죄 예측.pdf", body_font, (23, 71, 39))
        frames.append(image)
        durations.append(140)

    for step in range(8):
        image, draw = base_canvas()
        text(draw, (90, 84), "파일명구조대", title_font, (26, 48, 94))
        text(draw, (92, 152), "3. 한 번에 안전하게 변경", subtitle_font, (74, 89, 120))
        rounded_box(draw, (110, 250, 1170, 590), fill=(247, 250, 255), outline=(220, 229, 243), radius=30)

        completed = step / 7
        draw.rounded_rectangle((150, 310, 1130, 350), radius=18, fill=(231, 236, 246))
        draw.rounded_rectangle((150, 310, int(150 + 980 * completed), 350), radius=18, fill=(48, 130, 255))
        text(draw, (150, 384), "Ready", small_font, (98, 114, 142))
        text(draw, (1038, 384), "Done", small_font, (98, 114, 142))

        status_y = 450
        states = [
            ("코로나19로.pdf", completed > 0.15),
            ("가상자산 시계열.pdf", completed > 0.45),
            ("사이버 범죄 예측.pdf", completed > 0.75),
        ]
        for value, done in states:
            fill = (23, 71, 39) if done else (86, 99, 126)
            marker = "완료" if done else "대기"
            text(draw, (184, status_y), value, body_font, fill)
            text(draw, (1048, status_y), marker, body_font, fill)
            status_y += 72

        text(draw, (152, 548), "Preview after drag-and-drop. Rename only after checking conflicts.", small_font, (92, 107, 136))
        frames.append(image)
        durations.append(160)

    output = OUTPUT_DIR / "demo.gif"
    frames[0].save(
        output,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=False,
    )
    return output


def main() -> None:
    linkedin = create_linkedin_cover()
    blog = create_blog_cover()
    demo = create_demo_gif()
    print(linkedin)
    print(blog)
    print(demo)


if __name__ == "__main__":
    main()
