import os
import pygame
from pygame.locals import *
import random
import subprocess
import math
import tkinter as tk
from tkinter import filedialog
import threading

node_repulsion = -10
reference_attraction = 0.0
center_attraction = 0.0
node_damping = 0.0
transparency_radius = 0.5

paused = False

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)

def sigmoid(x, scale=2, shift=-0.5):
    return 1 / (1 + math.exp(-(x - shift) * scale))

def change_directory():                                         
    print("change_directory called")
    root = tk.Tk()
    root.withdraw()
    print("root withdrawn")
    start_thread()
    new_folder = filedialog.askdirectory()
    if new_folder:
        simulation.folder = new_folder
        start_thread()

def prompt_file():                                                  # from stackoverflow
    """Create a Tk file dialog and cleanup when finished"""
    print("prompt_file called")
    global target_folder
    global paused
    
    paused = True
    print("paused")
    top = tk.Tk() # this step causes the program to crash
    print("top created")
    
    top.withdraw()  # hide window
    print("top withdrawn")
    
    target_folder = tk.filedialog.askopenfilename(parent=top)
    print("file_name assigned")
    
    top.destroy()
    print("top destroyed")
    
    paused = False
    
    return target_folder
    

class Button:
    def __init__(self, x, y, width, height, text, command):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.command = command

    def draw(self, screen):
        pygame.draw.rect(screen, GRAY, self.rect)
        font = pygame.font.Font(None, 20)
        text_surface = font.render(self.text, True, WHITE)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.command()

    def get_rect(self):
        return self.rect


