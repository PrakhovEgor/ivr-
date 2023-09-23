from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

I = Image.open("../static/Абрикос маньчжурский.jpg")

Im = ImageDraw.Draw(I)
h, w = I.size

mf = ImageFont.truetype("arial.ttf", size=36)


Im.text((w // 20, h // 2), "Абрикос маньчжурский", fill=(0, 0, 0), font=mf)

# I.save("mm.png")
I.show()
print(I.size)