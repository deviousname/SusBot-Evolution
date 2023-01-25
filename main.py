#Susbot Evolution
import crewmate
import requests
import os
import json
import keyboard
import socketio #requires: python-socketio[client]==4.6.1
import random
import time
import urllib.request
import PIL
from PIL import Image
import threading
from threading import Thread, Semaphore
import queue
from queue import Queue
import math
from math import cos, sin
import numpy as np
from numpy import sqrt
import itertools
from itertools import cycle
import tkinter as tk
from tkinter import Label, Frame, Button
from functools import partial
from collections import Counter
from ast import literal_eval as make_tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

driver = webdriver.Firefox()
sio = socketio.Client()

semaphore = Semaphore(13)
lock=threading.Lock()

# Color data:
colors = {(255, 255, 255): 0,  (196, 196, 196): 1,
          (136, 136, 136): 2,  (85, 85, 85): 3,
          (34, 34, 34): 4,     (0, 0, 0): 5,
          (0, 54, 56): 39,     (0, 102, 0): 6,
          (27, 116, 0): 49,    (71, 112, 80): 40,
          (34, 177, 76): 7,    (2, 190, 1): 8,
          (81, 225, 25): 9,    (148, 224, 68): 10,
          (152, 251, 152): 41, (251, 255, 91): 11,
          (229, 217, 0): 12,   (230, 190, 12): 13,
          (229, 149, 0): 14,   (255, 112, 0): 42,
          (255, 57, 4): 21,    (229, 0, 0): 20,
          (206, 41, 57): 43,   (255, 65, 106): 44,
          (159, 0, 0): 19,     (107, 0, 0): 18,
          (255, 117, 95): 23,  (160, 106, 66): 15,
          (99, 60, 31): 17,    (153, 83, 13): 16,
          (187, 79, 0): 22,    (255, 196, 159): 24,
          (255, 223, 204): 25, (255, 167, 209): 26,
          (207, 110, 228): 27, (125, 38, 205): 45,
          (236, 8, 236): 28,   (130, 0, 128): 29,
          (51, 0, 119): 46,    (2, 7, 99): 31,
          (81, 0, 255): 30,    (0, 0, 234): 32,
          (4, 75, 255): 33,    (0, 91, 161): 47,
          (101, 131, 207): 34, (54, 186, 255): 35,
          (0, 131, 199): 36,   (0, 211, 221): 37,
          (69, 255, 200): 38,  (181, 232, 238): 48}
null = [(204,204,204)]
labels = ['Snow', 'Silver', 'Iron', 'Steel', 'Titanium', 'Outer-space', 'Dark jungle',
          'Jungle', 'Dark forest', 'Forest', 'Wetlands', 'Savannah', 'Sun',
          'Gold', 'Flame', 'Pine', 'Maple', 'Oak', 'Crimson', 'Red', 'Ruby',
          'Fuchsia', 'Mahogany', 'Salmon', 'Beach', 'Sand', 'Flamingo',
          'Pink sapphire', 'Hot pink', 'Velvet', 'Lavender',
          'Ocean depths', 'Ocean', 'Sea', 'Lake', 'Sky',
          'Stainless steel', 'Aether', 'Turquoise',
          'Marshland', 'Swamp', 'Azure', 'Pumpkin',
          'Blood', 'Grapefruit', 'Amenthyst',
          'Deep sea', 'Emerald', 'Concrete',
          'Woodland', 'Jade', 'Olive']
labeled_colors = {k: labels[v] for k, v in colors.items()}
colors_reverse = {value: key for key, value in zip(colors.keys(), colors.values())}
color_values = list(colors.values())

# change the number of chart to the same as the map number you want to play on
chart = 7 # main map

autologin = True # requires Reddit account details to be put into crewmate.py if set to True
unit_measurement = 'pixels' # for measuring areas with the line tool, or can use for other tools too
regular_speed = 0.02 # 0.02 is good, will draw 1 pixel every 0.02 seconds
speed = regular_speed # you can change the speed in game too

