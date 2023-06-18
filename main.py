#Susbot Evolution, by deviousname
import requests
import os
import re
import json
import keyboard
import socketio # requires: python-socketio[client]==4.6.1
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
from tkinter import Label, Frame, Button #pip install tk
from functools import partial
from collections import Counter, deque
from ast import literal_eval as make_tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import bisect
from scipy.stats import norm

# change the map number:
chart = 7

# speed settings
regular_speed = 0.015 # 0.02 is good, will draw 1 pixel every 0.02 seconds
speed = regular_speed # you can change the speed in game too

# Emergency Stop Button:
# - this will stop all threads
# - and await your next command
stop_key = 'shift+d'

print('')
class Item:
    def __init__(self):
        self.actions = {
            "acquired": ["swindled", "snatched", "claimed", "seized", "secured"],
            "bought": ["conned", "acquired", "procured", "obtained", "stole"],
            "stole": ["swiped", "lifted", "pinched", "pirated", '"borrowed"'],
        }
        self.descriptors = {
            "worn": ["Ꭿ battered", "Ꭿ tattered", "ඞ worn", "Ꭿ weathered","ꇺ damaged"],
            "old": ["ꇺn ancient", "ꇺn old", "ඞn antique", "ඞ vintage","Ꭿ stinky"],
            "dusty": ["ꇺ dusty", "ꇺ dingy", "Ꭿ dreary", "ඞ drab", "Ꭿ shiny"],
            "new": ["ඞ resplendent", "Ꭿ new", "ꇺn immaculate", "Ꭿ pristine", "ඞ mint"],
        }
        self.objects = {
            "shiny": ["gem", "scepter", "jewel", "coin"],
            "dagger": ["dagger", "map", "instrument", "rock"],
            "gear": ["sword", "purse", "scimitar", "music box", "guitar"]
        }
        self.action = random.choice(list(self.actions.keys()))
        self.descriptor = random.choice(list(self.descriptors.keys()))
        self.object = random.choice(list(self.objects.keys()))

    def generate_message(self):
        action = random.choice(self.actions[self.action])
        descriptor = random.choice(self.descriptors[self.descriptor])
        obj = random.choice(self.objects[self.object])

        return f"{action} {descriptor} {obj}"

class ScoredItem(Item):
    def __init__(self):
        super().__init__()
        self.score_actions = {
            "acquired": 3,
            "bought": 2,
            "stole": 1,
        }
        self.score_descriptors = {
            "worn": 2,
            "old": 4,
            "dusty": 6,
            "new": 8,
        }
        self.score_objects = {
            "shiny": 3,
            "dagger": 5,
            "gear": 7,
        }

    def generate_score(self):
        score = self.score_actions[self.action] + self.score_descriptors[self.descriptor] + self.score_objects[self.object]
        return min(100, score)
total = 0
for i in range(3):
    scored_item = ScoredItem()
    item_message = scored_item.generate_message()
    item_score = scored_item.generate_score()
    total += item_score 
    print("  " * (i * 2) + f"{item_message.capitalize()} + ${item_score}" + '\n')
    
print(' Buying:',total,'gallons of paint.')
print('\n   (n0 r3fUnD$)\n')

# start driver class for web browser and socketio
sio = socketio.Client()

firefox_options = Options()
firefox_options.binary_location = r'C:\Program Files\Mozilla Firefox\firefox.exe'
driver = webdriver.Firefox(options=firefox_options)

# create locks
lock = threading.Lock()
zone_lock = threading.Lock()
function_lock = threading.Lock()

# set up color data:
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

#titles and labels must be same length as number of colors
labels = ['Snow', 'Silver', 'Iron', 'Steel', 'Titanium', 'Outer Space', 'Dark Jungle',
          'Jungle', 'Dark Forest', 'Forest', 'Wetlands', 'Savannah', 'Sun',
          'Gold', 'Flame', 'Pine', 'Maple', 'Oak', 'Crimson', 'Red', 'Ruby',
          'Fuchsia', 'Mahogany', 'Salmon', 'Beach', 'Sand', 'Flamingo',
          'Pink Sapphire', 'Hot Pink', 'Velvet', 'Lavender',
          'Ocean Depths', 'Ocean', 'Sea', 'Lake', 'Sky',
          'Stainless Steel', 'Aether', 'Turquoise',
          'Marshland', 'Swamp', 'Azure', 'Pumpkin',
          'Blood', 'Grapefruit', 'Amenthyst',
          'Deep Sea', 'Emerald', 'Concrete',
          'Woodland',]

titles = ['King', 'Queen', 'Jester', 'Pirate', 'Ninja', 'Knight', 'Assassin',
          'Rook', 'Pawn', 'Bishop', 'Angel', 'Artist', 'Pharoah', 'Sultan',
          'Behemoth', 'Demon', 'Lawyer', 'Adventurer', 'Viking', 'Samurai',
          'Mage', 'Witch', 'Dwarf', 'Elf', 'Orc', 'Goblin', 'Dragon',
          'Centaur', 'Minotaur', 'Gargoyle', 'Hydra','Champion', 'Sorcerer',
          'Paladin', 'Archer', 'Druid', 'Bard', 'Necromancer', 'Enchanter',
          'Warrior', 'Maid', 'Valkyrie', 'Shaman', 'Cleric', 'Berserker',
          'Ranger', 'Thief', 'Rogue', 'Summoner', 'Alchemist']

labeled_colors = {k: labels[v] for k, v in colors.items()}
colors_reverse = {value: key for key, value in zip(colors.keys(), colors.values())}
color_values = list(colors.values())

print('    _____   _     _   _____  ')
print('   /  ___| | |   | | /  ___| ')
print('   | |___  | |   | | | |___  ')
print('   \___  \ | |   | | \____ \ ')
print('   ____| | | |___| |  ____| |')
print('   \____/  \_______/  \____/ ')
print('     ____    _____   ______  ')
print('    /  _ |  /  _  | |__ __|  ')
print('    | |/ /  | | | |   | |    ')
print('    | |\ \  | | | |   | |    ')
print('    | |_| | | |_| |   | |    ')
print('    \____/  \____/    |_|    ')
print('                             ')

