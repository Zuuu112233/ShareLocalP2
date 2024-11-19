from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import random
import string
import base64

app = Flask(__name__)
socketio = SocketIO(app)

# Dictionary untuk menyimpan hubungan kode unik dan socket ID
active_connections = {}


@app.route('/')
def home():
    return render_template('index.html')


@socketio.on('generate_code')
def generate_code():
    """Generate kode unik sesuai panjang yang ditentukan (3 digit)."""
    panjang_code = 3  # Menentukan panjang kode yang diinginkan
    code = ''.join(random.choices(string.digits, k=panjang_code))  # Kode dengan panjang 3 digit
    active_connections[code] = request.sid  # Simpan kode dengan socket ID
    emit('code_generated', {'code': code})



@app.route('/send_file', methods=['POST'])
def send_file():
    """Menerima file dari klien dan meneruskannya ke penerima berdasarkan kode unik."""
    recipient_code = request.form['code']
    file = request.files['file']
    recipient_sid = active_connections.get(recipient_code)

    if recipient_sid:
        # Baca file sebagai binary, lalu encode ke Base64
        file_data = base64.b64encode(file.read()).decode('utf-8')
        file_type = file.content_type
        file_name = file.filename

        # Kirim file ke penerima
        socketio.emit(
            'receive_file',
            {
                'file_data': file_data,
                'file_type': file_type,
                'file_name': file_name
            },
            room=recipient_sid
        )
        return 'File sent successfully', 200
    else:
        return 'Recipient code not found', 404


@socketio.on('disconnect')
def disconnect():
    """Hapus pengguna dari active_connections saat terputus."""
    sid_to_remove = request.sid
    for code, sid in list(active_connections.items()):
        if sid == sid_to_remove:
            del active_connections[code]
            break


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8080)

