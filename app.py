from flask import Flask, render_template, request, jsonify, Response
from flask_cors import CORS
from io import BytesIO
import re
import urllib.error
import urllib.request
import zipfile

try:
    import rarfile
except ImportError:  # RAR support stays optional.
    rarfile = None

app = Flask(__name__)
CORS(app)

MAX_BATCH_FILES = 100
ALLOWED_LABEL_EXTENSIONS = {'.txt', '.zpl'}


def decode_zpl_text(value):
    """Decodifica texto ZPL com ^FH usando _XX para bytes hexadecimais."""
    if not value:
        return None

    byte_buffer = bytearray()
    index = 0
    while index < len(value):
        char = value[index]
        if char == '_' and index + 2 < len(value):
            hex_part = value[index + 1:index + 3]
            try:
                byte_buffer.append(int(hex_part, 16))
                index += 3
                continue
            except ValueError:
                pass

        byte_buffer.extend(char.encode('utf-8'))
        index += 1

    decoded = byte_buffer.decode('utf-8', errors='ignore')
    return re.sub(r'\s+', ' ', decoded).strip()


def extract_first_match(pattern, zpl_content, group=1):
    match = re.search(pattern, zpl_content, re.DOTALL)
    if not match:
        return None
    return decode_zpl_text(match.group(group))

def extract_tracking_info(zpl_content):
    """Extrai informações de rastreamento do arquivo ZPL"""
    info = {
        'tracking_number': None,
        'package_id': None,
        'qr_data': None,
        'sender': None,
        'receiver': None,
        'destination': None,
        'cep': None,
        'address': None,
        'zpl': zpl_content,
    }

    info['tracking_number'] = extract_first_match(r'\^FD>:(\d+)', zpl_content)
    info['package_id'] = extract_first_match(r'Pack ID:\s*(\d+)', zpl_content)
    info['qr_data'] = extract_first_match(r'\^FDLA,\{.*?"id":"(\d+)".*?\}', zpl_content)
    info['sender'] = extract_first_match(r'\^FO120,20\^A0N,24,24\^FH\^FD(.*?)\^FS', zpl_content)
    info['receiver'] = extract_first_match(r'\^FO30,860\^A0N,26,26\^FB440,2,-2,L\^FH\^FD(.*?)\^FS', zpl_content)
    info['address'] = extract_first_match(r'\^FO30,930\^A0N,26,26\^FB440,3,0,L\^FH\^FDEndere_C3_A7o:\s*(.*?)\^FS', zpl_content)
    info['destination'] = extract_first_match(r'\^FO30,1050\^A0N,26,26\^FB440,2,0,L\^FH\^FDCidade de destino:\s*(.*?)\^FS', zpl_content)

    cep_raw = extract_first_match(r'\^FO30,1016\^A0N,30,30\^FDCEP:\s*(\d{8})\^FS', zpl_content)
    if cep_raw and len(cep_raw) == 8:
        info['cep'] = f'{cep_raw[:5]}-{cep_raw[5:]}'
    
    return info

def get_file_extension(filename):
    match = re.search(r'(\.[^.\\/:]+)$', filename or '')
    return match.group(1).lower() if match else ''

def is_label_file(filename):
    return get_file_extension(filename) in ALLOWED_LABEL_EXTENSIONS

def build_label_result(filename, content):
    info = extract_tracking_info(content)
    info['filename'] = filename
    return {
        'success': True,
        'filename': filename,
        'data': info,
    }

def build_error_result(filename, message):
    return {
        'success': False,
        'filename': filename or 'arquivo-sem-nome',
        'error': message,
    }

def append_label_result(results, filename, raw_content):
    if len(results) >= MAX_BATCH_FILES:
        return

    content = raw_content.decode('utf-8', errors='ignore')
    results.append(build_label_result(filename, content))

def extract_zip_labels(file_storage, results):
    try:
        with zipfile.ZipFile(BytesIO(file_storage.read())) as archive:
            members = [
                member for member in archive.infolist()
                if not member.is_dir() and is_label_file(member.filename)
            ]

            if not members:
                results.append(build_error_result(file_storage.filename, 'ZIP sem arquivos .txt ou .zpl'))
                return

            for member in members:
                if len(results) >= MAX_BATCH_FILES:
                    break
                with archive.open(member) as entry:
                    append_label_result(results, member.filename, entry.read())
    except zipfile.BadZipFile:
        results.append(build_error_result(file_storage.filename, 'ZIP inválido ou corrompido'))

