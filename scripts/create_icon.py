#!/usr/bin/env python3
"""
Gera o ícone do OptiScaler Center
Cria um PNG 256x256 com design de controle de videogame
"""

try:
    from PIL import Image, ImageDraw
except ImportError:
    print("Erro: Pillow não instalado. Execute: pip install Pillow")
    exit(1)

def create_icon(output_path='resources/icons/optiscaler-center.png', size=256):
    """Cria o ícone do OptiScaler Center"""
    
    # Criar imagem com fundo transparente
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Cores
    bg_color = '#1b2838'      # Fundo escuro (Steam-like)
    border_color = '#5c7e10'  # Verde escuro
    button_color = '#76b900'  # Verde claro (accent)
    
    # Corpo do controle (retângulo arredondado)
    margin = size * 0.1
    body_rect = [
        (margin, size * 0.35),
        (size - margin, size * 0.75)
    ]
    draw.rounded_rectangle(body_rect, radius=size * 0.1, fill=bg_color, outline=border_color, width=3)
    
    # Grips laterais (L/R)
    grip_width = size * 0.15
    grip_height = size * 0.1
    # Grip esquerdo
    draw.rounded_rectangle(
        [(margin + size * 0.05, size * 0.25), (margin + grip_width, size * 0.25 + grip_height)],
        radius=size * 0.02, fill=bg_color, outline=border_color, width=2
    )
    # Grip direito
    draw.rounded_rectangle(
        [(size - margin - grip_width, size * 0.25), (size - margin - size * 0.05, size * 0.25 + grip_height)],
        radius=size * 0.02, fill=bg_color, outline=border_color, width=2
    )
    
    # D-pad (esquerda) - cruz direcional
    dpad_x = size * 0.3
    dpad_y = size * 0.52
    dpad_size = size * 0.08
    dpad_thickness = size * 0.025
    
    # Horizontal
    draw.rounded_rectangle(
        [(dpad_x - dpad_size, dpad_y - dpad_thickness),
         (dpad_x + dpad_size, dpad_y + dpad_thickness)],
        radius=dpad_thickness * 0.5, fill=button_color
    )
    # Vertical  
    draw.rounded_rectangle(
        [(dpad_x - dpad_thickness, dpad_y - dpad_size),
         (dpad_x + dpad_thickness, dpad_y + dpad_size)],
        radius=dpad_thickness * 0.5, fill=button_color
    )
    
    # Botões ABXY (direita)
    button_x = size * 0.7
    button_y = size * 0.52
    button_radius = size * 0.03
    button_spacing = size * 0.07
    
    # Y (cima)
    draw.ellipse(
        [(button_x - button_radius, button_y - button_spacing - button_radius),
         (button_x + button_radius, button_y - button_spacing + button_radius)],
        fill=button_color
    )
    # B (direita)
    draw.ellipse(
        [(button_x + button_spacing - button_radius, button_y - button_radius),
         (button_x + button_spacing + button_radius, button_y + button_radius)],
        fill=button_color
    )
    # A (baixo)
    draw.ellipse(
        [(button_x - button_radius, button_y + button_spacing - button_radius),
         (button_x + button_radius, button_y + button_spacing + button_radius)],
        fill=button_color
    )
    # X (esquerda)
    draw.ellipse(
        [(button_x - button_spacing - button_radius, button_y - button_radius),
         (button_x - button_spacing + button_radius, button_y + button_radius)],
        fill=button_color
    )
    
    # Salvar
    import os
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, 'PNG')
    print(f"✅ Ícone criado: {output_path}")
    
    # Criar versões adicionais
    for extra_size in [48, 128, 512]:
        extra_img = img.resize((extra_size, extra_size), Image.Resampling.LANCZOS)
        extra_path = output_path.replace('.png', f'-{extra_size}.png')
        extra_img.save(extra_path, 'PNG')
        print(f"✅ Ícone {extra_size}x{extra_size} criado: {extra_path}")

if __name__ == '__main__':
    import sys
    output = sys.argv[1] if len(sys.argv) > 1 else 'resources/icons/optiscaler-center.png'
    create_icon(output)
    print("\n🎉 Ícones criados com sucesso!")
