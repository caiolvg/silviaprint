from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import qrcode
import barcode
from barcode.writer import ImageWriter
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import re
import os

app = Flask(__name__)
CORS(app)

def extract_tracking_info(zpl_content):
    """Extrai informações de rastreamento do arquivo ZPL"""
    info = {
        'tracking_number': None,
        'package_id': None,
        'qr_data': None,
        'sender': None,
        'receiver': None,
        'destination': None,
        'cep': None
    }
    
    # Extrair número de rastreamento (código de barras)
    barcode_match = re.search(r'\^FD>:(\d+)', zpl_content)
    if barcode_match:
        info['tracking_number'] = barcode_match.group(1)
    
    # Extrair ID do pacote
    package_match = re.search(r'Pack ID: (\d+)', zpl_content)
    if package_match:
        info['package_id'] = package_match.group(1)
    
    # Extrair dados do QR code
    qr_match = re.search(r'\^FDLA,\{.*?"id":"(\d+)".*?\}', zpl_content)
    if qr_match:
        info['qr_data'] = qr_match.group(1)
    
    # Extrair remetente
    sender_match = re.search(r'\^FD([A-Z0-9\s]+AUTO PE.*?)\^FS', zpl_content)
    if sender_match:
        info['sender'] = sender_match.group(1).strip()
    
    # Extrair CEP
    cep_match = re.search(r'CEP[:\s]+(\d{5}-\d{3})', zpl_content)
    if cep_match:
        info['cep'] = cep_match.group(1)
    
    # Extrair destinatário
    receiver_match = re.search(r'\^FD([A-Za-z\s]+)\(.*?\)\^FS', zpl_content)
    if receiver_match:
        info['receiver'] = receiver_match.group(1).strip()
    
    # Extrair cidade destino
    city_match = re.search(r'Cidade de destino:.*?(\w+),\s*(\w+)', zpl_content)
    if city_match:
        info['destination'] = f"{city_match.group(1)}, {city_match.group(2)}"
    
    return info

