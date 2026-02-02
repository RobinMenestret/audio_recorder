
import gradio as gr
from pydub import AudioSegment
import os
from datetime import datetime
import subprocess

OUTPUT_DIR = "chapitres"
os.makedirs(OUTPUT_DIR, exist_ok=True)
CHAPTERS_LIST = []

def save_chapter(audio, chapter_title):
    if audio is None:
        return "Aucun enregistrement."

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = chapter_title.strip().replace(" ", "_") or f"chapitre_{timestamp}"

    wav_path = f"{OUTPUT_DIR}/{safe_title}.wav"
    m4a_path = f"{OUTPUT_DIR}/{safe_title}.m4a"

    sample_rate, data = audio
    audio_segment = AudioSegment(
        data.tobytes(),
        frame_rate=sample_rate,
        sample_width=data.dtype.itemsize,
        channels=1
    )
    audio_segment.export(m4a_path, format="ipod")  # M4A

    # On garde en mémoire pour le M4B
    CHAPTERS_LIST.append((m4a_path, safe_title))
    return f"Chapitre sauvegardé : {m4a_path}"

def export_m4b(book_title="Mon_Livre"):
    if not CHAPTERS_LIST:
        return "Aucun chapitre à exporter."

    # Concaténation M4A
    concat_file = f"{OUTPUT_DIR}/concat.txt"
    with open(concat_file, "w") as f:
        for file_path, _ in CHAPTERS_LIST:
            f.write(f"file '{os.path.abspath(file_path)}'\n")

    # Génération du fichier de métadonnées FFmpeg
    metadata_file = f"{OUTPUT_DIR}/metadata.txt"
    total_ms = 0
    with open(metadata_file, "w", encoding="utf-8") as f:
        f.write(";FFMETADATA1\n")
        for idx, (file_path, title) in enumerate(CHAPTERS_LIST):
            audio_segment = AudioSegment.from_file(file_path)
            duration_ms = int(audio_segment.duration_seconds * 1000)
            f.write("[CHAPTER]\n")
            f.write("TIMEBASE=1/1000\n")
            f.write(f"START={total_ms}\n")
            f.write(f"END={total_ms + duration_ms}\n")
            f.write(f"title={title}\n")
            total_ms += duration_ms

    output_m4b = f"{OUTPUT_DIR}/{book_title}.m4b"

    # Commande FFmpeg pour concat + chapitres
    subprocess.run([
        "ffmpeg", "-f", "concat", "-safe", "0", "-i", concat_file,
        "-i", metadata_file,
        "-map_metadata", "1",
        "-c", "copy",
        output_m4b
    ], check=True)

    return f"Livre audio exporté : {output_m4b}"

# --- Interface Gradio ---
with gr.Blocks(title="Livre Audio – Enregistrement et Export M4B") as app:
    gr.Markdown("## 🎙️ Enregistrement de livre audio avec chapitres")

    chapter_title = gr.Textbox(label="Titre du chapitre", placeholder="Chapitre 1")
    audio_input = gr.Audio(
        sources=["microphone"],
        type="numpy",
        label="Enregistrement"
    )
    save_button = gr.Button("💾 Sauvegarder le chapitre")
    status = gr.Textbox(label="Statut", interactive=False)

    export_button = gr.Button("📦 Export M4B")
    export_status = gr.Textbox(label="Export", interactive=False)

    save_button.click(fn=save_chapter, inputs=[audio_input, chapter_title], outputs=status)
    export_button.click(fn=export_m4b, inputs=[chapter_title], outputs=export_status)

app.launch()