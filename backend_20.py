from flask import Flask, request, jsonify, Response
from functools import wraps
import sqlite3
import threading
import os
from dotenv import load_dotenv
from eth_account.messages import encode_defunct
from eth_account import Account
from web3 import Web3
from datetime import datetime
import secrets
import json # <--- ESTA ES LA LÍNEA AÑADIDA
# import ssl # Descomentar si se usa HTTPS

load_dotenv()

# === Configuración inicial ===
app = Flask(__name__)

RPC_URL = os.getenv("RPC_URL")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")
AUTH_USER = os.getenv("AUTH_USER")
AUTH_PASS = os.getenv("AUTH_PASS")

if not all([RPC_URL, PRIVATE_KEY, CONTRACT_ADDRESS, AUTH_USER, AUTH_PASS]):
    raise ValueError("Faltan variables de entorno necesarias en .env (RPC_URL, PRIVATE_KEY, CONTRACT_ADDRESS, AUTH_USER, AUTH_PASS)")

w3 = Web3(Web3.HTTPProvider(RPC_URL))
account = w3.eth.account.from_key(PRIVATE_KEY)

# === Cargar ABI ===
# Asegúrate de que la ruta sea correcta para tu entorno
abi_path = "/home/johanmolina/hardhat-moonbase/artifacts/contracts/ESIMRegistry_1.sol/ESIMRegistry.json"
if not os.path.exists(abi_path):
    raise FileNotFoundError(f"ABI no encontrado en {abi_path}")

# Ahora 'json' está definido gracias al import
with open(abi_path) as abi_file:
    contract_abi = json.load(abi_file)["abi"]

contract = w3.eth.contract(address=w3.to_checksum_address(CONTRACT_ADDRESS), abi=contract_abi)

# === Conexión a la Base de Datos ===
db_lock = threading.Lock()

