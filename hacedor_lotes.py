import streamlit as st
import asyncio
import edge_tts
import io
import zipfile
import time

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="Audiolibros Pro", page_icon="🎙️")

st.title("🎙️ Hacedor de Audiolibros Pro")

# --- SECCIÓN LATERAL: DATOS DEL LIBRO ---
st.sidebar.header("📝 Datos del Libro")
titulo_libro = st.sidebar.text_input("Nombre del libro:", "Mi Libro")
autor_libro = st.sidebar.text_input("Autor:", "Autor Desconocido")
nombre_archivo_final = f"{autor_libro} - {titulo_libro}.zip"

# Álvaro es el narrador más estable actualmente
voces_dict = {
    "Álvaro (Voz Principal)": "es-ES-AlvaroNeural",
    "Darío (Voz Alternativa)": "es-ES-DarioNeural",
    "Jorge (Castelar)": "es-ES-CastelarNeural"
}

voz_seleccionada = st.sidebar.selectbox("Selecciona la voz:", list(voces_dict.keys()))

# 2. CARGA DE ARCHIVOS
archivos_subidos = st.file_uploader("Sube tus capítulos (.txt):", type="txt", accept_multiple_files=True)

# 3. FUNCIÓN DE CONVERSIÓN
async def procesar_audio(texto, voz_code):
    try:
        communicate = edge_tts.Communicate(texto, voz_code)
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        return audio_data
    except:
        return None

# 4. BOTÓN Y LÓGICA
if st.button("🚀 Iniciar Conversión Masiva"):
    if not archivos_subidos:
        st.error("Por favor, sube los archivos primero.")
    else:
        archivos_ordenados = sorted(archivos_subidos, key=lambda x: x.name)
        buf_zip = io.BytesIO()
        barra = st.progress(0)
        estado = st.empty()
        exitos = 0
        
        with zipfile.ZipFile(buf_zip, "w") as zf:
            for i, archivo in enumerate(archivos_ordenados):
                nombre_mp3 = archivo.name.replace(".txt", ".mp3")
                estado.info(f"Procesando {i+1}/{len(archivos_ordenados)}: {nombre_mp3}")
                
                try:
                    contenido = archivo.read().decode("utf-8", errors="ignore").strip()
                    if contenido:
                        codigo_voz = voces_dict[voz_seleccionada]
                        
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        audio_bin = loop.run_until_complete(procesar_audio(contenido, codigo_voz))
                        loop.close()
                        
                        if audio_bin:
                            zf.writestr(nombre_mp3, audio_bin)
                            exitos += 1
                    
                    time.sleep(1.8) # Pausa de seguridad
                    
                except Exception as e:
                    st.error(f"Error en {archivo.name}: {e}")
                
                barra.progress((i + 1) / len(archivos_ordenados))
        
        estado.success(f"✅ ¡Proceso completado! {exitos} capítulos listos.")
        
        if exitos > 0:
            st.download_button(
                label=f"⬇️ Descargar: {nombre_archivo_final}",
                data=buf_zip.getvalue(),
                file_name=nombre_archivo_final,
                mime="application/zip"
            )
