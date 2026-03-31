# YubiKey Dashboard

Este proyecto es una herramienta para la gestión y control de inventario de YubiKeys en una organización. Permite visualizar, registrar y actualizar información sobre las YubiKeys disponibles, asignadas y en uso, utilizando un archivo base de inventario en formato JSON y una interfaz desarrollada en Python.

## Archivos principales

- **yubikey_dashboard.py**: Script principal de la aplicación. Contiene la lógica para cargar, mostrar y modificar el inventario de YubiKeys.
- **inventario_base.json**: Archivo de datos en formato JSON que almacena la información de todas las YubiKeys gestionadas por la aplicación.

## Requisitos

- Python 3.8 o superior
- (Opcional) Bibliotecas adicionales si el script las requiere (por ejemplo, `tkinter`, `pandas`, etc.)

## Instalación

1. Clona este repositorio o descarga los archivos `yubikey_dashboard.py` e `inventario_base.json` en una carpeta local.
2. Asegúrate de tener Python instalado. Puedes verificarlo ejecutando:
   ```bash
   python --version
   ```
3. Si el script requiere librerías externas, instálalas con:
   ```bash
   pip install -r requirements.txt
   ```
   *(Crea el archivo `requirements.txt` si es necesario, listando las dependencias.)*

## Uso

1. Abre una terminal en la carpeta del proyecto.
2. Ejecuta el script principal:
   ```bash
   python yubikey_dashboard.py
   ```
3. Sigue las instrucciones que aparecen en pantalla para consultar, agregar o modificar información de las YubiKeys.

## ¿Cómo funciona?

- El script lee el archivo `inventario_base.json` para cargar el inventario actual.
- Permite realizar operaciones como:
  - Consultar el estado de las YubiKeys (disponibles, asignadas, en uso, etc.)
  - Registrar nuevas YubiKeys en el inventario
  - Actualizar el estado o información de una YubiKey existente
  - Guardar los cambios realizados en el archivo JSON
- La interacción puede ser por consola o mediante una interfaz gráfica (dependiendo de la implementación en `yubikey_dashboard.py`).

## Personalización

- Puedes modificar el archivo `inventario_base.json` para agregar o quitar campos según las necesidades de tu organización.
- Si deseas agregar nuevas funcionalidades, edita el archivo `yubikey_dashboard.py`.

## Autor

- Josthin Paz

## Licencia

Este proyecto es de uso interno. Puedes modificarlo y adaptarlo según tus necesidades.
