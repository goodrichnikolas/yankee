#!/usr/bin/env python3
"""
Quick Image Filter - Visually review and delete unwanted ad images.

Controls:
- Ctrl+Left Arrow: Delete current image and move to next
- Ctrl+Right Arrow: Keep current image and move to next
- Escape: Exit the filter

Images that have been checked are saved to checked_images.json to avoid
reviewing them again on subsequent runs.
"""

import os
import json
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from pathlib import Path
import glob

# Configuration
BASE_DIR = Path(__file__).parent / "base_images"
JSON_FILE = Path(__file__).parent / "checked_images.json"
SUPPORTED_FORMATS = ["*.jpg", "*.jpeg", "*.png", "*.gif"]


class ImageFilterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Quick Image Filter")
        self.root.geometry("1200x900")
        self.root.configure(bg="#2b2b2b")

        # Load checked images history
        self.checked_images = self.load_checked_images()

        # Get list of all images
        self.image_paths = self.get_image_paths()
        self.current_index = 0

        # Animation state
        self.current_image = None
        self.is_animated = False
        self.frame_count = 0
        self.current_frame = 0
        self.animation_id = None
        self.frames = []
        self.frame_durations = []

        # Create UI
        self.create_ui()

        # Bind keyboard shortcuts
        self.root.bind("<Control-Left>", self.delete_and_next)
        self.root.bind("<Control-Right>", self.keep_and_next)
        self.root.bind("<Escape>", self.quit_app)

        # Show first image
        if self.image_paths:
            self.show_current_image()
        else:
            messagebox.showinfo("No Images", f"No unchecked images found in {BASE_DIR}")
            self.root.quit()

    def load_checked_images(self):
        """Load the list of already-checked images from JSON."""
        if JSON_FILE.exists():
            try:
                with open(JSON_FILE, 'r') as f:
                    data = json.load(f)
                    print(f"Loaded {len(data)} checked images from {JSON_FILE}")
                    return set(data)
            except Exception as e:
                print(f"Error loading checked images: {e}")
                return set()
        else:
            print("No checked_images.json found, starting fresh")
            return set()

    def save_checked_images(self):
        """Save the list of checked images to JSON."""
        try:
            with open(JSON_FILE, 'w') as f:
                json.dump(list(self.checked_images), f, indent=2)
        except Exception as e:
            print(f"Error saving checked images: {e}")

    def get_image_paths(self):
        """Get all image paths that haven't been checked yet."""
        all_images = []

        # Search in base_images folder
        for pattern in SUPPORTED_FORMATS:
            all_images.extend(glob.glob(str(BASE_DIR / "**" / pattern), recursive=True))

        # Filter out already-checked images
        unchecked = [img for img in all_images if img not in self.checked_images]

        print(f"Found {len(all_images)} total images")
        print(f"Already checked: {len(self.checked_images)}")
        print(f"Remaining to check: {len(unchecked)}")

        return sorted(unchecked)

    def create_ui(self):
        """Create the user interface."""
        # Top info panel
        info_frame = tk.Frame(self.root, bg="#2b2b2b")
        info_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        self.counter_label = tk.Label(
            info_frame,
            text="",
            font=("Arial", 14, "bold"),
            bg="#2b2b2b",
            fg="#ffffff"
        )
        self.counter_label.pack(side=tk.LEFT)

        self.filename_label = tk.Label(
            info_frame,
            text="",
            font=("Arial", 12),
            bg="#2b2b2b",
            fg="#aaaaaa"
        )
        self.filename_label.pack(side=tk.LEFT, padx=20)

        # Image display area
        self.image_label = tk.Label(self.root, bg="#1a1a1a")
        self.image_label.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        # Controls panel
        controls_frame = tk.Frame(self.root, bg="#2b2b2b")
        controls_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        # Instructions
        instructions = tk.Label(
            controls_frame,
            text="Ctrl+← Delete | Ctrl+→ Keep | Esc Exit",
            font=("Arial", 12, "bold"),
            bg="#2b2b2b",
            fg="#4CAF50"
        )
        instructions.pack()

    def stop_animation(self):
        """Stop any running animation."""
        if self.animation_id:
            self.root.after_cancel(self.animation_id)
            self.animation_id = None

    def animate_frame(self):
        """Display the next frame of an animated GIF."""
        if not self.is_animated or not self.frames:
            return

        # Get current frame
        photo = self.frames[self.current_frame]

        # Update display
        self.image_label.config(image=photo)
        self.image_label.image = photo

        # Get duration for this frame (in milliseconds)
        duration = self.frame_durations[self.current_frame]

        # Move to next frame
        self.current_frame = (self.current_frame + 1) % self.frame_count

        # Schedule next frame
        self.animation_id = self.root.after(duration, self.animate_frame)

    def show_current_image(self):
        """Display the current image."""
        # Stop any running animation first
        self.stop_animation()

        if self.current_index >= len(self.image_paths):
            messagebox.showinfo("Complete", "All images have been checked!")
            self.root.quit()
            return

        # Get current image path
        image_path = self.image_paths[self.current_index]

        # Update labels
        self.counter_label.config(
            text=f"Image {self.current_index + 1} / {len(self.image_paths)}"
        )
        self.filename_label.config(text=os.path.basename(image_path))

        # Load and display image
        try:
            self.current_image = Image.open(image_path)

            # Check if it's an animated GIF
            self.is_animated = False
            self.frame_count = 0
            self.frames = []
            self.frame_durations = []

            try:
                self.frame_count = self.current_image.n_frames
                if self.frame_count > 1:
                    self.is_animated = True
            except AttributeError:
                # Not an animated image
                pass

            # Resize dimensions
            display_width = 1180
            display_height = 750

            if self.is_animated:
                # Load all frames for animated GIF
                for frame_num in range(self.frame_count):
                    self.current_image.seek(frame_num)

                    # Get frame duration (default to 100ms if not specified)
                    try:
                        duration = self.current_image.info.get('duration', 100)
                    except:
                        duration = 100

                    self.frame_durations.append(duration)

                    # Make a copy and resize
                    frame = self.current_image.copy()
                    frame.thumbnail((display_width, display_height), Image.Resampling.LANCZOS)

                    # Convert to PhotoImage
                    photo = ImageTk.PhotoImage(frame)
                    self.frames.append(photo)

                # Start animation
                self.current_frame = 0
                self.animate_frame()

                # Update window title
                self.root.title(f"Quick Image Filter - {os.path.basename(image_path)} [ANIMATED GIF]")

            else:
                # Static image
                self.current_image.thumbnail((display_width, display_height), Image.Resampling.LANCZOS)

                # Convert to PhotoImage
                photo = ImageTk.PhotoImage(self.current_image)

                # Update label
                self.image_label.config(image=photo)
                self.image_label.image = photo

                # Update window title
                self.root.title(f"Quick Image Filter - {os.path.basename(image_path)}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image:\n{e}")
            # Mark as checked anyway and move on
            self.mark_checked_and_next()

    def delete_and_next(self, event=None):
        """Delete current image and move to next."""
        if self.current_index >= len(self.image_paths):
            return

        image_path = self.image_paths[self.current_index]

        try:
            # Delete the file
            os.remove(image_path)
            print(f"✗ Deleted: {image_path}")

            # Mark as checked
            self.checked_images.add(image_path)
            self.save_checked_images()

            # Move to next
            self.current_index += 1
            self.show_current_image()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete image:\n{e}")

    def keep_and_next(self, event=None):
        """Keep current image and move to next."""
        if self.current_index >= len(self.image_paths):
            return

        image_path = self.image_paths[self.current_index]

        print(f"✓ Kept: {image_path}")

        # Mark as checked
        self.checked_images.add(image_path)
        self.save_checked_images()

        # Move to next
        self.current_index += 1
        self.show_current_image()

    def mark_checked_and_next(self):
        """Mark current image as checked and move to next (for errors)."""
        if self.current_index >= len(self.image_paths):
            return

        image_path = self.image_paths[self.current_index]

        # Mark as checked
        self.checked_images.add(image_path)
        self.save_checked_images()

        # Move to next
        self.current_index += 1
        self.show_current_image()

    def quit_app(self, event=None):
        """Exit the application."""
        self.stop_animation()
        print(f"\nChecked {len(self.checked_images)} images total")
        print(f"Remaining: {len(self.image_paths) - self.current_index}")
        self.root.quit()


def main():
    """Main entry point."""
    # Verify base_images directory exists
    if not BASE_DIR.exists():
        print(f"Error: Directory not found: {BASE_DIR}")
        print("Please ensure base_images/ folder exists")
        return 1

    # Create and run the app
    root = tk.Tk()
    app = ImageFilterApp(root)
    root.mainloop()

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
