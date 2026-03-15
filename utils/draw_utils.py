from PIL import ImageDraw, ImageFont

def draw_single_text(draw, text, font, position, text_color, outline_color, outline_width=2, align="center"):
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    x, y = position
    if align == "center":
        x = x - text_width / 2
    elif align == "right":
        x = x - text_width

    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx != 0 or dy != 0:
                draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
    draw.text((x, y), text, font=font, fill=text_color)

def wrap_text(text, max_len=12):
    return '\n'.join([text[i:i+max_len] for i in range(0, len(text), max_len)])

def draw_multiline_text(draw, text, font, position, text_color, outline_color, outline_width=2, align="center", line_spacing=10):
    lines = text.split('\n')
    x, base_y = position
    start_y = base_y - (len(lines) - 1) * (font.size + line_spacing)
    
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        line_x = x
        if align == "center": line_x -= text_width / 2
        elif align == "right": line_x -= text_width
        
        line_y = start_y + i * (font.size + line_spacing)
        for dx in range(-outline_width, outline_width + 1):
            for dy in range(-outline_width, outline_width + 1):
                if dx != 0 or dy != 0: 
                    draw.text((line_x + dx, line_y + dy), line, font=font, fill=outline_color)
        draw.text((line_x, line_y), line, font=font, fill=text_color)