def generate_qr_code(data):
    """Gera uma imagem de QR code"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    return img_io

def generate_barcode(data):
    """Gera uma imagem de código de barras"""
    try:
        # Remover caracteres especiais
        clean_data = re.sub(r'[>:]', '', str(data))
        
        ean = barcode.get_barcode_class('code128')
        ean_instance = ean(clean_data, writer=ImageWriter())
        
        img_io = BytesIO()
        ean_instance.write(img_io)
        img_io.seek(0)
        return img_io
    except Exception as e:
        print(f"Erro ao gerar code de barras: {e}")
        return None

def generate_label_preview(info):
    """Gera uma imagem visual completa da etiqueta"""
    try:
        # Dimensões da etiqueta (100mm x 150mm, 300dpi)
        width, height = 1200, 800
        
        # Criar imagem com fundo branco
        img = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(img)
        
        # Tentar usar fonte do sistema, caso contrário usar fonte padrão
        try:
            title_font = ImageFont.truetype("arial.ttf", 24)
            label_font = ImageFont.truetype("arial.ttf", 16)
            value_font = ImageFont.truetype("arial.ttf", 18)
            small_font = ImageFont.truetype("arial.ttf", 12)
        except:
            title_font = ImageFont.load_default()
            label_font = ImageFont.load_default()
            value_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # Cores
        black = (0, 0, 0)
        gray = (100, 100, 100)
        light_gray = (220, 220, 220)
        
        # Margem
        margin = 40
        
        # ===== SEÇÃO SUPERIOR ESQUERDA: INFORMAÇÕES DO REMETENTE =====
        draw.rectangle([margin, margin, margin + 450, margin + 120], outline=gray, width=2)
        draw.text((margin + 15, margin + 10), "REMETENTE", fill=black, font=label_font)
        sender_text = info.get('sender', 'N/A')
        if sender_text and len(sender_text) > 40:
            sender_text = sender_text[:40]
        draw.text((margin + 15, margin + 40), sender_text, fill=black, font=small_font)
        
        # ===== SEÇÃO CENTRAL ESQUERDA: INFORMAÇÕES DO DESTINATÁRIO =====
        draw.rectangle([margin, margin + 150, margin + 450, margin + 380], outline=gray, width=2)
        draw.text((margin + 15, margin + 160), "DESTINATARIO", fill=black, font=label_font)
        
        receiver = info.get('receiver', 'N/A')
        draw.text((margin + 15, margin + 195), receiver[:35], fill=black, font=value_font)
        
        destination = info.get('destination', 'N/A')
        draw.text((margin + 15, margin + 235), f"Destino: {destination}", fill=black, font=small_font)
        
        cep = info.get('cep', 'N/A')
        draw.text((margin + 15, margin + 265), f"CEP: {cep}", fill=black, font=small_font)
        
        package_id = info.get('package_id', 'N/A')
        draw.text((margin + 15, margin + 295), f"Pacote: {package_id}", fill=black, font=small_font)
        
        tracking = info.get('tracking_number', 'N/A')
        draw.text((margin + 15, margin + 325), f"Rastreamento:", fill=gray, font=small_font)
        draw.text((margin + 15, margin + 350), tracking, fill=black, font=value_font)
        
        # ===== SEÇÃO DIREITA: QR CODE E CÓDIGO DE BARRAS =====
        try:
            # Gerar QR Code
            qr_data = info.get('qr_data') or info.get('tracking_number', '')
            if qr_data:
                qr_img_io = generate_qr_code(qr_data)
                qr_img = Image.open(qr_img_io)
                qr_img = qr_img.resize((200, 200), Image.Resampling.LANCZOS)
                img.paste(qr_img, (margin + 500, margin + 40))
        except Exception as e:
            print(f"Erro ao adicionar QR: {e}")
        
        try:
            # Gerar Código de Barras
            tracking = info.get('tracking_number', '')
            if tracking:
                barcode_img_io = generate_barcode(tracking)
                if barcode_img_io:
                    barcode_img = Image.open(barcode_img_io)
                    # Redimensionar código de barras
                    barcode_img = barcode_img.resize((280, 100), Image.Resampling.LANCZOS)
                    img.paste(barcode_img, (margin + 480, margin + 280))
        except Exception as e:
            print(f"Erro ao adicionar barcode: {e}")
        
        # ===== RODAPÉ: INFORMAÇÕES ADICIONAIS =====
        draw.line([(margin, margin + 420), (width - margin, margin + 420)], fill=light_gray, width=1)
        draw.text((margin, margin + 445), "Silviaprint - Gerador de Etiquetas", fill=gray, font=small_font)
        draw.text((width - margin - 250, margin + 445), f"Gerado em: {info.get('package_id', '-')}", fill=gray, font=small_font)
        
        # Salvar em BytesIO
        img_io = BytesIO()
        img.save(img_io, format='PNG')
        img_io.seek(0)
        return img_io
        
    except Exception as e:
        print(f"Erro ao gerar preview da etiqueta: {e}")
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Recebe arquivo e processa"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Arquivo não selecionado'}), 400
        
        # Ler conteúdo do arquivo
        content = file.read().decode('utf-8', errors='ignore')
        
        # Extrair informações
        info = extract_tracking_info(content)
        
        return jsonify({
            'success': True,
            'data': info,
            'message': 'Arquivo processado com sucesso'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-qr/<data>')
def get_qr(data):
    """Gera e retorna QR code"""
    try:
        img_io = generate_qr_code(data)
        return send_file(img_io, mimetype='image/png')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-barcode/<data>')
def get_barcode(data):
    """Gera e retorna código de barras"""
    try:
        img_io = generate_barcode(data)
        if img_io:
            return send_file(img_io, mimetype='image/png')
        else:
            return jsonify({'error': 'Erro ao gerar código de barras'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-label-preview', methods=['POST'])
def generate_label_preview_endpoint():
    """Gera e retorna preview completo da etiqueta"""
    try:
        data = request.json
        img_io = generate_label_preview(data)
        if img_io:
            return send_file(img_io, mimetype='image/png')
        else:
            return jsonify({'error': 'Erro ao gerar preview da etiqueta'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
