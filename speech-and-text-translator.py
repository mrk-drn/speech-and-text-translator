# pyaudio must be installed to use the (default) Microphone
# recognize_google() and gTTS require internet connection

import io
import pyglet
import threading
from pathlib import Path
from tkinter import *
from tkinter import scrolledtext 
from tkinter import messagebox
from tkinter import ttk
from gtts import gTTS
from google_trans_new import google_translator, LANGUAGES
import speech_recognition as sr

root = Tk()
root.title("Speech or Text Translation")

# center window
width = 1630
height = 490
pos_right = int(root.winfo_screenwidth()/2 - width/2)
pos_down = int(root.winfo_screenheight()/2 - height/2)
root.geometry("{}x{}+{}+{}".format(width, height, pos_right, pos_down))

pyglet.options["audio"] = ('directsound', 'openal', 'pulse')
f = io.BytesIO()
translation_playing = FALSE
playing_thread = NONE
translator = google_translator()
languages = [l.capitalize() for l in list(LANGUAGES.values())]
language_keys = list(LANGUAGES.keys())
translated_text = ''
default_input_language = StringVar(value='German')
default_output_language = StringVar(value='English')
r = sr.Recognizer()

# UI Elements (Buttons further below)
content_frame = Frame(root)
enter_text_label = Label(content_frame,text ="Enter Text", font = 'arial 15 bold', \
    bg ='white smoke')
output_text_label = Label(content_frame,text ="Translation", font = 'arial 15 bold', \
    bg ='white smoke')
enter_text_field = scrolledtext.ScrolledText(content_frame, width ='70', \
    height = '10', font = 'arial 12')
output_text_field = scrolledtext.ScrolledText(content_frame, width ='70', \
    height = '10', font = 'arial 12')
output_text_field.config(state=DISABLED)
input_language_label = Label(content_frame,text ="Input language", \
    font = 'arial 15 bold', bg ='white smoke')
output_language_label = Label(content_frame,text ="Output language", \
    font = 'arial 15 bold', bg ='white smoke')
input_language_combobox = ttk.Combobox(content_frame, textvariable=default_input_language, \
    values=languages, state='readonly')
output_language_combobox = ttk.Combobox(content_frame, textvariable=default_output_language, \
    values=languages, state='readonly')

# Translate text, create file-like audio object (stream) f and enable Play Button. 
# Closing stream f (f.close()) before new creation to remove old unplayed stream 
#   bytes (f.flush() did not work)
def Translate(audio_flag, audio=NONE):
    global translated_text, f
    in_language = language_keys[languages.index(input_language_combobox.get())]
    out_language = language_keys[languages.index(output_language_combobox.get())]
    output_text_field.config(state=NORMAL)
    output_text_field.delete('1.0', END)
    if audio_flag == 0:
        input_text = enter_text_field.get("1.0", END)
    elif audio_flag == 1:
        try:
            enter_text_field.delete('1.0', END)
            input_text = r.recognize_google(audio, language=in_language)
            enter_text_field.insert('1.0', input_text)
        except sr.UnknownValueError:
            messagebox.showerror("Error", "Google Speech Recognition could not \
                understand what you said. Try again.")
            return
        except sr.RequestError:
            messagebox.showerror("Error", "Could not request results from Google \
                Speech Recognition service. Check internet connection.")
            return
    else:
        raise Exception("Invalid audio_flag value.")
    translated_text = translator.translate(input_text, out_language, in_language)
    output_text_field.insert('1.0', translated_text)
    output_text_field.config(state=DISABLED)
    f.close()
    f = io.BytesIO()
    gTTS(text = translated_text, lang=out_language).write_to_fp(f)
    f.seek(0)
    button_play_translation_or_stop.config(state=NORMAL)

# seek back to beginning of file-like audio object and rename Play Button
def Reset_Play_Button():
    global f, button_play_translation_or_stop
    f.seek(0)
    button_play_translation_or_stop.config(text='Play Translation') 
    #print(str(threading.get_ident()) + 'C')
    
