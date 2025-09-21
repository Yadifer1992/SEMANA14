"""
Agenda Personal - Aplicación GUI con Tkinter
Archivo: Agenda_Tkinter.py
Descripción: Aplicación de agenda que permite agregar, ver y eliminar eventos.
Requisitos cumplidos:
 - Interfaz Tkinter con Treeview para la lista de eventos
 - Entradas para fecha (DatePicker con tkcalendar.DateEntry), hora y descripción
 - Botones: Agregar Evento, Eliminar Evento Seleccionado, Salir
 - Organización con Frames
 - Confirmación al eliminar (diálogo)
 - Guardado y carga automáticos en 'events.json' (opcional pero útil)

Instrucciones de uso:
 1) Instalar dependencias (si no las tienes): pip install tkcalendar
 2) Ejecutar: python Agenda_Tkinter.py

Autor: Código de ejemplo con comentarios explicativos.
"""

import json
import os
import re
import tkinter as tk
from tkinter import ttk, messagebox

# Intentamos importar DateEntry desde tkcalendar. Si no está instalado, el programa
# seguirá funcionando usando un campo Entry para la fecha y mostrando una instrucción
try:
    from tkcalendar import DateEntry
    TKCALENDAR_AVAILABLE = True
except ImportError:
    DateEntry = None
    TKCALENDAR_AVAILABLE = False

# Nombre del archivo donde se guardarán los eventos (persistencia sencilla)
STORAGE_FILE = 'events.json'