def extract_rar_labels(file_storage, results):
    if rarfile is None:
        results.append(build_error_result(
            file_storage.filename,
            'RAR precisa da dependência opcional rarfile e de uma ferramenta como unrar/bsdtar instalada no servidor',
        ))
        return

    try:
        with rarfile.RarFile(BytesIO(file_storage.read())) as archive:
            members = [
                member for member in archive.infolist()
                if not member.isdir() and is_label_file(member.filename)
            ]

            if not members:
                results.append(build_error_result(file_storage.filename, 'RAR sem arquivos .txt ou .zpl'))
                return

            for member in members:
                if len(results) >= MAX_BATCH_FILES:
                    break
                with archive.open(member) as entry:
                    append_label_result(results, member.filename, entry.read())
    except Exception as error:
        results.append(build_error_result(file_storage.filename, f'Falha ao ler RAR: {error}'))

def process_uploaded_files(files):
    results = []

    for file_storage in files:
        if len(results) >= MAX_BATCH_FILES:
            break

        filename = file_storage.filename or ''
        if not filename:
            results.append(build_error_result(filename, 'Arquivo sem nome'))
            continue

        extension = get_file_extension(filename)
        if is_label_file(filename):
            append_label_result(results, filename, file_storage.read())
        elif extension == '.zip':
            extract_zip_labels(file_storage, results)
        elif extension == '.rar':
            extract_rar_labels(file_storage, results)
        else:
            results.append(build_error_result(filename, 'Formato não suportado. Envie .txt, .zpl, .zip ou .rar'))

    return results

def render_zpl_preview(zpl_content, dpmm=8, width=4, height=6, index=0):
    """Renderiza a etiqueta Zebra real a partir do ZPL usando o serviço Labelary."""
    endpoint = (
        f'https://api.labelary.com/v1/printers/{dpmm}dpmm/'
        f'labels/{width}x{height}/{index}/'
    )
    request = urllib.request.Request(
        endpoint,
        data=zpl_content.encode('utf-8'),
        headers={
            'Accept': 'image/png',
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        method='POST',
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read()

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
        
        results = process_uploaded_files([file])
        first_result = results[0] if results else build_error_result(file.filename, 'Arquivo não processado')
        if not first_result['success']:
            return jsonify({'error': first_result['error']}), 400
        
        return jsonify({
            'success': True,
            'data': first_result['data'],
            'message': 'Arquivo processado com sucesso'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload-batch', methods=['POST'])
def upload_files_batch():
    """Recebe ate 100 etiquetas diretas ou dentro de ZIP/RAR e processa em lote."""
    try:
        files = request.files.getlist('files')
        if not files:
            single_file = request.files.get('file')
            files = [single_file] if single_file else []

        if not files:
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400

        if len(files) > MAX_BATCH_FILES:
            return jsonify({'error': f'Envie no máximo {MAX_BATCH_FILES} arquivos por vez'}), 400

        results = process_uploaded_files(files)
        success_count = sum(1 for result in results if result['success'])
        error_count = len(results) - success_count

        return jsonify({
            'success': success_count > 0,
            'results': results,
            'summary': {
                'total': len(results),
                'success': success_count,
                'errors': error_count,
                'limit': MAX_BATCH_FILES,
            },
            'message': f'{success_count} arquivo(s) processado(s)',
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-label-preview', methods=['POST'])
def generate_label_preview_endpoint():
    """Gera e retorna preview renderizado da etiqueta Zebra a partir do ZPL."""
    try:
        data = request.get_json(silent=True) or {}
        zpl_content = data.get('zpl')
        if not zpl_content:
            return jsonify({'error': 'Conteúdo ZPL não informado'}), 400

        image_bytes = render_zpl_preview(zpl_content)
        return Response(image_bytes, mimetype='image/png')
    except urllib.error.HTTPError as error:
        error_body = error.read().decode('utf-8', errors='ignore')
        return jsonify({'error': f'Falha ao renderizar ZPL: {error_body or error.reason}'}), 502
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
