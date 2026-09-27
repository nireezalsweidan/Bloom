import io
import logging
import math
import random

from django.conf import settings
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)


# ============================================================
# MOCK BOUQUET COLORS
# ============================================================

PALETTE_COLORS = {
    "Soft Pastels & Blush Rose": [
        "#F4DCD6",
        "#E8A3B5",
        "#FFFFFF",
        "#C6E7D5",
    ],
    "Sunset Terracotta & Warm Peach": [
        "#C97D60",
        "#F6C3A5",
        "#E8A3B5",
    ],
    "Pure Ivory & Botanical Sage": [
        "#FCFAF7",
        "#ADCEBC",
        "#476556",
    ],
    "Vibrant Jewel & Plum Velour": [
        "#58201C",
        "#75648A",
        "#3A0A08",
    ],
}

DEFAULT_COLORS = [
    "#E8A3B5",
    "#F4DCD6",
    "#ADCEBC",
    "#FFFFFF",
]


# ============================================================
# MOCK / FALLBACK BOUQUET
# ============================================================

def _draw_mock_bouquet(flowers, color_palette):
    """
    Creates a simple illustrated bouquet as a fallback if
    the external image provider fails.
    """

    from PIL import Image, ImageDraw

    size = 640

    img = Image.new(
        "RGB",
        (size, size),
        "#FAF6F0",
    )

    draw = ImageDraw.Draw(img)

    colors = PALETTE_COLORS.get(
        color_palette,
        DEFAULT_COLORS,
    )

    cx = size // 2

    tie_point = (
        cx,
        size - 60,
    )

    cluster_center = (
        cx,
        230,
    )

    paper_top_y = 300

    # --------------------------------------------------------
    # Wrapping paper
    # --------------------------------------------------------

    draw.polygon(
        [
            (tie_point[0] - 12, tie_point[1] + 10),
            (cx - 170, paper_top_y),
            (cx + 170, paper_top_y),
            (tie_point[0] + 12, tie_point[1] + 10),
        ],
        fill="#FFFDF8",
        outline="#E3D6C4",
        width=2,
    )

    draw.line(
        [
            (cx - 60, paper_top_y),
            (tie_point[0] - 6, tie_point[1]),
        ],
        fill="#EDE2D2",
        width=2,
    )

    draw.line(
        [
            (cx + 60, paper_top_y),
            (tie_point[0] + 6, tie_point[1]),
        ],
        fill="#EDE2D2",
        width=2,
    )

    # --------------------------------------------------------
    # Bloom positions
    # --------------------------------------------------------

    draws_per_flower = [
        min(f["quantity"], 6)
        for f in flowers[:8]
    ]

    total_draws = max(
        sum(draws_per_flower),
        1,
    )

    golden_angle = math.radians(137.5)
    max_radius = 130

    positions = []

    for i in range(total_draws):

        angle = i * golden_angle

        radius = (
            max_radius
            * math.sqrt(i / total_draws)
        )

        x = (
            cluster_center[0]
            + radius * math.cos(angle)
        )

        y = (
            cluster_center[1]
            + radius
            * math.sin(angle)
            * 0.65
        )

        positions.append(
            (x, y)
        )

    random.seed(
        total_draws * 7
        + len(flowers)
    )

    # --------------------------------------------------------
    # Stems
    # --------------------------------------------------------

    outer_positions = positions[
        -min(6, len(positions)):
    ]

    for px, py in outer_positions:

        draw.line(
            [
                tie_point,
                (px, py + 10),
            ],
            fill="#7A9A7E",
            width=3,
        )

    # --------------------------------------------------------
    # Greenery
    # --------------------------------------------------------

    for _ in range(10):

        gx = (
            cluster_center[0]
            + random.randint(-150, 150)
        )

        gy = (
            cluster_center[1]
            + random.randint(-90, 110)
        )

        leaf_w = random.randint(18, 30)
        leaf_h = random.randint(8, 14)

        draw.ellipse(
            [
                gx - leaf_w,
                gy - leaf_h,
                gx + leaf_w,
                gy + leaf_h,
            ],
            fill="#8AAE8C",
        )

    # --------------------------------------------------------
    # Flowers
    # --------------------------------------------------------

    idx = 0

    for f_i, count in enumerate(
        draws_per_flower
    ):

        color = colors[
            f_i % len(colors)
        ]

        for _ in range(count):

            if idx >= len(positions):
                break

            px, py = positions[idx]

            px += random.randint(-6, 6)
            py += random.randint(-6, 6)

            r = 24

            draw.ellipse(
                [
                    px - r,
                    py - r,
                    px + r,
                    py + r,
                ],
                fill=color,
            )

            draw.ellipse(
                [
                    px - 6,
                    py - 6,
                    px + 6,
                    py + 6,
                ],
                fill="#FCE9A8",
            )

            idx += 1

    # --------------------------------------------------------
    # Ribbon
    # --------------------------------------------------------

    ribbon_color = colors[0]

    draw.polygon(
        [
            (
                cx - 30,
                tie_point[1] - 6,
            ),
            (
                cx,
                tie_point[1] + 12,
            ),
            (
                cx - 4,
                tie_point[1] - 22,
            ),
        ],
        fill=ribbon_color,
    )

    draw.polygon(
        [
            (
                cx + 30,
                tie_point[1] - 6,
            ),
            (
                cx,
                tie_point[1] + 12,
            ),
            (
                cx + 4,
                tie_point[1] - 22,
            ),
        ],
        fill=ribbon_color,
    )

    draw.ellipse(
        [
            cx - 10,
            tie_point[1] - 14,
            cx + 10,
            tie_point[1] + 6,
        ],
        fill=ribbon_color,
    )

    # --------------------------------------------------------
    # Return PNG bytes
    # --------------------------------------------------------

    buffer = io.BytesIO()

    img.save(
        buffer,
        format="PNG",
    )

    return buffer.getvalue()


