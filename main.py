import itertools
import os
import pyglet
import random
import sys
import time

from pyglet.sprite import Sprite

LOGGING = False

def log(msg):
  if LOGGING:
    print(msg)

class cpu (pyglet.window.Window):
        
    def initialize(self):
        self.clear()
        self.memory = [0]*4096 # max 4096 bytes of memory
        self.gpio = [0]*16 # max 16 bytes
        self.display_buffer = [0]*64*32 # 64*32 display size
        self.stack = []
        self.key_inputs = [0]*16  
        self.opcode = 0
        self.index = 0
        
        self.delay_timer = 0
        self.sound_timer = 0
        self.should_draw = False
    
        self.pc = 0x200 # 0x000 to 0x200 is reserved so we start from 0x200
    
        i = 0
        while i < 80:
            # load 80-char font set
            self.memory[i] = self.fonts[i]
            i += 1
    
    def on_key_press(self, symbol, modifiers):
        return super().on_key_press(symbol, modifiers)
    
    def on_key_release(self, symbol, modifiers):
        return super().on_key_release(symbol, modifiers)
    
    def load_rom(self, rom_path):
        log("Loading %s..." % rom_path)
        binary = open(rom_path, "rb").read()
        for i in range(len(binary)):
            self.memory[i+0x200] = ord(binary[i])
            
    def cycle(self):
        self.opcode = self.memory[self.pc]
        
        #TODO: Process the opcode
        
        self.pc += 2
        
        if self.delay_timer > 0:
            self.delay_timer -= 1
        if self.sound_timer > 0:
            self.sound_timer -= 1
        if self.sound_timer == 0:
            # Play a sound here with pyglet
            return #TODO: Placeholder
    
    
    def main(self):
        
        self.initialize()
        self.load_rom(sys.argv[1])
        while not self.has_exit:
            self.dispatch_events()
            self.cycle()
            self.draw()