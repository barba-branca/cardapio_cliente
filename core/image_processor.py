# core/image_processor.py

import pytesseract
import cv2  # Importamos o OpenCV
import numpy as np
import json
import uuid

# --- CONFIGURAÇÃO DO TESSERACT (já está funcionando) ---
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
tessdata_dir_config = r'--tessdata-dir "C:\Program Files\Tesseract-OCR\tessdata"'
# ---------------------------------------------------------

def process_menu_for_template(image_path: str, job_id: str):
    """
    Processa a imagem de um cardápio para:
    1. Criar um template sem os textos.
    2. Salvar os metadados (posição, tamanho, cor) dos textos em um JSON.
    """
    # Usamos o OpenCV para ler a imagem, pois ele é melhor para manipulação
    img = cv2.imread(image_path)
    # Criamos uma cópia da imagem que será nosso template
    template_img = img.copy()

    # Usamos image_to_data para pegar as caixas delimitadoras (bounding boxes)
    data = pytesseract.image_to_data(img, lang='por', config=tessdata_dir_config, output_type=pytesseract.Output.DICT)
    
    text_metadata = []
    n_boxes = len(data['level'])

    for i in range(n_boxes):
        # Filtramos por uma confiança mínima para evitar ruído
        if int(data['conf'][i]) > 60:
            (x, y, w, h) = (data['left'][i], data['top'][i], data['width'][i], data['height'][i])
            
            # --- Extração de Metadados ---
            # Posição e Tamanho
            box = [x, y, w, h]
            
            # Cor: Uma heurística simples - pegamos a cor média dos pixels na borda da caixa
            # Isso geralmente funciona bem para texto sobre fundos sólidos
            # Pegamos uma pequena fatia de pixels para evitar pegar muito do fundo
            if y > 0 and x > 0: # Evita erros em caixas na borda da imagem
                text_color_area = img[y:y+1, x:x+w]
                # A cor em OpenCV é BGR, convertemos para RGB para ser mais padrão
                avg_color_bgr = np.mean(text_color_area, axis=(0, 1))
                avg_color_rgb = (int(avg_color_bgr[2]), int(avg_color_bgr[1]), int(avg_color_bgr[0]))
            else:
                avg_color_rgb = (0, 0, 0) # Cor padrão (preto)

            text_info = {
                "id": str(uuid.uuid4()), # ID único para cada bloco de texto
                "original_text": data['text'][i],
                "box": box,
                "approx_font_size": h,  # A altura da caixa é um ótimo substituto para o tamanho da fonte
                "approx_color_rgb": avg_color_rgb
            }
            text_metadata.append(text_info)

            # --- Remoção do Texto para criar o Template ---
            # Usamos "inpainting" do OpenCV, que preenche a área de forma inteligente
            # É muito melhor que apenas desenhar uma caixa branca por cima.
            # Criamos uma máscara preta com um retângulo branco onde está o texto
            mask = np.zeros(img.shape[:2], dtype=np.uint8)
            cv2.rectangle(mask, (x, y), (x + w, y + h), 255, -1)
            # Aplicamos o inpainting
            template_img = cv2.inpaint(template_img, mask, inpaintRadius=5, flags=cv2.INPAINT_TELEA)

    # --- Salvar os Resultados ---
    template_path = f"storage/templates/{job_id}_template.png"
    metadata_path = f"storage/metadata/{job_id}_metadata.json"
    
    cv2.imwrite(template_path, template_img)
    
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump({"text_areas": text_metadata}, f, indent=4, ensure_ascii=False)
        
    return template_path, metadata_path