# ============================================================
# HUGGING FACE / FLUX
# ============================================================

def _generate_huggingface_image(
    occasion,
    style,
    color_palette,
    flowers,
):
    """
    Generates the actual bouquet image using Hugging Face
    Inference API + fal-ai + FLUX.1-dev.
    """

    from huggingface_hub import InferenceClient

    flower_list = ", ".join(
        f"{f['quantity']} {f['name']}"
        for f in flowers
    )

    prompt = (
        "Professional florist photography of a beautiful "
        "hand-tied bouquet. "

        f"The bouquet is designed for a "
        f"{occasion.lower()} occasion. "

        f"Style: {style.lower()}. "

        f"Color palette: {color_palette}. "

        f"The bouquet contains: {flower_list}. "

        "Elegant balanced floral arrangement, "
        "natural soft lighting, "
        "realistic flowers, "
        "fresh stems, "
        "wrapped in elegant kraft paper, "
        "clean neutral botanical background, "
        "high-end florist photography, "
        "photorealistic, "
        "high detail."
    )

    logger.info(
        "Generating bouquet image with Hugging Face..."
    )

    client = InferenceClient(
        provider="fal-ai",
        api_key=settings.HF_TOKEN,
    )

    # IMPORTANT:
    # This is the same model that worked in your test.
    image = client.text_to_image(
        prompt,
        model="black-forest-labs/FLUX.1-dev",
    )

    logger.info(
        "Hugging Face bouquet image generated successfully."
    )

    buffer = io.BytesIO()

    image.save(
        buffer,
        format="PNG",
    )

    return buffer.getvalue()


# ============================================================
# GEMINI IMAGE
# ============================================================

