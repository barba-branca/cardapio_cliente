# main.py (VERSÃO FINAL COM SALVAMENTO DE ARQUIVO JSON)

import io
import os
import uuid
import json # Adicionado import para json
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Importa a única função que vamos usar
from core.image_processor import get_text_properties_from_image

# --- Configuração Inicial ---
app = FastAPI(title="CardápioAI - Analisador de Texto em Imagens")
origins = ["*"]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# Define o diretório de metadados
METADATA_DIR = "storage/metadata"
os.makedirs(METADATA_DIR, exist_ok=True) # Garante que a pasta exista

# --- Endpoints da API ---
@app.get("/verversao")
async def get_version():
    return {"version": "13.0-final-json-save"}

@app.post("/api/analyze_image")
async def analyze_image_for_text(menu_image: UploadFile = File(...)):
    """
    Recebe uma imagem, analisa, enriquece com fontes,
    SALVA o resultado em um arquivo JSON, e retorna sucesso.
    """
    job_id = str(uuid.uuid4())
    
    try:
        image_stream = io.BytesIO(await menu_image.read())
        
        # 1. Chama a função de análise que retorna o JSON
        text_properties_json = await get_text_properties_from_image(image_stream)
        
        # --- LÓGICA DE SALVAMENTO ADICIONADA AQUI ---
        # Define o caminho completo para o novo arquivo JSON
        save_path = os.path.join(METADATA_DIR, f"{job_id}_analysis.json")
        
        # Abre o arquivo em modo de escrita ('w') e salva o JSON
        with open(save_path, 'w', encoding='utf-8') as f:
            # json.dump escreve o objeto Python como um JSON formatado no arquivo
            json.dump(text_properties_json, f, ensure_ascii=False, indent=4)
        
        print(f"✅ Análise salva com sucesso em: {save_path}")
        
        # Retorna uma mensagem de sucesso para o frontend
        return JSONResponse(content={
            "status": "sucesso",
            "message": "A imagem foi analisada e o JSON foi salvo no servidor.",
            "file_path": save_path
        })

    except Exception as e:
        print(f"ERRO NO ENDPOINT /api/analyze_image: {e}")
        raise HTTPException(status_code=500, detail=str(e))