from PIL import Image, ImageDraw, ImageFont
import numpy as np
import cv2


def wrap_text_by_pixel(draw, text, font, max_width):
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = f"{current_line} {word}".strip()
        width = draw.textlength(test_line, font=font)
        if width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines


def draw_wrapped_custom_font_text_pil(
    cv2_img, text, box, font_path, font_size=40, color=(255, 0, 0), padding=10
):
    x, y, w, h = box
    pil_img = Image.fromarray(cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_img)
    font = ImageFont.truetype(font_path, font_size)

    lines = wrap_text_by_pixel(draw, text, font, w - 2 * padding)

    ascent, descent = font.getmetrics()
    line_height = ascent + descent + 4

    current_y = y + padding

    for line in lines:
        if current_y + line_height > y + h:
            break
        current_x = x + padding  # 👈 LEFT JUSTIFY HERE
        draw.text((current_x, current_y), line, font=font, fill=color)
        current_y += line_height

    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)


image_path = "./base.png"
font_path = "./JetBrainsMono/JetBrainsMonoNerdFont-Italic.ttf"  # Use full path to your .ttf file
content = 'The First Computer Bug: The term "bug" in computer science originated from a real insect, a moth, found causing issues in a computer in 1947'
reference = "https://medium.com/"
title = "\ueb80 Tech Facts"
title_box = (150, 250, 750, 200)
content_box = (150, 510, 750, 470)
reference_box = (125, 1175, 775, 55)


image = cv2.imread(image_path)
image = draw_wrapped_custom_font_text_pil(
    image, title, title_box, font_path, font_size=100
)
image = draw_wrapped_custom_font_text_pil(
    image, content, content_box, font_path, font_size=40
)
image = draw_wrapped_custom_font_text_pil(
    image, reference, reference_box, font_path, font_size=30
)

cv2.imshow("PIL Text Render", image)
cv2.waitKey(0)
cv2.destroyAllWindows()