class Slider:
    def __init__(self, x, y, length, min_value, max_value, initial_value, label):
        self.x = x
        self.y = y
        self.length = length
        self.min_value = min_value
        self.max_value = max_value
        self.current_value = initial_value
        self.slider_rect = pygame.Rect(self.x, self.y, self.length, 10)
        self.slider_button_rect = pygame.Rect(self.x, self.y - 5, 10, 20)
        self.dragging = False
        self.label = label

    def draw(self, screen):
        pygame.draw.rect(screen, GRAY, self.slider_rect)
        pygame.draw.rect(screen, WHITE, self.slider_button_rect)

        # Render label text
        font = pygame.font.Font(None, 20)
        text_surface = font.render(self.label, True, WHITE)
        text_rect = text_surface.get_rect(center=(self.x + self.length // 2, self.y - 15))
        screen.blit(text_surface, text_rect)

    def update(self):
        if self.dragging:
            mouse_x, _ = pygame.mouse.get_pos()
            # Constrain slider button movement within the range of min and max values
            self.slider_button_rect.centerx = max(self.x, min(mouse_x, self.x + self.length))
            # Update current value based on slider button position within the range
            self.current_value = self.min_value + \
                (self.slider_button_rect.centerx - self.x) / self.length * \
                (self.max_value - self.min_value)
            print(self.current_value)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.slider_button_rect.collidepoint(event.pos):
                self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        if self.dragging:
            self.update()

class Node:
    def __init__(self, position, file_name, size):
        self.positionx, self.positiony = position
        self.velocityx, self.velocityy = 0, 0
        self.file_name = file_name
        self.references = []
        self.size = size

    def update_velocity(self, repulsion_force_x, repulsion_force_y, attraction_force_x, attraction_force_y, center_attraction_x, center_attraction_y):
        global node_repulsion, reference_attraction, node_damping
        total_force_x = repulsion_force_x * node_repulsion + attraction_force_x * reference_attraction + center_attraction_x
        total_force_y = repulsion_force_y * node_repulsion + attraction_force_y * reference_attraction + center_attraction_y

        self.velocityx += total_force_x
        self.velocityy += total_force_y
        self.velocityx *= node_damping
        self.velocityy *= node_damping

    def update_position(self):
        self.positionx += self.velocityx
        self.positiony += self.velocityy

class Simulation:
    
    def __init__(self, folder, screen_width, screen_height):
        self.folder = folder
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.nodes = []
        
        self.dialog_open = False


        # Initialize Pygame
        pygame.init()

        # Initialize Pygame screen
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption('Markdown References Simulation')
        
        self.change_directory_button = Button(self.screen_width // 2 - 75, self.screen_height - 50, 150, 30, "Change Directory", prompt_file)

        # Create sliders
        
        self.slider_node_repulsion = Slider(50, # x
                                            50, # y
                                            200, # length
                                                                0, # min_value
                                                                -100, # max_value
                                                                -50, # initial_value
                                            "Repulsion"
                                            )
        
        self.slider_reference_attraction = Slider(50,
                                                  100,
                                                  200,
                                                                0,
                                                                0.1,
                                                                0,
                                                  "Reference Attraction")
        
        self.slider_center_attraction = Slider(50,
                                               150,
                                               200,
                                                                0,
                                                                0.05,
                                                                0.02,
                                               "Gravity")
        
        self.slider_node_damping = Slider(50,
                                          200,
                                          200,
                                                                1,
                                                                0,
                                                                0.9,
                                          "Damping")
        
        self.slider_transparency_radius = Slider(50,
                                    250,
                                    200,
                                                        -1,
                                                        2,
                                                        0.7,
                                    "Transparency Radius")
    
    def change_directory(self):
        print("self.change_directory called")

        threading.Thread(target=self.open_file_dialog).start()
        
    def open_file_dialog(self):
        print("self.open_file_dialog called")
        self.dialog_open = True
        print("step 1")
        root = tk.Tk() # this step causes the program to crash with "zsh: trace trap"
        print("root created")
        root.withdraw()
        print("step 2")
        new_folder = filedialog.askdirectory()
        print(f"passed the new folder step")
        if new_folder:
            self.folder = new_folder
            self.load_nodes(self.folder)
        self.dialog_open = False

    def load_nodes(self, folder):
        self.nodes.clear()  # Clear existing nodes
        for root, dirs, files in os.walk(folder):
            for file in files:
                if file.endswith(".md"):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        references = []
                        # Calculate size based on file size or character count
                        size = os.path.getsize(file_path)  # Example: Using file size
                        for line in content.split('\n'):
                            if '[[' in line and ']]' in line:
                                start = line.index('[[')
                                end = line.index(']]')
                                reference = line[start + 2:end]
                                references.append(reference)
                        position = random.uniform(0, self.screen_width), random.uniform(0, self.screen_height)
                        node = Node(position, file, size)
                        node.references = references
                        self.nodes.append(node)

    def update_simulation(self):
        for node in self.nodes:
            repulsion_force_x, repulsion_force_y = 0, 0
            attraction_force_x, attraction_force_y = 0, 0
            center_attraction_x, center_attraction_y = 0, 0

            for other_node in self.nodes:
                if node != other_node:
                    distance_x = other_node.positionx - node.positionx
                    distance_y = other_node.positiony - node.positiony
                    distance_squared = distance_x ** 2 + distance_y ** 2
                    distance = distance_squared ** 0.5

                    repulsion_force_x += distance_x / (distance_squared + 1e-5)
                    repulsion_force_y += distance_y / (distance_squared + 1e-5)
            
            for reference in node.references:
                for other_node in self.nodes:
                    if other_node.file_name == (reference + ".md"):
                        attraction_force_x = other_node.positionx - node.positionx
                        attraction_force_y = other_node.positiony - node.positiony
                        
            center_attraction_x = (self.screen_width / 2 - node.positionx) * center_attraction
            center_attraction_y = (self.screen_height / 2 - node.positiony) * center_attraction

            node.update_velocity(repulsion_force_x, repulsion_force_y, attraction_force_x * reference_attraction, attraction_force_y * reference_attraction, center_attraction_x, center_attraction_y)
            node.update_position()

    def draw_simulation(self):
        global transparency_radius
        
        self.screen.fill((0, 0, 0))
        line_color = pygame.Color(255, 255, 0)
        line_color.a = 100
        line_surface = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)

        self.slider_node_repulsion.draw(self.screen)
        self.slider_node_repulsion.slider_button_rect.centerx = int(self.slider_node_repulsion.x + self.slider_node_repulsion.length * (self.slider_node_repulsion.current_value - self.slider_node_repulsion.min_value) / (self.slider_node_repulsion.max_value - self.slider_node_repulsion.min_value))
        self.slider_reference_attraction.draw(self.screen)
        self.slider_reference_attraction.slider_button_rect.centerx = int(self.slider_reference_attraction.x + self.slider_reference_attraction.length * (self.slider_reference_attraction.current_value - self.slider_reference_attraction.min_value) / (self.slider_reference_attraction.max_value - self.slider_reference_attraction.min_value))
        self.slider_center_attraction.draw(self.screen)
        self.slider_center_attraction.slider_button_rect.centerx = int(self.slider_center_attraction.x + self.slider_center_attraction.length * (self.slider_center_attraction.current_value - self.slider_center_attraction.min_value) / (self.slider_center_attraction.max_value - self.slider_center_attraction.min_value))
        self.slider_node_damping.draw(self.screen)
        self.slider_node_damping.slider_button_rect.centerx = int(self.slider_node_damping.x + self.slider_node_damping.length * (self.slider_node_damping.current_value - self.slider_node_damping.min_value) / (self.slider_node_damping.max_value - self.slider_node_damping.min_value))
        self.slider_transparency_radius.draw(self.screen)
        self.slider_transparency_radius.slider_button_rect.centerx = int(self.slider_transparency_radius.x + self.slider_transparency_radius.length * (self.slider_transparency_radius.current_value - self.slider_transparency_radius.min_value) / (self.slider_transparency_radius.max_value - self.slider_transparency_radius.min_value))
        
        mouse_x, mouse_y = pygame.mouse.get_pos()

        self.change_directory_button.draw(self.screen)

        for node in self.nodes:
            
            int_node_pos = (int(node.positionx), int(node.positiony))
            
            node_radius = int((node.size)**0.15+1)
            visible_radius = 20
            if (int_node_pos[0] - mouse_x) ** 2 + (int_node_pos[1] - mouse_y) ** 2 < visible_radius ** 2:
                font = pygame.font.Font(None, 20)
                label = font.render(str(node.file_name), True, (255, 255, 255))
                label_rect = label.get_rect(center=int_node_pos, y=int_node_pos[1] - 30)
                self.screen.blit(label, label_rect)
            
            x,y = int_node_pos
            pygame.draw.circle(self.screen, (255, 255, 255), (x,y), node_radius)
            
            for reference in node.references:
                for other_node in self.nodes:
                    if other_node.file_name == (reference + ".md"):
                        #print(f"Drawing line from {node.file_name} to {other_node.file_name}")
                        distance = ((int_node_pos[0] - other_node.positionx) ** 2 + (int_node_pos[1] - other_node.positiony) ** 2) ** 0.5

                        transparency = int(255 - sigmoid(transparency_radius) * (distance + 1))
                        if (int_node_pos[0] - mouse_x) ** 2 + (int_node_pos[1] - mouse_y) ** 2 < visible_radius ** 2:
                            transparency = max(0, min(255, 255))
                        else:
                            transparency = max(0, min(255, transparency))
                        line_color = pygame.Color(255, 255, 255, transparency)
                    
                        pygame.draw.line(line_surface, line_color, int_node_pos, (int(other_node.positionx), int(other_node.positiony)), 1)

        self.screen.blit(line_surface, (0, 0))
        pygame.display.flip()

    def run_simulation(self):
        self.load_nodes(target_folder)

        global paused
        paused = False
        while not paused:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    paused = True
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Left mouse button
                    mouse_x, mouse_y = event.pos
                    self.change_directory_button.handle_event(event)
                    for node in self.nodes:
                        if self.node_clicked(node, mouse_x, mouse_y):
                            print(f"Opening {node.file_name}")
                            self.open_md_file(node.file_name[:-3])
                            break
                self.slider_node_repulsion.handle_event(event)
                self.slider_reference_attraction.handle_event(event)
                self.slider_center_attraction.handle_event(event)
                self.slider_node_damping.handle_event(event)
                self.slider_transparency_radius.handle_event(event)

            global node_repulsion, reference_attraction, center_attraction, node_damping
            node_repulsion = self.slider_node_repulsion.current_value
            reference_attraction = self.slider_reference_attraction.current_value
            center_attraction = self.slider_center_attraction.current_value
            node_damping = self.slider_node_damping.current_value
            
            global transparency_radius
            transparency_radius = self.slider_transparency_radius.current_value

            self.update_simulation()
            self.draw_simulation()
        print("Quitting")
        pygame.quit()

    def open_md_file(self, file_name):
        md_file_path = os.path.join(self.folder, file_name + ".md")
        subprocess.run(["open", md_file_path]) # may be mac-specific
        
    def node_clicked(self, node, mouse_x, mouse_y):
        node_radius = 5
        distance_squared = (node.positionx - mouse_x) ** 2 + (node.positiony - mouse_y) ** 2
        return distance_squared <= node_radius ** 2
    
target_folder = "/Users/gagehowe/Library/Mobile Documents/iCloud~md~obsidian/Documents/Gage's Vault"
screen_width = 1500
screen_height = 900

simulation = Simulation(target_folder, screen_width, screen_height)
simulation.run_simulation()
