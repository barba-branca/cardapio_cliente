# main.py

import os
import uuid
import io
from fastapi import FastAPI, File, UploadFile, Response, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import google.generativeai as genai

# --- Configuração Inicial ---
app = FastAPI(title="CardapioAI - Real Image Gen")
origins = ["*"]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
GOOGLE_API_KEY = "AIzaSyDXAHKIxNmUJW9WG93C9Hq88xFccWS1TMA"
genai.configure(api_key=GOOGLE_API_KEY)
os.makedirs("storage/uploads", exist_ok=True)
os.makedirs("storage/results", exist_ok=True)
os.makedirs("fonts", exist_ok=True)

# --- Endpoints da API ---
@app.get("/verversao")
async def get_version(): return Response(content="11.0-final-image-gen", media_type="text/plain")

@app.post("/api/menu/render")
async def render_menu(excel: UploadFile = File(...), original_menu: UploadFile = File(...)):
    print(f"Iniciando renderização com geração de imagem real...")
    try:
        df = pd.read_excel(excel.file)
        reference_image = Image.open(original_menu.file).convert('RGB')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao ler os arquivos de entrada: {e}")

    try:
        # --- PROMPT ATUALIZADO PARA FORÇAR GERAÇÃO DE IMAGEM ---
        print("Pedindo para a IA gerar a imagem de fundo...")
        
        # Usamos o modelo 'pro' pois ele tem melhor integração com as ferramentas de geração de imagem
        model = genai.GenerativeModel('gemini-1.5-pro') 

        prompt = f"""
        Analise a imagem de referência que enviei.
        Crie uma única imagem de fundo (background) para um cardápio, com proporção 2:3 (retrato).
        O estilo, as cores e as texturas devem ser inspirados na imagem de referência.
        O fundo deve ser bonito, profissional e NÃO PODE CONTER NENHUM TEXTO, PALAVRAS OU LOGOS.
        """
        
        # Faz a chamada real para a IA
        response = model.generate_content([prompt, reference_image])

        # Extrai os dados da imagem da resposta da IA
        generated_image_part = None
        for part in response.candidates[0].content.parts:
            # A API pode retornar em diferentes formatos de imagem
            if part.mime_type.startswith("image/"): 
                generated_image_part = part
                break
        
        if not generated_image_part:
            raise Exception("A IA não retornou uma imagem. Resposta recebida: " + response.text)

        image_data = generated_image_part.inline_data.data
        background_image = Image.open(io.BytesIO(image_data)).resize((800, 1200))
        draw = ImageDraw.Draw(background_image)
        print("Fundo real gerado pela IA recebido com sucesso.")

        # --- Renderização do Texto (sem alterações) ---
        y_pos = 50
        for index, row in df.iterrows():
            text, font_family, font_size, color, pos_x, pos_y = (
                str(row.get('text', '')), str(row.get('font_family', 'arial')).lower().strip(),
                int(row.get('font_size', 20)), str(row.get('color', '#000000')),
                int(row.get('position_x', 100)), int(row.get('position_y', y_pos))
            )
            if not text.strip():
                if 'position_y' not in row: y_pos += font_size // 2
                continue
            font_path = os.path.join("fonts", f"{font_family}.ttf")
            try:
                font = ImageFont.truetype(font_path, font_size)
            except IOError:
                font = ImageFont.load_default()
            draw.text((pos_x, pos_y), text, font=font, fill=color)
            if 'position_y' not in row: y_pos += int(font_size * 1.5)

        # --- Salva e Retorna ---
        job_id = str(uuid.uuid4())
        result_path = f"storage/results/{job_id}_final.png"
        background_image.save(result_path)
        print(f"Imagem final renderizada salva em: {result_path}")
        return {"status": "sucesso", "job_id": job_id, "result_url": f"/download/result/{job_id}"}

    except Exception as e:
        print(f"ERRO DURANTE A GERAÇÃO COM IA OU RENDERIZAÇÃO: {e}")
        # Retorna o erro específico da API do Google, se houver
        if "429" in str(e):
             raise HTTPException(status_code=429, detail="Cota da API do Google excedida. Tente novamente mais tarde ou habilite o faturamento.")
        raise HTTPException(status_code=500, detail=f"Erro ao gerar a imagem final: {e}")

@app.get("/download/result/{job_id}")
async def download_result(job_id: str):
    file_path = f"storage/results/{job_id}_final.png"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Imagem gerada não encontrada.")
    return FileResponse(file_path)