# executed by playing_thread
def Play():
    global translation_playing, button_play_translation_or_stop, f
    player = pyglet.media.load('_.mp3', file=f).play()
    translation_playing=TRUE
    button_play_translation_or_stop.config(text='Stop')
    while player.playing:
        if translation_playing==FALSE:
            player.pause()
            player.delete()
            #print(str(threading.get_ident()) + 'B')
            Reset_Play_Button()
            return
        else:
            pyglet.app.platform_event_loop.dispatch_posted_events()
            pyglet.clock.tick()
    translation_playing=FALSE
    Reset_Play_Button()
    
# play and listen to user clicking "Stop" 
def Play_Translation_or_Stop(): 
    global translation_playing, playing_thread
    if translation_playing==FALSE:
        playing_thread = threading.Thread(target=Play)
        playing_thread.start()
    else:
        translation_playing=FALSE
        #print(str(threading.get_ident()) + 'A')
        '''
        it seems as if joining here causes a deadlock: second thread can't access
        button_play_translation_or_stop in Reset_Play_Button() function if main
        thread is waiting. commented print() statements for investigation.
        '''
        #playing_thread.join()
        
# reset text and translation    
def Reset():
    global translated_text 
    enter_text_field.delete('1.0', END)
    output_text_field.config(state=NORMAL)
    output_text_field.delete('1.0', END)
    output_text_field.config(state=DISABLED)
    translated_text = ''
    button_play_translation_or_stop.config(state=DISABLED) 
 
# record speech and forward to translate function    
def Listen():
    global r, translated_text
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source)
        audio = r.listen(source)
    Translate(1, audio)
   
# swap the chosen languages and prior translation (if existent) 
def Swap_Languages():
    in_language = input_language_combobox.get()
    out_language = output_language_combobox.get()
    input_language_combobox.set(out_language)
    output_language_combobox.set(in_language)
    # to remove line break use 'end-1c' and not END
    prior_translation = output_text_field.get("1.0", 'end-1c')
    enter_text_field.delete('1.0', END)
    if len(prior_translation) != 0:
        enter_text_field.insert('1.0', prior_translation)
        Translate(0)

# Buttons        
button_translate_text = Button(content_frame, text = "Translate Text", \
    font = 'arial 15 bold' , command = lambda: Translate(0))
button_reset_text = Button(content_frame, font = 'arial 15 bold',text = 'Reset Text', \
    command = Reset)
button_record_and_translate = Button(content_frame, font = 'arial 15 bold', \
    fg = 'white', text = 'Record and Translate Speech', command = Listen, bg = 'red')
button_play_translation_or_stop = Button(content_frame, font = 'arial 15 bold', \
    text = 'Play Translation', command = Play_Translation_or_Stop, state = DISABLED)
button_swap_languages = Button(content_frame, font = 'arial 15 bold', \
    text = 'Swap languages', command = Swap_Languages)

# Layout
content_frame.grid(column=0, row=0)
enter_text_label.grid(column=0, row=0, columnspan=2, sticky = W, padx = 10, pady= 10)
output_text_label.grid(column=2, row=0, columnspan=2, sticky = W, padx = 10, pady=10)
enter_text_field.grid(column=0, row=1, columnspan=2, rowspan=4, padx = 10)
output_text_field.grid(column=2, row=1, columnspan=2, rowspan=4, padx = 10)
input_language_label.grid(column=0, row=5, columnspan=1, sticky = W, padx = 10, \
    pady = 10)
input_language_combobox.grid(column=1, row=5, sticky=(N, S, E, W), padx = 10, \
    pady = 10)
output_language_label.grid(column=2, row=5, columnspan=1, sticky = W, padx = 10, \
    pady = 10)
output_language_combobox.grid(column=3, row=5, sticky=(N, S, E, W), padx = 10, \
    pady = 10)
button_translate_text.grid(column=0,row=8, columnspan=1, sticky=(N, S, E, W), \
    padx = 10, pady = 10)
button_reset_text.grid(column=1, row=8, columnspan=1, sticky=(N, S, E, W), padx = 10, \
    pady = 10)
button_record_and_translate.grid(column=0, row=9, columnspan=2, sticky=(N, S, E, W), \
    padx = 10, pady = 10)
button_play_translation_or_stop.grid(column=2, row=8, columnspan=2, sticky=(N, S, E, W), \
    padx = 10, pady = 10)
button_swap_languages.grid(column=2, row=9, columnspan=2, sticky=(N, S, E, W), \
    padx = 10, pady = 10)    

root.mainloop() 

