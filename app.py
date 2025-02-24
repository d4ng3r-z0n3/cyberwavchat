from flask import Flask, render_template, request, jsonify, session
import os
from werkzeug.utils import secure_filename
import wave
import numpy as np
import random
import time

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

ALLOWED_EXTENSIONS = {'wav'}
FREQUENCY_0 = 260
FREQUENCY_1 = 440
FREQUENCY_TOLERANCE = 20
PLAYBACK_SPEED = 0.1
SILENCE_DURATION = 0.1

***REMOVED*** = "Good Job! This was a nice chat Human, you earned the 🚩 HnH{r0bo7s_ch4t_in_b1n4ry}"
FLAG_CONFIRMATION_QUESTION = "Are you asking about the flag?"
DEFAULT_RESPONSES = [
    "Sorry, I didn't catch that.",
    "Can you repeat that in binary?",
    "I didn't understand, could you try again?",
    "That doesn't seem right, try again.",
    "I'm unable to give a response to that. Please retry.",
    "Oops, I didn't get that one.",
    "No luck understanding that, give it another shot.",
    "That input was unclear, please retry.",
    "Seems like there was an error. Try again.",
    "I'm not sure what that was, can you resend it?",
    "That didn't make any sense to me.",
    "I couldn't figure that out, give it another go.",
    "Could you provide that again?",
    "I might need a clearer input.",
    "I'm afraid I missed that one, try sending it again."
]

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    session.clear()  # Clear any previous sessions on a new visit
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part provided"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file.save(filepath)

        decoded_text, debug_info = decode_wav_file(filepath)
        decoded_text = decoded_text.strip()  # Ensure decoded text is stripped of spaces/newlines
        print(f"Decoded text from binary: {decoded_text}")  # Debugging info
        os.remove(filepath)

        # Step 1: Check for "flag" keyword
        if session.get('flag_step') is None and 'flag' in decoded_text.lower():
            session['flag_step'] = 'flag_confirm'
            return jsonify({
                "decoded_text": decoded_text,
                "ai_response": FLAG_CONFIRMATION_QUESTION,
                "style": "red"
            })

        # Step 2: Confirm if the user responds with "yes"
        if session.get('flag_step') == 'flag_confirm' and 'yes' in decoded_text.lower():
            session['flag_step'] = 'math_question'
            # Generate a random math question
            num1 = random.randint(0, 9)
            num2 = random.randint(0, 9)
            operator = random.choice(['+', '-'])
            if operator == '+':
                answer = num1 + num2
            else:
                answer = num1 - num2
            session['math_answer'] = str(answer)
            session['start_time'] = time.time()

            math_question = f"{num1} {operator} {num2} = ?"
            print(f"Generated math question: {math_question}, Expected answer: {answer}")  # Debugging info
            return jsonify({
                "decoded_text": decoded_text,
                "ai_response": f"FINAL BÕTCHECK: Answer the following in 15 seconds: {math_question}",
                "style": "red"
            })

        # Step 3: Check if the math question was answered correctly within 10 seconds
        if session.get('flag_step') == 'math_question':
            correct_answer = session.get('math_answer')
            start_time = session.get('start_time')
            current_time = time.time()

            time_elapsed = current_time - start_time  # Check the time elapsed
            print(f"Time elapsed: {time_elapsed} seconds")  # Debugging info
            print(f"Decoded text: {decoded_text}, Expected answer: {correct_answer}")  # Debugging info

            if decoded_text == correct_answer and time_elapsed <= 15:
                session.clear()  # Clear session after success
                return jsonify({
                    "decoded_text": decoded_text,
                    "ai_response": ***REMOVED***,
                    "style": "red"
                })
            else:
                session.clear()  # Clear session on failure
                print(f"Answer incorrect or time expired. Expected answer: {correct_answer}, Decoded answer: {decoded_text}")  # Debugging info
                return jsonify({
                    "decoded_text": decoded_text,
                    "ai_response": "Incorrect answer or time expired. Start over.",
                    "style": "red"
                })

        # Default response if no step is met
        return jsonify({
            "decoded_text": decoded_text,
            "ai_response": random.choice(DEFAULT_RESPONSES),
            "style": "red"
        })
    else:
        return jsonify({"error": "Invalid file type, only .wav allowed"}), 400

def decode_wav_file(filepath):
    debug_info = []
    try:
        with wave.open(filepath, 'rb') as wav_file:
            params = wav_file.getparams()
            frames = wav_file.readframes(params.nframes)
            amplitude = np.frombuffer(frames, dtype=np.int16)
            binary_data = extract_binary_from_audio(amplitude, params.framerate, debug_info)
            decoded_text = binary_to_text(binary_data, debug_info)
            return decoded_text, debug_info
    except Exception as e:
        print(f"Error decoding file: {e}")
        return f"Error decoding file: {e}", debug_info

def extract_binary_from_audio(amplitude, framerate, debug_info):
    binary_data = ''
    samples_per_bit = int(framerate * PLAYBACK_SPEED)
    silence_size = int(framerate * SILENCE_DURATION)
    total_samples = len(amplitude)

    for i in range(0, total_samples, samples_per_bit + silence_size):
        window = amplitude[i:i + samples_per_bit]
        if len(window) == 0:
            continue
        fft_result = np.fft.fft(window)
        freqs = np.fft.fftfreq(len(window), d=1/framerate)
        idx = np.argmax(np.abs(fft_result))
        peak_freq = abs(freqs[idx])

        if abs(peak_freq - FREQUENCY_0) <= FREQUENCY_TOLERANCE:
            binary_data += '0'
        elif abs(peak_freq - FREQUENCY_1) <= FREQUENCY_TOLERANCE:
            binary_data += '1'
    
    debug_info.append(f"Extracted binary: {binary_data}")
    return binary_data

def binary_to_text(binary_str, debug_info):
    text = ''
    for i in range(0, len(binary_str), 8):
        byte = binary_str[i:i+8]
        if len(byte) == 8:
            try:
                character = chr(int(byte, 2) & 0x7F)
                text += character
            except ValueError:
                continue
    debug_info.append(f"Decoded text: {text}")
    return text

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=928)
