from tkinter import *
import pygame

root = Tk() # create tkinter window
# root.geometry('904x604+230+50')

pygame.mixer.init()

def play():
    pygame.mixer.music.load("danger.mp3")
    pygame.mixer.music.play(loops=0)

button = Button(root, text = 'Play', command = play)

button.pack()
root.mainloop()