stop_key = 'shift+d' #press this to stop all painting operations

class SusBot():        
    def __init__(self): #initiliaze class variables
        self.speed = speed
        self.load_map_into_cache()
        self.root = tk.Tk()
        self.root.title("Colors") 
        if autologin == True:
            self.login()
        else:
            driver.get(f"https://pixelplace.io/{chart}")
        self.authid, self.authtoken, self.authkey = None, None, None
        while self.authid == None and self.authtoken == None and self.authkey == None:
            try:
                self.auth_data()
            except:
                pass
        if chart != 7:
            driver.get(f"https://pixelplace.io/{chart}")
        self.emit_counter = 0
        self.hotkey_preload()
        self.color_counts = {}
        self.hotkeys()
        self.work_order ={}
        self.brush_size = 2
        self.color = self.return_color()
        connection_thread = Thread(target=self.connection)
        connection_thread.start()
        connection_thread.join()
        self.colorweights = {color: 0 for color in colors.keys()}
        self.colorfilter = set()
        self.colorfilter.add(colors_reverse[self.color])
        self.colorweights[colors_reverse[self.color]] = 1
        self.queue = queue.LifoQueue()
        self.label_frame = Frame(self.root)
        self.show_image = False
        self.label_frame.pack(side='left')
        self.update_labels()
        self.root.wm_attributes("-topmost", True)
        self.root.overrideredirect(True)
        self.root.mainloop()
        
    def hotkey_preload(self):
        self.linekey = 'x'
        self.piekey = 's'
        self.circle_fill_key = 'd'
        self.river_bend_key = 'a'
        self.darken_key = 'r'
        self.lighten_key = 'shift+r'
        self.copykey = 'f8'
        self.pastekey = 'f9'
        self.windkey = 'shift+v'
        self.downspeed = 'shift+insert'
        self.upspeed = 'shift+del'
        self.fillborderskey = 'b'
        self.sample_colors_key='`'
        
        # SET YOUR HOTKEY DESCRIPTIONS HERE:
        controls = ['',
            "Controls:",
            '',
            f'{self.sample_colors_key} # hold/drag/release to get areas colors',
            f'{self.sample_colors_key} # tapping will move the color menu',
            f'-left click on a color menu color to remove half of that color',
            f'-right click to remove all of that color',
            f'-hover mouse over menu and use scroll wheel to the value',
            f'-press ~ (Tilde) to remove half of all sampled colors',
            f'-spamming ~ (Tilde) will completely clear the sampled colors',
            '',   
            f'{self.linekey} # hold/drag/release to draw line',
            f'{self.piekey} # hold/drag/release to draw circle outline',
            f'{self.circle_fill_key} # hold/drag/release to draw filled circle',
            f'{self.windkey} # press to pour bucket',
            '',
            f'{self.fillborderskey} # hold/drag/release over an area to draw borders',
            f'{self.river_bend_key} # hold/drag/release to draw bendable line',
            f'{self.darken_key} # hold/drag/release to darken area',
            f'{self.lighten_key} # hold/drag/release to lighten area',
            '',
            f'{self.copykey} # hold/drag/release over an area to copy',
            f'{self.pastekey} # press to paste centered at location',
            '',
            f'{self.downspeed} # decrease bot speed',
            f'{self.upspeed} # increase bot speed',

            f'stop key = {stop_key}',
            '',
            '# ~ ~ ~ ~ ~* ~* ~ ~*','']
        for control in controls:
            print(control)
        
    def circle_outline_hotkey(self, key):
        semaphore.acquire()
        thread = Thread(target=self.circle_outline, args = key)
        thread.start()
        thread.join()
        semaphore.release()

    def mighty_wind_hotkey(self, key):
        semaphore.acquire()
        thread = Thread(target=self.mighty_wind, args = (key,))
        thread.start()
        thread.join()
        semaphore.release()
            
    def border_helper_hotkey(self, key):
        semaphore.acquire()
        thread = Thread(target=self.border_helper, args = key)
        thread.start()
        thread.join()
        semaphore.release()

    def transparent_circle_hotkey(self, key):
        semaphore.acquire()
        thread = Thread(target=self.transparent_circle, args = (key,))
        thread.start()
        thread.join()
        semaphore.release()
        
    def circle_fill_hotkey(self, key):
        semaphore.acquire()
        thread = Thread(target=self.circle_fill, args = key)
        thread.start()
        thread.join()
        semaphore.release()
        
    def thick_line_hotkey(self, key, width):
        semaphore.acquire()
        thread = Thread(target=self.thick_line, args=(self.linekey, width))
        thread.start()
        thread.join()
        semaphore.release()
        
    def river_bend_hotkey(self, key):
        semaphore.acquire()
        thread = Thread(target=self.river_bend, args = key)
        thread.start()
        thread.join()
        semaphore.release()

    def hotkeys(self):
        keyboard.add_hotkey(self.linekey,lambda:Thread(target=self.thick_line_hotkey, args=(self.linekey,1)).start())
        keyboard.add_hotkey(self.piekey,lambda:Thread(target=self.circle_outline_hotkey, args=(self.piekey)).start())
        keyboard.add_hotkey(self.circle_fill_key, lambda: Thread(target=self.circle_fill_hotkey, args=(self.circle_fill_key)).start())
        keyboard.add_hotkey(self.copykey,lambda: self.copypaste(self.copykey))                            
        keyboard.add_hotkey(self.pastekey,lambda: self.copypaste(self.pastekey))                           
        keyboard.add_hotkey(self.windkey,lambda: Thread(target=partial(self.mighty_wind_hotkey, self.windkey)).start())
        keyboard.add_hotkey(self.fillborderskey,lambda:Thread(target=self.border_helper_hotkey, args=(self.fillborderskey)).start())                            
        keyboard.add_hotkey(self.sample_colors_key, lambda:Thread(target=self.sample_colors).start())
        keyboard.add_hotkey(self.darken_key,lambda:Thread(target=partial(self.transparent_circle_hotkey, self.darken_key)).start())
        keyboard.add_hotkey(self.lighten_key,lambda:Thread(target=partial(self.transparent_circle_hotkey, self.lighten_key)).start())
        keyboard.add_hotkey(self.river_bend_key,lambda:Thread(target=self.river_bend_hotkey(self.river_bend_key)).start())                     
        keyboard.add_hotkey(self.downspeed, lambda: self.change_speed(self.downspeed))
        keyboard.add_hotkey(self.upspeed, lambda: self.change_speed(self.upspeed))
        for i in range(1, 10):
            keyboard.add_hotkey(f'{i}', lambda i=i: Thread(target=self.adjust_weights(i)).start())
            keyboard.add_hotkey(f'shift+{i}', lambda i=i: Thread(target=self.adjust_weights(-i)).start())
        keyboard.add_hotkey('shift+~', lambda: Thread(target=self.adjust_weights('half')).start())
        
    def emitsleep(self, x, y, color = None):
        try:
            self.queue.put((x, y, color))        
            x, y, color = self.queue.get(block=False)
            if color == None:
                color = self.random_weighted_color()
            if self.cache[x, y] not in [colors_reverse[color]] + null + [i for i in self.colorfilter]:
                lock.acquire()
                sio.emit('p',[x, y, color, 1])
                if keyboard.is_pressed(stop_key):
                    self.queue = queue.LifoQueue()
                time.sleep(self.speed - (self.start - time.perf_counter()))
                self.start = time.perf_counter()
                lock.release()
        except:
            pass
            
    def sample_colors(self):
        try:
            self.update_window_pos()
            end, start = self.zone(self.sample_colors_key)
            x2, y2 = start
            x1, y1 = end
            r = int(math.sqrt((x2-x1)**2 + (y2-y1)**2))
            coords = self.spiral_coords(start, r)
            color_count = {}  # create a dictionary to store the color occurrences
            for coord in coords:
                if self.cache[coord[0], coord[1]]:
                    color = self.cache[coord[0], coord[1]]  # get the color at the current coord
                else:
                    continue
                if color == (204, 204, 204):  # check if the color is (204, 204, 204)
                    continue  # skip this iteration if the color is (204, 204, 204)
                if color in color_count:
                    color_count[color] += 1  # increase the count if the color already exists in the dictionary
                else:
                    color_count[color] = 1  # add the color to the dictionary with a count of 1
            for color, count in color_count.items():
                self.colorweights[color] += count  # increase the weight for each color by the count of that color
            self.reduce_weights()
        except:
            pass
        
    def transparent_circle(self, key):
        try:
            end, start = self.zone(key)
        except:
            return
        x2, y2 = end
        x1, y1 = start
        r = int(math.sqrt((x2-x1)**2 + (y2-y1)**2))
        coords = self.spiral_coords(start, r)            
        self.start = time.perf_counter()        
        if key == self.darken_key:
            self.emitsleep(x2, y2, self.reverse_color_shift(self.cache[x2, y2]))
        elif key == self.lighten_key:
            self.emitsleep(x2, y2, self.color_shift(self.cache[x2, y2]))
        for coord in coords:
            if keyboard.is_pressed(stop_key):
                return
            if key == self.darken_key:
                self.emitsleep(coord[0], coord[1], self.reverse_color_shift(self.cache[coord[0], coord[1]]))
            elif key == self.lighten_key:
                self.emitsleep(coord[0], coord[1], self.color_shift(self.cache[coord[0], coord[1]]))
                
    def river_bend(self, key):
        self.start=time.perf_counter()
        try:
            river_thickness_fill_list = []
            rotations = [1,-1]
            rotation_cycle = cycle(rotations)
            def r():
                return next(rotation_cycle)
            start, end, control = self.xy(),self.xy(),self.xy()
            control_stack = set()
            while keyboard.is_pressed(key):
                self.xy()
                control_stack.add((self.x, self.y))
            end = self.xy()
            control_average = []
            control_average += self.coordinate_list_average(control_stack, start, end)
            distance = self.distance(start, end) + self.distance(control_average, end)
            river_set = set()
            for i in range(distance):
                t = i / distance
                xfl = (1-t)**2 * start[0] + (2 * t * (1-t) * control_average[0]) + (t**2 * end[0])
                yfl = (1-t)**2 * start[1] + (2 * t * (1-t) * control_average[1]) + (t**2 * end[1])
                for i in ((xfl+r(),yfl),(xfl+r(),yfl),(xfl,yfl+r()),(xfl,yfl+r())):                    
                    self.emitsleep(i[0], i[1])
                    if keyboard.is_pressed(stop_key):
                        return
        except:
            pass
        
    def copypaste(self, key):#need to update to queue usage
        self.start = time.perf_counter()
        try:
            if key == self.copykey:
                self.work_order=set()
                self.xy()
                start, end = self.zone(key)
                x1, y1 = start
                x2, y2 = end           
                print('Copying.')
                cx = (x2 - x1) // 2
                cy = (y2 - y1) // 2
                for X in range(x1, x2):
                    for Y in range(y1, y2):
                        if self.cache[X, Y] not in null + [i for i in self.colorfilter]:
                            self.work_order.add((X-x1-cx, Y-y1-cy, colors[self.cache[X, Y]]))
                print('Done.')
            elif key == self.pastekey:
                if self.work_order:
                    print('Pasting.')
                    self.xy()
                    for i in self.work_order:
                        self.emitsleep(i[0]+self.x, i[1]+self.y, i[2])
                        if keyboard.is_pressed(stop_key):
                            return
        except:
            pass
        
    def circle_outline(self, key):
        try:
            self.start = time.perf_counter()
            try:
                start, end = self.zone(key)
            except:
                return
            x2, y2 = start
            x1, y1 = end
            r = int((((x2-x1)**2 + (y2-y1)**2))**0.5)
            x = r-1
            y = 0
            dx = 1
            dy = 1
            err = dx - (r << 1)
            while x >= y:
                for c in self.circxy(x1, x, y1, y):
                    self.emitsleep(c[0],c[1])
                if err > 0:
                    x -= 1
                    dx += 2
                    err += dx - (r << 1)
                if err <= 0:
                    y += 1
                    err += dy
                    dy += 2
                if keyboard.is_pressed(stop_key):
                    return
        except:
            pass

    def mighty_wind(self, key):
        try:
            self.start = time.perf_counter()
            locs = set()            
            def locate():
              locs.add(self.xy())
            locate()
            while len(set(locs)) > 0:
                x, y = locs.pop()
                for i in ((x, y),(x+1, y),(x-1, y),(x, y-1),(x, y+1)):
                    if self.cache[i[0], i[1]] not in null + [i for i in self.colorfilter]:
                        self.emitsleep(i[0], i[1])
                        locs.add((i[0], i[1]))
                    if keyboard.is_pressed(key):
                        locate()
                    if keyboard.is_pressed(stop_key):
                        return
        except:
            pass
        
    def border_helper(self, key):
        try:
            self.start = time.perf_counter()
            try:
                start, end = self.zone(key)
            except:
                return            
            x2, y2 = start
            x1, y1 = end
            border_list = set()
            for x in range(min(x1,x2), max(x1,x2)):
                for y in range(min(y1,y2), max(y1,y2)):
                    for i in ((x, y),(x+1, y),(x-1, y),(x, y-1),(x, y+1)):
                        for ap in [(i[0]+1, i[1]), (i[0]-1, i[1]), (i[0], i[1]+1), (i[0], i[1]-1)]:
                            if self.cache[ap[0], ap[1]] in [(204,204,204)] and self.cache[i[0], i[1]] not in [(204,204,204)]:
                                border_list.add((i[0], i[1]))
            for i in border_list:
                self.emitsleep(i[0], i[1])
        except:
            pass
        
    def circle_fill(self, key):
        try:
            self.start = time.perf_counter()
            try:
                start, end = self.zone(key)
            except:
                return        
            x2, y2 = start
            x1, y1 = end
            r = int((((x2-x1)**2 + (y2-y1)**2))**0.5)
            x = r-1
            y = 0
            dx = 1
            dy = 1
            err = dx - (r << 1)
            set1=set()
            while x >= y:
                for c in self.circxy(x1, x, y1, y):
                    set1.add((c[0], c[1]))
                if err > 0:
                    x -= 1
                    dx += 2
                    err += dx - (r << 1)
                if err <= 0:
                    y += 1
                    dy += 2
                    err += dy
            for i in range(x1-r,x1+r):
                for j in range(y1-r,y1+r):
                    if ((i-x1)**2 + (j-y1)**2)**0.5 <= r:
                        set1.add((i,j))
            color = self.return_color()
            for c in set1:
                self.emitsleep(c[0],c[1])
                if keyboard.is_pressed(stop_key):
                    return
        except:
            pass
        
    def thick_line(self, key, width):
        self.start = time.perf_counter()
        set1 = set()
        try:
            color=self.return_color()
            start, end = self.zone(key)
            x2, y2 = end
            x1, y1 = start
            x_difference = x2 - x1
            y_difference = y2 - y1
            x_length = abs(x_difference)
            y_length = abs(y_difference)
            length = max([x_length, y_length])
            if length == 0:
                length = 1
            if x_difference == 0:
                x_difference = 1
            if y_difference == 0:
                y_difference = 1
            slope = y_difference / x_difference
            for i in range(1, length):
                x3 = int(x1 + (i * (x_difference / length)))
                y3 = int(y1 + (i * (y_difference / length)))
                for j in range(-width // 2, width // 2 + 1):
                    set1.add((x3 + j, y3))
                    set1.add((x3, y3 + j))
            color = self.return_color()
            for c in set1:
                self.emitsleep(c[0],c[1])
        except:
            pass
               
    def update_labels(self):
        try:
            for widget in self.label_frame.winfo_children():
                widget.destroy()
            self.update_colorfilter()
            if all(val == 0 for val in self.colorweights.values()):
                self.label_frame.pack_forget()
                self.root.withdraw()
            else:
                self.root.deiconify()
                self.label_frame.pack(side='left')
                i=0
                for color, weight in self.colorweights.items():
                    if weight > 0:
                        color_name = self.get_color_name(color)
                        brightness = self.rgb_to_brightness(color)
                        if brightness < 128:
                            text_color = 'white'
                        else:
                            text_color = 'black'
                        self.label = Label(self.label_frame)
                        self.label.config(text=f"{color_name}: {weight}", bg=f'#{color[0]:02x}{color[1]:02x}{color[2]:02x}', fg=text_color)
                        self.label.bind("<Button-1>", lambda event, color=color: self.half_color_filter(color))
                        self.label.bind("<Button-3>", lambda event, color=color: self.set_colorweight_to_zero(color))
                        self.label.bind("<MouseWheel>", lambda event, color=color: self.adjust_colorweight(event, color))
                        self.label.pack()
                        i+=1
            self.root.after(100, self.update_labels)
            self.root.geometry(f"{self.root.winfo_reqwidth()}x{self.root.winfo_reqheight()}")
        except:
            pass

    def adjust_colorweight(self, event, color):
        if event.delta > 0:
            self.colorweights[color] += 1
        elif event.delta < 0:
            self.colorweights[color] -= 1
            if self.colorweights[color] < 0:
                self.colorweights[color] = 0
        
    def adjust_colorweight(self, event, color):
        if event.delta > 0:
            self.colorweights[color] += 1
        elif event.delta < 0:
            self.colorweights[color] -= 1
        
    def half_color_filter(self, color):
        self.colorweights[color] = self.colorweights[color] // 2

    def adjust_weights(self, char):
        if char in ['clear', 'half']:
            self.clear_colorweights(char)
        else:
            color = colors_reverse[self.return_color()]              
            self.colorweights[color] = max(0, self.colorweights[color] + char)
            time.sleep(self.speed*5)
        
    def clear_colorweights(self, char):
        if char == 'clear':
            for color in self.colorweights:
                if self.colorweights[color] == 1:
                    self.colorweights[color] = 0
                if self.colorweights[color] > 0:
                    self.colorweights[color] = 1                
        if char == 'half':
            for color in self.colorweights:
                self.colorweights[color] = self.colorweights[color] // 2
                if self.colorweights[color] < 0:
                    self.colorweights[color] = 0
        
    def set_colorweight_to_zero(self, color):
        self.colorweights[color] = 0
            
    def update_colorfilter(self):
        self.colorfilter.clear()
        for color, weight in self.colorweights.items():
            if weight > 0:
                self.colorfilter.add(color) 
        
    def random_weighted_color(self):
        color_weights = self.colorweights
        total_weight = sum(weight for color, weight in color_weights.items())
        try:
          color_weights = {color:weight/total_weight for color,weight in color_weights.items()}
        except:
          color = self.return_color()
          return color
        color = random.choices(list(colors_reverse.keys()),weights=color_weights.values(), k=1)
        return color[0]
        
    def rgb_to_brightness(self, rgb):
        return int(0.299*rgb[0] + 0.587*rgb[1] + 0.114*rgb[2])    

    def update_window_pos(self):
        mouse_x = self.root.winfo_pointerx()
        mouse_y = self.root.winfo_pointery()
        width, height = self.root.winfo_reqwidth(), self.root.winfo_reqheight()
        mx = mouse_x - width/2
        my = mouse_y - height/2
        mx, my = int(mx), int(my)
        self.root.geometry(f"{width}x{height}+{mx-200}+{my}")
        self.root.update()

    def reduce_weights(self):
        try:
            non_zero_weights = {color: weight for color, weight in self.colorweights.items() if weight > 0}
            gcd = non_zero_weights[next(iter(non_zero_weights))]
            for weight in non_zero_weights.values():
                gcd = math.gcd(gcd, weight)
            if gcd > 1:
                for color in non_zero_weights:
                    self.colorweights[color] = self.colorweights[color] // gcd
                return True
            return False
        except:
            pass
       
    def get_color_name(self, rgb):
        lista = labeled_colors
        return lista[rgb]
    
    def spiral_coords(self, center, radius):
      x, y = center
      coords = []
      x_offset, y_offset = 0, 0
      for r in range(radius+1):
        # Move right
        for i in range(r*2):
          x += 1
          distance = math.sqrt((x - center[0])**2 + (y - center[1])**2)
          if distance <= radius:
            coords.append((x, y))
        # Move up
        for i in range(r*2):
          y += 1
          distance = math.sqrt((x - center[0])**2 + (y - center[1])**2)
          if distance <= radius:
            coords.append((x, y))
        # Move left
        for i in range(r*2+1):
          x -= 1
          distance = math.sqrt((x - center[0])**2 + (y - center[1])**2)
          if distance <= radius:
            coords.append((x, y))
        # Move down
        for i in range(r*2+1):
          y -= 1
          distance = math.sqrt((x - center[0])**2 + (y - center[1])**2)
          if distance <= radius:
            coords.append((x, y))
      return coords

    def circxy(self, x1, x, y1, y):
        circ = [[x1 + x, y1 + y],[x1 + y, y1 + x],[x1 - y, y1 + x],[x1 - x, y1 + y],
                [x1 - x, y1 - y],[x1 - y, y1 - x],[x1 + y, y1 - x],[x1 + x, y1 - y]]
        return circ

                    
    def change_speed(self, key):
        if key == self.downspeed:
            self.speed  += 0.001
            self.speed  = float('%.3f'%self.speed)
        elif key == self.upspeed:
            self.speed  -= 0.001
            self.speed  = float('%.3f'%self.speed)
        if self.speed < 0.0155:
            print(f"Going too fast now, defaulting to {regular_speed} to prevent perma ban.")
            self.speed = regular_speed
        if self.speed == 0.016:
            print(f"Warning: You are in speed throttling territory.")
        print("Speed:", self.speed)

    def xy(self):
        try:
            self.x, self.y = make_tuple(driver.find_element(By.XPATH,'/html/body/div[3]/div[4]').text)
            return self.x, self.y
        except:
            pass
          
    def distance(self, xy1, xy2):
        return int(math.sqrt((xy2[0] - xy1[0])**2 + (xy2[1] - xy1[1])**2))

    def coordinate_list_average(self, coordinate_set, start_coordinate, end_coordinate):
        try:
            x_sum = 0
            y_sum = 0
            weight_sum = 0
            for coordinate in coordinate_set:
                distance_from_start = math.sqrt((coordinate[0] - start_coordinate[0]) ** 2 + (coordinate[1] - start_coordinate[1]) ** 2)
                distance_from_end = math.sqrt((coordinate[0] - end_coordinate[0]) ** 2 + (coordinate[1] - end_coordinate[1]) ** 2)
                weight = max(distance_from_start, distance_from_end)
                x_sum += coordinate[0] * weight
                y_sum += coordinate[1] * weight
                weight_sum += weight
            return int(x_sum/weight_sum), int(y_sum/weight_sum)
        except:
            pass

    def zone(self, key):
        x1, y1 = self.xy()
        while True:
            if not keyboard.is_pressed(key):
                break
        x2, y2 = self.xy()
        time.sleep(1)
        return [x1, y1], [x2, y2]

    def get_color_index(self):
        try:
            cid = str(driver.find_element(By.XPATH,'/html/body/div[3]/div[2]').get_attribute("style"))
            a = cid.find('(')
            b = cid.find(')');b+=1
            cid = cid[a:b]
        finally:
            return self.get_color(make_tuple(cid))
          
    def return_color(self):
        return int(self.get_color_index())
      
    def get_color(self, input1):
        if type(input1) == int:
            return input1
        elif type(input1) == tuple:
            return colors[(input1)]
          
    def color_shift(self, color):
        if isinstance(color, int):
            for c, i in colors.items():
                if i == color:
                    color = c
                    break
        color_int = None
        for c, i in colors.items():
            if c == color:
                color_int = i
                break
        if color_int is None:
            return -1
        next_color_int = (color_int + 1) % len(colors)
        while next_color_int not in colors.values():
            next_color_int = (next_color_int + 1) % len(colors)
        return next_color_int
      
    def reverse_color_shift(self, color):
        if isinstance(color, int):
            for c, i in reversed(list(colors.items())):
                if i == color:
                    color = c
                    break
        color_int = None
        for c, i in reversed(list(colors.items())):
            if c == color:
                color_int = i
                break
        if color_int is None:
            return -1
        next_color_int = (color_int - 1) % len(colors)
        while next_color_int not in colors.values():
            next_color_int = (next_color_int - 1) % len(colors)
        return next_color_int
    
    def load_map_into_cache(self):
        with open(f'{chart}.png', 'wb') as f:
            f.write(requests.get(f'https://pixelplace.io/canvas/{chart}.png?t={random.randint(9999,99999)}').content)
        self.image = PIL.Image.open(f'{chart}.png').convert('RGB')
        self.cache = self.image.load()
        self.width, self.height = self.image.size
        
    def clear_cookies(self, url):
        driver.get(url)
        driver.delete_all_cookies()
        
    def login(self):
        if autologin == True:
            self.clear_cookies('https://reddit.com')
        driver.get("https://pixelplace.io/api/sso.php?type=2&action=login")
        driver.find_element(By.ID,'loginUsername').send_keys(crewmate.username)
        driver.find_element(By.ID,'loginPassword').send_keys(crewmate.password)
        driver.find_elements(By.XPATH,'/html/body/div/main/div[1]/div/div[2]/form/fieldset')[4].click()
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH,'/html/body/div[3]/div/div[2]/form/div/input'))).click()
        try:
            WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH,'/html/body/div[5]/div[2]/a/img'))).click()
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH,'/html/body/div[3]/div[8]/a[2]/div[3]/button[2]'))).click()
        except:
            pass
        print('Logged in.')
        return
      
    def auth_data(self):
        self.authkey = driver.get_cookie("authKey").get('value')
        self.authtoken = driver.get_cookie("authToken").get('value')
        self.authid = driver.get_cookie("authId").get('value')
        
    def connection(self):
        sio.connect('https://pixelplace.io', transports=['websocket'])
        @sio.event
        
        def connect():
            sio.emit("init",{"authKey":f"{self.authkey}","authToken":f"{self.authtoken}","authId":f"{self.authid}","boardId":chart})
            threading.Timer(15, connect).start()
            
        @sio.on("p")        
        def update_pixels(p: tuple):
            try:
                for i in p:
                    self.cache[i[0], i[1]] = colors_reverse[i[2]]
            except:
                pass
            
    def visibility_state(self):
        try:
            vis = driver.execute_script("return document.visibilityState") == "visible"
        except:
            driver.switch_to.window(driver.window_handles[0])
            vis = driver.execute_script("return document.visibilityState") == "visible"
        if vis == False:
            p = driver.current_window_handle
            chwd = driver.window_handles
            for w in chwd:
                if(w!=p):
                    driver.switch_to.window(w)
                    
if __name__ == '__main__':
    susbot = SusBot()
