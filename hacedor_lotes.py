import streamlit as st
import asyncio
import edge_tts
import io
import zipfile
import time

# Configuración de la página
st.set_page_config(page_title="Audiolibros España", page_icon="🇪🇸")

st.title("🎙️ Hacedor de Audiolibros (Voces de España)")
st.markdown("Procesador optimizado con voces masculinas peninsulares.")

# 1. SELECCIÓN DE VOCES MASCULINAS DE ESPAÑA
voces_dict = {
    "Álvaro (Estándar)": "es-ES-AlvaroNeural",
    "Darío (Profundo)": "es-ES-DarioNeural",
    "Arnau (Suave)": "es-ES-ArnauNeural"
}

voz_seleccionada = st.selectbox("Selecciona un narrador:", list(voces_dict.keys()))

# 2. CARGA DE ARCHIVOS
archivos_subidos = st.file_uploader("Sube tus capítulos (.txt):", type="txt", accept_multiple_files=True)

# 3. FUNCIÓN DE CONVERSIÓN (SIN PARÁMETROS EXTRA PARA EVITAR ERRORES)
async def procesar_audio(texto, voz_code):
    communicate = edge_tts.Communicate(texto, voz_code)
    audio_data = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_data += chunk["data"]
    return audio_data

# 4. BOTÓN Y LÓGICA
if st.button("🚀 Iniciar Conversión"):
    if not archivos_subidos:
        st.error("Por favor, sube los archivos primero.")
    else:
        # Ordenamos los archivos por nombre
        archivos_ordenados = sorted(archivos_subidos, key=lambda x: x.name)
        
        buf_zip = io.BytesIO()
        barra = st.progress(0)
        estado = st.empty()
        
        exitos = 0
        
        with zipfile.ZipFile(buf_zip, "w") as zf:
            for i, archivo in enumerate(archivos_ordenados):
                nombre_mp3 = archivo.name.replace(".txt", ".mp3")
                estado.info(f"Convirtiendo: {nombre_mp3}...")
                
                try:
                    # Leer y limpiar el texto
                    contenido = archivo.read().decode("utf-8", errors="ignore").strip()
                    
                    if contenido:
                        # Ejecutamos la conversión
                        codigo_voz = voces_dict[voz_seleccionada]
                        # Usamos asyncio.run de forma directa para estabilidad
                        audio_bin = asyncio.run(procesar_audio(contenido, codigo_voz))
                        
                        if audio_bin:
                            zf.writestr(nombre_mp3, audio_bin)
                            exitos += 1
                    
                    # Pausa de 1.5 segundos (importante para no ser bloqueado)
                    time.sleep(1.5)
                    
                except Exception as e:
                    st.error(f"Error en {archivo.name}: {e}")
                
                # Actualizar progreso
                barra.progress((i + 1) / len(archivos_ordenados))
        
        estado.success(f"✅ ¡Completado! Se han generado {exitos} archivos MP3.")
        
        if exitos > 0:
            st.download_button(
                label="⬇️ Descargar Carpeta de Audios (.zip)",
                data=buf_zip.getvalue(),
                file_name="mis_audiolibros_espanoles.zip",
                mime="application/zip"
            )