def connect_db():
    """Función centralizada para conectar a la base de datos."""
    conn = sqlite3.connect("esim_data.db", check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def initialize_database():
    """Crea las tablas de la base de datos si no existen."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS devices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        eid TEXT UNIQUE NOT NULL,
        iccid TEXT NOT NULL,
        mno TEXT NOT NULL
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS operator_changes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        eid TEXT NOT NULL,
        old_iccid TEXT NOT NULL,
        old_mno TEXT NOT NULL,
        new_iccid TEXT NOT NULL,
        new_mno TEXT NOT NULL,
        change_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS device_keys (
        eid TEXT PRIMARY KEY,
        pubkey TEXT NOT NULL
    )''')
    conn.commit()
    conn.close()

initialize_database()

# === Autenticación ===
def check_auth(username, password):
    return username == AUTH_USER and password == AUTH_PASS

def authenticate():
    return Response("Autenticación requerida", 401, {"WWW-Authenticate": "Basic realm='Login'"})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

# === Rutas de la API ===
@app.route("/", methods=["GET"])
@requires_auth
def home():
    return jsonify({"message": "Backend eSIM funcionando con Hardhat"})

@app.route("/register_identity", methods=["POST"])
@requires_auth
def register_identity():
    data = request.get_json()
    eid = data["eid"]
    iccid = data["iccid"]
    mno = data["mno"]
    pubkey = w3.to_checksum_address(data["pubkey"])

    with db_lock:
        conn = connect_db()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id FROM devices WHERE eid = ?", (eid,))
            if cursor.fetchone():
                return jsonify({"status": "error", "message": "Dispositivo con este EID ya existe."}), 400

            cursor.execute("INSERT INTO devices (eid, iccid, mno) VALUES (?, ?, ?)", (eid, iccid, mno))
            cursor.execute("INSERT INTO device_keys (eid, pubkey) VALUES (?, ?)", (eid, pubkey))
            conn.commit()
        except Exception as e:
            conn.rollback()
            return jsonify({"status": "error", "message": f"Error de base de datos: {str(e)}"}), 500
        finally:
            conn.close()

    try:
        nonce = w3.eth.get_transaction_count(account.address)
        tx = contract.functions.registerDevice(eid, iccid, mno, pubkey).build_transaction({
            'from': account.address,
            'nonce': nonce,
            'gas': 2000000,
            'gasPrice': w3.to_wei('1', 'gwei')
        })
        signed_tx = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error en transacción Blockchain: {str(e)}"}), 500

    return jsonify({"status": "success", "tx_hash": tx_hash.hex()}), 201

@app.route('/devices', methods=['GET'])
@requires_auth
def list_devices():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT eid, iccid, mno FROM devices")
    devices = cursor.fetchall()
    conn.close()

    device_list = [{"eid": eid, "iccid": iccid, "mno": mno} for (eid, iccid, mno) in devices]
    return jsonify({"status": "success", "devices": device_list})

@app.route("/request_operator_change", methods=["POST"])
@requires_auth
def request_operator_change():
    """
    Ruta corregida y completa para el cambio de operador.
    Valida la firma, actualiza la DB local y registra en la Blockchain.
    """
    data = request.get_json()
    eid = data.get("eid")
    new_iccid = data.get("new_iccid")
    new_mno = data.get("new_mno")
    signature = data.get("signature")

    if not all([eid, new_iccid, new_mno, signature]):
        return jsonify({"status": "error", "message": "Faltan parámetros"}), 400

    # 1. Obtener la clave pública del dispositivo para verificar la firma
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT pubkey FROM device_keys WHERE eid = ?", (eid,))
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        return jsonify({"status": "error", "message": "Dispositivo no encontrado"}), 404
    pubkey = result[0]

    # 2. Verificar la firma
    try:
        message_to_sign = f"{eid}:{new_iccid}:{new_mno}"
        message_hash = encode_defunct(text=message_to_sign)
        recovered_address = w3.eth.account.recover_message(message_hash, signature=signature)
    except Exception as e:
        return jsonify({"status": "error", "message": f"Firma inválida: {str(e)}"}), 400

    if recovered_address.lower() != pubkey.lower():
        return jsonify({"status": "error", "message": "La firma no coincide"}), 401
    
    # 3. Actualizar la base de datos local
    with db_lock:
        conn = connect_db()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT iccid, mno FROM devices WHERE eid = ?", (eid,))
            old_device_data = cursor.fetchone()
            if not old_device_data:
                 return jsonify({"status": "error", "message": "Dispositivo no encontrado para actualizar"}), 404
            
            old_iccid, old_mno = old_device_data
            
            cursor.execute("UPDATE devices SET iccid = ?, mno = ? WHERE eid = ?", (new_iccid, new_mno, eid))
            cursor.execute("INSERT INTO operator_changes (eid, old_iccid, old_mno, new_iccid, new_mno) VALUES (?, ?, ?, ?, ?)",
                           (eid, old_iccid, old_mno, new_iccid, new_mno))
            conn.commit()
        except Exception as e:
            conn.rollback()
            return jsonify({"status": "error", "message": f"Error de base de datos al actualizar: {str(e)}"}), 500
        finally:
            conn.close()

    # 4. Enviar transacción a la Blockchain
    try:
        nonce = w3.eth.get_transaction_count(account.address)
        tx = contract.functions.changeOperator(eid, new_iccid, new_mno).build_transaction({
            'from': account.address,
            'nonce': nonce,
            'gas': 2000000,
            'gasPrice': w3.to_wei('1', 'gwei')
        })
        signed_tx = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error en transacción Blockchain: {str(e)}"}), 500
    
    return jsonify({"status": "success", "message": "Cambio de operador completado", "tx_hash": tx_hash.hex()})

@app.route('/operator_history/<string:eid>', methods=['GET'])
@requires_auth
def get_operator_history(eid):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT old_iccid, new_iccid, old_mno, new_mno, change_date FROM operator_changes WHERE eid = ?", (eid,))
    rows = cursor.fetchall()
    conn.close()

    history = [
        {
            "old_iccid": row[0],
            "new_iccid": row[1],
            "old_mno": row[2],
            "new_mno": row[3],
            "timestamp": row[4]
        }
        for row in rows
    ]
    return jsonify({"status": "success", "history": history})

# === Bloque de ejecución ===
if __name__ == "__main__":
    # Para pruebas locales sin HTTPS, es más sencillo así:
    #app.run(host='0.0.0.0', port=5000, debug=True)

    # Si necesitas HTTPS, asegúrate de tener los archivos cert.pem y key.pem
    ssl_context = ('cert.pem', 'key.pem')
    app.run(host='0.0.0.0', port=5000, ssl_context=ssl_context, debug=True)