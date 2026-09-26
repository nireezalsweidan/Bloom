import io
import logging
import random

from django.conf import settings
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)

# Rough color associations so the mock illustration isn't just random circles
PALETTE_COLORS = {
    "Soft Pastels & Blush Rose": ["#F4DCD6", "#E8A3B5", "#FFFFFF", "#C6E7D5"],
    "Sunset Terracotta & Warm Peach": ["#C97D60", "#F6C3A5", "#E8A3B5"],
    "Pure Ivory & Botanical Sage": ["#FCFAF7", "#ADCEBC", "#476556"],
    "Vibrant Jewel & Plum Velour": ["#58201C", "#75648A", "#3A0A08"],
}
DEFAULT_COLORS = ["#E8A3B5", "#F4DCD6", "#ADCEBC", "#FFFFFF"]


import math
import random


def _draw_mock_bouquet(flowers, color_palette):
    """
    Best-effort illustrative placeholder: a stylized bouquet silhouette
    (wrapped paper, stems, clustered blooms, greenery, ribbon) sized
    roughly by each flower's quantity. This is NOT a photo of the real
    product — it exists so the customer has something visual to react
    to before a real florist assembles the order.
    """
    from PIL import Image, ImageDraw

    size = 640
    img = Image.new("RGB", (size, size), "#FAF6F0")
    draw = ImageDraw.Draw(img)

    colors = PALETTE_COLORS.get(color_palette, DEFAULT_COLORS)
    cx = size // 2
    tie_point = (cx, size - 60)          # where the ribbon binds the stems
    cluster_center = (cx, 230)           # center of the bloom cluster
    paper_top_y = 300                    # where wrapping paper meets the blooms

    # --- Wrapping paper cone ---
    draw.polygon(
        [
            (tie_point[0] - 12, tie_point[1] + 10),
            (cx - 170, paper_top_y),
            (cx + 170, paper_top_y),
            (tie_point[0] + 12, tie_point[1] + 10),
        ],
        fill="#FFFDF8", outline="#E3D6C4", width=2,
    )
    # a couple of fold lines for texture
    draw.line([(cx - 60, paper_top_y), (tie_point[0] - 6, tie_point[1])], fill="#EDE2D2", width=2)
    draw.line([(cx + 60, paper_top_y), (tie_point[0] + 6, tie_point[1])], fill="#EDE2D2", width=2)

    # --- Build a tightly-packed bloom layout using a phyllotaxis spiral ---
    draws_per_flower = [min(f["quantity"], 6) for f in flowers[:8]]
    total_draws = max(sum(draws_per_flower), 1)
    golden_angle = math.radians(137.5)
    max_radius = 130

    positions = []
    for i in range(total_draws):
        angle = i * golden_angle
        radius = max_radius * math.sqrt(i / total_draws)
        x = cluster_center[0] + radius * math.cos(angle)
        y = cluster_center[1] + radius * math.sin(angle) * 0.65  # flatten vertically
        positions.append((x, y))

    random.seed(total_draws * 7 + len(flowers))

    # --- Stems: a few lines fanning from the tie point up to outer blooms ---
    outer_positions = positions[-min(6, len(positions)):] if positions else []
    for px, py in outer_positions:
        draw.line([tie_point, (px, py + 10)], fill="#7A9A7E", width=3)

    # --- Greenery behind the blooms ---
    for _ in range(10):
        gx = cluster_center[0] + random.randint(-150, 150)
        gy = cluster_center[1] + random.randint(-90, 110)
        leaf_w, leaf_h = random.randint(18, 30), random.randint(8, 14)
        draw.ellipse([gx - leaf_w, gy - leaf_h, gx + leaf_w, gy + leaf_h], fill="#8AAE8C")

    # --- Blooms, colored and grouped per flower type ---
    idx = 0
    for f_i, count in enumerate(draws_per_flower):
        color = colors[f_i % len(colors)]
        for _ in range(count):
            if idx >= len(positions):
                break
            px, py = positions[idx]
            px += random.randint(-6, 6)
            py += random.randint(-6, 6)
            r = 24
            draw.ellipse([px - r, py - r, px + r, py + r], fill=color, outline="#00000010")
            # small center to read as a flower, not a plain dot
            draw.ellipse([px - 6, py - 6, px + 6, py + 6], fill="#FCE9A8")
            idx += 1

    # --- Ribbon bow at the tie point ---
    ribbon_color = colors[0]
    draw.polygon(
        [(cx - 30, tie_point[1] - 6), (cx, tie_point[1] + 12), (cx - 4, tie_point[1] - 22)],
        fill=ribbon_color,
    )
    draw.polygon(
        [(cx + 30, tie_point[1] - 6), (cx, tie_point[1] + 12), (cx + 4, tie_point[1] - 22)],
        fill=ribbon_color,
    )
    draw.ellipse([cx - 10, tie_point[1] - 14, cx + 10, tie_point[1] + 6], fill=ribbon_color)

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()

def _generate_openai_image(occasion, style, color_palette, flowers):
    import openai

    flower_list = ", ".join(f"{f['quantity']} {f['name']}" for f in flowers)
    prompt = (
        f"Professional florist photography of a hand-tied bouquet for a {occasion.lower()} occasion, "
        f"{style.lower()} style, color palette: {color_palette}. Contains {flower_list}. "
        f"Natural light, wrapped in kraft paper, clean neutral background."
    )
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    response = client.images.generate(model="dall-e-3", prompt=prompt, size="1024x1024", n=1)
    image_url = response.data[0].url

    import urllib.request
    with urllib.request.urlopen(image_url, timeout=20) as resp:
        return resp.read()

def _generate_gemini_image(occasion, style, color_palette, flowers):
    from google import genai
    from google.genai import types

    flower_list = ", ".join(f"{f['quantity']} {f['name']}" for f in flowers)
    prompt = (
        f"A professional florist photograph of a hand-tied bouquet for a {occasion.lower()} occasion, "
        f"{style.lower()} style, color palette: {color_palette}. Contains {flower_list}. "
        f"Natural lighting, wrapped in kraft paper, clean neutral background, realistic photography."
    )

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    response = client.models.generate_content(
        model="gemini-2.5-flash-image-preview",
        contents=prompt,
    )

    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            return part.inline_data.data  # raw image bytes

    raise ValueError("Gemini response contained no image data")

def generate_bouquet_image(occasion, style, color_palette, flowers):
    """
    Returns raw image bytes, or None if generation isn't possible/fails.
    Never raises — image generation is a nice-to-have, not required for
    a recommendation to succeed.
    """
    try:
        if settings.AI_IMAGE_PROVIDER == "gemini" and settings.GEMINI_API_KEY:
            return _generate_gemini_image(occasion, style, color_palette, flowers)
        if settings.AI_IMAGE_PROVIDER == "openai" and settings.OPENAI_API_KEY:
            return _generate_openai_image(occasion, style, color_palette, flowers)
        return _draw_mock_bouquet(flowers, color_palette)
    except Exception as exc:
        logger.warning("Bouquet image generation failed: %s", exc)
        return None

def save_recommendation_image(recommendation, image_bytes):
    if not image_bytes:
        return
    filename = f"recommendation_{recommendation.pk}.png"
    recommendation.generated_image.save(filename, ContentFile(image_bytes), save=True)