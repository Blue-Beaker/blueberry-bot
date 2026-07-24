from io import BytesIO
from typing import IO
from PIL import Image

color_codes = {
    0x000000: "§0",
    0x0000AA: "§1",
    0x00AA00: "§2",
    0x00AAAA: "§3",
    0xAA0000: "§4",
    0xAA00AA: "§5",
    0xFFAA00: "§6",
    0xAAAAAA: "§7",
    0x555555: "§8",
    0x5555FF: "§9",
    0x55FF55: "§a",
    0x55FFFF: "§b",
    0xFF5555: "§c",
    0xFF55FF: "§d",
    0xFFFF55: "§e",
    0xFFFFFF: "§f",
}

palette_rgb = [(color>>16, (color>>8)&255, color&255) for color in color_codes.keys()]

def create_palette(rgb_colors):
    """
    将自定义 RGB 颜色列表转换为 Pillow 可用的调色板列表（长度 768）。
    rgb_colors: 列表，每个元素是 (R, G, B) 元组
    """
    palette = []
    # 先添加你定义的颜色
    for color in rgb_colors:
        palette.extend(color)  # 将 (R,G,B) 拆开成三个数值
    # 如果不足 256 种颜色，用第一种颜色（或黑色）填充剩余位置
    while len(palette) < 768:
        palette.extend(rgb_colors[0] if rgb_colors else (0,0,0))
    # 如果超过 256 种颜色（一般不会），截取前 768 个
    return palette[:768]

def image_to_mc_text(image_content:str|IO[bytes], max_width=100, max_height=22, char_ratio=5):
    # 读取图片
    image = Image.open(image_content)
    # 将图片转换为RGB模式
    image = image.convert("RGB")
    # 获取图片的宽度和高度
    width, height = image.size
    
    # max_width = 128 # 横向字符数
    # max_height = 22 # 纵向行数
    
    # char_ratio = 4 # 字符比例
    
    ratio = image.width*char_ratio / image.height
    
    if ratio > max_width / max_height:
        image = image.resize((max_width, int(height * max_width / width / char_ratio)))
    else:
        image = image.resize((int(width * char_ratio * max_height / height), max_height))
        
    print(f"Resized image to {image.size}")
    
    # 创建调色板图像
    palette_img = Image.new('P', (1, 1))
    # 将 RGB 调色板展平为一维列表
    flat_palette = create_palette(palette_rgb)
    palette_img.putpalette(flat_palette)
    
    # 应用调色板进行量化
    quantized_image = image.quantize(palette=palette_img)
    # quantized_image.show()
    text=""
    
    codes = [*color_codes.values()]
    
    imagedata = list(quantized_image.getdata()) # type: ignore
    
    for i in range(len(imagedata)):
        pixel = imagedata[i]
        assert isinstance(pixel,int)
        text += (codes[pixel]+"❘")
        if(i+1)%quantized_image.width==0:
            text += "\n"
        
    return text+color_codes[0xFFFFFF]

if __name__ == "__main__":
    print(image_to_mc_text("xiaozu_bot/plugins/zhua/data/神金比心卒.png"))