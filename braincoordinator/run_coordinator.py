import sys
from os import system, name, path
from os.path import dirname

import cv2

import numpy as np
#from openpyxl import load_workbook
#from shutil import copyfile

from datetime import datetime

from braincoordinator.utilities.manager import Manager
from braincoordinator.utilities.computations import *
from braincoordinator.utilities.arguments import Arguments
from braincoordinator.utilities.get_atlas import Getter

from tkinter import *
from tkinter import ttk
import tkinter as tk
from tkinter.filedialog import asksaveasfile
from PIL import Image, ImageTk

font = cv2.FONT_HERSHEY_SIMPLEX

bold_font = 'Helvetica 14 bold'
letters = ["a", "s", "z", "x", "d", "f"]

class CommandPanel(tk.Frame):
    def __init__(self, parent, root):
        root.log = ""
        tk.Frame.__init__(self, parent)
        self.canvas = tk.Canvas(self, borderwidth=0)
        window = self.canvas


        Label(window ,text = "marker ", font=bold_font).grid(row = 0,column = 0, sticky=E)

        Label(window ,text = "ap ",width=3, font=bold_font).grid(row = 1,column = 0, sticky=E)
        Label(window ,text = "ml ",width=3, font = bold_font).grid(row = 2,column = 0, sticky=E)
        Label(window ,text = "dv ",width=3, font=bold_font).grid(row = 3,column = 0, sticky=E)


        root.tkt_log = tk.Text(window, width=60)
        root.tkt_log.grid(row = 5, column = 0, columnspan=5, rowspan=4, sticky=W)
        root.tkt_log.insert(END, "brain coordinator initiated\n")

        def tkt_log_callback(*args):
            root.tkt_log.see(END)

        root.tkt_log.bind('<<Modified>>', tkt_log_callback)

        scroll = tk.Scrollbar(window, orient="vertical", command=root.tkt_log.yview)
        scroll.configure(orient="vertical", command=root.tkt_log.yview)
        root.tkt_log.configure(yscrollcommand=scroll.set)
        scroll.grid(row=5, rowspan=4, column=5,sticky="nsew")


        def ignore_letters(e):
            key = e.char
            if key in letters:

                #self.window.focus_set()
                root.tkt_key(key, False)
                return "break"

        root.tkt_ap = Entry(window)
        root.tkt_ap.grid(row = 1,column = 1, sticky=N+S+E+W,columnspan=3)
        root.tkt_ap.bind('<Return>', root.coord_callback)
        root.tkt_ap.bind('<Key>', ignore_letters)
        #root.tkt_ap.bind('<Control-a>', lambda x:print("JJJJ"))

        root.tkt_ml = Entry(window)
        root.tkt_ml.grid(row = 2,column = 1, sticky=N+S+E+W,columnspan=3)
        root.tkt_ml.bind('<Return>', root.coord_callback)
        root.tkt_ml.bind('<Key>', ignore_letters)

        root.tkt_dv = Entry(window)
        root.tkt_dv.grid(row = 3,column = 1, sticky=N+S+E+W,columnspan=3)
        root.tkt_dv.bind('<Return>', root.coord_callback)
        root.tkt_dv.bind('<Key>', ignore_letters)



        def mark():

            #print(self.tkt_ap.get(), self.tkt_ml.get(), self.tkt_dv.get())
            try:
                point = (float(eval(root.tkt_ap.get())), float(eval(root.tkt_ml.get())), float(eval(root.tkt_dv.get())))
            except Exception as e:
                print("invalid coordinates")
                print(e)
                return
            nearest_coronal, nearest_sagittal = root.manager.find_nearest_slices(point[:2])


            pixels_point = root.manager.to_pixel(point, 0) #self.manager.convert_to_pixels(point)



            if root.tkt_selection == 0:
                root.markers.append([pixels_point, nearest_coronal, point, 0])
                label=f"M{len(root.markers)-1}"
                root.drop_down['menu'].add_command(label=label, command=tk._setit(root.tkt_variable, label))
                root.tkt_log.insert(END, f"{label} added\n")
            else: #replace
                root.markers[root.tkt_selection - 1] = [pixels_point, nearest_coronal, point, 0]
                root.tkt_log.insert(END, f"M{root.tkt_selection - 1} saved\n")

            c, s = root.update()

            root.update_coronal_tkt(c)
            root.update_sagittal_tkt(s)

        root.save_txt = StringVar()
        root.save_txt.set("add")
        ttk.Button(window, textvariable=root.save_txt,command=mark, width=4).grid(row=4, column=0, columnspan=1)


        OPTIONS = ["new"] + [f"M{i}" for i,_ in enumerate(root.markers)]
        root.tkt_variable = variable = StringVar(window)
        root.tkt_selection = 0

        def go_new():
            variable.set(OPTIONS[0])


        gonew_btn = ttk.Button(window ,text="<<",command=go_new,width=3)
        gonew_btn.grid(row=0, column=5, sticky=N+S+E+W)

        ttk.Button(window, text="show position",command=root.coord_callback,width=7).grid(row=4, column=1, sticky=N+S+E+W)
        ttk.Button(window, text="clear",command=root.coord_callback,width=3).grid(row=4, column=2, sticky=N+S+E+W)
        ttk.Button(window, text="export",command=root.export,width=4).grid(row=4, column=3, sticky=N+S+E+W)


        def callback(*args):
            OPTIONS = ["new"] + [f"M{i}" for i,_ in enumerate(root.markers)]
            root.tkt_selection = selection = OPTIONS.index(variable.get())
            if selection == 0:# new marker
                root.tkt_log.insert(END, "add new marker coordinates\n")
                root.save_txt.set("add")
                gonew_btn["state"] = DISABLED

                #self.tkt_ap.delete(0,END)
                #self.tkt_ml.delete(0,END)
                #self.tkt_dv.delete(0,END)
            else:

                #root.tkt_msg.set(root.log)
                root.tkt_log.insert(END, f"M{selection-1} loaded\n")
                root.save_txt.set("save")

                gonew_btn["state"] = "normal"
                marker_coords = root.markers[selection - 1][2]
                root.tkt_ap.delete(0,END)
                root.tkt_ml.delete(0,END)
                root.tkt_dv.delete(0,END)
                root.tkt_ap.insert(0, marker_coords[0])
                root.tkt_ml.insert(0, marker_coords[1])
                root.tkt_dv.insert(0, marker_coords[2])

                def remove_mark():
                    # if pair, remove both. Open prompt first (are you sure)
                    marker_index = root.tkt_selection - 1
                    if len(root.markers)%2 == 0:
                        #if self.tkt_selection == len(self.markers):
                        root.paths.pop(marker_index//2 - 1)
                        root.markers.pop(marker_index - 1)

                    root.markers.pop(marker_index)

                    root.drop_down['menu'].delete(root.tkt_selection )
                    variable.set(OPTIONS[root.tkt_selection - 1])


                    c, s = self.update()

                    self.update_coronal_tkt(c)
                    self.update_sagittal_tkt(s)

                #ttk.Button(window ,text="remove",command=remove_mark).grid(row=6,column=1)

        variable.trace("w", callback)
        variable.set(OPTIONS[0]) # default value

        root.drop_down = OptionMenu(window, variable, *list(OPTIONS))
        #self.drop_down.configure(background = "yellow")
        root.drop_down.grid(row = 0,column = 1, sticky=N+S+E+W, columnspan=3)

        gonew_btn["state"] = DISABLED

        self.canvas.pack(side="left", fill="both", expand=True)

class Example(tk.Frame):
    def __init__(self, parent, data):

        tk.Frame.__init__(self, parent)

        scope_frame = tk.Frame(self)
        scope_frame.pack(side="top", fill="x")

        ttk.Button(scope_frame, text="scope", command=self.set_scope).pack(side=RIGHT)

        self.scope_entry = Entry(scope_frame)
        self.scope_entry.pack(side=TOP, fill="x")
        self.scope_entry.bind('<Return>', self.set_scope)


        self.make_frame()

        tk.Label(self.frame, text="search for abbreviations above", anchor="w").grid(row=0, column=1,columnspan=2, sticky=N+S+E+W)

        self.data = data
        self.scope = "all"

        #self.populate()

    def make_frame(self):
        self.canvas = tk.Canvas(self, highlightthickness=1, highlightbackground="#a1a1a1")
        self.frame = tk.Frame(self.canvas)
        self.hsb = tk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)

        self.vsb = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)
        self.canvas.configure(xscrollcommand=self.hsb.set)

        self.vsb.pack(side="right", fill="y")
        self.hsb.pack(side="bottom", fill="x")

        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.create_window((4,4), window=self.frame, anchor="nw",
                                  tags="self.frame")

        self.frame.bind("<Configure>", self.onFrameConfigure)

    def set_scope(self, *args):
        self.scope = str(self.scope_entry.get())
        self.frame.destroy()
        self.canvas.destroy()
        self.vsb.destroy()
        self.hsb.destroy()

        self.make_frame()
        self.populate()

    def populate(self):
        scope = self.scope.lower()
        i = 0
        if scope == "all" or self.scope == "":
            for row, abbr in enumerate(self.data):
                if abbr["description"] == "":
                    tk.Label(self.frame, text=abbr["abbreviation"], font=bold_font).grid(row=row, column=0,columnspan=2, sticky=N+S+E+W)
                else:
                    tk.Label(self.frame, text=abbr["abbreviation"], font=bold_font).grid(row=row, column=0,sticky=N+S+E+W)

                    tk.Label(self.frame, text=abbr["description"], anchor="w").grid(row=row, column=1,sticky=N+S+E+W)

        else:
            for row, abbr in enumerate(self.data):

                if abbr["abbreviation"][:len(scope)].lower() == scope:

                    tk.Label(self.frame, text=abbr["abbreviation"], font=bold_font).grid(row=row, column=0,sticky=N+S+E+W)

                    tk.Label(self.frame, text=abbr["description"], anchor="w").grid(row=row, column=1,sticky=N+S+E+W)
                    i+=1
            if i == 0:
                tk.Label(self.frame, text="no areas found, try again (e.g., 'CTX', 'all')", anchor="w").grid(row=0, column=1,columnspan=2, sticky=N+S+E+W)

    def onFrameConfigure(self, event):
        '''Reset the scroll region to encompass the inner frame'''
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

