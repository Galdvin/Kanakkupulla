from PIL import Image, ImageDraw
from pathlib import Path

icon_dir = Path("assets/icons")
icon_dir.mkdir(parents=True, exist_ok=True)

size = (256, 256)
img = Image.new("RGBA", size, color=(15, 23, 42, 255))
draw = ImageDraw.Draw(img)

# Outer circle
draw.ellipse([(16, 16), (240, 240)], fill=(2, 132, 199), outline=(56, 189, 248), width=6)
# Inner circle
draw.ellipse([(36, 36), (220, 220)], fill=(15, 23, 42))

# Draw 'K'
draw.rectangle([(80, 70), (105, 186)], fill=(56, 189, 248))
draw.polygon([(105, 128), (170, 70), (195, 70), (120, 138)], fill=(56, 189, 248))
draw.polygon([(115, 128), (175, 186), (200, 186), (135, 124)], fill=(16, 185, 129))

png_path = icon_dir / "app_icon.png"
ico_path = icon_dir / "app_icon.ico"
img.save(png_path)
img.save(ico_path, format="ICO", sizes=[(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)])
print("Icons created successfully at", ico_path)