def _generate_gemini_image(
    occasion,
    style,
    color_palette,
    flowers,
):

    from google import genai

    flower_list = ", ".join(
        f"{f['quantity']} {f['name']}"
        for f in flowers
    )

    prompt = (
        "A professional florist photograph "
        "of a beautiful hand-tied bouquet. "

        f"Occasion: {occasion}. "
        f"Style: {style}. "
        f"Color palette: {color_palette}. "

        f"Flowers: {flower_list}. "

        "Natural lighting, "
        "wrapped in kraft paper, "
        "clean neutral background, "
        "realistic photography, "
        "high detail."
    )

    client = genai.Client(
        api_key=settings.GEMINI_API_KEY
    )

    response = client.models.generate_content(
        model="gemini-3.1-flash-image",
        contents=prompt,
    )

    for part in response.candidates[0].content.parts:

        if part.inline_data is not None:
            return part.inline_data.data

    raise ValueError(
        "Gemini response contained no image data."
    )


# ============================================================
# OPENAI IMAGE
# ============================================================

def _generate_openai_image(
    occasion,
    style,
    color_palette,
    flowers,
):

    import openai
    import urllib.request

    flower_list = ", ".join(
        f"{f['quantity']} {f['name']}"
        for f in flowers
    )

    prompt = (
        "Professional florist photography of "
        "a beautiful hand-tied bouquet. "

        f"Occasion: {occasion}. "
        f"Style: {style}. "
        f"Color palette: {color_palette}. "

        f"Flowers: {flower_list}. "

        "Natural light, "
        "wrapped in kraft paper, "
        "clean neutral background, "
        "realistic photography."
    )

    client = openai.OpenAI(
        api_key=settings.OPENAI_API_KEY
    )

    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        n=1,
    )

    image_url = response.data[0].url

    with urllib.request.urlopen(
        image_url,
        timeout=20,
    ) as resp:

        return resp.read()


# ============================================================
# MAIN IMAGE GENERATOR
# ============================================================

def generate_bouquet_image(
    occasion,
    style,
    color_palette,
    flowers,
):
    """
    Selects the configured image provider.

    Hugging Face is currently the preferred provider.
    If the provider fails, we fall back to the local
    illustrative bouquet so recommendation generation
    does not completely fail.
    """

    provider = getattr(
        settings,
        "AI_IMAGE_PROVIDER",
        "huggingface",
    )

    logger.info(
        "AI image provider: %s",
        provider,
    )

    try:

        if (
            provider == "huggingface"
            and getattr(
                settings,
                "HF_TOKEN",
                "",
            )
        ):

            return _generate_huggingface_image(
                occasion,
                style,
                color_palette,
                flowers,
            )

        if (
            provider == "gemini"
            and getattr(
                settings,
                "GEMINI_API_KEY",
                "",
            )
        ):

            return _generate_gemini_image(
                occasion,
                style,
                color_palette,
                flowers,
            )

        if (
            provider == "openai"
            and getattr(
                settings,
                "OPENAI_API_KEY",
                "",
            )
        ):

            return _generate_openai_image(
                occasion,
                style,
                color_palette,
                flowers,
            )

        logger.warning(
            "No valid image provider configured: %s",
            provider,
        )

    except Exception as exc:

        logger.exception(
            "AI image generation failed: %s",
            exc,
        )

        print("=" * 60)
        print("AI IMAGE GENERATION FAILED")
        print("Provider:", provider)
        print("Error type:", type(exc).__name__)
        print("Error:", str(exc))
        print("=" * 60)

    # --------------------------------------------------------
    # Local fallback
    # --------------------------------------------------------

    logger.warning(
        "Using local mock bouquet fallback."
    )

    return _draw_mock_bouquet(
        flowers,
        color_palette,
    )


# ============================================================
# SAVE IMAGE TO RECOMMENDATION
# ============================================================

def save_recommendation_image(
    recommendation,
    image_bytes,
):
    """
    Saves generated PNG bytes into the recommendation's
    ImageField.
    """

    if not image_bytes:
        logger.warning(
            "No image bytes received for recommendation %s",
            recommendation.pk,
        )
        return

    filename = (
        f"recommendation_{recommendation.pk}.png"
    )

    recommendation.generated_image.save(
        filename,
        ContentFile(image_bytes),
        save=True,
    )

    logger.info(
        "Saved generated image for recommendation %s",
        recommendation.pk,
    )