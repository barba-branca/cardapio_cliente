# CardápioAI - Analisador Inteligente de Layouts

Este projeto utiliza uma abordagem híbrida de Inteligência Artificial e Visão Computacional para analisar imagens de cardápios. O objetivo é extrair cada bloco de texto e suas respectivas propriedades visuais (posição, tamanho, cor e fonte), gerando um arquivo JSON detalhado como saída.

O sistema é projetado para ser robusto, identificando estilos, buscando fontes online e fornecendo uma análise estruturada que pode ser usada como base para a recriação ou alteração automática de cardápios.

## Como Funciona: A Abordagem Híbrida

O processo de análise é dividido em etapas para garantir a melhor qualidade e precisão:

1.  **Análise de Estilo com IA:** A imagem completa é enviada para um modelo de IA multimodal (Ollama com LLaVA). O objetivo desta etapa não é ler o texto, mas sim identificar as **principais regiões** (ex: área do título, área da lista de itens) e extrair o **estilo visual** de cada uma, como o nome da fonte sugerido e a cor predominante do texto.

2.  **Detecção e Leitura com OCR Clássico:** Em paralelo, a imagem é processada com a biblioteca Tesseract, a ferramenta padrão da indústria para OCR. Usando a função `image_to_data`, o Tesseract é capaz de detectar de forma exaustiva a **posição (`box`) e o conteúdo (`text`)** de cada palavra ou linha na imagem, algo que a IA sozinha tem dificuldade em fazer com precisão em imagens densas.

3.  **Fusão Inteligente:** O sistema combina os resultados das duas etapas. Para cada bloco de texto encontrado pelo Tesseract, ele verifica em qual "região de estilo" (identificada pela IA) ele se encaixa com base em sua posição. Com isso, ele atribui o estilo correto (sugestão de fonte e cor da IA) a cada texto lido pelo Tesseract.

4.  **Enriquecimento de Fontes:** Para cada sugestão de fonte (ex: "Montserrat Bold"), o sistema chama a função `resolve_font`. Esta função primeiro busca na pasta local `/fonts`. Se não encontrar, ela usa a **API do Google Fonts** para buscar e baixar o arquivo de fonte `.ttf` correspondente, salvando-o localmente para uso futuro.

5.  **Saída Final:** O resultado é um único arquivo JSON contendo uma lista de todos os blocos de texto encontrados, cada um enriquecido com seu conteúdo, coordenadas em pixels, tamanho, cor e o nome do arquivo da fonte real a ser utilizada.

## Estrutura do Projeto

cardapio_backend/
├── core/
│ └── image_processor.py # Contém toda a lógica de análise híbrida e busca de fontes.
├── fonts/ # Pasta para armazenar arquivos de fonte .ttf (locais e baixados).
├── storage/
│ ├── metadata/ # Onde os arquivos JSON finais são salvos.
│ ├── templates/ # Usado para salvar imagens de template (na abordagem anterior).
│ └── uploads/ # Armazenamento temporário de imagens enviadas.
├── venv/ # Ambiente virtual do Python.
├── main.py # Servidor FastAPI com o endpoint da API.
├── requirements.txt # Lista de dependências do Python.
└── README.md # Este arquivo.


## Tecnologias Utilizadas

*   **Backend:** Python 3.11+
*   **API Framework:** FastAPI
*   **Inteligência Artificial Local:** Ollama (com o modelo `llava`)
*   **OCR:** Tesseract OCR (via `pytesseract`)
*   **Manipulação de Imagem:** OpenCV, Pillow (PIL)
*   **Busca de Fontes:** API do Google Fonts (via `requests`)
*   **Manipulação de Dados:** Pandas

## Setup e Instalação

Siga estes passos para configurar o ambiente de desenvolvimento local.

### 1. Pré-requisitos

*   **Python 3.11+:** Certifique-se de ter o Python instalado.
*   **Tesseract OCR:**
    *   Instale o Tesseract a partir do [repositório oficial](https://github.com/tesseract-ocr/tesseract/wiki).
    *   **Importante:** Durante a instalação no Windows, adicione o Tesseract ao seu PATH do sistema ou certifique-se de que o caminho no `image_processor.py` (`pytesseract.pytesseract.tesseract_cmd`) esteja correto.
    *   Configure a variável de ambiente `TESSDATA_PREFIX` para apontar para a sua pasta `tessdata`.
*   **Ollama:**
    *   Instale o Ollama a partir do [site oficial](https://ollama.com/).
    *   Após a instalação, puxe os modelos necessários pelo terminal:
      ```bash
      ollama pull llava       # Modelo principal para análise de imagem
      ollama pull llava:7b    # Modelo menor e mais rápido para testes
      ```

### 2. Configuração do Projeto

1.  **Clone o repositório:**
    ```bash
    git clone (https://github.com/barba-branca/cardapio_cliente.git)
    cd cardapio_backend
    ```

2.  **Crie e ative um ambiente virtual:**
    ```bash
    # Windows
    python -m venv venv
    .\venv\Scripts\activate

    # macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

### 3. Configuração da Chave de API

O sistema usa a API do Google Fonts para baixar fontes automaticamente.

1.  Siga as instruções para criar uma **Chave de API** simples (não OAuth) no [Google Cloud Console](https://console.cloud.google.com/).
2.  Ative a **"Web Fonts Developer API"** para o seu projeto.
3.  Abra o arquivo `core/image_processor.py`.
4.  Cole sua chave na seguinte variável:
    ```python
    GOOGLE_FONTS_API_KEY = "SUA_CHAVE_DE_API_AQUI"
    ```

## Como Rodar a Aplicação

1.  **Inicie o serviço Ollama** (geralmente ele inicia automaticamente, mas você pode garantir rodando `ollama serve` em um terminal separado).
2.  **Inicie o servidor Backend:**
    ```bash
    uvicorn main:app --reload --port 8001
    ```
3.  **Abra o Frontend:** Abra o arquivo `prototipo/InserirConteudo.html` no seu navegador. A aplicação estará pronta para uso.

## Documentação da API

### Analisar Imagem

*   **Endpoint:** `POST /api/analyze_image`
*   **Descrição:** Recebe uma imagem, executa o fluxo completo de análise híbrida e enriquecimento de fontes, e salva o resultado em um arquivo JSON na pasta `storage/metadata`.
*   **Entrada:** `multipart/form-data` com um único campo:
    *   `menu_image`: O arquivo de imagem (ex: `.jpg`, `.png`).
*   **Saída (Sucesso):** `200 OK` com um corpo JSON indicando o sucesso e o caminho do arquivo salvo.
    ```json
    {
      "status": "sucesso",
      "message": "A imagem foi analisada e o JSON foi salvo no servidor.",
      "file_path": "storage/metadata/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx_analysis.json"
    }
    ```
*   **Saída (JSON gerado):** O arquivo JSON salvo conterá uma lista de objetos, cada um com a seguinte estrutura:
    ```json
    {
        "text": "PIZZAS",
        "box_pixels": [367, 281, 265, 59],
        "font_size": 59,
        "font_name_suggestion": "Montserrat Bold",
        "color_rgb": [200, 50, 50],
        "font_file": "Montserrat-Regular.ttf"
    }
    ```
