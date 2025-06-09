import requests
import json
from eth_account import Account
from eth_account.messages import encode_defunct
from web3 import Web3 # Web3 no es estrictamente necesario aquí, pero lo mantenemos por si lo usas para otra cosa
from dotenv import load_dotenv
import os

# === Cargar variables de entorno ===
load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL", "https://127.0.0.1:5000")
IPA_PRIVKEY = os.getenv("IPA_PRIVKEY")
VERIFY_SSL = False  # Para certificados autofirmados

# === Validación clave privada ===
if not IPA_PRIVKEY or len(IPA_PRIVKEY.replace("0x", "")) != 64:
    raise ValueError("❌ IPA_PRIVKEY no es válida. Asegúrate de que tenga 64 caracteres hexadecimales.")

# === Datos del dispositivo y nuevo perfil ===
eid = "89049032000000000010"
new_iccid = "895531223591588529"
new_mno = "Digi"

# === 1. Construir el mensaje EXACTAMENTE IGUAL que en el backend (con :) ===
message_text = f"{eid}:{new_iccid}:{new_mno}"

# === 2. Codificar el mensaje para firmar (sin hashing previo) ===
# La función encode_defunct ya se encarga del hashing necesario.
message_to_sign = encode_defunct(text=message_text)

# === 3. Firmar el mensaje codificado ===
account = Account.from_key(IPA_PRIVKEY)
signed_message = account.sign_message(message_to_sign)

# === 4. Obtener la firma en formato hexadecimal (más simple y directo) ===
signature_hex = signed_message.signature.hex()

# === Armar payload y enviar ===
payload = {
    "eid": eid,
    "new_iccid": new_iccid,
    "new_mno": new_mno,
    "signature": signature_hex
}

auth = ("admin", "1234")
print("Enviando payload:", json.dumps(payload, indent=2))

response = requests.post(
    f"{BACKEND_URL}/request_operator_change",
    json=payload,
    auth=auth,
    verify=VERIFY_SSL
)

# === Mostrar respuesta del backend ===
print("\nRespuesta del backend:")
print("Status Code:", response.status_code)
try:
    print("Response JSON:", response.json())
except json.JSONDecodeError:
    print("Response Text:", response.text)

print("\nClave pública usada para firmar (debería coincidir con la recuperada en el backend):", account.address)