class AgendaApp:
    def __init__(self, root):
        self.root = root
        self.root.title('Agenda Personal')
        self.root.geometry('720x480')
        self.root.resizable(False, False)

        # Contenedores (Frames)
        self.frame_inputs = ttk.Frame(root, padding=10)
        self.frame_inputs.pack(fill='x')

        self.frame_actions = ttk.Frame(root, padding=10)
        self.frame_actions.pack(fill='x')

        self.frame_list = ttk.Frame(root, padding=10)
        self.frame_list.pack(fill='both', expand=True)

        # --- Campos de entrada ---
        # Fecha: usar DateEntry si está disponible, si no usar Entry
        ttk.Label(self.frame_inputs, text='Fecha (DD/MM/AAAA):').grid(row=0, column=0, sticky='w')
        if TKCALENDAR_AVAILABLE:
            self.input_fecha = DateEntry(self.frame_inputs, date_pattern='dd/mm/y')
        else:
            # Fallback: entrada de texto y una etiqueta que explica cómo ingresar la fecha
            self.input_fecha = ttk.Entry(self.frame_inputs)
            ttk.Label(self.frame_inputs, text='(Instalar tkcalendar para seleccionar fecha)').grid(row=1, column=0, sticky='w')

        self.input_fecha.grid(row=0, column=1, padx=6, pady=2)

        # Hora
        ttk.Label(self.frame_inputs, text='Hora (HH:MM):').grid(row=0, column=2, sticky='w')
        self.input_hora = ttk.Entry(self.frame_inputs)
        self.input_hora.grid(row=0, column=3, padx=6, pady=2)

        # Descripción
        ttk.Label(self.frame_inputs, text='Descripción:').grid(row=1, column=2, sticky='w')
        self.input_desc = ttk.Entry(self.frame_inputs, width=50)
        self.input_desc.grid(row=1, column=3, columnspan=2, padx=6, pady=2, sticky='w')

        # --- Botones de acción ---
        self.btn_add = ttk.Button(self.frame_actions, text='Agregar Evento', command=self.add_event)
        self.btn_add.pack(side='left', padx=6)

        self.btn_delete = ttk.Button(self.frame_actions, text='Eliminar Evento Seleccionado', command=self.delete_selected)
        self.btn_delete.pack(side='left', padx=6)

        self.btn_exit = ttk.Button(self.frame_actions, text='Salir', command=self.on_exit)
        self.btn_exit.pack(side='right', padx=6)

        # --- Treeview para mostrar los eventos ---
        cols = ('fecha', 'hora', 'descripcion')
        self.tree = ttk.Treeview(self.frame_list, columns=cols, show='headings', selectmode='browse')
        self.tree.heading('fecha', text='Fecha')
        self.tree.heading('hora', text='Hora')
        self.tree.heading('descripcion', text='Descripción')

        self.tree.column('fecha', width=100, anchor='center')
        self.tree.column('hora', width=80, anchor='center')
        self.tree.column('descripcion', width=480, anchor='w')

        # Barra de desplazamiento vertical
        vsb = ttk.Scrollbar(self.frame_list, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side='right', fill='y')

        self.tree.pack(fill='both', expand=True)

        # Cargar eventos guardados
        self.load_events()

        # Atajos y bindings
        self.root.protocol('WM_DELETE_WINDOW', self.on_exit)
        # Enter en el campo de descripción agrega el evento (comodidad)
        self.input_desc.bind('<Return>', lambda e: self.add_event())

    def validate_time(self, time_str):
        """Valida que la hora tenga formato HH:MM y sea una hora válida."""
        if not time_str:
            return False
        m = re.match(r'^(\d{1,2}):(\d{2})$', time_str)
        if not m:
            return False
        h = int(m.group(1))
        mm = int(m.group(2))
        return 0 <= h <= 23 and 0 <= mm <= 59

    def add_event(self):
        """Toma los datos de los campos, valida y agrega un nuevo evento al Treeview y al almacenamiento."""
        fecha = self.input_fecha.get().strip()
        hora = self.input_hora.get().strip()
        desc = self.input_desc.get().strip()

        # Validaciones básicas
        if not fecha:
            messagebox.showwarning('Validación', 'Por favor ingrese una fecha.')
            return
        if not hora:
            messagebox.showwarning('Validación', 'Por favor ingrese una hora.')
            return
        if not self.validate_time(hora):
            messagebox.showwarning('Validación', 'La hora debe tener formato HH:MM y ser válida (00:00 - 23:59).')
            return
        if not desc:
            messagebox.showwarning('Validación', 'Por favor ingrese una descripción.')
            return

        # Insertar en Treeview
        self.tree.insert('', 'end', values=(fecha, hora, desc))

        # Limpiar campos
        if not TKCALENDAR_AVAILABLE:
            self.input_fecha.delete(0, 'end')
        self.input_hora.delete(0, 'end')
        self.input_desc.delete(0, 'end')

        # Guardar cambios
        self.save_events()
        messagebox.showinfo('Éxito', 'Evento agregado correctamente.')

    def delete_selected(self):
        """Elimina el evento seleccionado previa confirmación."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning('Eliminar', 'No hay ningún evento seleccionado.')
            return

        # Confirmación opcional
        confirm = messagebox.askyesno('Confirmar eliminación', '¿Está seguro que desea eliminar el evento seleccionado?')
        if not confirm:
            return

        self.tree.delete(selected[0])
        self.save_events()
        messagebox.showinfo('Eliminar', 'Evento eliminado.')

    def get_all_events(self):
        """Devuelve una lista de diccionarios con los eventos presentes en el Treeview."""
        events = []
        for iid in self.tree.get_children():
            fecha, hora, desc = self.tree.item(iid, 'values')
            events.append({'fecha': fecha, 'hora': hora, 'descripcion': desc})
        return events

    def save_events(self):
        """Guarda los eventos en un archivo JSON para persistencia simple."""
        events = self.get_all_events()
        try:
            with open(STORAGE_FILE, 'w', encoding='utf-8') as f:
                json.dump(events, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror('Error', f'No se pudo guardar el archivo: {e}')

    def load_events(self):
        """Carga eventos desde el archivo JSON si existe."""
        if not os.path.exists(STORAGE_FILE):
            return
        try:
            with open(STORAGE_FILE, 'r', encoding='utf-8') as f:
                events = json.load(f)
            # Vaciar Treeview
            for iid in self.tree.get_children():
                self.tree.delete(iid)
            # Insertar cada evento
            for ev in events:
                fecha = ev.get('fecha', '')
                hora = ev.get('hora', '')
                desc = ev.get('descripcion', '')
                self.tree.insert('', 'end', values=(fecha, hora, desc))
        except Exception as e:
            messagebox.showerror('Error', f'No se pudo leer el archivo de eventos: {e}')

    def on_exit(self):
        """Acción a ejecutar al cerrar la aplicación: guardar y salir."""
        # Guardamos antes de salir
        try:
            self.save_events()
        except Exception:
            pass
        self.root.destroy()


if __name__ == '__main__':
    root = tk.Tk()

    if not TKCALENDAR_AVAILABLE:
        # Si tkcalendar no está instalado, informamos en consola y con un diálogo opcional
        print('Aviso: No se encontró "tkcalendar". Para activar DatePicker ejecute: pip install tkcalendar')

    app = AgendaApp(root)
    root.mainloop()
