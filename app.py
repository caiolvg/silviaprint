from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import qrcode
import barcode
from barcode.writer import ImageWriter
from io import BytesIO
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

if __name__ == '__main__':
    app.run(debug=True, port=5000)
