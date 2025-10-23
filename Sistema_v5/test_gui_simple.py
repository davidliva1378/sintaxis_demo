#!/usr/bin/env python3
"""Test simple para verificar que Tkinter funciona"""
import tkinter as tk
from tkinter import messagebox

root = tk.Tk()
root.title("Test Tkinter")
root.geometry("400x200")

# Forzar al frente en macOS
root.lift()
root.attributes('-topmost', True)
root.after_idle(root.attributes, '-topmost', False)

label = tk.Label(root, text="Si ves esta ventana, Tkinter funciona correctamente", pady=20)
label.pack()

button = tk.Button(root, text="Cerrar", command=root.quit, padx=20, pady=10)
button.pack()

print("✅ Ventana Tkinter creada - debería estar visible")
root.mainloop()
print("✅ Ventana cerrada")
