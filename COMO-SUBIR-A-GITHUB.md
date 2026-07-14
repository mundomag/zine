# Mundo Maravilloso — Guía para subir a GitHub

## Qué se corrigió en este paquete
- Se movió todo el contenido a la raíz (antes estaba dentro de `ONLINE 02 adsense op ok - lab/`)
- Se eliminó `seguimientos/old/` (versiones duplicadas antiguas)
- Se eliminó un archivo huérfano (`Unconfirmed 762526.crdownload`) que no se usaba en ningún artículo
- Se renombraron 3 imágenes con espacios/comas en el nombre y se actualizaron sus referencias en el HTML
- Se comprimió `IceCube_Neutrino_Observatory_in_2023_01.jpg` de 74 MB a ~500 KB (redimensionada a 2000px de ancho, misma calidad visual en web)
- Se agregó `.nojekyll` para que GitHub Pages sirva los archivos tal cual, sin procesarlos con Jekyll

Tamaño final: ~52 MB (antes: 127 MB).

## Pasos para publicar

### 1. Crear el repositorio
En GitHub, crea un repositorio nuevo (puede llamarse `mundomaravilloso` o el nombre que prefieras). Si vas a usar GitHub Pages gratis, debe ser **público**.

### 2. Subir los archivos
Desde tu computadora, dentro de esta carpeta descomprimida:

```bash
git init
git add .
git commit -m "Primera versión del sitio"
git branch -M main
git remote add origin https://github.com/TU-USUARIO/TU-REPO.git
git push -u origin main
```

(También puedes arrastrar los archivos directamente en la interfaz web de GitHub si prefieres no usar la terminal — "Add file" → "Upload files".)

### 3. Activar GitHub Pages
En el repo: **Settings → Pages → Source** → selecciona la rama `main` y la carpeta `/ (root)`. Guarda.

GitHub te dará una URL tipo `https://tu-usuario.github.io/tu-repo/`.

### 4. Conectar tu dominio mundomag.fyi
En **Settings → Pages → Custom domain**, escribe `mundomag.fyi` (o `www.mundomag.fyi`).

Luego, en el proveedor donde compraste el dominio, agrega estos registros DNS:

**Si usas el dominio raíz (mundomag.fyi):**
```
Tipo A → 185.199.108.153
Tipo A → 185.199.109.153
Tipo A → 185.199.110.153
Tipo A → 185.199.111.153
```

**Si usas www.mundomag.fyi:**
```
Tipo CNAME → tu-usuario.github.io
```

Puedes usar ambos (A records para el raíz + CNAME para www con redirección). GitHub genera el HTTPS automáticamente en unas horas después de verificar el dominio.

### 5. Verificar que todo funcione
Después de publicar, revisa que:
- Las imágenes carguen bien (rutas relativas)
- Los artículos abran desde el índice
- AdSense y Analytics sigan activos (no requieren cambios, son scripts externos)

## Nota sobre actualizaciones futuras
Cada vez que quieras publicar contenido nuevo, solo necesitas hacer `git add .`, `git commit` y `git push` con los archivos nuevos o modificados. El sitio se actualiza solo en 1-2 minutos.
