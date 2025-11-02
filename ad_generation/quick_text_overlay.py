#!/usr/bin/env python3
"""
Quick Text Overlay - Interactively add text to images with drag-and-drop positioning.

Features:
- Click "Add Text" to create draggable text on image
- Drag text anywhere with mouse
- Live text editing - type and see changes instantly
- Font size slider for real-time resizing
- Color picker and outline options
- Click text to select and edit it
- Save burns text into image permanently
- Navigate through folder of images

Controls:
- Click and drag text to move it
- Click text to select it for editing
- Ctrl+S: Save image with text overlays
- Ctrl+N: Next image
- Ctrl+P: Previous image
- Delete: Remove selected text
- Escape: Exit
"""

import os
import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, colorchooser
from PIL import Image, ImageTk, ImageDraw, ImageFont
from pathlib import Path
import glob

# Configuration
BASE_DIR = Path(__file__).parent / "base_images"
OUTPUT_DIR = Path(__file__).parent / "text_overlay_output"
JSON_DIR = OUTPUT_DIR / "jsons"
SUPPORTED_FORMATS = ["*.jpg", "*.jpeg", "*.png", "*.gif"]


class TextItem:
    """Represents a text overlay on the canvas."""
    _id_counter = 0

    def __init__(self, canvas_id, text, x, y, font_family, font_size, color, outline_width, outline_color):
        TextItem._id_counter += 1
        self.id = TextItem._id_counter
        self.canvas_id = canvas_id
        self.outline_ids = []  # List of canvas IDs for outline pieces
        self.text = text
        self.x = x
        self.y = y
        self.font_family = font_family
        self.font_size = font_size
        self.color = color
        self.outline_width = outline_width
        self.outline_color = outline_color


class TextOverlayApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Quick Text Overlay")
        self.root.geometry("1400x900")
        self.root.configure(bg="#2b2b2b")

        # Get list of images
        self.image_paths = self.get_image_paths()
        self.current_index = 0

        # Image state
        self.current_image = None
        self.canvas_image = None
        self.image_scale = 1.0
        self.canvas_width = 1200
        self.canvas_height = 700

        # GIF animation state
        self.is_animated_gif = False
        self.gif_frames = []  # PIL Image frames
        self.gif_durations = []  # Frame durations
        self.gif_current_frame = 0
        self.animation_id = None
        self.image_canvas_id = None  # Track the canvas image ID

        # Text overlay state
        self.text_items = []  # List of TextItem objects
        self.selected_text = None
        self.drag_data = {"x": 0, "y": 0, "item": None}
        self.current_original_path = None  # Track the original image path

        # Create output directories
        OUTPUT_DIR.mkdir(exist_ok=True)
        JSON_DIR.mkdir(exist_ok=True)

        # Create UI
        self.create_ui()

        # Bind keyboard shortcuts
        self.root.bind("<Control-s>", self.save_image)
        self.root.bind("<Control-n>", self.next_image)
        self.root.bind("<Control-p>", self.prev_image)
        self.root.bind("<Delete>", self.delete_selected_text)
        self.root.bind("<Escape>", self.quit_app)

        # Load first image
        if self.image_paths:
            self.load_image()
        else:
            messagebox.showinfo("No Images", f"No images found in {BASE_DIR}")
            self.root.quit()

    def get_image_paths(self):
        """Get all image paths."""
        all_images = []
        for pattern in SUPPORTED_FORMATS:
            all_images.extend(glob.glob(str(BASE_DIR / "**" / pattern), recursive=True))

        print(f"Found {len(all_images)} images in {BASE_DIR}")
        return sorted(all_images)

    def create_ui(self):
        """Create the user interface."""
        # Main container
        main_container = tk.Frame(self.root, bg="#2b2b2b")
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left panel - Controls
        left_panel = tk.Frame(main_container, bg="#3a3a3a", width=250)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_panel.pack_propagate(False)

        # Title
        title = tk.Label(left_panel, text="Text Overlay Controls", font=("Arial", 14, "bold"),
                        bg="#3a3a3a", fg="#ffffff")
        title.pack(pady=10)

        # Text input
        tk.Label(left_panel, text="Text:", bg="#3a3a3a", fg="#ffffff", font=("Arial", 10)).pack(pady=(10, 2))
        self.text_entry = tk.Entry(left_panel, font=("Arial", 12), width=25)
        self.text_entry.pack(pady=5, padx=10)
        self.text_entry.bind("<KeyRelease>", self.update_selected_text)

        # Font size
        tk.Label(left_panel, text="Font Size:", bg="#3a3a3a", fg="#ffffff", font=("Arial", 10)).pack(pady=(15, 2))
        self.font_size_var = tk.IntVar(value=36)
        font_size_frame = tk.Frame(left_panel, bg="#3a3a3a")
        font_size_frame.pack(pady=5)

        self.font_size_slider = tk.Scale(font_size_frame, from_=12, to=200, orient=tk.HORIZONTAL,
                                        variable=self.font_size_var, command=self.update_selected_text,
                                        bg="#3a3a3a", fg="#ffffff", highlightthickness=0, length=150)
        self.font_size_slider.pack(side=tk.LEFT)

        self.font_size_label = tk.Label(font_size_frame, textvariable=self.font_size_var,
                                       bg="#3a3a3a", fg="#ffffff", font=("Arial", 10), width=4)
        self.font_size_label.pack(side=tk.LEFT, padx=5)

        # Text color
        tk.Label(left_panel, text="Text Color:", bg="#3a3a3a", fg="#ffffff", font=("Arial", 10)).pack(pady=(15, 2))
        color_frame = tk.Frame(left_panel, bg="#3a3a3a")
        color_frame.pack(pady=5)

        self.text_color_var = tk.StringVar(value="white")
        colors = [("White", "white"), ("Black", "black"), ("Red", "red"),
                 ("Yellow", "yellow"), ("Blue", "blue"), ("Custom", "custom")]

        for text, color in colors:
            btn = tk.Button(color_frame, text=text, bg=color if color != "custom" else "#888888",
                          fg="black" if color in ["white", "yellow", "custom"] else "white",
                          command=lambda c=color: self.set_text_color(c), width=8)
            btn.pack(pady=2)

        # Outline
        tk.Label(left_panel, text="Outline:", bg="#3a3a3a", fg="#ffffff", font=("Arial", 10)).pack(pady=(15, 2))

        self.outline_enabled_var = tk.BooleanVar(value=True)
        outline_check = tk.Checkbutton(left_panel, text="Enable Outline", variable=self.outline_enabled_var,
                                      command=self.update_selected_text, bg="#3a3a3a", fg="#ffffff",
                                      selectcolor="#555555", font=("Arial", 10))
        outline_check.pack(pady=5)

        outline_width_frame = tk.Frame(left_panel, bg="#3a3a3a")
        outline_width_frame.pack(pady=5)
        tk.Label(outline_width_frame, text="Width:", bg="#3a3a3a", fg="#ffffff", font=("Arial", 9)).pack(side=tk.LEFT)

        self.outline_width_var = tk.IntVar(value=3)
        outline_width_spinner = tk.Spinbox(outline_width_frame, from_=1, to=10, textvariable=self.outline_width_var,
                                          command=self.update_selected_text, width=5, font=("Arial", 10))
        outline_width_spinner.pack(side=tk.LEFT, padx=5)

        # Buttons
        tk.Label(left_panel, text="", bg="#3a3a3a").pack(pady=10)  # Spacer

        add_btn = tk.Button(left_panel, text="➕ Add Text", command=self.add_text,
                           bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), pady=8)
        add_btn.pack(pady=5, padx=10, fill=tk.X)

        delete_btn = tk.Button(left_panel, text="🗑 Delete Selected", command=self.delete_selected_text,
                              bg="#f44336", fg="white", font=("Arial", 11), pady=6)
        delete_btn.pack(pady=5, padx=10, fill=tk.X)

        save_btn = tk.Button(left_panel, text="💾 Save Image (Ctrl+S)", command=self.save_image,
                            bg="#2196F3", fg="white", font=("Arial", 11, "bold"), pady=8)
        save_btn.pack(pady=15, padx=10, fill=tk.X)

        # Navigation
        nav_frame = tk.Frame(left_panel, bg="#3a3a3a")
        nav_frame.pack(side=tk.BOTTOM, pady=10)

        prev_btn = tk.Button(nav_frame, text="⬅ Previous", command=self.prev_image,
                           bg="#555555", fg="white", font=("Arial", 10))
        prev_btn.pack(side=tk.LEFT, padx=5)

        next_btn = tk.Button(nav_frame, text="Next ➡", command=self.next_image,
                           bg="#555555", fg="white", font=("Arial", 10))
        next_btn.pack(side=tk.LEFT, padx=5)

        # Right panel - Canvas
        right_panel = tk.Frame(main_container, bg="#1a1a1a")
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Image info
        info_frame = tk.Frame(right_panel, bg="#1a1a1a")
        info_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 5))

        self.counter_label = tk.Label(info_frame, text="", font=("Arial", 12, "bold"),
                                     bg="#1a1a1a", fg="#ffffff")
        self.counter_label.pack(side=tk.LEFT)

        self.filename_label = tk.Label(info_frame, text="", font=("Arial", 10),
                                      bg="#1a1a1a", fg="#aaaaaa")
        self.filename_label.pack(side=tk.LEFT, padx=20)

        # Canvas for image display
        self.canvas = tk.Canvas(right_panel, bg="#1a1a1a", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Bind canvas events
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)

        # Instructions
        instructions = tk.Label(right_panel,
                              text="💡 Click 'Add Text', then drag it to position | Click text to select & edit",
                              font=("Arial", 10), bg="#1a1a1a", fg="#888888")
        instructions.pack(side=tk.BOTTOM, pady=5)

    def set_text_color(self, color):
        """Set text color."""
        if color == "custom":
            color_code = colorchooser.askcolor(title="Choose text color")
            if color_code[1]:
                self.text_color_var.set(color_code[1])
        else:
            self.text_color_var.set(color)
        self.update_selected_text()

    def stop_animation(self):
        """Stop GIF animation."""
        if self.animation_id:
            self.root.after_cancel(self.animation_id)
            self.animation_id = None

    def animate_gif_frame(self):
        """Animate GIF by cycling through frames."""
        if not self.is_animated_gif or not self.gif_frames:
            return

        # Get current frame
        frame = self.gif_frames[self.gif_current_frame]
        duration = self.gif_durations[self.gif_current_frame]

        # Convert frame to PhotoImage
        photo = ImageTk.PhotoImage(frame)

        # Update the image on canvas (keep text layers on top)
        if self.image_canvas_id:
            self.canvas.itemconfig(self.image_canvas_id, image=photo)
            self.canvas.image = photo  # Keep reference

        # Move to next frame
        self.gif_current_frame = (self.gif_current_frame + 1) % len(self.gif_frames)

        # Schedule next frame
        self.animation_id = self.root.after(duration, self.animate_gif_frame)

    def save_text_overlay_data(self, json_path):
        """Save text overlay data to JSON file."""
        # Ensure we have the original path
        if not self.current_original_path:
            self.current_original_path = self.image_paths[self.current_index]

        data = {
            "original_image_path": str(self.current_original_path),
            "is_animated_gif": self.is_animated_gif,
            "image_width": self.current_image.width,
            "image_height": self.current_image.height,
            "canvas_width": self.canvas_width,
            "canvas_height": self.canvas_height,
            "image_scale": self.image_scale,
            "text_items": []
        }

        # Get canvas image position
        canvas_items = self.canvas.find_withtag("image")
        if canvas_items:
            img_x = self.canvas.coords(canvas_items[0])[0]
            img_y = self.canvas.coords(canvas_items[0])[1]
        else:
            img_x = 0
            img_y = 0

        for text_item in self.text_items:
            # Store canvas coordinates relative to image
            item_data = {
                "text": text_item.text,
                "canvas_x": text_item.x,
                "canvas_y": text_item.y,
                "img_offset_x": img_x,
                "img_offset_y": img_y,
                "font_family": text_item.font_family,
                "font_size": text_item.font_size,
                "color": text_item.color,
                "outline_width": text_item.outline_width,
                "outline_color": text_item.outline_color
            }
            data["text_items"].append(item_data)

        with open(json_path, 'w') as f:
            json.dump(data, f, indent=2)

    def load_text_overlay_data(self, json_path):
        """Load text overlay data from JSON file and recreate text items."""
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)

            # Load the original image as base
            original_path = data.get("original_image_path")
            if original_path and os.path.exists(original_path):
                self.current_original_path = original_path
                self.current_image = Image.open(original_path)
            else:
                # If original not found, use currently loaded image
                print(f"Warning: Original image not found at {original_path}, using current image")

            # Get stored canvas position
            stored_img_offset_x = None
            stored_img_offset_y = None

            # Recreate text items
            for item_data in data["text_items"]:
                if stored_img_offset_x is None:
                    stored_img_offset_x = item_data.get("img_offset_x", 0)
                    stored_img_offset_y = item_data.get("img_offset_y", 0)

                # Get current canvas image position
                canvas_items = self.canvas.find_withtag("image")
                if canvas_items:
                    current_img_x = self.canvas.coords(canvas_items[0])[0]
                    current_img_y = self.canvas.coords(canvas_items[0])[1]
                else:
                    current_img_x = 0
                    current_img_y = 0

                # Calculate position adjustment (in case canvas size changed)
                x_adjust = current_img_x - stored_img_offset_x
                y_adjust = current_img_y - stored_img_offset_y

                # Recreate text at adjusted position
                x = item_data["canvas_x"] + x_adjust
                y = item_data["canvas_y"] + y_adjust

                canvas_id, outline_ids = self.create_outlined_text(
                    x, y,
                    item_data["text"],
                    item_data["font_size"],
                    item_data["color"],
                    item_data["outline_width"],
                    item_data["outline_color"]
                )

                text_item = TextItem(
                    canvas_id,
                    item_data["text"],
                    x, y,
                    item_data["font_family"],
                    item_data["font_size"],
                    item_data["color"],
                    item_data["outline_width"],
                    item_data["outline_color"]
                )
                text_item.outline_ids = outline_ids
                self.text_items.append(text_item)

            print(f"Loaded {len(self.text_items)} text overlays from {json_path}")

        except Exception as e:
            print(f"Error loading text overlay data: {e}")

    def load_image(self):
        """Load and display the current image."""
        if self.current_index >= len(self.image_paths):
            return

        # Stop any running animation
        self.stop_animation()

        # Clear existing text items
        self.text_items = []
        self.selected_text = None
        self.canvas.delete("all")

        # Reset GIF state
        self.is_animated_gif = False
        self.gif_frames = []
        self.gif_durations = []
        self.gif_current_frame = 0
        self.image_canvas_id = None

        # Get current image path (always start from the original)
        original_image_path = self.image_paths[self.current_index]
        self.current_original_path = original_image_path

        # Check if a JSON file exists for this image
        image_name = os.path.basename(original_image_path)
        base_name, ext = os.path.splitext(image_name)

        # Look for JSON files in jsons/ subfolder (most recent one)
        json_files = []
        json_files.append(JSON_DIR / f"{base_name}_text.json")

        counter = 1
        while True:
            json_path = JSON_DIR / f"{base_name}_text_{counter}.json"
            if json_path.exists():
                json_files.append(json_path)
                counter += 1
            else:
                break

        # Find most recent JSON
        most_recent_json = None
        if json_files and any(j.exists() for j in json_files):
            existing_jsons = [j for j in json_files if j.exists()]
            if existing_jsons:
                most_recent_json = max(existing_jsons, key=lambda p: p.stat().st_mtime)

        # Update labels
        self.counter_label.config(text=f"Image {self.current_index + 1} / {len(self.image_paths)}")

        # Load the original image
        image_path = original_image_path
        filename_text = os.path.basename(image_path)

        if most_recent_json:
            filename_text += " [EDITABLE - Has saved overlays]"
            print(f"Found editable overlay data: {most_recent_json}")

        self.filename_label.config(text=filename_text)

        # Load image
        try:
            self.current_image = Image.open(image_path)

            # Check if it's an animated GIF
            try:
                frame_count = self.current_image.n_frames
                if frame_count > 1:
                    self.is_animated_gif = True
                    print(f"Detected animated GIF with {frame_count} frames")
            except AttributeError:
                # Not an animated image
                pass

            # Calculate scaling to fit canvas
            img_width, img_height = self.current_image.size

            # Update canvas size based on window
            self.canvas.update()
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()

            if canvas_width < 100:  # Initial size not ready
                canvas_width = 1200
                canvas_height = 700

            self.canvas_width = canvas_width
            self.canvas_height = canvas_height

            # Calculate scale to fit
            scale_x = canvas_width / img_width
            scale_y = canvas_height / img_height
            self.image_scale = min(scale_x, scale_y, 1.0)  # Don't scale up

            # Resize dimensions
            display_width = int(img_width * self.image_scale)
            display_height = int(img_height * self.image_scale)

            # Center position
            x_offset = (canvas_width - display_width) // 2
            y_offset = (canvas_height - display_height) // 2

            if self.is_animated_gif:
                # Load all GIF frames
                for frame_num in range(frame_count):
                    self.current_image.seek(frame_num)

                    # Get frame duration
                    try:
                        duration = self.current_image.info.get('duration', 100)
                    except:
                        duration = 100

                    self.gif_durations.append(duration)

                    # Copy and resize frame
                    frame = self.current_image.copy().convert('RGBA')
                    frame = frame.resize((display_width, display_height), Image.Resampling.LANCZOS)
                    self.gif_frames.append(frame)

                # Create canvas image with first frame
                self.canvas_image = ImageTk.PhotoImage(self.gif_frames[0])
                self.image_canvas_id = self.canvas.create_image(
                    x_offset, y_offset, image=self.canvas_image, anchor=tk.NW, tags="image"
                )

                # Start animation
                self.gif_current_frame = 0
                self.animate_gif_frame()

                # Update window title
                self.root.title(f"Quick Text Overlay - {os.path.basename(image_path)} [ANIMATED GIF]")

            else:
                # Static image
                display_image = self.current_image.resize((display_width, display_height), Image.Resampling.LANCZOS)
                self.canvas_image = ImageTk.PhotoImage(display_image)
                self.image_canvas_id = self.canvas.create_image(
                    x_offset, y_offset, image=self.canvas_image, anchor=tk.NW, tags="image"
                )

                # Update window title
                self.root.title(f"Quick Text Overlay - {os.path.basename(image_path)}")

            # Load text overlay data if JSON exists (text appears on top of animation)
            if most_recent_json:
                self.load_text_overlay_data(most_recent_json)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image:\n{e}")

    def add_text(self, event=None):
        """Add a new text item to the canvas."""
        text = self.text_entry.get() or "New Text"
        font_size = self.font_size_var.get()
        color = self.text_color_var.get()
        outline_width = self.outline_width_var.get() if self.outline_enabled_var.get() else 0

        # Add text to center of canvas
        x = self.canvas_width // 2
        y = self.canvas_height // 2

        # Create canvas text with outline effect
        canvas_id, outline_ids = self.create_outlined_text(x, y, text, font_size, color, outline_width, "black")

        # Store text item
        text_item = TextItem(canvas_id, text, x, y, "Arial", font_size, color, outline_width, "black")
        text_item.outline_ids = outline_ids
        self.text_items.append(text_item)

        # Select the new text
        self.select_text(text_item)

    def create_outlined_text(self, x, y, text, font_size, color, outline_width, outline_color):
        """Create text on canvas with outline effect. Returns (text_id, [outline_ids])."""
        font = ("Arial", font_size, "bold")
        outline_ids = []

        # Create outline (draw text multiple times offset)
        if outline_width > 0:
            for offset_x in range(-outline_width, outline_width + 1):
                for offset_y in range(-outline_width, outline_width + 1):
                    if offset_x != 0 or offset_y != 0:
                        outline_id = self.canvas.create_text(
                            x + offset_x, y + offset_y,
                            text=text, font=font, fill=outline_color
                        )
                        outline_ids.append(outline_id)

        # Create main text
        text_id = self.canvas.create_text(
            x, y, text=text, font=font, fill=color
        )

        return text_id, outline_ids

    def select_text(self, text_item):
        """Select a text item for editing."""
        self.selected_text = text_item

        # Update UI controls
        self.text_entry.delete(0, tk.END)
        self.text_entry.insert(0, text_item.text)
        self.font_size_var.set(text_item.font_size)
        self.text_color_var.set(text_item.color)
        self.outline_width_var.set(text_item.outline_width)
        self.outline_enabled_var.set(text_item.outline_width > 0)

        # Highlight selected text (you could add a selection indicator here)
        print(f"Selected text: '{text_item.text}'")

    def update_selected_text(self, event=None):
        """Update the selected text item with current control values."""
        if not self.selected_text:
            return

        # Get new values
        new_text = self.text_entry.get()
        new_font_size = self.font_size_var.get()
        new_color = self.text_color_var.get()
        new_outline_width = self.outline_width_var.get() if self.outline_enabled_var.get() else 0

        # Update text item
        self.selected_text.text = new_text
        self.selected_text.font_size = new_font_size
        self.selected_text.color = new_color
        self.selected_text.outline_width = new_outline_width

        # Redraw text on canvas
        self.redraw_text(self.selected_text)

    def redraw_text(self, text_item):
        """Redraw a text item on the canvas."""
        # Remove old text and its outline
        self.canvas.delete(text_item.canvas_id)
        for outline_id in text_item.outline_ids:
            self.canvas.delete(outline_id)

        # Redraw the text with new properties
        text_item.canvas_id, text_item.outline_ids = self.create_outlined_text(
            text_item.x, text_item.y, text_item.text, text_item.font_size,
            text_item.color, text_item.outline_width, text_item.outline_color
        )

    def on_canvas_click(self, event):
        """Handle canvas click - select text or start drag."""
        # Check if clicked on any text
        clicked_items = self.canvas.find_overlapping(event.x - 5, event.y - 5, event.x + 5, event.y + 5)

        for item_id in clicked_items:
            # Find text item - check both main text and outline pieces
            for text_item in self.text_items:
                if text_item.canvas_id == item_id or item_id in text_item.outline_ids:
                    self.select_text(text_item)
                    self.drag_data["item"] = text_item
                    self.drag_data["x"] = event.x
                    self.drag_data["y"] = event.y
                    return

    def on_canvas_drag(self, event):
        """Handle canvas drag - move selected text."""
        if self.drag_data["item"]:
            # Calculate delta
            delta_x = event.x - self.drag_data["x"]
            delta_y = event.y - self.drag_data["y"]

            # Update text position
            text_item = self.drag_data["item"]
            text_item.x += delta_x
            text_item.y += delta_y

            # Move main text
            self.canvas.move(text_item.canvas_id, delta_x, delta_y)

            # Move this item's outline pieces
            for outline_id in text_item.outline_ids:
                self.canvas.move(outline_id, delta_x, delta_y)

            # Update drag position
            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y

    def on_canvas_release(self, event):
        """Handle canvas release - stop dragging."""
        self.drag_data["item"] = None

    def delete_selected_text(self, event=None):
        """Delete the selected text item."""
        if not self.selected_text:
            messagebox.showinfo("No Selection", "Please select a text item first")
            return

        # Remove from canvas - delete main text and all outline pieces
        self.canvas.delete(self.selected_text.canvas_id)
        for outline_id in self.selected_text.outline_ids:
            self.canvas.delete(outline_id)

        # Remove from list
        self.text_items.remove(self.selected_text)
        self.selected_text = None

        # Clear text entry
        self.text_entry.delete(0, tk.END)

    def save_image(self, event=None):
        """Save the image with text overlays burned in."""
        if not self.current_image:
            return

        try:
            # Get canvas image position
            canvas_items = self.canvas.find_withtag("image")
            if canvas_items:
                img_x = self.canvas.coords(canvas_items[0])[0]
                img_y = self.canvas.coords(canvas_items[0])[1]
            else:
                img_x = 0
                img_y = 0

            # Prepare text drawing function
            def draw_text_on_image(img):
                """Apply text overlays to a single image."""
                draw = ImageDraw.Draw(img)

                for text_item in self.text_items:
                    # Convert canvas coordinates to image coordinates
                    img_text_x = int((text_item.x - img_x) / self.image_scale)
                    img_text_y = int((text_item.y - img_y) / self.image_scale)

                    # Scale font size
                    scaled_font_size = int(text_item.font_size / self.image_scale)

                    # Load font
                    try:
                        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", scaled_font_size)
                    except:
                        font = ImageFont.load_default()

                    # Draw outline
                    if text_item.outline_width > 0:
                        outline_width = max(1, int(text_item.outline_width / self.image_scale))
                        for offset_x in range(-outline_width, outline_width + 1):
                            for offset_y in range(-outline_width, outline_width + 1):
                                if offset_x != 0 or offset_y != 0:
                                    draw.text(
                                        (img_text_x + offset_x, img_text_y + offset_y),
                                        text_item.text,
                                        font=font,
                                        fill=text_item.outline_color,
                                        anchor="mm"
                                    )

                    # Draw main text
                    draw.text(
                        (img_text_x, img_text_y),
                        text_item.text,
                        font=font,
                        fill=text_item.color,
                        anchor="mm"
                    )

                return img

            # Get original filename
            image_name = os.path.basename(self.current_original_path or self.image_paths[self.current_index])
            base_name, ext = os.path.splitext(image_name)

            # Remove existing _text or _text_N suffix
            import re
            base_name = re.sub(r'_text(_\d+)?$', '', base_name)

            output_path = OUTPUT_DIR / f"{base_name}_text{ext}"
            json_path = JSON_DIR / f"{base_name}_text.json"

            # Handle duplicate filenames
            counter = 1
            while output_path.exists():
                output_path = OUTPUT_DIR / f"{base_name}_text_{counter}{ext}"
                json_path = JSON_DIR / f"{base_name}_text_{counter}.json"
                counter += 1

            if self.is_animated_gif:
                # Save as animated GIF - apply text to all frames
                print(f"Saving animated GIF with {len(self.gif_frames)} frames...")

                # Reopen original to get full-resolution frames
                original_gif = Image.open(self.current_original_path)
                output_frames = []

                for frame_num in range(original_gif.n_frames):
                    original_gif.seek(frame_num)
                    frame = original_gif.copy().convert('RGBA')

                    # Apply text to this frame
                    frame = draw_text_on_image(frame)

                    # Convert back to palette mode for GIF
                    frame = frame.convert('P', palette=Image.ADAPTIVE)
                    output_frames.append(frame)

                # Get original durations
                original_gif.seek(0)
                durations = []
                for frame_num in range(original_gif.n_frames):
                    original_gif.seek(frame_num)
                    durations.append(original_gif.info.get('duration', 100))

                # Save animated GIF
                output_frames[0].save(
                    output_path,
                    save_all=True,
                    append_images=output_frames[1:],
                    duration=durations,
                    loop=0,
                    optimize=False
                )

                print(f"Saved animated GIF with text overlays!")

            else:
                # Save static image
                output_image = self.current_image.copy()
                output_image = draw_text_on_image(output_image)
                output_image.save(output_path, quality=95)

            # Save text overlay data as JSON
            self.save_text_overlay_data(json_path)

            messagebox.showinfo("Saved", f"Image saved to:\n{output_path}\n\nEditable overlay data:\n{json_path}\n\nYou can continue editing this image!")

            # Reload the image to show the saved version
            self.load_image()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save image:\n{e}")

    def next_image(self, event=None):
        """Load next image."""
        if self.current_index < len(self.image_paths) - 1:
            self.current_index += 1
            self.load_image()
        else:
            messagebox.showinfo("End", "This is the last image")

    def prev_image(self, event=None):
        """Load previous image."""
        if self.current_index > 0:
            self.current_index -= 1
            self.load_image()
        else:
            messagebox.showinfo("Start", "This is the first image")

    def quit_app(self, event=None):
        """Exit the application."""
        self.stop_animation()
        self.root.quit()


def main():
    """Main entry point."""
    # Verify base_images directory exists
    if not BASE_DIR.exists():
        print(f"Error: Directory not found: {BASE_DIR}")
        print("Please ensure base_images/ folder exists")
        return 1

    # Create output directories
    OUTPUT_DIR.mkdir(exist_ok=True)
    JSON_DIR.mkdir(exist_ok=True)

    # Create and run the app
    root = tk.Tk()
    app = TextOverlayApp(root)
    root.mainloop()

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
