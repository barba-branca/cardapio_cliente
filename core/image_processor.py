# core/image_processor.py (VERSÃO FINAL HÍBRIDA: IA + OPENCV + TESSERACT)

import base64
import json
import ollama
import asyncio
import httpx
import traceback
import os
import requests
from PIL import Image, ImageDraw, ImageFont
import io
import cv2
import numpy as np
import pytesseract

# --- CONFIGURAÇÕES E CONSTANTES ---
# ... (Mantenha as configurações de chave, diretórios, etc.) ...
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
GOOGLE_FONTS_API_KEY = "AIzaSyBPfj_t8GHPJSnB_vh-HpKzITMTOREV8W4"
FONTS_DIR = "fonts"
os.makedirs(FONTS_DIR, exist_ok=True)
AVAILABLE_FONTS = [f for f in os.listdir(FONTS_DIR) if f.lower().endswith(('.ttf', '.otf'))] if os.path.exists(FONTS_DIR) else []

# --- FUNÇÃO DE RESOLUÇÃO DE FONTES (Mantenha a sua) ---
def resolve_font(font_name: str) -> str:
    # ... (Sua função resolve_font que já funciona) ...
    return "ARIAL.TTF" # Placeholder

# --- FUNÇÃO PRINCIPAL DE ANÁLISE HÍBRIDA ---
async def get_text_properties_from_image(image_stream):
    image_bytes = image_stream.read()
    
    # Carrega a imagem uma vez para uso em várias funções
    nparr = np.frombuffer(image_bytes, np.uint8)
    img_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    img_pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img_width, img_height = img_pil.size

    # --- ETAPA 1: ANÁLISE DE ESTILO COM IA ---
    print("Iniciando análise de ESTILO com IA (pode demorar)...")
    style_prompt = "Analise o ESTILO desta imagem de cardápio. NÃO leia o texto. Apenas identifique as principais regiões (ex: 'título', 'lista_de_itens') e, para cada uma, descreva a 'font_name' e a 'color_rgb'. Retorne um objeto JSON com as regiões como chaves."
    
    try:
        client = ollama.AsyncClient(timeout=300.0)
        response = await client.chat(
            model='llava',
            messages=[{'role': 'user', 'content': style_prompt, 'images': [base64.b64encode(image_bytes).decode('utf-8')]}],
            format="json", options={"temperature": 0.0}
        )
        style_data = json.loads(response['message']['content'])
        print(f"Estilos detectados pela IA: {style_data}")
    except Exception as e:
        print(f"AVISO: Análise de estilo com IA falhou: {e}. Usando estilos padrão.")
        # Define estilos padrão se a IA falhar
        style_data = {
            'titulo': {'font_name': 'Arial Bold', 'color_rgb': [139, 0, 0]},
            'lista_de_itens': {'font_name': 'Arial', 'color_rgb': [60, 60, 60]}
        }

    # --- ETAPA 2: DETECÇÃO E LEITURA DE TEXTO COM OPENCV E TESSERACT ---
    print("Iniciando detecção e leitura de texto com Tesseract...")
    # Usa o image_to_data do Tesseract, que é excelente para encontrar todos os blocos de texto
    ocr_data = pytesseract.image_to_data(img_cv, lang='por', output_type=pytesseract.Output.DICT)
    
    final_data = []
    num_boxes = len(ocr_data['level'])
    for i in range(num_boxes):
        text = ocr_data['text'][i].strip()
        confidence = int(ocr_data['conf'][i])
        
        # Filtra blocos vazios ou com baixa confiança
        if text and confidence > 50:
            # Pega as coordenadas em pixels diretamente do Tesseract
            x, y, w, h = ocr_data['left'][i], ocr_data['top'][i], ocr_data['width'][i], ocr_data['height'][i]
            
            # --- ETAPA 3: FUSÃO INTELIGENTE ---
            # Determina o estilo a ser aplicado com base na posição do texto
            # (Exemplo simples: textos no topo são títulos, o resto é item de lista)
            if y < img_height * 0.3: # Se estiver nos 30% superiores da imagem
                applied_style = style_data.get('titulo', style_data.get('lista_de_itens'))
            else:
                applied_style = style_data.get('lista_de_itens')
            
            font_name_suggestion = applied_style.get('font_name', 'Arial')
            color_rgb = applied_style.get('color_rgb', [0, 0, 0])

            # Cria o bloco de JSON final
            block = {
                "text": text,
                "box_pixels": [x, y, w, h],
                "font_size": h, # Usa a altura detectada pelo Tesseract como tamanho
                "font_name_suggestion": font_name_suggestion,
                "color_rgb": color_rgb,
                "font_file": resolve_font(font_name_suggestion) # Resolve a fonte
            }
            final_data.append(block)

    print(f"Processamento Híbrido concluído. {len(final_data)} blocos de texto encontrados.")
    return final_data