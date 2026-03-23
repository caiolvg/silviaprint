# Gerador de Etiquetas Silviaprint

Um site para ler arquivos de etiqueta em ZPL, extrair os dados principais e renderizar a etiqueta real de impressoras Zebra.

## Funcionalidades

- Upload de arquivos de etiqueta (.txt, .zpl)
- Extração automática de informações principais
- Renderização da etiqueta Zebra a partir do ZPL real
- Visualização de QR Code e código de barras
- Download das imagens geradas
- Interface responsiva

## Pré-requisitos

- Python 3.10 ou superior
- pip (gerenciador de pacotes Python)

## Instalação e Execução

### 1. Clonar/Acessar o projeto

```bash
cd c:\Users\caiol\OneDrive\Área de Trabalho\silviaprint
```

### 2. Criar ambiente virtual (recomendado)

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Instalar dependências

```bash
pip install -r requirements.txt
```

### 4. Executar a aplicação

```bash
python app.py
```

### 5. Acessar no navegador

Abra seu navegador e acesse: **http://localhost:5000**

## 📁 Estrutura do Projeto

```
silviaprint/
├── app.py                 # Backend Flask
├── requirements.txt       # Dependências Python
├── templates/
│   └── index.html        # Interface HTML
└── static/
    ├── style.css         # Estilos CSS
    └── script.js         # Lógica JavaScript
```

## Como Usar

1. **Upload**: Arraste um arquivo de etiqueta (.txt ou .zpl) ou clique para selecionar
2. **Extração**: O sistema automaticamente extrai informações do arquivo
3. **Visualização**: Veja os dados extraídos e a etiqueta Zebra renderizada
4. **Download**: Baixe o QR Code e Código de Barras em PNG

## Dados Extraídos

- **ID do Pacote**: Identificador único do pacote
- **Rastreamento**: Número principal do envio
- **Remetente**: Informações de quem está enviando
- **Destinatário**: Nome de quem vai receber
- **Destino**: Cidade de entrega
- **CEP**: Código de endereçamento postal

## Tecnologias Utilizadas

- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3, JavaScript vanilla
- **Renderização ZPL**: Labelary API para prévia real da etiqueta Zebra
- **Imagens auxiliares**: serviços externos para QR Code e código de barras

## Formato de Arquivo Suportado

O sistema suporta arquivos no formato **ZPL (Zebra Programming Language)**, comumente usado em etiquetas de envio.

Exemplo de estrutura extraída:

```
- Pack ID: 20000
- Tracking: 09075825485
- QR Data: 45445840547
- Sender: AUTO PEÇAS SAVANA
- Receiver: Nome do Destinatário
- Destination: Cidade, Estado
- CEP: 20251-380
```

## Troubleshooting

### Erro: "ModuleNotFoundError"

```bash
pip install -r requirements.txt
```

### Erro: "Porta 5000 já em uso"

Edite `app.py` e altere a porta:

```python
app.run(debug=True, port=5001)
```

### Erro: "Arquivo não processado"

Verifique se o arquivo está em formato ZPL válido

### Erro: preview da etiqueta não aparece

Verifique se a máquina tem acesso externo ao serviço de renderização ZPL usado pela aplicação.

## Suporte

Para mais informações ou reportar problemas, entre em contato com o desenvolvedor.

## Licença

Projeto desenvolvido para Silviaprint.

---

**Versão**: 1.0.0  
**Última atualização**: 2026-03-23
