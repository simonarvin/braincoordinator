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
from PIL import Image, ImageTk

font = cv2.FONT_HERSHEY_SIMPLEX

class Coordinator:
    """
    todo: musseplacering skal give et zoomed-billede nederst
    Sagital slides skal spejles så der også er negative værdier
    når man taster ting ind i marker, skal der komme cursor op på canvas
    ---- se på paths, virker ikke helt (kan måske være to_pixels)
    Gennemtænk marker-txt placering. Det kan gøres smartere, måske
        bedre 3d
        tykkelse af line
    """
    def __init__(self, args, ap:float = 0, ml:float = 0, dv:float =0) -> None:

        self.arguments = Arguments(args)
        self.cursor_color = (0,0,0)

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

        self.primary_color = [0, 0, 255]
        self.second_color = [50, 50, 255]
        self.third_color = [150,150,150]

        self.x, self.y = [0,0], [0,0]
        self.hover_window = 0
        self.setup_manual_prompt()

        self.print_instructions()

        self.manager.set_values(ap, ml, dv)
        self.iterate()

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
        A/S - previous/next coronal slice.
        Z/X - previous/next sagittal slice.
        D   - place marker.
        F   - remove marker.

        Click and drag to move markers.
        """

        print(instructions)

    def img_to_tk(self, img):
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        return ImageTk.PhotoImage(Image.fromarray(img))

    def setup_manual_prompt(self):
        self.window = window = Tk()
        window.title("Welcome to TutorialsPoint")
        #window.geometry('300x200')
        #window.configure(background = "white")
        self.coronal_txt = StringVar()
        self.coronal_txt.set("move cursor to canvas")
        Label(window,textvariable = self.coronal_txt, height = 2).grid(row = 0, column = 0, columnspan =5)

        Label(window ,text = "marker").grid(row = 2,column = 0)

        Label(window ,text = "ap").grid(row = 3,column = 0)
        Label(window ,text = "ml").grid(row = 4,column = 0)
        Label(window ,text = "dv").grid(row = 5,column = 0)
        self.tkt_msg = StringVar()

        Label(window ,textvariable = self.tkt_msg).grid(row = 7,column = 1)

        def ignore_letters(e):
            key = e.char
            if key in ["a", "s", "z", "x", "d", "f"]:

                #self.window.focus_set()
                self.tkt_key(key, False)
                return "break"


        def coord_callback(*args):
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

            coronal_image, sagittal_image = self.update()

            if ap != -99:
                sagittal_image[:, pixels_point_sagittal[0]] = self.third_color

            if dv != -99:
                sagittal_image[pixels_point_sagittal[1], :] = self.third_color
                coronal_image[pixels_point_coronal[1], :] = self.third_color

            if ml != -99:
                coronal_image[:,pixels_point_coronal[0]] = self.third_color



            self.update_sagittal_tkt(sagittal_image)
            self.update_coronal_tkt(coronal_image)


        self.tkt_ap = Entry(window)
        self.tkt_ap.grid(row = 3,column = 1)
        self.tkt_ap.bind('<Return>', coord_callback)
        self.tkt_ap.bind('<Key>', ignore_letters)


        self.tkt_ml = Entry(window)
        self.tkt_ml.grid(row = 4,column = 1)
        self.tkt_ml.bind('<Return>', coord_callback)
        self.tkt_ml.bind('<Key>', ignore_letters)

        self.tkt_dv = Entry(window)
        self.tkt_dv.grid(row = 5,column = 1)
        self.tkt_dv.bind('<Return>', coord_callback)
        self.tkt_dv.bind('<Key>', ignore_letters)


        def mark():

            #print(self.tkt_ap.get(), self.tkt_ml.get(), self.tkt_dv.get())
            if self.tkt_selection == 0:
                print("NEW")
            try:
                point = (float(eval(self.tkt_ap.get())), float(eval(self.tkt_ml.get())), float(eval(self.tkt_dv.get())))
            except Exception as e:
                print("invalid coordinates")
                print(e)
            nearest_coronal, nearest_sagittal = self.manager.find_nearest_slices(point[:2])


            pixels_point = self.manager.to_pixel(point, 0) #self.manager.convert_to_pixels(point)

            self.markers.append([pixels_point, nearest_coronal, point, 0])
            label=f"M{len(self.markers)-1}"
            self.drop_down['menu'].add_command(label=label, command=tk._setit(self.tkt_variable, label))

            coronal_image, sagittal_image = self.update()

            self.update_coronal_tkt(coronal_image)
            self.update_sagittal_tkt(sagittal_image)


        ttk.Button(window ,text="save",command=mark).grid(row=6,column=0)



    def manual_marker(self):
        OPTIONS = ["new"] + [f"M{i}" for i,_ in enumerate(self.markers)]
        self.tkt_variable = variable = StringVar(self.window)
        self.tkt_selection = 0

        def go_new():
            variable.set(OPTIONS[0])


        gonew_btn = ttk.Button(self.window ,text="<< transfer to new",command=go_new)
        gonew_btn.grid(row=2, column=2)

        def callback(*args):
            OPTIONS = ["new"] + [f"M{i}" for i,_ in enumerate(self.markers)]
            self.tkt_selection = selection = OPTIONS.index(variable.get())
            if selection == 0:# new marker
                self.tkt_msg.set("input new marker coords..")
                gonew_btn["state"] = DISABLED

                #self.tkt_ap.delete(0,END)
                #self.tkt_ml.delete(0,END)
                #self.tkt_dv.delete(0,END)
            else:
                self.tkt_msg.set(f"M{selection-1} loaded")
                gonew_btn["state"] = "normal"
                marker_coords = self.markers[selection - 1][2]
                self.tkt_ap.delete(0,END)
                self.tkt_ml.delete(0,END)
                self.tkt_dv.delete(0,END)
                self.tkt_ap.insert(0, marker_coords[0])
                self.tkt_ml.insert(0, marker_coords[1])
                self.tkt_dv.insert(0, marker_coords[2])

                def remove_mark():
                    # if pair, remove both. Open prompt first (are you sure)
                    marker_index = self.tkt_selection - 1
                    if len(self.markers)%2 == 0:
                        #if self.tkt_selection == len(self.markers):
                        self.paths.pop(marker_index//2 - 1)
                        self.markers.pop(marker_index - 1)

                    self.markers.pop(marker_index)

                    self.drop_down['menu'].delete(self.tkt_selection )
                    variable.set(OPTIONS[self.tkt_selection - 1])


                    coronal_image, sagittal_image = self.update()

                    self.update_coronal_tkt(coronal_image)
                    self.update_sagittal_tkt(sagittal_image)

                ttk.Button(self.window ,text="remove",command=remove_mark).grid(row=6,column=1)

        variable.trace("w", callback)
        variable.set(OPTIONS[0]) # default value

        self.drop_down = OptionMenu(self.window, variable, *list(OPTIONS))
        self.drop_down.grid(row = 2,column = 1)


        gonew_btn["state"] = DISABLED

        def close_():
            self.window.destroy()

        ttk.Button(self.window ,text="close",command=close_).grid(row=6, column=2)

        coronal_image, sagittal_image = self.update()
        coronal_image=self.img_to_tk(coronal_image)
        self.tkt_coronal = Label(self.window, image = coronal_image,bd=0)
        self.tkt_coronal.image = coronal_image
        self.tkt_coronal.grid(row=1, column=0, columnspan=5)

        self.tkt_coronal.bind('<Motion>', self.frontal_mouse_move)
        self.window.bind('<Key>',self.tkt_key)

        sagittal_image=self.img_to_tk(sagittal_image)
        self.tkt_sagittal = Label(self.window, image = sagittal_image,bd=1)
        self.tkt_sagittal.image = sagittal_image
        self.tkt_sagittal.grid(row=1, column=5, columnspan = 5)
        self.tkt_sagittal.bind('<Motion>', self.sagittal_mouse_move)

        self.window.mainloop()
        self.setup_manual_prompt()

    def tkt_key(self, e, type = True):
        if type:
            key =e.char
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

        coronal_image, sagittal_image = self.update()

        self.update_coronal_tkt(coronal_image)
        self.update_sagittal_tkt(sagittal_image)


    def frontal_mouse_move(self, e) -> None:
        x,y = e.x,e.y

        self.hover_window = 0

        if self.selected_marker != None:
            if self.selected_marker[3] == self.hover_window:
                self.manager.update_marker(self.selected_marker, (x, y), self.hover_window)
                coronal_image, sagittal_image = self.update()
                cv2.imshow("Sagittal", sagittal_image)

        coronal_image= self.coronal_image.copy()
        try:
            coronal_image[:,x] = self.cursor_color
            coronal_image[y,:] = self.cursor_color
        except:
            return

        coords = self.manager.convert_to_mm((x,y), 0)
        #cv2.putText(coronal_image, f"ap: {coords[0]}; ml: {coords[1]}; dv: {coords[2]}", self.manager.sagital_dvs_txt, font,  .5, self.primary_color, 1, cv2.LINE_AA)
        self.coronal_txt.set(f"ap: {coords[0]}; ml: {coords[1]}; dv: {coords[2]}")

        self.x[0], self.y[0] = x, y
        self.update_coronal_tkt(coronal_image)


    def update_coronal_tkt(self, rawimg):
        img = self.img_to_tk(rawimg)
        self.tkt_coronal.configure(image=img)
        self.tkt_coronal.image = img

    def sagittal_mouse_move(self, e) -> None:
        x, y = e.x, e.y

        self.hover_window = 1

        if self.selected_marker != None:
            if self.selected_marker[3] == self.hover_window:
                self.manager.update_marker(self.selected_marker, (x, y), self.hover_window)
                coronal_image, sagittal_image = self.update()
                cv2.imshow("Coronal", coronal_image)

        sagittal_image = self.sagittal_image.copy()
        try:
            sagittal_image[:,x] = self.cursor_color
            sagittal_image[y,:] = self.cursor_color
        except:
            return

        coords = self.manager.convert_to_mm((x,y), 1)
        cv2.putText(sagittal_image, f"ap: {coords[0]}; ml: {coords[1]}; dv: {coords[2]}", self.manager.sagital_dvs_txt, font,  .5, self.primary_color, 1, cv2.LINE_AA)

        #cv2.imshow("Sagittal", sagittal_image)
        self.update_sagittal_tkt(sagittal_image)

        self.x[1], self.y[1] = x, y

    def update_sagittal_tkt(self, rawimg):
        img = self.img_to_tk(rawimg)
        self.tkt_sagittal.configure(image=img)
        self.tkt_sagittal.image = img

    def frontal_mouse(self, event, x:float, y:float, flags, param) -> None:

        if event == cv2.EVENT_MOUSEMOVE:
            self.hover_window = 0

            if self.selected_marker != None:
                if self.selected_marker[3] == self.hover_window:
                    self.manager.update_marker(self.selected_marker, (x, y), self.hover_window)
                    coronal_image, sagittal_image = self.update()
                    cv2.imshow("Sagittal", sagittal_image)

            coronal_image= self.coronal_image.copy()
            coronal_image[:,x] = self.cursor_color
            coronal_image[y,:] = self.cursor_color

            coords = self.manager.convert_to_mm((x,y), 0)
            cv2.putText(coronal_image, f"ap: {coords[0]}; ml: {coords[1]}; dv: {coords[2]}", self.manager.sagital_dvs_txt, font,  .5, self.primary_color, 1, cv2.LINE_AA)

            cv2.imshow("Coronal", coronal_image)


        if event == cv2.EVENT_LBUTTONDOWN:
            if self.selected_marker == None:
                distance, marker = self.find_nearest_marker((x, y))
                if distance < 20:
                    self.selected_marker = marker

        elif event == cv2.EVENT_LBUTTONUP:

            self.selected_marker = None

        self.x[0], self.y[0] = x, y

    def sagittal_mouse(self, event, x:float, y:float, flags, param) -> None:

        if event == cv2.EVENT_MOUSEMOVE:
            self.hover_window = 1

            if self.selected_marker != None:
                if self.selected_marker[3] == self.hover_window:
                    self.manager.update_marker(self.selected_marker, (x, y), self.hover_window)
                    coronal_image, sagittal_image = self.update()
                    cv2.imshow("Coronal", coronal_image)

            sagittal_image = self.sagittal_image.copy()
            sagittal_image[:,x] = self.cursor_color
            sagittal_image[y,:] = self.cursor_color

            coords = self.manager.convert_to_mm((x,y), 1)
            cv2.putText(sagittal_image, f"ap: {coords[0]}; ml: {coords[1]}; dv: {coords[2]}", self.manager.sagital_dvs_txt, font,  .5, self.primary_color, 1, cv2.LINE_AA)

            cv2.imshow("Sagittal", sagittal_image)


        if event == cv2.EVENT_LBUTTONDOWN:
            if self.selected_marker == None:
                distance, marker = self.find_nearest_marker((x, y))
                if distance < 20:
                    self.selected_marker = marker

        elif event == cv2.EVENT_LBUTTONUP:

            self.selected_marker = None

        self.x[1], self.y[1] = x, y

    def place_cross(self, source: np.ndarray, point: tuple, color: tuple) -> None:

        source[max(point[1] - 7, 0):point[1] + 8, point[0]] = color

        source[point[1], max(point[0] - 7,0):point[0] + 8] = color

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
                            cv2.line(img, (start,offset), (width+i,offset), self.primary_color, 1)
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


    def update(self) -> tuple:

        coronal_image, sagittal_image = self.manager.get_images()

        #self.scale = self.get_scale(img)  #tuple center, pixels per mm
        #self.scale[0] = self.scale[0] - self.scale[1] * 2
        #img[self.scale[0],30] = self.primary_color
        #print(self.scale)

        self.manager.set_scale()

        #self.clear()
        self.print_instructions()
        print("Markers")

        for i, marker in enumerate(self.markers):

            print("     M{} - ap: {}; ml: {}; dv: {}".format(i,marker[2][0],marker[2][1],marker[2][2]))

            if (i + 1) % 2 == 0:
                angle_front = np.degrees(np.arctan2(-self.markers[i - 1][2][1] + marker[2][1], -self.markers[i-1][2][2] + marker[2][2]))
                angle_sag = np.degrees(np.arctan2(-self.markers[i - 1][2][0]+marker[2][0], -self.markers[i-1][2][2] + marker[2][2]))
                distance = distance3d(marker[2], self.markers[i - 1][2])

                if len(self.paths) > 0:
                    if i != self.paths[len(self.paths)-1][0]:
                        self.paths.append([i, self.markers[i - 1], marker, angle_front, angle_sag, distance])
                else:
                    self.paths.append([i,self.markers[i - 1], marker, angle_front, angle_sag, distance])


                print("     |M{}M{}| {} mm; ang_cor: {} deg; ang_sag: {} deg".format(i - 1, i, round(distance, 2), np.round(angle_front, 2), np.round(angle_sag, 2)))


            if marker[3] == 0: #frontal

                if marker[1] == self.manager.coronal_index:

                    self.place_cross(coronal_image, marker[0],self.primary_color)

                    #if (i + 1) % 2 == 0:
                    #    cv2.line(coronal_image, self.markers[i - 1][0], marker[0], self.primary_color, 1)

                    cv2.putText(coronal_image, "M"+str(i), tuple([mark + 5 for mark in marker[0]]), font,  .5, self.primary_color, 1, cv2.LINE_AA)
                else:
                    size = max(.5 - abs(self.manager.coronal_index - marker[1]) * .01, .2)
                    print(size, (self.manager.coronal_index, marker[1]))
                    self.place_cross(coronal_image, marker[0],self.primary_color)

                    cv2.putText(coronal_image, "M"+str(i), tuple([mark + 5 for mark in marker[0]]), font,  size, self.primary_color, 1, cv2.LINE_AA)

                if (i + 1) % 2 == 0:
                    cv2.line(coronal_image, self.markers[i - 1][0], marker[0], self.primary_color, 1)

                coord_float=str_to_float(self.manager.coordinate[1])
                if (i + 1) % 2 == 0:

                    if self.markers[i - 1][2][1] > coord_float > marker[2][1] or self.markers[i - 1][2][1] < coord_float < marker[2][1]:
                        fraction = (coord_float - self.markers[i - 1][2][1])/(marker[2][1] - self.markers[i - 1][2][1])

                        new_marker = self.manager.to_pixel(marker[2], 1)
                        old_marker = self.manager.to_pixel(self.markers[i - 1][2], 1)

                        ml_diff = (new_marker[0] - old_marker[0]) * fraction
                        dv_diff = (new_marker[1] - old_marker[1]) * fraction

                        cv2.line(sagittal_image, old_marker, new_marker, self.second_color, 1)
                        cv2.circle(sagittal_image, old_marker, 2, self.second_color, -1)
                        cv2.circle(sagittal_image, new_marker, 2, self.second_color, -1)

                        start = np.array([old_marker[0] + ml_diff, old_marker[1] + dv_diff], dtype = int)

                        cv2.circle(sagittal_image, tuple(start), 4, self.primary_color, -1)

                size = max(.7 - abs(coord_float - marker[2][1]) * .2, .2)
                new_marker = self.manager.to_pixel(marker[2], 1)
                self.place_cross(sagittal_image, new_marker, self.primary_color)
                cv2.putText(sagittal_image, "M" + str(i), tuple([mark + 5 for mark in new_marker]), font,  size, self.primary_color, 1, cv2.LINE_AA)

            else:

                if marker[1] == self.manager.sagittal_index:
                    self.place_cross(sagittal_image, marker[0], self.primary_color)

                    if (i + 1) % 2 == 0:
                        cv2.line(sagittal_image, self.markers[i - 1][0], marker[0], self.primary_color, 1)

                    cv2.putText(sagittal_image, "M" + str(i), tuple([mark + 5 for mark in marker[0]]), font, .5, self.primary_color, 1, cv2.LINE_AA)

                coord_float = str_to_float(self.manager.coordinate[0])
                if (i + 1) % 2 == 0:

                    if self.markers[i - 1][2][0] > coord_float > marker[2][0] or self.markers[i - 1][2][0] < coord_float < marker[2][0]:

                        fraction = (coord_float - self.markers[i - 1][2][0])/(marker[2][0] - self.markers[i - 1][2][0])

                        new_marker = self.manager.to_pixel(marker[2], 0)
                        old_marker = self.manager.to_pixel(self.markers[i - 1][2], 0)
                        ml_diff = (new_marker[0] - old_marker[0]) * fraction
                        dv_diff = (new_marker[1] - old_marker[1]) * fraction

                        cv2.line(coronal_image, old_marker, new_marker, self.second_color, 1)
                        cv2.circle(coronal_image, old_marker, 2, self.second_color, -1)
                        cv2.circle(coronal_image, new_marker, 2, self.second_color, -1)

                        start = np.array([old_marker[0] + ml_diff, old_marker[1] + dv_diff], dtype = int)

                        cv2.circle(coronal_image, tuple(start), 4, self.primary_color, -1)

                size = max(.7 - abs(coord_float - marker[2][0]) * .2, .3)
                new_marker = self.manager.to_pixel(marker[2], 0)

                self.place_cross(coronal_image, new_marker, self.primary_color)
                cv2.putText(coronal_image, "M" + str(i), tuple([mark + 5 for mark in new_marker]), font,  size, self.primary_color, 1, cv2.LINE_AA)

        self.coronal_image, self.sagittal_image = coronal_image, sagittal_image
        return coronal_image, sagittal_image


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



    def keyHandler(self, key):
        if key == ord("x"):
            self.manager.next("sagittal")

        elif key == ord("z"):
            self.manager.previous("sagittal")

        elif key == ord("a"):
            self.manager.next("coronal")

        elif key == ord("s"):
            self.manager.previous("coronal")

        elif key == ord("p"):
            self.manual_marker()

        elif key==ord("d"):
            try:
                point = (self.x[self.hover_window], self.y[self.hover_window])
                self.place_marker(point)

            except AttributeError:
                print("Click image once to gain focus.")


        elif key == ord("f"):
            try:
                if len(self.markers)%2 == 0:
                    self.paths.pop()

                self.markers.pop()
            except:
                pass
        # elif key == ord("p"):
        #     self.save_data()
        elif key == ord("q"):
            return True

        return False

    def iterate(self):

        self.manager.coronal_index, self.manager.sagittal_index = self.manager.find_nearest_slices()

        coronal_image, sagittal_image = self.update()

        cv2.imshow("Coronal", coronal_image)
        cv2.imshow("Sagittal", sagittal_image)
        cv2.setMouseCallback("Coronal", self.frontal_mouse)
        cv2.setMouseCallback("Sagittal", self.sagittal_mouse)

        while True:

            coronal_image, sagittal_image = self.update()

            cv2.imshow("Coronal", coronal_image)
            cv2.imshow("Sagittal", sagittal_image)

            key = cv2.waitKey(0)

            if self.keyHandler(key):
                break

def main():
    print("Brain coordinator initiated")
    Coordinator(sys.argv[1:])

if __name__ == '__main__':
    main()
