import os
import pygame
from pygame.locals import *
import random
import re

node_repulsion = -2
reference_attraction = 100
center_attraction = 0.001
node_damping = 0.95

class Node:
    def __init__(self, position, file_name):
        self.positionx, self.positiony = position
        self.velocityx, self.velocityy = 0, 0
        self.file_name = file_name

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
        self.references = {}

        # Initialize Pygame
        pygame.init()

        # Initialize Pygame screen
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption('Markdown References Simulation')

    def extract_references(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            references = re.findall(r'\[\[(.*?)\]\]', content)
            return references

    def load_nodes(self):
        for root, dirs, files in os.walk(self.folder):
            for file in files:
                if file.endswith(".md"):
                    file_path = os.path.join(root, file)
                    position = random.uniform(0, self.screen_width), random.uniform(0, self.screen_height)
                    node = Node(position, file)
                    self.nodes.append(node)
                    self.references[file] = self.extract_references(file_path)
        print(self.references)  # print the references dictionary
        
    def update_simulation(self):
        for node in self.nodes:
            repulsion_force_x, repulsion_force_y = 0, 0
            attraction_force_x, attraction_force_y = 0, 0
            center_attraction_x, center_attraction_y = 0, 0

            # Calculate forces from other nodes
            for other_node in self.nodes:
                if node != other_node:
                    distance_x = other_node.positionx - node.positionx
                    distance_y = other_node.positiony - node.positiony
                    distance_squared = distance_x ** 2 + distance_y ** 2
                    distance = distance_squared ** 0.5  # Calculate magnitude

                    # Repulsion force inversely proportional to distance
                    repulsion_force_x += distance_x / (distance_squared + 1e-5)
                    repulsion_force_y += distance_y / (distance_squared + 1e-5)

                    # Check if other_node is referenced by node
                    if other_node.file_name in self.references.get(node.file_name, []):
                        # Attraction force towards the referenced node
                        attraction_force_x += distance_x
                        attraction_force_y += distance_y

            # Calculate center attraction force
            center_attraction_x = (self.screen_width / 2 - node.positionx) * center_attraction
            center_attraction_y = (self.screen_height / 2 - node.positiony) * center_attraction

            # Update velocity and position
            node.update_velocity(repulsion_force_x, repulsion_force_y, attraction_force_x * reference_attraction, attraction_force_y * reference_attraction, center_attraction_x, center_attraction_y)
            node.update_position()


    def draw_simulation(self):
        self.screen.fill((0, 0, 0))  # Black background
        
        # Get mouse position
        mouse_x, mouse_y = pygame.mouse.get_pos()

        # Check if mouse is hovering over a node
        for node in self.nodes:
            node_pos = (int(node.positionx), int(node.positiony))
            node_radius = 3
            visible_radius = 20
            if (node_pos[0] - mouse_x) ** 2 + (node_pos[1] - mouse_y) ** 2 < visible_radius ** 2:
                font = pygame.font.Font(None, 20)
                label = font.render(str(node.file_name), True, (255, 255, 255))
                label_rect = label.get_rect(center=node_pos, y=node_pos[1] - 30)
                self.screen.blit(label, label_rect)
            
            # Draw nodes
            pygame.draw.circle(self.screen, (255, 255, 255), node_pos, node_radius)
            
        '''
        # Draw grey lines between nodes that have references
        for node1 in self.nodes:
            for node2 in self.nodes:
                if node2.file_name in self.references.get(node1.file_name, []):
                    pygame.draw.line(self.screen, (128, 128, 128), (node1.positionx, node1.positiony), (node2.positionx, node2.positiony), 1)
        '''          

        pygame.display.flip()

    def run_simulation(self):
        self.load_nodes()

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == QUIT:
                    running = False

            self.update_simulation()
            self.draw_simulation()

        pygame.quit()

folder = "/Users/gagehowe/Library/Mobile Documents/iCloud~md~obsidian/Documents/Gage's Vault"
screen_width = 1500
screen_height = 900

simulation = Simulation(folder, screen_width, screen_height)
simulation.run_simulation()
