#!/usr/bin/env python3
"""
Générateur de grilles HDF5 pour le système JPS/TSP
Interface utilisateur pour créer des grilles au format attendu.
"""

import h5py
import numpy as np
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import json
import os


class GridGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("Générateur de Grilles HDF5 - JPS/TSP")
        self.root.geometry("1200x800")
        
        # État de l'application
        self.grid = None
        self.points_of_interest = []
        self.hedge_size = 1.0
        
        self.setup_ui()
        
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        # Frame principal
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Frame de contrôles
        control_frame = ttk.LabelFrame(main_frame, text="Paramètres de la grille", padding="10")
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Ligne 1: Dimensions
        dim_frame = ttk.Frame(control_frame)
        dim_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(dim_frame, text="Largeur:").pack(side=tk.LEFT)
        self.width_var = tk.StringVar(value="50")
        ttk.Entry(dim_frame, textvariable=self.width_var, width=8).pack(side=tk.LEFT, padx=(5, 15))
        
        ttk.Label(dim_frame, text="Hauteur:").pack(side=tk.LEFT)
        self.height_var = tk.StringVar(value="50")
        ttk.Entry(dim_frame, textvariable=self.height_var, width=8).pack(side=tk.LEFT, padx=(5, 15))
        
        ttk.Label(dim_frame, text="Taille cellule:").pack(side=tk.LEFT)
        self.hedge_size_var = tk.StringVar(value="1.0")
        ttk.Entry(dim_frame, textvariable=self.hedge_size_var, width=8).pack(side=tk.LEFT, padx=(5, 15))
        
        # Ligne 2: Boutons de génération
        gen_frame = ttk.Frame(control_frame)
        gen_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(gen_frame, text="Grille vide", command=self.create_empty_grid).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(gen_frame, text="Grille aléatoire", command=self.create_random_grid).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(gen_frame, text="Charger image", command=self.load_image).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(gen_frame, text="Charger grille", command=self.load_grid).pack(side=tk.LEFT, padx=(0, 15))
        
        ttk.Button(gen_frame, text="Sauvegarder HDF5", command=self.save_hdf5).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(gen_frame, text="Sauvegarder JSON", command=self.save_json).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Frame pour la visualisation et les contrôles
        viz_frame = ttk.Frame(main_frame)
        viz_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame de gauche pour les outils
        tools_frame = ttk.LabelFrame(viz_frame, text="Outils d'édition", padding="10")
        tools_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # Mode d'édition
        ttk.Label(tools_frame, text="Mode:").pack(anchor=tk.W)
        self.edit_mode = tk.StringVar(value="obstacle")
        ttk.Radiobutton(tools_frame, text="Placer obstacles", variable=self.edit_mode, value="obstacle").pack(anchor=tk.W)
        ttk.Radiobutton(tools_frame, text="Effacer obstacles", variable=self.edit_mode, value="free").pack(anchor=tk.W)
        ttk.Radiobutton(tools_frame, text="Points d'intérêt", variable=self.edit_mode, value="poi").pack(anchor=tk.W)
        ttk.Radiobutton(tools_frame, text="Supprimer POI", variable=self.edit_mode, value="remove_poi").pack(anchor=tk.W, pady=(0, 10))
        
        # Liste des points d'intérêt
        ttk.Label(tools_frame, text="Points d'intérêt:").pack(anchor=tk.W)
        
        poi_list_frame = ttk.Frame(tools_frame)
        poi_list_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 10))
        
        self.poi_listbox = tk.Listbox(poi_list_frame, height=10)
        scrollbar = ttk.Scrollbar(poi_list_frame, orient=tk.VERTICAL, command=self.poi_listbox.yview)
        self.poi_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.poi_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        ttk.Button(tools_frame, text="Effacer tous les POI", command=self.clear_all_poi).pack(fill=tk.X)
        
        # Frame de droite pour le canvas
        canvas_frame = ttk.LabelFrame(viz_frame, text="Grille", padding="10")
        canvas_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Configuration matplotlib
        self.fig = Figure(figsize=(8, 8), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, canvas_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Événements de clic
        self.canvas.mpl_connect('button_press_event', self.on_canvas_click)
        
        # Créer une grille par défaut
        self.create_empty_grid()
        
    def create_empty_grid(self):
        """Crée une grille vide"""
        try:
            width = int(self.width_var.get())
            height = int(self.height_var.get())
            self.hedge_size = float(self.hedge_size_var.get())
            
            self.grid = np.zeros((height, width), dtype=np.int8)
            self.points_of_interest = []
            self.update_display()
            self.update_poi_list()
            
        except ValueError:
            messagebox.showerror("Erreur", "Veuillez entrer des valeurs numériques valides")
    
    def create_random_grid(self):
        """Crée une grille avec des obstacles aléatoires"""
        try:
            width = int(self.width_var.get())
            height = int(self.height_var.get())
            self.hedge_size = float(self.hedge_size_var.get())
            
            # Grille avec 20% d'obstacles
            self.grid = np.random.choice([0, -1], size=(height, width), p=[0.8, 0.2]).astype(np.int8)
            self.points_of_interest = []
            
            # Ajouter quelques points d'intérêt aléatoires
            for _ in range(5):
                while True:
                    x = np.random.randint(0, width)
                    y = np.random.randint(0, height)
                    if self.grid[y, x] == 0:  # Cell libre
                        self.points_of_interest.append((x, y))
                        break
            
            self.update_display()
            self.update_poi_list()
            
        except ValueError:
            messagebox.showerror("Erreur", "Veuillez entrer des valeurs numériques valides")
    
    def load_image(self):
        """Charge une image et la convertit en grille"""
        filename = filedialog.askopenfilename(
            title="Charger une image",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.tiff"), ("Tous les fichiers", "*.*")]
        )
        
        if filename:
            try:
                from PIL import Image
                
                img = Image.open(filename).convert('L')  # Convertir en niveaux de gris
                
                # Redimensionner si nécessaire
                width = int(self.width_var.get())
                height = int(self.height_var.get())
                img = img.resize((width, height))
                
                # Convertir en grille (seuil à 128 pour noir/blanc)
                img_array = np.array(img)
                self.grid = np.where(img_array < 128, -1, 0).astype(np.int8)
                
                self.hedge_size = float(self.hedge_size_var.get())
                self.points_of_interest = []
                
                self.update_display()
                self.update_poi_list()
                
            except ImportError:
                messagebox.showerror("Erreur", "PIL/Pillow n'est pas installé. Installez-le avec: pip install Pillow")
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de charger l'image: {e}")
    
    def load_grid(self):
        """Charge une grille depuis un fichier JSON ou HDF5"""
        filename = filedialog.askopenfilename(
            title="Charger une grille",
            filetypes=[("HDF5", "*.h5 *.hdf5"), ("JSON", "*.json"), ("Tous les fichiers", "*.*")]
        )
        
        if filename:
            try:
                if filename.endswith(('.h5', '.hdf5')):
                    self.load_hdf5(filename)
                elif filename.endswith('.json'):
                    self.load_json(filename)
                else:
                    messagebox.showerror("Erreur", "Format de fichier non supporté")
                    
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de charger le fichier: {e}")
    
    def load_hdf5(self, filename):
        """Charge une grille HDF5"""
        with h5py.File(filename, 'r') as f:
            self.grid = f['matrix'][:]
            self.hedge_size = f['matrix'].attrs.get('hedge_size', 1.0)
            
            if 'points_of_interest' in f:
                poi_data = f['points_of_interest'][:]
                self.points_of_interest = [(int(poi_data[i, 0]), int(poi_data[i, 1])) 
                                         for i in range(poi_data.shape[0])]
            else:
                self.points_of_interest = []
        
        # Mettre à jour les champs
        self.height_var.set(str(self.grid.shape[0]))
        self.width_var.set(str(self.grid.shape[1]))
        self.hedge_size_var.set(str(self.hedge_size))
        
        self.update_display()
        self.update_poi_list()
    
    def load_json(self, filename):
        """Charge une grille JSON"""
        with open(filename, 'r') as f:
            data = json.load(f)
        
        self.grid = np.array(data['matrix'], dtype=np.int8)
        self.hedge_size = data.get('hedge_size', 1.0)
        self.points_of_interest = [tuple(poi) for poi in data.get('points_of_interest', [])]
        
        # Mettre à jour les champs
        self.height_var.set(str(self.grid.shape[0]))
        self.width_var.set(str(self.grid.shape[1]))
        self.hedge_size_var.set(str(self.hedge_size))
        
        self.update_display()
        self.update_poi_list()
    
    def save_hdf5(self):
        """Sauvegarde la grille en HDF5"""
        if self.grid is None:
            messagebox.showerror("Erreur", "Aucune grille à sauvegarder")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Sauvegarder la grille HDF5",
            defaultextension=".h5",
            filetypes=[("HDF5", "*.h5 *.hdf5"), ("Tous les fichiers", "*.*")]
        )
        
        if filename:
            try:
                with h5py.File(filename, 'w') as f:
                    # Dataset matrix
                    matrix_ds = f.create_dataset('matrix', data=self.grid, dtype='int8')
                    matrix_ds.attrs['hedge_size'] = self.hedge_size
                    
                    # Dataset points_of_interest
                    if self.points_of_interest:
                        poi_array = np.array(self.points_of_interest, dtype='int16')
                        f.create_dataset('points_of_interest', data=poi_array, dtype='int16')
                
                messagebox.showinfo("Succès", f"Grille sauvegardée: {filename}")
                
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de sauvegarder: {e}")
    
    def save_json(self):
        """Sauvegarde la grille en JSON"""
        if self.grid is None:
            messagebox.showerror("Erreur", "Aucune grille à sauvegarder")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Sauvegarder la grille JSON",
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("Tous les fichiers", "*.*")]
        )
        
        if filename:
            try:
                data = {
                    'matrix': self.grid.tolist(),
                    'hedge_size': self.hedge_size,
                    'points_of_interest': self.points_of_interest,
                    'width': self.grid.shape[1],
                    'height': self.grid.shape[0]
                }
                
                with open(filename, 'w') as f:
                    json.dump(data, f, indent=2)
                
                messagebox.showinfo("Succès", f"Grille sauvegardée: {filename}")
                
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de sauvegarder: {e}")
    
    def on_canvas_click(self, event):
        """Gestionnaire de clic sur le canvas"""
        if self.grid is None or event.inaxes != self.ax:
            return
        
        # Convertir les coordonnées du canvas en indices de grille
        x = int(round(event.xdata))
        y = int(round(event.ydata))
        
        if 0 <= x < self.grid.shape[1] and 0 <= y < self.grid.shape[0]:
            mode = self.edit_mode.get()
            
            if mode == "obstacle":
                self.grid[y, x] = -1  # Obstacle
            elif mode == "free":
                self.grid[y, x] = 0   # Espace libre
            elif mode == "poi":
                if (x, y) not in self.points_of_interest:
                    self.points_of_interest.append((x, y))
                    self.update_poi_list()
            elif mode == "remove_poi":
                if (x, y) in self.points_of_interest:
                    self.points_of_interest.remove((x, y))
                    self.update_poi_list()
            
            self.update_display()
    
    def clear_all_poi(self):
        """Efface tous les points d'intérêt"""
        self.points_of_interest = []
        self.update_poi_list()
        self.update_display()
    
    def update_poi_list(self):
        """Met à jour la liste des points d'intérêt"""
        self.poi_listbox.delete(0, tk.END)
        for i, (x, y) in enumerate(self.points_of_interest):
            self.poi_listbox.insert(tk.END, f"POI {i+1}: ({x}, {y})")
    
    def update_display(self):
        """Met à jour l'affichage de la grille"""
        if self.grid is None:
            return
        
        self.ax.clear()
        
        # Affichage de la grille
        # -1 = obstacle (noir), 0 = libre (blanc), 1 = POI (rouge)
        display_grid = self.grid.copy().astype(float)
        
        # Marquer les POI
        for x, y in self.points_of_interest:
            if 0 <= y < self.grid.shape[0] and 0 <= x < self.grid.shape[1]:
                display_grid[y, x] = 1
        
        # Colormap: noir pour obstacles, blanc pour libre, rouge pour POI
        colors = ['black', 'white', 'red']
        from matplotlib.colors import ListedColormap
        cmap = ListedColormap(colors)
        
        self.ax.imshow(display_grid, cmap=cmap, vmin=-1, vmax=1, origin='upper')
        self.ax.set_title(f"Grille {self.grid.shape[1]}x{self.grid.shape[0]} - Taille cellule: {self.hedge_size}")
        self.ax.set_xlabel("X")
        self.ax.set_ylabel("Y")
        
        # Grille pour faciliter l'édition
        self.ax.set_xticks(np.arange(-0.5, self.grid.shape[1], 1), minor=True)
        self.ax.set_yticks(np.arange(-0.5, self.grid.shape[0], 1), minor=True)
        self.ax.grid(which="minor", color="gray", linestyle='-', linewidth=0.5, alpha=0.3)
        
        self.canvas.draw()


def main():
    """Point d'entrée principal"""
    root = tk.Tk()
    app = GridGenerator(root)
    root.mainloop()


if __name__ == "__main__":
    main()