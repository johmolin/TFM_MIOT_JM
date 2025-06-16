## **Tecnología Blockchain Aplicada a la Securización e Interoperabilidad de eSIMs en Dispositivos IoT**
- Autor: Johan Molina Medina
- Universidad Complutense de Madrid
- Master en Internet de las Cosas

## Resumen

El crecimiento exponencial del Internet de las Cosas (IoT) y la necesidad de una conectividad flexible han posicionado a la tecnología eSIM (Embedded Subscriber Identity Module) como un pilar fundamental. Sin embargo, su gestión sigue anclada en modelos centralizados controlados por un único operador o proveedor, lo que genera una fricción operativa significativa, limita la verdadera interoperabilidad entre actores y carece de un registro unificado y auditable del ciclo de vida de los dispositivos. Esta falta de transparencia y la dependencia de intermediarios representan una barrera para la escalabilidad y la confianza en un ecosistema que demanda agilidad y seguridad.

Este trabajo aborda directamente estos desafíos proponiendo un modelo innovador que utiliza la tecnología blockchain para crear un marco de gestión descentralizado. Se diseñan dos arquitecturas técnicas donde un componente clave, el IoT Profile Assistant (IPA), gestiona los perfiles de conectividad del dispositivo. En la primera arquitectura, el IPA se aloja en el dispositivo IoT, y en la segunda, se integra en la eUICC (Embedded Universal Integrated Circuit Card), reforzando aún más la seguridad. Ambas arquitecturas se orquestan mediante un backend y utilizan contratos inteligentes (smart contracts) para registrar de forma inmutable y transparente eventos críticos como la activación de perfiles, los cambios de operador y las operaciones de autenticación.

La viabilidad de la solución fue demostrada mediante una prueba de concepto técnica en un entorno controlado y validada cualitativamente a través de una encuesta a 57 profesionales del sector. Los resultados concluyen que la integración de blockchain mejora significativamente la securización, trazabilidad y auditabilidad, ofreciendo un marco de gestión de eSIMs más resiliente y automatizable. De este modo, el trabajo no solo presenta una solución técnica, sino que sienta las bases para un ecosistema IoT más abierto, interoperable y confiable, alineado con las futuras normativas regulatorias y modelos de gobernanza distribuida.

Palabras claves
API, Backend, Blockchain, eUICC, IoT, GSMA, Smart contracts.

## Estructura

- `contracts/ESIMRegistry_1.sol`  
  Smart contract para registrar identidades eSIM y gestionar cambios de operador.

- `backend/backend_20.py`  
  API desarrollada en Flask que expone endpoints para registrar eSIMs y solicitar cambios de operador.  
  Integra firma digital, verificación en blockchain y almacenamiento en SQLite.

- `ipa/ipa_sim.py`  
  Script que simula el comportamiento del IoT Profile Assistant (IPA), incluyendo autenticación mediante firma digital.

- `.env.example`
  Variables de entorno a configurar en la raiz del proyecto

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