class Coordinator:
    """
    Xtodo: musseplacering skal give et zoomed-billede nederst
    Sagital slides skal spejles så der også er negative værdier
    Xnår man taster ting ind i marker, skal der komme cursor op på canvas
    X---- se på paths, virker ikke helt (kan måske være to_pixels)
    xxxx^^^^^^^ MANGLER STADIG. NEGATIVE OG POSITIVE TAL FORBYTTES

    Gennemtænk marker-txt placering. Det kan gøres smartere, måske
        bedre 3d
        tykkelse af line
    Fix remove markers
    XAdd acronyms
    Fjern gamle GUI
    XRyk command panel over i sin egen class (SKAL FIXES)
    XFix billedeoperationer så de laves på mindste billeder
    Gør så man kan bevæge cursor på zoom-image
    Gør så man kan gemme og loade markers (evt lav numpy save/load)
    """

    def __init__(self, args, ap:float = 0, ml:float = 0, dv:float =0) -> None:

        self.arguments = Arguments(args)
        self.cursor_color = (0,0,0)
        self.bg_color = "#262626"
        self.zoom_size = 100

        if self.get(self.arguments.get):
            return

        self.reference = int(str(self.arguments.reference[0]).lower() == "l") #bregma = 0; lambda = 1
        self.counterreference = int(self.reference == 0)
        self.dir_path = dirname(path.realpath(__file__))
        self.animal = self.arguments.animal
        self.preload = self.arguments.preload

        animal_path = "{}/atlas/{}/".format(self.dir_path, self.animal)

        try:
            self.manager = Manager(animal_path, self.preload, self.reference)
        except FileNotFoundError as e:
            print(e)
            print("")
            print("Atlas not available.")
            print("Write '--get [atlas]' to download an atlas.")
            print("Or, write '--get list' to list all atlases.")
            return


        self.selected_marker = None

        self.markers = []
        self.paths = []

        self.primary_color = [255, 0, 0]
        self.second_color = [255, 50, 50]
        self.third_color = [150,150,150]

        self.x, self.y = [0,0], [0,0]

        self.hover_window = 0


        self.print_instructions()

        self.manager.set_values(ap, ml, dv)
        self.manager.coronal_index, self.manager.sagittal_index = self.manager.find_nearest_slices()
        self.setup_manual_prompt()
        self.manual_marker()


    def get(self, get:str):

        if get != "":
            Getter(get)
            return True

        return False

    def print_instructions(self):
        instructions = """
                        BRAIN COORDINATOR
            Developed by Simon Arvin
            https://github.com/simonarvin/braincoordinator

        INSTRUCTIONS:
        Hold Control and press...:
        A/S - previous/next coronal slice.
        Z/X - previous/next sagittal slice.
        D   - place marker.
        F   - remove marker.

        Click and drag to move markers.
        """

        print(instructions)

    def abbr_popup(self):
        win = tk.Toplevel()
        win.wm_title("Abbreviations")
        win.geometry("400x200")


        example = Example(win, self.manager.abbreviations)
        example.pack(side="top", fill="both", expand=True)

    def img_to_tk(self, img):
        #img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        return ImageTk.PhotoImage(Image.fromarray(img))

    def export(self):
        if len(self.markers) == 0:
            print("no markers: Nothing to export.")
            return
        export_file = asksaveasfile(title="Select Location", initialfile = "brainy_export.txt", filetypes=(("Text Files", "*.txt"),))
        verbs = []
        for i, marker in enumerate(self.markers):
            verbs.append(self.print_markers(i, marker))
        verbs=list(sum(verbs, ()))
        #verbs[:] = [v for v in verbs if v != ""]
        for i, verb in enumerate(verbs):
            export_file.write(verb+"\n")
            if (i + 1) % 3 == 0:
                export_file.write("\n")

    def coord_callback(self,*args):
        ap = ml = dv = -99

        try:
            ap = float(eval(self.tkt_ap.get()))
        except:
            pass

        try:
            ml = float(eval(self.tkt_ml.get()))
        except:
            pass

        try:
            dv = float(eval(self.tkt_dv.get()))
        except:
            pass

        point = (ap, ml, dv)
        pixels_point_coronal = self.manager.to_pixel(point, 0)
        pixels_point_sagittal = self.manager.to_pixel(point, 1)

        coronal_image, sagittal_image = self.coronal_image.copy(), self.sagittal_image.copy()

        nearest_coronal, nearest_sagittal = self.manager.find_nearest_slices((ap, ml))
        upd=False
        if ap != -99:
            #sagittal_image[:, pixels_point_sagittal[0]] = self.third_color
            self.manager.coronal_index = nearest_coronal
            self.x[1] = pixels_point_sagittal[0]
            upd=True


        if dv != -99:
            #sagittal_image[pixels_point_sagittal[1], :] = self.third_color
            #coronal_image[pixels_point_coronal[1], :] = self.third_color
            self.y = [pixels_point_coronal[1], pixels_point_sagittal[1]]

        if ml != -99:
            #coronal_image[:,pixels_point_coronal[0]] = self.third_color
            self.manager.sagittal_index = nearest_sagittal
            self.x[0] = pixels_point_coronal[0]
            upd=True

        if upd:
            self.update()

        self.hover_window = -1

        self.update_cursors()



    def setup_manual_prompt(self):
        self.window = window = Tk()
        #self.window.configure(background=self.bg_color)
        window.title("stereotaxic coordinator")
        #window.geometry('300x200')
        #window.configure(background = "white")
        self.coronal_txt = StringVar()
        self.coronal_txt.set("move cursor to canvas")

        Label(window,textvariable = self.coronal_txt, height = 1).grid(row = 0, column = 0, columnspan =20)

        self.sagittal_txt = StringVar()
        self.sagittal_txt.set("move cursor to canvas")
        Label(window,textvariable = self.sagittal_txt, height = 1).grid(row = 0, column = 20, columnspan =20)

        self.zoom_txt = StringVar()
        self.zoom_txt.set("")
        self.zoom_txt2 = StringVar()
        self.zoom_txt2.set("Zoom canvas")
        Label(window, textvariable = self.zoom_txt, height = 1).grid(row = 2, column = 20, columnspan = 10)

        Label(window, textvariable = self.zoom_txt2, height = 1, font = bold_font).grid(row = 2, column = 10, columnspan = 10, sticky=E)

        Label(window,text="Command panel", height = 1, font=bold_font).grid(row = 2, column = 0, columnspan =10)
        command_panel = CommandPanel(window, self)
        command_panel.grid(row=3, column=0, rowspan=20, columnspan=10, sticky=N)

        Label(window ,text = "Abbreviations", font=bold_font).grid(row = 2, column = 30, columnspan=10)
        example = Example(window, self.manager.abbreviations)

        example.grid(row=3, column=30, rowspan=20, columnspan=10,sticky=N+S+E+W)

        window.update()

        self.zoom_size = (int(example.winfo_height()*.6), int(example.winfo_height()*.3))

        #Grid.columnconfigure(self.window, 4, weight=1)


    def manual_marker(self):


        def close_():
            self.window.destroy()

        menubar = Menu(self.window)
        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_command(label="Export as..", command=close_)
        filemenu.add_command(label="Exit", command=close_)

        menubar.add_cascade(label="File", menu=filemenu)

        editmenu = Menu(menubar, tearoff=0)
        editmenu.add_command(label="Undo", command=close_)

        menubar.add_cascade(label="Edit", menu=editmenu)

        helpmenu = Menu(menubar, tearoff=0)
        helpmenu.add_command(label="Abbreviations", command=self.abbr_popup)
        helpmenu.add_command(label="About", command=lambda:None)
        menubar.add_cascade(label="Help", menu=helpmenu)

        self.window.config(menu=menubar)

        #ttk.Button(self.window ,text="close",command=close_).grid(row=6, column=3, columnspan=2)

        coronal_image, sagittal_image = self.update()
        coronal_image=self.img_to_tk(coronal_image)
        self.tkt_coronal = Label(self.window, image = coronal_image,bd=0, cursor="cross")
        self.tkt_coronal.image = coronal_image
        self.tkt_coronal.grid(row=1, column=0, columnspan=20)

        self.tkt_coronal.bind('<Motion>', self.frontal_mouse_move)
        #self.window.bind('<Key>',self.tkt_key)
        for letter in letters:

            self.window.bind(f'<Control-{letter}>', lambda _, char=letter:self.tkt_key(char, False))


        self.tkt_zoom = Label(self.window, bd=0)
        self.tkt_zoom.grid(row=3, column=10, columnspan=20, rowspan=20, sticky=N)


        sagittal_image=self.img_to_tk(sagittal_image)
        self.tkt_sagittal = Label(self.window, image = sagittal_image,bd=1, cursor="cross")
        self.tkt_sagittal.image = sagittal_image
        self.tkt_sagittal.grid(row = 1, column=20, columnspan = 20)
        self.tkt_sagittal.bind('<Motion>', self.sagittal_mouse_move)

        self.window.mainloop()
        self.setup_manual_prompt()

    def tkt_key(self, e, type = True):

        if type:
            key = e.char
        else:
            key = e

        if key=="d":
            point = (self.x[self.hover_window], self.y[self.hover_window])
            self.place_marker(point)

        elif key == "x":
            self.manager.next("sagittal")

        elif key == "z":
            self.manager.previous("sagittal")

        elif key == "a":
            self.manager.next("coronal")

        elif key == "s":
            self.manager.previous("coronal")
        else:
            return

        self.update()
        self.update_cursors()



    def frontal_mouse_move(self, e) -> None:
        x,y = e.x, e.y

        self.hover_window = 0

        if self.selected_marker != None:
            if self.selected_marker[3] == self.hover_window:
                self.manager.update_marker(self.selected_marker, (x, y), self.hover_window)
                coronal_image, sagittal_image = self.update()


        coords = self.manager.convert_to_mm((x,y), 0)
        #cv2.putText(coronal_image, f"ap: {coords[0]}; ml: {coords[1]}; dv: {coords[2]}", self.manager.sagital_dvs_txt, font,  .5, self.primary_color, 1, cv2.LINE_AA)
        self.coronal_txt.set(f"ap: {coords[0]}; ml: {coords[1]}; dv: {coords[2]}")
        self.zoom_txt.set(f"ap: {coords[0]}; ml: {coords[1]}; dv: {coords[2]}")
        self.zoom_txt2.set("Zoom: coronal")

        self.x[0], self.y[0] = x, y

        nearest_coronal, nearest_sagittal = self.manager.find_nearest_slices((*coords[:2],))
        self.manager.sagittal_index = nearest_sagittal
        self.update()

        self.update_cursors()

    def update_cursors(self):
        coronal_image, sagittal_image = np.array(self.coronal_image, order='K', copy=True), np.array(self.sagittal_image, order='K', copy=True)
        #coronal_image, sagittal_image = self.coronal_image.copy(), self.sagittal_image.copy()
        x0, x1 = self.x
        y0, y1 = self.y

        if self.hover_window == 0:
            try:

                pixel = self.manager.to_pixel((str_to_float(self.manager.coronals[self.manager.coronal_index][0]), -1, -1), 1)
                coronal_image[:,x0] = self.cursor_color
                coronal_image[y0,:] = self.cursor_color
                sagittal_image[y0,:] = self.cursor_color

                sagittal_image[:, pixel[0]] = self.cursor_color
            except:
                pass
        elif self.hover_window==1:
            try:
                pixel = self.manager.to_pixel((-1, str_to_float(self.manager.sagittals[self.manager.sagittal_index]), -1), 0)
                sagittal_image[:,x1] = self.cursor_color
                sagittal_image[y1,:] = self.cursor_color
                coronal_image[y1,:] = self.cursor_color
                coronal_image[:, pixel[0]] = self.cursor_color
            except Exception as e:
                print(e)
                pass
        else:
            coronal_image[:,x0] = self.cursor_color
            coronal_image[y0,:] = self.cursor_color
            sagittal_image[:,x1] = self.cursor_color
            sagittal_image[y1,:] = self.cursor_color


        self.update_sagittal_tkt(sagittal_image)
        self.update_coronal_tkt(coronal_image)


    def update_coronal_tkt(self, img):
        img = self.img_to_tk(img)
        self.tkt_coronal.configure(image=img)
        self.tkt_coronal.image = img


        if self.hover_window == 0:
            self.update_zoom(self.full_coronal_image)

    def sagittal_mouse_move(self, e) -> None:
        x,y = e.x, e.y

        self.hover_window = 1

        if self.selected_marker != None:
            if self.selected_marker[3] == self.hover_window:
                self.manager.update_marker(self.selected_marker, (x, y), self.hover_window)
                coronal_image, sagittal_image = self.update()
                #cv2.imshow("Coronal", coronal_image)

        coords = self.manager.convert_to_mm((x,y), 1)
        #cv2.putText(sagittal_image, f"ap: {coords[0]}; ml: {coords[1]}; dv: {coords[2]}", self.manager.sagital_dvs_txt, font,  .5, self.primary_color, 1, cv2.LINE_AA)
        self.sagittal_txt.set(f"ap: {coords[0]}; ml: {coords[1]}; dv: {coords[2]}")
        self.zoom_txt.set(f"ap: {coords[0]}; ml: {coords[1]}; dv: {coords[2]}")
        self.zoom_txt2.set("Zoom: sagittal")
        #cv2.imshow("Sagittal", sagittal_imagexr)
        self.x[1], self.y[1] = x, y

        #todo: update AP view according to: coords[0]

        nearest_coronal, nearest_sagittal = self.manager.find_nearest_slices((*coords[:2],))
        self.manager.coronal_index = nearest_coronal
        self.update()
        self.update_cursors()


    def update_sagittal_tkt(self, img):
        img = self.img_to_tk(img)
        self.tkt_sagittal.configure(image=img)
        self.tkt_sagittal.image = img

        if abs(self.hover_window) == 1:
            self.update_zoom(self.full_sagittal_image)

    def update_zoom(self, rawimg):
        x, y = round(self.x[self.hover_window]/self.manager.scale_factor), round(self.y[self.hover_window]/self.manager.scale_factor)
        zoom_size = self.zoom_size
        size = rawimg.shape

        y_1 = max(y - zoom_size[1], 0)
        subtr_y2 = (y - zoom_size[1]) - y_1
        y_2 = min(y + zoom_size[1], size[0])
        subtr_y1 = (y + zoom_size[1]) - y_2


        x_1 = max(x - zoom_size[0], 0)
        subtr_x2 = (x - zoom_size[0]) - x_1
        x_2 = min(x + zoom_size[0], size[1])
        subtr_x1 = (x + zoom_size[0]) - x_2
        #rawimg = rawimg.copy()
        rawimg = np.array(rawimg, order='K', copy=True)
        try:
            rawimg[:, x] = self.cursor_color
            rawimg[y,:] = self.cursor_color
        except:
            pass

        img = self.img_to_tk(rawimg[y_1 - subtr_y1:y_2-subtr_y2, x_1 - subtr_x1:x_2-subtr_x2])
        self.tkt_zoom.configure(image=img)
        self.tkt_zoom.image = img


    def place_cross(self, source: np.ndarray, point: tuple, color: tuple, size = 8) -> None:

        source[max(point[1] - size, 0):point[1] + size, point[0]] = color

        source[point[1], max(point[0] - size,0):point[0] + size] = color

        #cv2.circle(source, point,4,color,1)



    def get_scale(self, img, type:int = 0):
        """
        This function is used to extract scales for all slices. We save this data as a .sc file and then use set_scale instead.
        type 0 => horisontal axis
        type 1 => vertical axis
        """
        i = 0
        if type == 0:
            width = int(img.shape[1]/2) + 50
            offset = 45
        else:
            height = int(img.shape[0]/4) + 5
            offset = 45

        start = 0
        ready = 0

        try:
            while i < 500:
                if type == 0:
                    pixel = img[offset, width + i]
                else:
                    pixel = img[height + i, offset]

                if pixel[0] < 245:
                    if start == 0:
                        if type == 0:
                            start = width+i
                        else:
                            start = height + i

                    elif ready > 5:
                        if type == 0:
                            cv2.line(img, (start, offset), (width+i,offset), self.primary_color, 1)
                            return [start, abs(start - (width + i))] #center, pixels per mm
                        else:
                            cv2.line(img, (offset, start), (offset, height+i), self.primary_color, 1)
                            return [start, abs(start - (height + i))] #center, pixels per mm

                elif start != 0:

                    ready += 1
                i += 1
        except:
            pass # out of bounds


    def find_nearest_marker(self, mouse_pos:tuple) -> tuple:

        distance_pairs = []

        for marker in self.markers:
            if marker[3] == self.hover_window:
                if (marker[3] == 0 and self.manager.coronal_index == marker[1]) or (marker[3] == 1 and self.manager.sagittal_index == marker[1]):
                    distance_pairs.append([distance2d(marker[0], mouse_pos), marker])

        try:
            distance_pairs = sorted(distance_pairs, key=lambda x: float(x[0]))
            return distance_pairs[0]
        except:
            return (30, -1)

    def line(self, img, start, stop, fraction, color):

        n = int(np.sqrt((start[0] - stop[0])**2 + (start[1] - stop[1])**2)*.1)

        diff_y = (stop[0] - start[0])/n
        diff_x = (stop[1] - start[1])/n
        i = 0
        while i < n:

            start_ = (round(start[0] + diff_y * i), round(start[1] + diff_x * i))
            stop_ = (round(start[0] + diff_y * (i + 1)), round(start[1] + diff_x * (i + 1)))
            #size_ =abs(fraction - i/n) * 5 + 1
            #size = max(int(round(3/size_**1.2)), 1)
            size=1

            cv2.line(img, start_, stop_, color, size, lineType=cv2.LINE_AA)


            i += 2

    def print_markers(self, i, marker):
        raw="M{} - ap: {}; ml: {}; dv: {}".format(i, round(marker[2][0],2), round(marker[2][1], 2), round(marker[2][2], 2))

        if (i + 1) % 2 == 0:
            angle_front = np.degrees(np.arctan2(-self.markers[i - 1][2][1] + marker[2][1], -self.markers[i-1][2][2] + marker[2][2]))
            angle_sag = np.degrees(np.arctan2(-self.markers[i - 1][2][0]+marker[2][0], -self.markers[i-1][2][2] + marker[2][2]))
            distance = distance3d(marker[2], self.markers[i - 1][2])

            if len(self.paths) > 0:
                if i != self.paths[len(self.paths)-1][0]:
                    self.paths.append([i, self.markers[i - 1], marker, angle_front, angle_sag, distance])
            else:
                self.paths.append([i,self.markers[i - 1], marker, angle_front, angle_sag, distance])


            instruction = "Position the stereotaxic tip over M{} with a coronal angle of: {} deg; and a sagital angle of: {} deg.\nThen, go this deep: |M{}M{}| {} mm;\n****".format(i - 1, np.round(angle_front, 2), np.round(angle_sag, 2),i - 1, i, round(distance, 2))

            return (raw, instruction)
        else:
            return (raw,)

    def update(self) -> tuple:

        coronal_image, sagittal_image = self.manager.get_images()

        self.manager.set_scale()

        #self.clear()
        self.print_instructions()
        print("Markers")
        verbs =[]
        for i, marker in enumerate(self.markers):
            verbs.append(self.print_markers(i, marker))

            coord_float=str_to_float(self.manager.coordinate[1])
            if (i + 1) % 2 == 0:

                if abs(self.markers[i - 1][2][1] - coord_float) < .11 and self.markers[i - 1][2][1] == marker[2][1]:
                    new_marker = self.manager.to_pixel_r(marker[2], 1)
                    old_marker = self.manager.to_pixel_r(self.markers[i - 1][2], 1)

                    cv2.line(sagittal_image, old_marker, new_marker, self.second_color, 1)


                elif self.markers[i - 1][2][1] > coord_float > marker[2][1] or self.markers[i - 1][2][1] < coord_float < marker[2][1]:
                    fraction = (coord_float - self.markers[i - 1][2][1])/(marker[2][1] - self.markers[i - 1][2][1])

                    new_marker = self.manager.to_pixel_r(marker[2], 1)
                    old_marker = self.manager.to_pixel_r(self.markers[i - 1][2], 1)

                    ml_diff = (new_marker[0] - old_marker[0]) * fraction
                    dv_diff = (new_marker[1] - old_marker[1]) * fraction

                    level = np.round(np.array([old_marker[0] + ml_diff, old_marker[1] + dv_diff])).astype(int)

                    self.line(sagittal_image, old_marker, new_marker, fraction, self.second_color)
                    cv2.circle(sagittal_image, tuple(level), 4, (255,255,255), -1)
                    #self.place_cross(sagittal_image, tuple(level), self.primary_color, size=30)
                    cv2.circle(sagittal_image, tuple(level), 5, self.primary_color, 1,lineType=cv2.LINE_AA)

            size = max(.7 - abs(coord_float - marker[2][1]) * .3, .1)
            new_marker = self.manager.to_pixel_r(marker[2], 1)
            sagittal_overlay = sagittal_image.copy()

            self.place_cross(sagittal_overlay, new_marker, self.primary_color)

            cv2.putText(sagittal_overlay, "M" + str(i), tuple([mark + 8 for mark in new_marker]), font,  size, self.primary_color, 1, cv2.LINE_AA)
            alpha = size/.7

            cv2.addWeighted(sagittal_overlay, alpha, sagittal_image, 1 - alpha, 0, sagittal_image)

            coord_float = str_to_float(self.manager.coordinate[0])

            new_marker = self.manager.to_pixel_r(marker[2], 0)
            old_marker = self.manager.to_pixel_r(self.markers[i - 1][2], 0)
            if (i + 1) % 2 == 0:

                if abs(self.markers[i - 1][2][0] - coord_float) < .11 and self.markers[i - 1][2][0] == marker[2][0]:
                    #new_marker = self.manager.to_pixel(marker[2], 0)
                    #old_marker = self.manager.to_pixel_r(self.markers[i - 1][2], 0)

                    cv2.line(coronal_image, old_marker, new_marker, self.second_color, 1)

                elif self.markers[i - 1][2][0] > coord_float > marker[2][0] or self.markers[i - 1][2][0] < coord_float < marker[2][0]:

                    fraction = (coord_float - self.markers[i - 1][2][0])/(marker[2][0] - self.markers[i - 1][2][0])
                    #fraction = (coord_float - marker[2][0])/(-marker[2][0] + self.markers[i - 1][2][0])

                    ml_diff = (new_marker[0] - old_marker[0]) * fraction
                    dv_diff = (new_marker[1] - old_marker[1]) * fraction

                    #cv2.line(coronal_image, old_marker, new_marker, self.second_color, 1)

                    start = np.round(np.array([old_marker[0] + ml_diff, old_marker[1] + dv_diff])).astype(int)
                    self.line(coronal_image, old_marker, new_marker, fraction, self.second_color)
                    cv2.circle(coronal_image, tuple(start), 4, (255,255,255), -1)
                    cv2.circle(coronal_image, tuple(start), 4, self.primary_color, 1,lineType=cv2.LINE_AA)

            size = max(.7 - abs(coord_float - marker[2][0]) * .3, .1)
            #new_marker = self.manager.to_pixel(marker[2], 0)

            coronal_overlay = coronal_image.copy()
            self.place_cross(coronal_overlay, new_marker, self.primary_color)
            cv2.putText(coronal_overlay, "M" + str(i), tuple([mark + 8 for mark in new_marker]), font,  size, self.primary_color, 1, cv2.LINE_AA)

            alpha = size/.7

            cv2.addWeighted(coronal_overlay, alpha, coronal_image, 1 - alpha, 0, coronal_image)

        verbs=list(sum(verbs, ()))
        for verb in verbs:
            print(verb)

        self.full_coronal_image, self.full_sagittal_image = coronal_image, sagittal_image
            #img = cv2.resize(img, None, fx=self.manager.scale_factor, fy=self.manager.scale_factor,interpolation = self.manager.interpolation)
        if self.manager.scale_factor != 1:

            self.coronal_image = cv2.resize(coronal_image, None, fx=self.manager.scale_factor, fy=self.manager.scale_factor,interpolation = self.manager.interpolation)
            self.sagittal_image = cv2.resize(sagittal_image, None, fx=self.manager.scale_factor, fy=self.manager.scale_factor,interpolation = self.manager.interpolation)
        else:
            self.coronal_image, self.sagittal_image = coronal_image, sagittal_image

        return self.coronal_image, self.sagittal_image


    def clear(self):
        # for windows
        if name == 'nt':
            _ = system('cls')

        # for mac and linux(here, os.name is 'posix')
        else:
            _ = system('clear')


    def place_marker(self, point):

        if self.hover_window==0:
            self.markers.append([point, self.manager.coronal_index, self.manager.convert_to_mm(point, 0), self.hover_window])
        else:
            self.markers.append([point, self.manager.sagittal_index, self.manager.convert_to_mm(point, 1), self.hover_window])

        label= f"M{len(self.markers)-1}"
        self.drop_down['menu'].add_command(label=label, command=tk._setit(self.tkt_variable, label))




def main():
    print("Brain coordinator initiated")
    Coordinator(sys.argv[1:])

if __name__ == '__main__':
    main()
