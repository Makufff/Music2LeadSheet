import os
import streamlit as st
import numpy as np
import librosa
import subprocess
from base64 import b64encode
from music21 import note, stream, meter, tempo, metadata , environment

# setup environment
us = environment.UserSettings()
us['musicxmlPath'] = r'C://Program Files//MuseScore 4//bin//MuseScore4.exe'
us['musescoreDirectPNGPath'] = r'C://Program Files//MuseScore 4//bin//MuseScore4.exe'
us['lilypondPath'] = r'C://Music2leadsheet//lilypond-2.24.3//bin//lilypond.exe'

# not updated yet :3 note C3 - C6
note_frequencies = {
    "A3": 220.0,
    "A#3": 233.1,
    "B3": 246.9, 
    "C4": 261.6,
    "C#4": 277.2,
    "D4": 293.7,
    "D#4": 311.1,
    "E4": 329.6,
    "F4": 349.2,
    "F#4": 370.0,
    "G4": 392.0,
    "G#4": 415.3,
    "A4": 440.0
}

# not updated yet :3 function =====================================
def find_bpm():
    return
def find_keys(): # not update yed :3 camelots wheel 
    return
def find_chords():
    return 
# =================================================================

#หาชื่อโน้ต
def find_closest_note(frequency):
    return min(note_frequencies.keys(), key=lambda x: abs(note_frequencies[x] - frequency))

#หาตัวโน้ต
def note_name_to_object(note_name, duration):
    return note.Note(note_name, quarterLength=duration)

#ความยาวโน้ตดนตรี
def round_duration(duration, subdivision=16):
    return round(duration * subdivision) / subdivision

# Functions สร้างกระดาษ leadsheet
def create_leadsheet(onset_results , sheet_name="Generated Leadsheet" , composer="Generate APP"):
    # สร้าง leadsheet
    leadsheet_stream = stream.Score()
    # สร้างชิ้นส่วนของ leadsheet
    part = stream.Part()

    # เพิ่มส่วนประกอบใน leadsheet 
    part.append(meter.TimeSignature('4/4')) #
    part.append(tempo.MetronomeMark(number=60))  # Adjust the tempo as needed

    # เพิ่ม Note ทั้งหมดลงใน leadsheet
    for result in onset_results:
        rounded_duration = round_duration(result['duration'])
        note_obj = note_name_to_object(result['detected_note'], rounded_duration)
        part.append(note_obj)

    # เพิ่มส่วนหัวข้อใน leadsheet
    leadsheet_stream.append(part)
    leadsheet_stream.insert(0, metadata.Metadata())
    leadsheet_stream.metadata.composer = composer #ชื่อผู้แต่ง
    leadsheet_stream.metadata.title = sheet_name #=ชื่อเพลง
    return leadsheet_stream

# generate_sheet --> Pdf file
def generate_sheet(y , sr , sheet_name="Generated Leadsheet" , composer="Generate APP"):
    onset_results = []
    # ทำ Onset ของแต่ละเสียง
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    onset_frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr)
    onset_times = librosa.frames_to_time(onset_frames, sr=sr)

    # Note Analysis --> สร้างชุดข้อมูลของโน๊ต
    for i in range(len(onset_times) - 1):
        start_time = onset_times[i]
        end_time = onset_times[i + 1]

        onset_interval = y[int(sr * start_time):int(sr * end_time)]

        # Fast Furious Transform
        fft_result = np.fft.fft(onset_interval)
        freqs = np.fft.fftfreq(len(onset_interval), 1/sr)
        freqs = freqs[:len(freqs)//2]
        fft_result = 2.0/len(onset_interval) * np.abs(fft_result[:len(onset_interval)//2])

        dominant_freq_index = np.argmax(fft_result)
        dominant_freq = freqs[dominant_freq_index]

        detected_note = find_closest_note(dominant_freq)

        duration = end_time - start_time
        
        # ชุดข้อมูลของโน๊ต
        onset_dict = {
            'start_time': start_time, # จุดเริ่มต้นของเสียง
            'end_time': end_time, # จุดสิ้นสุดของเสียง
            'detected_note': detected_note, # ชื่อโน๊ต
            'dominant_frequency': dominant_freq, # ความถี่สูงสุด
            'duration': duration # ความยาวของเสียง
        }

        onset_results.append(onset_dict)
    
    # สร้างชีท
    leadsheet = create_leadsheet(onset_results, sheet_name=sheet_name, composer=composer)
    # แปลงชีทเป็นไฟล์ xml สำหรับ MuseScore4
    leadsheet.write('musicxml', 'C:/Music2leadsheet/output/result.xml')
    # แปลงไฟล์ xml เป็น Pdf
    subprocess.run([us['musicxmlPath'], 'C:/Music2leadsheet/output/result.xml', '-o', 'C:/Music2leadsheet/output/result.pdf'])

# แสดง pdf file
def show_pdf(pdf_path):
    # เปิดไฟล์ pdf
    with open(pdf_path, "rb") as f:
        # อ่านไฟล์ pdf เป็น byte
        pdf_bytes = f.read()
    # แปลง byte --> base64 encoded
    pdf_base64 = b64encode(pdf_bytes).decode("utf-8")
    # สร้างไฟล์สำหรับแสดงบนเว็บโดย base64 
    pdf_display = f'<iframe src="data:application/pdf;base64,{pdf_base64}" width="700" height="800" type="application/pdf"></iframe>'
    # แสดงไฟล์ pdf ที่ได้ทำไว้
    st.markdown(pdf_display, unsafe_allow_html=True)

# Function หน้าเว็บ โดยใช้ Streamlit
def main():
    # ชื่อแอพ
    st.title("Seperate music transfrom")

    # ชื่อเพลง
    sheet_name = st.text_input("Enter Sheet Name:")
    # ชื่อคนแต่ง
    composer_name = st.text_input("Enter Composer Name:")
    # อัพโหลดไฟล์ WAV โดยใช้ Drag and Drop
    uploaded_file = st.file_uploader("Upload a WAV file", type=["wav"])

    if uploaded_file is not None: #ถ้ามีไฟล์
        st.audio(uploaded_file, format="audio/wav", start_time=0) #อัพโหลดไฟล์
        if st.button("Generate Leadsheet"): #แสดงปุ่ม Generate
            filename = "uploaded_file.wav" # ชื่อไฟล์ที่ save
            with open(filename, "wb") as f: #อ่านไฟล์เพลง
                f.write(uploaded_file.getbuffer()) #save 
            #แยกเสียง
            os.system(f"demucs -d cpu {filename}") 
            #ที่อยู่ไฟล์ เสียงร้อง
            file_path = r'C:\Music2leadsheet\separated\htdemucs\uploaded_file\vocals.wav'
            # อ่านไฟล์เพลง
            y, sr = librosa.load(file_path)

            # สร้างเพลงโดยใช้ข้อมูลที่อ่านเพลง ชื่อชีท ผู้แต่ง
            generate_sheet(y=y, sr=sr, sheet_name=sheet_name, composer=composer_name)
            # แสดง Pdf
            show_pdf(r"C:\Music2leadsheet\output\result.pdf")

if __name__ == "__main__":
    main()