# set up the main bot class
class SusBot():

    # initiliaze class variables    
    def __init__(self): # . . .
        self.chart = chart
        self.speed = speed
        
        # set up the gui window, part 1
        self.root = tk.Tk()
        self.root.title("SusBot: Evolution")
        self.authid, self.authtoken, self.authkey = None, None, None
        print(' Please log in.')
        driver.get(f"https://pixelplace.io/{self.chart}")
        while self.authid == None and self.authtoken == None and self.authkey == None:
            try:
                self.auth_data()
            except:
                pass            
            
        if self.chart != 7:
            driver.get(f"https://pixelplace.io/{self.chart}")

        # load map into cache
        self.load_map_into_cache(self.chart)
        
        # define a bunch of variables:
        self.function_name = 'SusBot: Evolution'
        self.lastx, self.lasty = random.randint(0, total), random.randint(0, total)
        self.x, self.y = random.randint(0, total), random.randint(0, total)
        self.cx, self.cy = 0, 0
        self.semaphores = {}
        self.work_order ={}
        self.color = 5
        self.coordinates = ()
        self.start_time = time.time()
        self.sorted_color_weights = {}
        self.current_pattern_index = 0
        self.logos = True
        self.reverse_gradient = True
        self.flag = True #use for hotkey handler
        self.colorfilter = set()
        
        # colorweights init and random items:   
        self.colorweights = {color: random.randint(0, 1) for color in colors.keys()}
        self.colorweights = {color: random.randint(0, 1) if self.colorweights[color] > 0 else 0 for color in colors.keys()}
        self.colorweights = {color: random.randint(0, total) if self.colorweights[color] > 0 else 0 for color in colors.keys()}
        self.titleweights = {title: random.randint(0, total) for title in titles}
        try:
            self.material_1_weighted = labels[random.choices(list(colors_reverse.keys()),weights=self.colorweights.values(), k=1)[0]]
            self.material_2_weighted = labels[random.choices(list(colors_reverse.keys()),weights=self.colorweights.values(), k=1)[0]]
            self.material_3_weighted = labels[random.choices(list(colors_reverse.keys()),weights=self.colorweights.values(), k=1)[0]]        
            self.weighted_title = titles[random.choices(list(colors_reverse.keys()),weights=self.titleweights.values(), k=1)[0]]
        except:
            self.material_1_weighted = 'error'
            self.material_2_weighted = 'error'
            self.material_3_weighted = 'error'
            self.weighted_title = 'error'
        self.names  =  [f"{self.material_2_weighted} Miner Master", f"{self.material_2_weighted} Drill Master",
                        f'{self.material_2_weighted} Shoveler', f'{self.material_2_weighted} Earth Mover',
                        f'{self.material_2_weighted} Chisel', f'{self.material_2_weighted} Rock Ripper',
                        f'{self.material_2_weighted} Gem Cutter', f'{self.material_2_weighted} Dirt Mover',
                        f'{self.material_2_weighted} {self.material_3_weighted} Blaster',f'{self.material_2_weighted} Paintbrush',
                        f'{self.material_2_weighted} Pickaxe',f'{self.material_2_weighted} Pistol',
                        f"{self.material_2_weighted} Longsword", f"{self.material_2_weighted} Battle Axe",
                        f"{self.material_2_weighted} War Hammer", f"{self.material_2_weighted} Spear",
                        f"{self.material_2_weighted} Shield", f"{self.material_2_weighted} Halberd",
                        f"{self.material_2_weighted} Flail", f"{self.material_2_weighted} Dagger",
                        f"{self.material_2_weighted} Broadsword", f"{self.material_2_weighted} Scimitar",
                        f"{self.material_2_weighted} Wand", f"{self.material_2_weighted} Magic Crystal",
                        f"{self.material_2_weighted} Enchanted Book", f"{self.material_2_weighted} Magic Gem",
                        f"{self.material_2_weighted} Magic Amulet", f"{self.material_2_weighted} Magic Ring",
                        f"{self.material_2_weighted} Dagger", f"{self.material_2_weighted} Shield",
                        f"{self.material_2_weighted} Magic Potion", f"{self.material_2_weighted} Magic Cloak"]
        self.random_item_name1 = random.choice(self.names)
        self.title = f' ᴌⱠᛚꞀ {self.material_1_weighted} {self.weighted_title} ꞀLⱠᴌ '
        self.mighty_wind_labels = ["",
                                   self.title,
                                   "    . . . embarks upon the land . . .\n"+
                                   " __̴ı̴̴̴ı̴̴̡ ̡̡ ̡ ̡̡ ̡͌l̡̡̡ ̡͌l̡*̡̡ ̴̡ı̴̴̡\n"+
                                   "  ͡|̲̲̲͡͡͡ ̲▫̲̲͡͡͡ ̲▫̲͡ ̲̲̲͡͡π̲̲͡͡ ̲̲͡▫̲̲͡͡ ̲̲͡▫̲̲͡͡ ̲|̡̡̡l̡̡̡̡\n"+
                                   "  ̴̡ı̴̴̡̡ı̴̡̡ ̡͌l̡̡̡̡.__̴̡̡ı̴__̴̡̡ı̴̡̡̡̡. Ꭿ\n"+
                                   " ͜ʖ ͜ʖ ͜ʖ ͜ʖ ͜ʖ ͜ʖ ͜ʖ ͜ʖ ͜ʖ ͜ʖ ͜ʖ ͜ʖ ͜ʖ ͜ʖ\n"+
                                   " ͜ʖ ͜ʖ ͜ʖ ͜ʖ ͜ʖ ͜ʖ ͜ʖ ͜ʖ ͜ʖ ͜ʖ ͜ʖ ͜ʖ ͜ʖ ͜ʖ\n"+
                                   " ͜ʖ ͜ʖ ͜ʖ ͜ʖ ͜ʖ ͜ʖ ͜ʖ ͜ʖ ͜ʖ ͜ʖ ͜ʖ ͜ʖ ͜ʖ ͜ʖ\n"+
                                   " ͜ʖ ͜ʖ ͜ʖ ͜ʖ ͜ʖ ͜ʖ ͜ʖ ͜ʖ ͜ʖ ͜ʖ ͜ʖ ͜ʖ ͜ʖ ͜ʖ\n"+
                                   " ͜ʖ ͜ʖ ͜ʖ ͜ʖ ͜ʖ ͜ʖ ͜ʖ ͜ʖ ͜ʖ ͜ʖ ͜ʖ ͜ʖ ͜ʖ ͜ʖ"]
        self.mighty_wind_labels2 = ["\n   +Pawn+", f"\n   Knight ꞀL"]
        self.mighty_wind_labels_flag = False
        self.fill_patterns = [((0, 1),(-1, 0),(0, -1),(1,0)),
        ((2, 1),(1, 2),(-2, 1),(-1, 2),(-2, -1),(-1, -2),(2, -1),(1,-2))]
            
        # get queue ready
        self.queue = queue.LifoQueue()
        
        # set up the gui window, part 2
        self.label_frame = Frame(self.root)
        self.label_frame.pack(side='left')        
        self.update_labels()        
        self.root.wm_attributes("-topmost", True)
        self.root.overrideredirect(True)

        # start connection
        self.connection_thread = threading.Thread(target=self.connection, args=(self.chart,))
        self.connection_thread.start()
        
        # load hotkeys
        self.hotkey_preload()
        self.hotkeys()
        
        # start gui
        self.update_window_pos()
        self.root.mainloop()
                
    def connection(self, chart): #maintain socket connection and update pixel cache
        sio.connect('https://pixelplace.io', transports=['websocket'])        
        @sio.event
        def connect():
            self.chart = chart
            sio.emit("init",{"authKey":f"{self.authkey}","authToken":f"{self.authtoken}","authId":f"{self.authid}","boardId":self.chart})
            threading.Timer(15, connect).start()
            
        @sio.on("p")
        def update_pixels(p: tuple):
            for i in p:
                if self.cache[i[0], i[1]] not in null:
                    self.cache[i[0], i[1]] = colors_reverse[i[2]]

    # keybindings:    
    def hotkey_preload(self):
        self.swap_colors_keys = 'shift+]'
        self.amogus_key = 'shift+e'
        self.toggle_logos_key = '='
        self.linekey = 'shift+X'
        self.circle_fill_key = 'shift+r'
        self.river_bend_key = 'shift+j'
        self.copykey = 'f8'
        self.pastekey = 'f9'
        self.fill_bucket_key = 'shift+q'
        self.gradientkey = 'shift+v'
        self.magic_wand_key = 'shift+W'
        self.toggle_pattern_key = 'f4'
        self.toggle_gradient_key = 'f2'
        self.downspeed = 'shift+insert'
        self.upspeed = 'shift+del'
        self.fillborderskey = 'shift+s'
        self.sample_colors_key='`'
        
        # key descriptions:        
        controls = ['',
            " Controls:",
            '',
            '   Press any letter to print it at your mouse location.',
            '    (the colors are decided by your equipped colors)',
            '',
            f'  {self.sample_colors_key}  hold/drag/release: areas colors',
            f'  tap {self.sample_colors_key} to reposition the color menu',
            '',
            f'  Left click color to double weight',
            f'  Right click color to divide weight',
            f'  Scroll wheel over color to finetune weight',
            f'  Middle mouse color to delete it',
            f'  Shift + ~ (shift+Tilde) to divide all',
            f'  Hold shift + ~ (shift+Tilde) to clear all',
            f'  Press 0 to switch all zeros and ones',
            '',   
            f'  {self.fill_bucket_key}   bucket tool',
            f'  {self.gradientkey}   gradient bucket tool',
            f'  {self.toggle_gradient_key}   switch gradient direction',
            f'  {self.magic_wand_key}   neural brush',
            f'  {self.toggle_pattern_key}   switch stance',
            '',
            f'  {self.circle_fill_key}   hold/drag/release: circle tool',
            f'  {self.linekey}   hold/drag/release: line tool',
            f'  {self.river_bend_key}   hold/drag/release: curve tool',
            f'  {self.fillborderskey}   hold/drag/release: border tool',
            '',
            f'  {self.copykey}   hold/drag/release: copy area',
            f'  {self.pastekey}   paste',
            '',
            f'  {self.upspeed}   increase speed',
            f'  {self.downspeed}   decrease speed',
            f'  {stop_key}   emergency stop button',
            '',
            ' # ~ ~ ~ ~ ~* ~* ~ ~*']
        for control in controls:
            print(control)

    # set up managers for threading and hotkey synchronization
    def semaphore_handler(self, semaphore):
        if semaphore not in self.semaphores:
            self.semaphores[semaphore] = Semaphore(semaphore)
        return self.semaphores[semaphore]
        
    def hotkey_handler(self, key, function_name, semaphore=None, *args):
        with function_lock:
            time.sleep(speed*2)
            self.function_name = function_name
        if semaphore is not None:
            semaphore = self.semaphore_handler(semaphore)
            if not semaphore.acquire(blocking=False):
                if not self.flag:
                    self.function_name = f"{self.function_name}."
                    self.function_name = self.function_name.replace("_", " ")
                    time.sleep(speed*5)
                    self.flag = True
            else:
                self.flag = False
                thread = Thread(target=getattr(self, self.function_name), args=(key, *args))
                thread.start()
                thread.join()
                semaphore.release()
        else:
            thread = Thread(target=getattr(self, self.function_name), args=(key, *args))
            thread.start()
            thread.join()
                
    # bind hotkeys to functions            
    def hotkeys(self):
        keyboard.add_hotkey(self.magic_wand_key,lambda: Thread(target=partial(self.hotkey_handler, self.magic_wand_key, 'magic_wand', 1)).start())
        keyboard.add_hotkey(self.swap_colors_keys,lambda: Thread(target=partial(self.hotkey_handler, self.swap_colors_keys, 'swap_colors')).start())
        keyboard.add_hotkey(self.amogus_key, lambda: Thread(target=partial(self.hotkey_handler, self.amogus_key, 'amogus')).start())        
        keyboard.add_hotkey(self.toggle_pattern_key,lambda:  Thread(target=partial(self.hotkey_handler, self.toggle_pattern_key, 'toggle_pattern')).start())
        keyboard.add_hotkey(self.toggle_gradient_key,lambda:  Thread(target=partial(self.hotkey_handler, self.toggle_gradient_key, 'toggle_gradient')).start())
        keyboard.add_hotkey(self.toggle_logos_key,lambda:Thread(target=partial(self.hotkey_handler, self.toggle_logos_key, 'toggle_logos')).start())
        keyboard.add_hotkey(self.linekey,lambda:Thread(target=partial(self.hotkey_handler, self.linekey, "thick_line")).start())
        keyboard.add_hotkey(self.circle_fill_key, lambda: Thread(target=partial(self.hotkey_handler, self.circle_fill_key, 'circle_fill')).start())
        keyboard.add_hotkey(self.copykey,lambda:  self.copypaste(self.copykey))
        keyboard.add_hotkey(self.pastekey,lambda:  self.copypaste(self.pastekey))
        keyboard.add_hotkey(self.fill_bucket_key,lambda: Thread(target=partial(self.hotkey_handler, self.fill_bucket_key, 'mighty_wind',1)).start())   
        keyboard.add_hotkey(self.gradientkey,lambda: Thread(target=partial(self.hotkey_handler, self.gradientkey, 'gradient_fill',1)).start())                            
        keyboard.add_hotkey(self.fillborderskey,lambda:Thread(target=partial(self.hotkey_handler, self.fillborderskey, 'border_tool')).start())                            
        keyboard.add_hotkey(self.sample_colors_key,lambda:Thread(target=partial(self.hotkey_handler, self.sample_colors_key, 'sample_colors')).start())                          
        keyboard.add_hotkey(self.river_bend_key, lambda: Thread(target=partial(self.hotkey_handler, self.river_bend_key, 'river_bend',1)).start()) 
        keyboard.add_hotkey(self.downspeed, lambda: self.change_speed(self.downspeed))
        keyboard.add_hotkey(self.upspeed, lambda: self.change_speed(self.upspeed))
        for i in range(1, 10):
            keyboard.add_hotkey(f'{i}', lambda i=i: Thread(target=self.adjust_weights(i)).start())
            keyboard.add_hotkey(f'shift+{i}', lambda i=i: Thread(target=self.adjust_weights(-i)).start())
        keyboard.add_hotkey('shift+~', lambda: Thread(target=self.adjust_weights('half')).start())
        keyboard.add_hotkey('0', lambda: Thread(target=self.flip_colorweights()).start())
        for letter in 'abcdefghijklmnopqrstuvwxyz':
            keyboard.add_hotkey(letter, lambda letter=letter: Thread(target=partial(self.hotkey_handler, letter, 'draw_character_v2', 1)).start())

    def scale_character(self, key, zone_width, zone_height):
        # Get the points for the character in its default size
        default_points = letters.get(key, ())
        
        # Calculate the default width and height of the character
        default_width = max(x for x, y in default_points) - min(x for x, y in default_points) if default_points else 0
        default_height = max(y for x, y in default_points) - min(y for x, y in default_points) if default_points else 0
        
        # If character is 1D (like 'i'), set default_width to a non-zero value
        if default_width == 0:
            default_width = 1

        # If character is 1D (like '-'), set default_height to a non-zero value
        if default_height == 0:
            default_height = 1

        # Calculate the scaling factors
        width_scale = round(zone_width / default_width)
        height_scale = round(zone_height / default_height)
        
        # Scale the points and adjust them to be relative to the center of the character
        scaled_points = set()
        for x, y in default_points:
            for i in range(width_scale):
                for j in range(height_scale):
                    scaled_points.add((round((x - default_width / 2) * width_scale + i), round((y - default_height / 2) * height_scale + j)))
        
        return list(scaled_points)

    def draw_character_v2(self, key, scale_factor=1):
        self.start = time.perf_counter()
        try:              
            if not keyboard.is_pressed('shift'):
                start, end = self.zone(key)
                zone_width = abs(end[0] - start[0])
                zone_height = abs(end[1] - start[1])
                letter = self.scale_character(key, zone_width, zone_height)
                for i in range(len(letter) - 1):
                    p1 = letter[i]
                    p2 = letter[i + 1]
                    points = self.interpolate_points(p1, p2)
                    for point in points:
                        # Scale the point to a larger square
                        for i in range(scale_factor):
                            try:
                                light_color, dark_color = self.get_darkest_lightest_rgb()
                            except:
                                light_color, dark_color = self.color, self.color  
                            for j in range(scale_factor):
                                self.emitsleep(point[0] + i, point[1] + j, dark_color, timer=True)
                for a, b in letter:
                    for i in range(scale_factor):
                        try:
                            light_color, dark_color = self.get_darkest_lightest_rgb()
                        except:
                            light_color, dark_color = self.color, self.color  
                        for j in range(scale_factor):
                            self.emitsleep(int(end[0] + a) + i, int(end[1] + b) + j, dark_color, priority=True, timer=True)   
                time.sleep(self.speed*3)
                for c, d in letter:
                    for i in range(scale_factor):
                        try:
                            light_color, dark_color = self.get_darkest_lightest_rgb()
                        except:
                            light_color, dark_color = self.color, self.color  
                        for j in range(scale_factor):
                            self.emitsleep(int(end[0] + c) + i, int(end[1] + d + 1) + j, light_color, priority=True, timer=True)
        except Exception as e:
            print(e)

    def emitsleep(self, x, y, color=None, priority=False, timer=None, timing_system=True):
        self.queue.put((x, y, color))
        try:
            with lock:
                x, y, color = self.queue.get(block=False)
                if x >= 0 and x <= self.width - 1 and y >= 0 and y <= self.height - 1:
                    curcol = self.cache[x,y]
                    if curcol not in null:
                        if color == None:
                            color = self.random_weighted_color()
                        if self.colorweights[curcol] > self.colorweights[colors_reverse[color]] and not priority:
                            return False
                        if priority and curcol in self.colorfilter:
                            return False
                        if keyboard.is_pressed(stop_key):
                            self.queue = queue.LifoQueue()
                            return False
                        sio.emit('p',[x, y, color, 1])
                        self.color = color
                        if timing_system:
                            time.sleep(self.speed - (self.start - time.perf_counter()))
                            self.start = time.perf_counter()
                        return True
            return False
        except:
            return False

    def brightness(self, color_weight):
        color, weight = color_weight
        return 0.2126 * color[0] + 0.7152 * color[1] + 0.0722 * color[2]


    def gradient_fill(self, key):
        self.start = time.perf_counter()
        try:
            x, y = self.xy()
            locs = set()
            curcol = self.cache[x, y]
            if curcol not in null:
                color_value = colors[curcol]
                color_weight = self.colorweights[curcol]
                self.colorweights[curcol] = 0

                locs.add(self.xy())
                self.update_colorfilter()
                
                color_weights = {color: weight for color, weight in self.colorweights.items() if color in self.colorfilter}
                self.sorted_color_weights = sorted(color_weights.items(), key=self.brightness)

                cumulative_weights = []
                total_weight = sum(weight for color, weight in self.sorted_color_weights)
                acc = 0
                for color, weight in self.sorted_color_weights:
                    acc += weight
                    cumulative_weights.append(acc / total_weight)

                y_values = [coord[1] for coord in locs]
                y_min, y_max = min(y_values), max(y_values)
                y_range = max(y_max - y_min, 1)  # avoid division by zero

                while len(locs) > 0:
                    if keyboard.is_pressed(stop_key):
                        return
                    if keyboard.is_pressed(key):
                        locs.add(self.xy())
                    y_min = min(y for x, y in locs)
                    y_max = max(y for x, y in locs)
                    y_range = y_max - y_min
                    x, y = locs.pop()
                    color_to_use = self.choose_color(y, self.reverse_gradient, y_min, y_max, y_range)
                    if self.emitsleep(x, y, color_to_use, priority=True, timer=True):
                        for a in self.fill_patterns[self.current_pattern_index]:
                            coord = (a[0] + x, a[1] + y)
                            locs.add((coord))
        except:
            pass

    def choose_color(self, y, reverse, y_min, y_max, y_range):
        sorted_colors = self.sorted_color_weights[::-1] if reverse else self.sorted_color_weights

        if len(sorted_colors) == 1:
            return colors[sorted_colors[0][0]]
        elif len(sorted_colors) == 2:
            weight_color_1 = sorted_colors[0][1]
            weight_color_2 = sorted_colors[1][1]
            middle_y = (y_min * weight_color_2 + y_max * weight_color_1) / (weight_color_1 + weight_color_2)
            return colors[sorted_colors[0][0]] if y <= middle_y else colors[sorted_colors[1][0]]
        else:
            cumulative_weights = []
            total_weight = sum(weight for color, weight in sorted_colors)
            acc = 0
            for color, weight in sorted_colors:
                acc += weight
                cumulative_weights.append(acc / total_weight)

            section_centers = [(cumulative_weights[i-1] + cumulative_weights[i]) / 2 * y_range + y_min 
                            for i in range(1, len(cumulative_weights))]
            section_centers.insert(0, y_min)
            section_centers.append(y_max)

            epsilon = 1e-5  # small constant to avoid division by zero
            probabilities = []
            for i in range(len(section_centers)-1):
                if i == 0 or i == len(section_centers)-2:  # Edge colors
                    scale = max((section_centers[i+2]-section_centers[i])/2, epsilon) if i == 0 else max((section_centers[i]-section_centers[i-2])/2, epsilon)
                else:  # Middle colors
                    scale = max((section_centers[i+1]-section_centers[i-1])/2, epsilon)
                probabilities.append(norm.pdf(y, loc=section_centers[i], scale=scale))

            # Calculate the last probability to complete the list
            last_probability = 1 - sum(probabilities)
            probabilities.append(last_probability)

            probabilities = [p * weight for p, weight in zip(probabilities, [cw[1] for cw in sorted_colors])]
            probabilities = [p / sum(probabilities) for p in probabilities]

            color = random.choices(sorted_colors, weights=probabilities, k=1)[0][0]
            return colors[color]

    # fill bucket tool
    def mighty_wind(self, key):
        self.start = time.perf_counter()
        try:
            x, y = self.xy()
            locs = set()                 
            curcol = self.cache[x, y]
            if curcol not in null:
                color_value = colors[curcol]
                color_weight = self.colorweights[curcol]
                self.colorweights[curcol] = 0            
                def locate():
                    x, y = self.xy()
                    locs.add((x, y))
                locate()
                self.update_colorfilter()
                while len(locs) > 0:
                    if keyboard.is_pressed(stop_key):
                        return
                    if keyboard.is_pressed(key):
                        locate()                    
                    x, y = locs.pop()
                    if self.emitsleep(x, y, priority=True, timer=True):
                        for a in self.fill_patterns[self.current_pattern_index]:
                            coord = (a[0]+ x, a[1] + y)
                            locs.add((coord))
        except:
            pass
        
    def magic_wand(self, key):
        self.start = time.perf_counter()
        try:
            self.x, self.y = self.xy()
            locs = set([(self.x, self.y)])
            while True:
                if self.cache[self.x, self.y] not in null:
                    self.x, self.y = locs.pop()
                    curcol = self.cache[self.x, self.y]
                    self.colorweights[curcol] = 0
                    locs.add((self.x, self.y))
                while locs:
                    self.reduce_weights()
                    self.update_colorfilter()
                    if keyboard.is_pressed(stop_key):
                        return
                    self.x, self.y = locs.pop()
                    sleep = self.emitsleep(self.x, self.y, priority = True if self.current_pattern_index == 0 else False, timer = True)            
                    for a in self.fill_patterns[0]:
                        for b in self.fill_patterns[1]:
                            coord = (a[0] * b[0] + self.x, a[1] * b[1] + self.y)
                            if coord[0] >= 0 and coord[0] <= self.width - 1 and coord[1] >= 0 and coord[1] <= self.height - 1:
                                if sleep:
                                    locs.add(coord)
                                    if self.cache[coord[0], coord[1]] not in null + [curcol]:
                                        new_value = self.colorweights[self.cache[coord[0], coord[1]]] + (a[0] * b[0] + a[1] * b[1])
                                        if new_value > 0:
                                            self.colorweights[self.cache[coord[0], coord[1]]] = new_value
                                            self.decay_large_weights()
                                else:
                                    if self.cache[coord[0], coord[1]] not in null + [curcol]:
                                        new_value = self.colorweights[self.cache[coord[0], coord[1]]] - (a[0] * b[0] + a[1] * b[1])
                                        if new_value > 0:
                                            self.colorweights[self.cache[coord[0], coord[1]]] = new_value
                                            self.decay_weights() 
                while not locs:
                    for a in set(self.fill_patterns[0]):
                        for b in set(self.fill_patterns[1]):
                            nextcolor = a[0]*b[0]+self.x, a[1]*b[1]+self.y
                            if (0 <= nextcolor[0] < self.width and 0 <= nextcolor[1] < self.height and 
                                self.cache[nextcolor] not in null):
                                locs.add(nextcolor)
        except:
            pass
    
    def interpolate_points(self, p1, p2):
        x1, y1 = p1
        x2, y2 = p2
        points = []

        if x1 != x2:
            slope = (y2 - y1) / (x2 - x1)
            for x in range(x1, x2 + 1):
                y = y1 + slope * (x - x1)
                points.append((x, int(y)))
        else:
            if y1 != y2:
                for y in range(y1, y2 + 1):
                    points.append((x1, y))

        return points

    def draw_character(self, key):
        self.start = time.perf_counter()
        try:               
            if not keyboard.is_pressed('shift'):
                start, end = self.zone(key)
                zone_width = abs(end[0] - start[0])
                zone_height = abs(end[1] - start[1])
                letter = self.scale_character(key, zone_width, zone_height)
                for i in range(len(letter) - 1):
                    p1 = letter[i]
                    p2 = letter[i + 1]
                    points = self.interpolate_points(p1, p2)
                    for point in points:
                        try:
                            light_color, dark_color = self.get_darkest_lightest_rgb()
                        except:
                            light_color, dark_color = self.color, self.color 
                        self.emitsleep(point[0], point[1], dark_color, timer=True)
                for a, b in letter:
                    try:
                        light_color, dark_color = self.get_darkest_lightest_rgb()
                    except:
                        light_color, dark_color = self.color, self.color 
                    self.emitsleep(int(end[0] + a), int(end[1] + b), dark_color, priority=True, timer=True)   
                time.sleep(speed*3)
                for c, d in letter:
                    try:
                        light_color, dark_color = self.get_darkest_lightest_rgb()
                    except:
                        light_color, dark_color = self.color, self.color 
                    self.emitsleep(int(end[0] + c), int(end[1] + d + 1), light_color, priority=True, timer=True)
        except Exception as e:
            print(e)
        
    def flip_colorweights(self):
        flipped_colorweights = {}
        for color, weight in self.colorweights.items():
            if weight == 0:
                flipped_colorweights[color] = 1
            elif weight == 1:
                flipped_colorweights[color] = 0
            else:
                flipped_colorweights[color] = weight
        self.colorweights = flipped_colorweights
        
    def swap_colors(self, key):
        try:
            max_value = max(value for value in self.colorweights.values() if value > 0)
            self.colorweights = {key: max_value - value if value > 0 else value for key, value in self.colorweights.items()}
        except:
            pass
        
    # amogus
    def amogus(self, key):
        self.start = time.perf_counter()
        try:
            # Get the mouse coordinates
            X, Y = self.xy()
            # Determine the grid cell size
            cell_size = 8        
            # Round the mouse coordinates to the nearest half cell size
            X = round(X / (cell_size / 2)) * (cell_size / 2)
            Y = round(Y / (cell_size / 2)) * (cell_size / 2)        
            # Snap the brush to the nearest grid cell center
            grid_x = round(X / cell_size) * cell_size
            grid_y = round(Y / cell_size) * cell_size        
            # Set the character's direction based on the change in position
            delta_x = X - self.lastx
            delta_y = Y - self.lasty
            facing_right = delta_x >= 0
            facing_up = delta_y <= 0        
            # Create the body
            body = [(x*cell_size, y*cell_size) for x in range(-2, 3) for y in range(-2, 3) if abs(x) > 1 or abs(y) > 1]
            if facing_right and facing_up:                
                self.emitsleep(X - 1, Y, 36, True if self.current_pattern_index > 0 else False, timer=True)                
            elif facing_right and not facing_up:
                for n in range(2):
                    self.emitsleep(X - (-n * -1), Y, 38 if facing_right else 37,  True if self.current_pattern_index > 0 else False, timer=True)
            elif not facing_right and facing_up:
                self.emitsleep(X + 1, Y,  35, True if self.current_pattern_index > 0 else False, timer=True)                
            else:
                for n in range(2):
                    self.emitsleep(X - (n * -1), Y, 38 if facing_right else 37,  True if self.current_pattern_index > 0 else False, timer=True)
            # Create the body and backpack variations
            x = X + (-1 if facing_right else -1)
            y = Y + (2 if facing_up else -2)            
            body_main_right_up = [(-1,-1),(0,-1),(1,-1),(0,0),(0,1),(1,1),(-1,2),(1,2),]
            backpack_right_up = [(-1,0),(-2,0),(-2,1),(-1,1),]
            body_main_right_down = [(-1,-1),(-1,1),(0,-1),(1,-1),(-1,0),(-1,1),(0,1),(1,1),(-1,2),(1,2),]
            backpack_right_down  = [(-2,0),(-2,1),]            
            body_main_left_up = [(x * -1, y) for x, y in body_main_right_up]
            backpack_left_up = [(x * -1, y) for x, y in backpack_right_up]            
            body_main_left_down = [(x * -1, y) for x, y in body_main_right_down]
            backpack_left_down = [(x * -1, y) for x, y in backpack_right_down]
            # check the last location data to determine which body and backpack to use
            if facing_right and facing_up:
                body = body_main_left_up
                backpack = backpack_left_up
            elif facing_right and not facing_up:
                body = body_main_left_down
                backpack = backpack_left_down
            elif not facing_right and facing_up:
                body = body_main_right_up
                backpack = backpack_right_up
            else:
                body = body_main_right_down
                backpack = backpack_right_down
            # pick the color of the body and backpack
            try:
                c1, c2 = self.get_darkest_lightest_rgb()
            except:
                c1, c2 = self.color, self.color
            # send the coordinate and color data to the server
            for n in body:
                self.emitsleep(n[0]+X, n[1]+Y, c2, True if self.current_pattern_index > 0 else False, timer=True)
            for n in backpack:
                self.emitsleep(n[0]+X, n[1]+Y, c1, True if self.current_pattern_index > 0 else False, timer=True)
            # save the location data to memory for the next one to access
            self.lastx, self.lasty = X, Y
        except:
            pass

    # get the lightest and darkest values from a list of rgb colors    
    def get_darkest_lightest_rgb(self):
        if len(self.colorfilter) >= 2:
            color_weights = {color: weight for color, weight in self.colorweights.items() if color in self.colorfilter}
            sorted_color_weights = sorted(color_weights.items(), key=self.brightness)
            n = len(sorted_color_weights)
            light_colors = sorted_color_weights[:n//2]
            dark_colors = sorted_color_weights[n//2:]
            light_color = random.choices([color for color, weight in light_colors],
                                         weights=[weight for color, weight in light_colors], k=1)
            dark_color = random.choices([color for color, weight in dark_colors],
                                        weights=[weight for color, weight in dark_colors], k=1)
            return colors[light_color[0]], colors[dark_color[0]]
        else:
            c1, c2 = self.random_weighted_color(), self.random_weighted_color()
            return c1, c2
        
    # draw a circle starting from outer perimeter, cancel early for outline only
    def circle_fill(self, key):
        self.start = time.perf_counter()
        try:
            start, end = self.zone(key)    
            x2, y2 = start
            x1, y1 = end
            r = int((((x2-x1)**2 + (y2-y1)**2))**0.5)
            self.coordinates  = self.spiral_order([(x,y) for x in range(x1-r, x1+r+1) for y in range(y1-r, y1+r+1) if ((x-x1)**2 + (y-y1)**2)**0.5 <= r], x1, y1)
            for c in self.coordinates:
                self.emitsleep(c[0],c[1], color = None, priority = True if self.current_pattern_index == 0 else False, timer=True)
                if keyboard.is_pressed(stop_key):
                    return
            self.coordinates = ()
        except:
            pass

    # draw a road or river bend    
    def river_bend(self, key):
        self.start = time.perf_counter()
        try:
            river_thickness_fill_list = []
            rotations = [1,-1]
            rotation_cycle = cycle(rotations)
            start, control = self.xy(), self.xy()
            control_stack = set()
            while keyboard.is_pressed(key):
                control_stack.add((self.xy()))
                time.sleep(speed)
            end = self.xy()
            control_average = []
            control_average.extend(self.coordinate_list_average(control_stack, start, end))
            distance = self.distance(start, end) + self.distance(control_average, end)
            for i in range(distance):
                t = i / distance
                xfl = (1-t)**2 * start[0] + (2 * t * (1-t) * control_average[0]) + (t**2 * end[0])
                yfl = (1-t)**2 * start[1] + (2 * t * (1-t) * control_average[1]) + (t**2 * end[1])
                for rotation in rotations:
                    for i in ((xfl+rotation,yfl),(xfl,yfl+rotation)):
                        self.emitsleep(i[0], i[1], priority=True, timer=True)
                        if keyboard.is_pressed(stop_key):
                            return
        except:
            pass

    # copy or paste area    
    def copypaste(self, key):
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
                self.cx, self.cy = cx, cy
                for X in range(x1, x2+1):
                    for Y in range(y1, y2+1):
                        if self.cache[X, Y] not in null + list(self.colorfilter):
                            self.work_order.add((X-x1-cx, Y-y1-cy, colors[self.cache[X, Y]]))
                print(f'Copied {len(self.work_order)} pixels.')
            elif key == self.pastekey:
                if self.work_order:
                    self.xy()
                    self.ordered_work = self.spiral_order(self.work_order, self.cx, self.cy, False)
                    for i in self.ordered_work:
                        self.emitsleep(i[0]+self.x, i[1]+self.y, i[2], True, timer=True)
                        if keyboard.is_pressed(stop_key):
                            return
        except:
            pass
           
    def border_tool(self, key):
        self.start = time.perf_counter()
        try:
            start, end = self.zone(key)            
            x2, y2 = start
            x1, y1 = end
            border_list = set()
            for x in range(min(x1,x2), max(x1,x2)):
                for y in range(min(y1,y2), max(y1,y2)):
                    for i in ((x, y),(x+1, y),(x-1, y),(x, y-1),(x, y+1)):
                        for ap in [(i[0]+1, i[1]), (i[0]-1, i[1]), (i[0], i[1]+1), (i[0], i[1]-1)]:
                            if self.cache[ap[0], ap[1]] in null and self.cache[i[0], i[1]] not in null:
                                border_list.add((i[0], i[1]))
            for i in border_list:
                self.emitsleep(i[0], i[1], timer=True)
        except:
            pass

    # line tool, change the width in the parameter width=4 below to your preference int
    def thick_line(self, key, width=1):
        self.start = time.perf_counter()
        try:
            set1 = set()
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
            for c in set1:
                self.emitsleep(c[0],c[1], priority=True, timer=True)
        except:
            pass
        
    # change the fill bucket pattern between Pawn or Knight (fill spread)
    def toggle_pattern(self, key):
        self.current_pattern_index = (self.current_pattern_index + 1) % len(self.fill_patterns)
        self.current_fill_pattern = self.fill_patterns[self.current_pattern_index]
        if self.mighty_wind_labels_flag == False:
            print(f'\n With their trusty {self.random_item_name1} by their side,\n    The legendary figure, known as the:\n')
            print("       ",self.mighty_wind_labels[self.current_pattern_index])
            print(f'\n    . . . embarks upon the land . . .\n')
            print(f'  - {self.fill_bucket_key} to pour bucket.\n')
            print(f'  - {self.toggle_pattern_key} to switch stance.\n')
            print(f'  - {self.swap_colors_keys} to invert colors.\n')
            self.mighty_wind_labels_flag = True
        time.sleep(speed * 3)

    def toggle_gradient(self, key):
        self.reverse_gradient = not self.reverse_gradient
        time.sleep(speed*3)
        
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

    def get_color_name(self, rgb):
        return labeled_colors[rgb]
    
    def name_to_rgb(self, color_name):
        color_to_rgb = dict(zip(labels, colors.keys()))
        return color_to_rgb[color_name]
   
    def update_labels(self):
        try:
            for widget in self.label_frame.winfo_children():
                widget.destroy()
            if all(val == 0 for val in self.colorweights.values()):
                self.label_frame.pack_forget()
                self.root.withdraw()
            else:
                self.root.deiconify()
                self.label_frame.pack(side='left')
                i=0
                # add the title label

                if self.function_name in ["magic_wand", "Magic_wand"]:
                    self.function_name = self.random_item_name1
                elif self.function_name in ["toggle_pattern", "Toggle_pattern",]:
                    if self.current_pattern_index == 0:
                        self.function_name = f'-+|{self.material_1_weighted} {self.weighted_title}|+-'
                    else:
                        self.function_name = f' ᴌⱠᛚꞀ {self.material_1_weighted} {self.weighted_title} ꞀLⱠᴌ '
                self.function_name = self.function_name.replace("_", " ")
                title_label = Label(self.label_frame, text=f"{self.function_name}")
                title_label.config(relief="groove")
                title_label.pack()
                self.update_colorfilter()
                for color, weight in self.colorweights.items():
                    if weight > 0:
                        color_name = self.get_color_name(color)
                        brightness = self.rgb_to_brightness(color)
                        if brightness < 128:
                            text_color = 'white'
                        else:
                            text_color = 'black'
                        self.label = Label(self.label_frame)
                        self.label.config(text=f"{color_name}: {weight}", bg=f'#{color[0]:02x}{color[1]:02x}{color[2]:02x}', fg=text_color, bd=1)
                        self.label.config(relief="ridge")
                        self.label.bind("<Button-3>", lambda event, color=color: self.half_color_filter(color))
                        self.label.bind("<Button-1>", lambda event, color=color: self.double_color(color))
                        self.label.bind("<Button-2>", lambda event, color=color: self.set_colorweight_to_zero(color))
                        self.label.bind("<MouseWheel>", lambda event, color=color: self.adjust_colorweight(event, color))
                        self.label.pack()
                        i+=1
            self.root.after(37*2, self.update_labels)
            self.root.geometry(f"{self.root.winfo_reqwidth()}x{self.root.winfo_reqheight()}")
        except:
            pass
        
    def double_color(self, color):
        self.colorweights[color] = self.colorweights[color] * 2
    
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

    def clear_colorweights(self, char):
        if char == 'clear':
            for color in self.colorweights:
                self.colorweights[color] = 0
        if char == 'half':
            for color in self.colorweights:
                self.colorweights[color] = self.colorweights[color] // 2
        
    def set_colorweight_to_zero(self, color):        
        self.colorweights[color] = 0
        
    # grab the sums for every color in swiped area        
    def sample_colors(self, key = None, x1=None, y1=None, x2=None, y2=None):
        self.update_window_pos()
        self.reduce_weights()
        end, start = self.zone(self.sample_colors_key)
        x2, y2 = start
        x1, y1 = end
        r = int(math.sqrt((x2-x1)**2 + (y2-y1)**2))
        coords = self.spiral_coords(start, r)
        color_count = {}  # create a dictionary to store the color occurrences
        for coord in coords:
            try:
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
            except:
                pass
        for color, count in color_count.items():                
            self.colorweights[color] += count  # increase the weight for each color by the count of that color
        
    def reduce_weights(self):
        non_zero_weights = {color: weight for color, weight in self.colorweights.items() if weight > 0 and weight != -1}
        if non_zero_weights:
            gcd = non_zero_weights[next(iter(non_zero_weights))]
            for weight in non_zero_weights.values():
                gcd = math.gcd(int(gcd), int(weight))
            if gcd > 1:
                for color in non_zero_weights:                    
                    self.colorweights[color] = self.colorweights[color] // gcd
                return True
            return False
        
    def decay_large_weights(self):
        total_weight = sum(self.colorweights.values())
        decay_factor = 0.001  # adjust this value to control the speed of decay

        max_weight_color = max(self.colorweights, key=self.colorweights.get)
        max_weight = self.colorweights[max_weight_color]

        if max_weight > 1:
            self.colorweights[max_weight_color] -= decay_factor * total_weight

    def decay_weights(self):
        total_weight = sum(self.colorweights.values())
        decay_factor = 0.001 # adjust this value to control the speed of decay

        for color, weight in self.colorweights.items():
            if 0 < weight <= 1:
                self.colorweights[color] -= decay_factor * total_weight
     
    def update_colorfilter(self):
        self.colorweights = {color: weight if weight == -1 else max(0, weight) for color, weight in self.colorweights.items()}
        self.colorfilter = set(color for color, weight in self.colorweights.items() if weight > 0 or weight == -1)    

    def return_max_rgb(self):
        max_weight = max(self.colorweights.values())
        for color, weight in self.colorweights.items():
            if weight == max_weight:
                return color
        
    def return_min_rgb(self):
        min_weight = min([weight for color, weight in self.colorweights.items() if weight > 0])
        for color, weight in self.colorweights.items():
            if weight == min_weight:
                return color
      
    def rgb_to_brightness(self, rgb):
        return int(0.299*rgb[0] + 0.587*rgb[1] + 0.114*rgb[2])

    # update the gui window position when called self.update_window_pos()
    def update_window_pos(self):
        mouse_x = self.root.winfo_pointerx()
        mouse_y = self.root.winfo_pointery()
        width, height = self.root.winfo_reqwidth(), self.root.winfo_reqheight()
        mx = mouse_x - width/2
        my = mouse_y - height/2
        mx, my = int(mx), int(my)
        self.root.geometry(f"{width}x{height}+{mx-128}+{my-128}")
        self.root.update()

    def spiral_order(self, coordinates, center_x, center_y, reverse=True):
        if self.current_pattern_index != 0:
            try:
                random.shuffle(coordinates)
            except:
                coordinates=coordinates
        else:
            coordinates = sorted(set(coordinates), key=lambda x: ((x[0]-center_x)**2 + (x[1]-center_y)**2)**0.5, reverse=reverse)
        return coordinates
            
    def spiral_coords(self, center, radius):
      x, y = center
      coords = []
      x_offset, y_offset = 0, 0
      for r in range(radius+1):
        for i in range(r*2):
          x += 1
          distance = math.sqrt((x - center[0])**2 + (y - center[1])**2)
          if distance <= radius:
            coords.append((x, y))
        for i in range(r*2):
          y += 1
          distance = math.sqrt((x - center[0])**2 + (y - center[1])**2)
          if distance <= radius:
            coords.append((x, y))
        for i in range(r*2+1):
          x -= 1
          distance = math.sqrt((x - center[0])**2 + (y - center[1])**2)
          if distance <= radius:
            coords.append((x, y))
        for i in range(r*2+1):
          y -= 1
          distance = math.sqrt((x - center[0])**2 + (y - center[1])**2)
          if distance <= radius:
            coords.append((x, y))
      return coords

    def xy(self):
        self.lastx, self.lasty = self.x, self.y
        try:
            self.x, self.y = make_tuple(driver.find_element(By.XPATH,'/html/body/div[3]/div[4]').text)
        except:
            self.x, self.y = self.lastx, self.lasty
        return self.x, self.y
          
    def distance(self, xy1, xy2):
        return int(math.sqrt((xy2[0] - xy1[0])**2 + (xy2[1] - xy1[1])**2))

    def coordinate_list_average(self, coordinate_set, start_coordinate, end_coordinate):
        try:
            weight_sum = sum(max(math.sqrt((coordinate[0] - start_coordinate[0]) ** 2 + (coordinate[1] - start_coordinate[1]) ** 2),
                                math.sqrt((coordinate[0] - end_coordinate[0]) ** 2 + (coordinate[1] - end_coordinate[1]) ** 2))
                                for coordinate in coordinate_set)
            x_sum = sum(coordinate[0] * max(math.sqrt((coordinate[0] - start_coordinate[0]) ** 2 + (coordinate[1] - start_coordinate[1]) ** 2),
                                           math.sqrt((coordinate[0] - end_coordinate[0]) ** 2 + (coordinate[1] - end_coordinate[1]) ** 2))
                                           for coordinate in coordinate_set)
            y_sum = sum(coordinate[1] * max(math.sqrt((coordinate[0] - start_coordinate[0]) ** 2 + (coordinate[1] - start_coordinate[1]) ** 2),
                                           math.sqrt((coordinate[0] - end_coordinate[0]) ** 2 + (coordinate[1] - end_coordinate[1]) ** 2))
                                           for coordinate in coordinate_set)
            return int(x_sum/weight_sum), int(y_sum/weight_sum)
        except:
            pass
        
    def zone(self, key):
        with zone_lock:
            x1, y1 = self.xy()
            while True:
                if not keyboard.is_pressed(key):
                    break
            x2, y2 = self.xy()
            return [x1, y1], [x2, y2]
    
    def get_color_index(self):
        try:
            cid = str(driver.find_element(By.XPATH,'/html/body/div[3]/div[2]').get_attribute("style"))
            a = cid.find('(')
            b = cid.find(')')
            b+=1
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
          
    def color_shift(self, color, direction): # 1 or -1 for direction
        color_int = None
        for c, i in colors.items():
            if c == color or i == color:
                color_int = i
                break
        if color_int is None:
            return -1
        next_color_int = (color_int + direction) % len(colors)
        if next_color_int not in colors.values():
            next_color_int = next(i % len(colors) for i in range(next_color_int+direction, next_color_int+len(colors)*direction, direction) if i % len(colors) in colors.values())
        return next_color_int
        
    def load_map_into_cache(self, chart):
        with open(f'{self.chart}.png', 'wb') as f:
            f.write(requests.get(f'https://pixelplace.io/canvas/{chart}.png?t={random.randint(9999,99999)}').content)
        self.image = Image.open(f'{self.chart}.png').convert('RGB')
        self.width, self.height = self.image.size
        if self.chart != 7:
            self.image.putpixel((self.width-1, self.height-1), (0, 0, 0))
        self.image.save(f'{self.chart}.png')
        self.cache = self.image.load()
        print(f' Successfully loaded chart: {self.chart}')
   
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
      
    def auth_data(self):
        self.authkey = driver.get_cookie("authKey").get('value')
        print('  -Got Key -')
        self.authtoken = driver.get_cookie("authToken").get('value')
        print('    -Got Token -')
        self.authid = driver.get_cookie("authId").get('value')
        print('     - Got ID -')
                
    # toggle guild war logos on or off with the toggle_logos_key you set earlier, by default the equals -> = <- sign        
    def toggle_logos(self, key):
        if self.logos == True:
            for lg in range(10):
                try:
                    driver.execute_script("arguments[0].style.display = 'none';",driver.find_element(By.XPATH,f'//*[@id="areas"]/div[{lg}]'))
                    driver.execute_script("arguments[0].style.display = 'none';",driver.find_element(By.XPATH,f'/html/body/div[3]/div[1]/div[2]/div/a[{lg}]'))
                except:
                    pass
            self.logos = False
        else:
            for lg in range(10):
                try:
                    driver.execute_script("arguments[0].style.display = 'block';",driver.find_element(By.XPATH,f'//*[@id="areas"]/div[{lg}]'))
                    driver.execute_script("arguments[0].style.display = 'inline';",driver.find_element(By.XPATH,f'/html/body/div[3]/div[1]/div[2]/div/a[{lg}]'))
                except:
                    pass
            self.logos = True
        time.sleep(speed * 3)        
        
    # speed control helper    
    def change_speed(self, key):
        increment = 0.000001
        if key == self.downspeed:
            self.speed  += increment
            self.speed  = float('%.7f'%self.speed)
        elif key == self.upspeed:
            self.speed  -= increment
            self.speed  = float('%.7f'%self.speed)
        if self.speed < 0.013:
            print(f"Going too fast now, defaulting to {0.016} to prevent perma ban.")
            self.speed = regular_speed
        if self.speed <= 0.01421:
            print(f"Warning: You are in speed throttling territory.")
        print("Speed:", self.speed)
        
letters= {
            'a': {(-1,-1),(0, -1),(1, -1), 
                 (-1, 0),         (1, 0),
                 (-1, 1), (0, 1), (1, 1),
                 (-1, 2),         (1, 2),},
            
            'b': {(-1,-2),(0,-2), 
                  (-1,-1),      (1,-1),
                  (-1,0),(0,0),
                  (-1,1),       (1,1),
                  (-1,2),(0,2),},

            'c': {      (-1,-2),(0,-2),
                  (-2,-1),           
                  (-2,0),
                  (-2,1),        
                        (-1,2),(0,2),},

            'd': {(-1,-2),(0,-2),
                  (-1,-1),     (1,-1),      
                  (-1,0),      (1,0),
                  (-1,1),      (1,1),   
                  (-1,2),(0,2),},

            'e': {(0, -2), (1, -2), 
                  (0, -1),
                  (0, 0), (1, 0),
                  (0, 1),
                  (0, 2), (1, 2)},
            
            'f': {(0, -2), (1, -2),
                  (0, -1),
                  (0, 0), (1, 0),
                  (0, 1),
                  (0, 2)}, 

            'g': {      (-1,-2),(0,-2),
                  (-2,-1),           
                  (-2,0),    (0,0),
                  (-2,1),         (1,1),
                        (-1,2),(0,2),},
            
            'h': {(-1, -1),     (1, -1), 
                  (-1, 0),(0, 0),(1, 0),
                  (-1, 1),      (1, 1),},

            'i': {(0, -1),
                  (0, 1),
                  (0, 2)},
                  
            'j': {(1, -2), 
                  (1, -1),
                  (1, 0),
                  (-1, 1),(1, 1),
                  (-1, 2),(0, 2),(1, 2)},
                  
            'k': {(-1, -1),     (1, -1),
                  (-1, 0),(0, 0),
                  (-1, 1),      (1, 1),},
                  
            'l': {(0, -2), 
                  (0, -1),
                  (0, 0),
                  (0, 1), (1, 1),},
            
            'm': {(-2, -2),                      (2, -2),
                  (-2, -1),(-1, -1),     (1, -1),(2, -1),
                  (-2, 0),        (0, 0),         (2, 0),
                  (-2, 1),                        (2, 1),},
             
            'n': {(-1, -2),             (2, -2),
                  (-1, -1),(0, -1),     (2, -1),
                  (-1, 0),       (1, 0),(2, 0),
                  (-1, 1),            (2, 1)},
                  
            'o': {      (-1, -1),(0, -1),  
                  (-2, 0),               (1, 0),
                  (-2, 1),               (1, 1),
                        (-1, 2),(0, 2)},

            'p': {(-1, -1),(0, -1),(1, -1),
                  (-1, 0),         (1, 0),
                  (-1, 1), (0, 1), (1, 1),
                  (-1, 2)},
            
            'q': {        (0, -2), 
                  (-1, -1),       (1,-1),
                  (-1, 0),        (1, 0),
                          (0, 1), (1, 1),
                                         (2, 2)},
                  
            'r': {(-1, -2),(0, -2),
                  (-1, -1),      (1, -1), 
                  (-1, 0),(0, 0), 
                  (-1, 1),      (1, 1),  },
                  
            's': {(-1, -1),(0, -1),
                  (-1, 0),
                           (0, 1),
                  (-1, 2), (0, 2), },

            't': {(-1, -1), (0, -1), (1, -1),
                          (0, 0),
                          (0, 1),
                          (0, 2), },
                  
            'u': {(-1, -2),         (1, -2), 
                  (-1, -1),         (1, -1), 
                  (-1, 0),         (1, 0), 
                  (-1, 1), (0, 1), (1, 1), },

            'v': {(-1, -2),     (1, -2), 
                  (-1, -1),     (1, -1), 
                  (-1, 0),     (1, 0), 
                        (0, 1), },

            'w': {(-2, -1),                  (2, -1), 
                  (-2, 0),      (0, 0),      (2, 0), 
                        (-1, 1),    (1, 1)},

            'x': {(-1, -1),      (1, -1), 
                        (0, 0),
                  (-1, 1),      (1, 1), },

            'y': {(-1, -1),       (1, -1),
                  (-1, 0),        (1, 0),
                          (0, 1),
                          (0, 2), },

            'z': {(0, -1), (1, -1),
                          (1, 0),
                  (0, 1),
                  (0, 2), (1, 2), },
        }
letters = {k: sorted(v) for k, v in letters.items()}

if __name__ == '__main__':
    # create 'SusBot' instance
    susbot = SusBot()

# End of the line, partner.
