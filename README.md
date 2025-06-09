# TFM_MIOT_JM

Repositorio del Trabajo de Fin de Máster:  
**Tecnología Blockchain Aplicada a la Securización e Interoperabilidad de eSIMs en Dispositivos IoT**

## Estructura

- `contracts/ESIMRegistry_1.sol`  
  Smart contract para registrar identidades eSIM y gestionar cambios de operador.

- `backend/backend_20.py`  
  API desarrollada en Flask que expone endpoints para registrar eSIMs y solicitar cambios de operador.  
  Integra firma digital, verificación en blockchain y almacenamiento en SQLite.

- `ipa/ipa_sim.py`  
  Script que simula el comportamiento del IoT Profile Assistant (IPA), incluyendo autenticación mediante firma digital.

## Requisitos

- Python 3.10+
- Node.js + Hardhat
- Ganache o Hardhat Node
- SQLite 3

## Instalación rápida

```bash
git clone https://github.com/tuusuario/TFM_MIOT_JM.git
cd TFM_MIOT_JM
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

## Variables de entorno

RPC_URL=http://127.0.0.1:8545
PRIVATE_KEY=0xTUTUCLAVEPRIVADA
CONTRACT_ADDRESS=0xDIRECCIONCONTRATO
AUTH_USER=admin
AUTH_PASS=1234
IPA_PRIVKEY=0xCLAVEPRIVADADELIPA

## Endpoints disponibles

POST /register_identity
POST /request_operator_change
GET /devices
GET /operator_history/<eid>


