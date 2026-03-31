# YubiKey Dashboard
## Uso y portabilidad

Para asegurar que el programa funcione en cualquier computador, sigue estos pasos:

### 1. Instala Python 3.x
Descarga e instala Python desde [python.org](https://www.python.org/downloads/).

### 2. Crea un entorno virtual (recomendado)
Esto aísla las dependencias y evita conflictos con otros programas.

En Windows:
```bash
python -m venv venv
venv\Scripts\activate
```
En Mac/Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instala las dependencias
```bash
pip install -r requirements.txt
```

### 4. Ejecuta el programa principal
```bash
python yubikey_dashboard.py
```

### Notas de portabilidad
- Usa rutas relativas en el código para acceder a archivos como `inventario_base.json`.
- Asegúrate de que todos los archivos necesarios estén en la misma carpeta.
- Si compartes el proyecto, incluye siempre este README y el archivo requirements.txt.

## Archivos

- `yubikey_dashboard.py`: Interfaz principal y lógica del programa.
- `inventario_base.json`: Base de datos de inventario de YubiKeys.
- `requirements.txt`: Dependencias necesarias.

## Autor

Tu nombre aquí
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
