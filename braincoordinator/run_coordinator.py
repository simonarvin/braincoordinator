import cv2
import os
from os import listdir
from os.path import isfile, join
import numpy as np
from os import system, name
from openpyxl import load_workbook
from shutil import copyfile

from datetime import datetime

#TODO: overvej at tilføje så man kan klikke og rykke rundt på markers.
#Sagen er, at det kræver, at du laver "3d" til en generel mekanisme, så du særskiller ikke behandling af markers.
#så en streg kan være 3d i begge views

dir_path = os.path.dirname(os.path.realpath(__file__))
font = cv2.FONT_HERSHEY_SIMPLEX

class Coordinator:
    def __init__(self, animal:str, reference:str, preload:int, ap:float = 0, ml:float = 0, dv:float =0) -> None:

        self.reference = int(str(reference[0]).lower() == "l") #bregma = 0; lambda = 1
        self.counterreference = int(self.reference == 0)
        self.animal = animal
        self.animal_path = "{}/{}/".format(dir_path, animal)
        self.slices = [file_name for file_name in listdir(self.animal_path) if isfile(join(self.animal_path, file_name))]
        self.coronals = []
        self.sagittals = []
        self.coronal_index = 0
        self.selected_marker=None

        self.markers = []
        self.paths = []

        self.resize_factor = 1
        self.primary_color = [0, 0, 255]
        self.second_color = [50, 50, 255]

        self.parse_slices()

        self.preload = int(preload)
        if self.preload == 1:
            self.load_images()

        self.retrieve_coronal_scale()
        self.retrieve_sagittal_scale()

        self.x, self.y = [0,0], [0,0]
        self.hover_window = 0

        cv2.namedWindow('Sagittal', cv2.WINDOW_NORMAL)
        self.set_values(ap, ml, dv)

    def load_images(self):
        self.coronal_images = np.zeros(len(self.coronals), dtype=object)
        self.sagittal_images = np.zeros(len(self.sagittals), dtype=object)

        print("Preloading images..")

        for index, _ in enumerate(self.coronals):
            coronal_tuple = self.coronals[index]

            if coronal_tuple[1] != "":
                coronal_tuple_str = "b" + coronal_tuple[0] + "a" + coronal_tuple[1]
            else:
                coronal_tuple_str = "b" + coronal_tuple[0]

            coronal_image = cv2.imread(self.animal_path+"/{}.jpg".format(coronal_str), cv2.IMREAD_UNCHANGED)

            if self.resize_factor != 1:
                size = coronal_image.shape
                coronal_image = cv2.resize(coronal_image, (int(size[1]*self.resize_factor),int(size[0]*self.resize_factor)),interpolation=cv2.INTER_AREA)
            self.coronal_images[index] = coronal_image

            print("Loading coronal {}/{}".format(index, len(self.coronals) - 1))

        for index, _ in enumerate(self.sagittals):
            sagittal_slice = self.sagittals[index]
            sagittal_image = cv2.imread(self.animal_path+"/l{}.jpg".format(agittal_slice))

            if self.resize_factor != 1:
                size = sagittal_image.shape
                sagittal_image = cv2.resize(sagittal_image, (int(size[1] * self.resize_factor), int(size[0] * self.resize_factor)), interpolation=cv2.INTER_AREA)

            print("Loading sagittal {}/{}".format(index, len(self.sagittals) - 1))
            self.sagittal_images[index] = sagittal_image

        print("Preloading succeeded")

    def set_values(self, ap:float, ml:float, dv:float) -> None:

        vals = self.to_decimal(ap, ml, dv)
        self.ap, self.ml, self.dv = vals
        self.coordinate = vals[0], vals[1]

        self.iterate()

    def to_decimal(self, *args):
        if len(args) != 1:
            return [format(arg, '.2f') for arg in args]
        else:
            return format(args[0], '.2f')

    def find_nearest_value(self, array:np.ndarray, value:float) -> int:
        index = (np.abs(array - value)).argmin()
        return index

    def find_nearest_slices(self) -> tuple:

        split_float = np.delete(np.array(self.coronals), int(self.reference==0), 1)

        split_float = np.array([self.str_to_float(coronal_str[0]) for coronal_str in split_float])
        nearest_coronal = self.find_nearest_value(split_float, float(self.coordinate[0]))

        split_float = np.array([self.str_to_float(sagittal_str) for sagittal_str in self.sagittals])
        nearest_sagittal = self.find_nearest_value(split_float, float(self.coordinate[1]))

        return nearest_coronal, nearest_sagittal


    def parse_slices(self) -> None:
        for slice in self.slices:

            if slice[len(slice)-4:] != ".jpg":
                continue

            slice = slice[:-4] #remove .jpg

            if slice[0] == "l": #lateral/ml
                slice = slice[1:]
                self.sagittals.append(slice)
            else: #ap
                if "a" in slice:
                    slice = slice[1:]
                    split = slice.split("a") #[0] = bregma; [1] = lambda
                    self.coronals.append(split)
                else:
                    slice = slice[1:]
                    self.coronals.append([slice, ""])

        self.sagittals = sorted(self.sagittals, key=lambda x: float(x))
        self.coronals = sorted(self.coronals, key=lambda x: float(x[0]))

    def find_nearest_marker(self, mouse_pos:tuple) -> tuple:

        distance_pairs = []

        for marker in self.markers:
            if marker[3] == self.hover_window:
                if (marker[3] == 0 and self.coronal_index == marker[1]) or (marker[3] == 1 and self.sagittal_index == marker[1]):
                    distance_pairs.append([self.distance2d(marker[0], mouse_pos), marker])

        try:
            distance_pairs = sorted(distance_pairs, key=lambda x: float(x[0]))
            return distance_pairs[0]
        except:
            return (30, -1)

    def update_marker(self, marker, point,):
        marker[0] = point
        marker[2] = self.convert_to_mm(point, self.hover_window)

    def frontal_mouse(self, event, x:float, y:float, flags, param) -> None:

        if event == cv2.EVENT_MOUSEMOVE:
            self.hover_window = 0

            if self.selected_marker != None:
                if self.selected_marker[3] == self.hover_window:
                    self.update_marker(self.selected_marker, (x, y))
                    coronal_image, sagittal_image = self.update()
                    cv2.imshow("Coronal", coronal_image)
                    cv2.imshow("Sagittal", sagittal_image)


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
                    self.update_marker(self.selected_marker, (x, y))
                    coronal_image, sagittal_image = self.update()
                    cv2.imshow("Coronal", coronal_image)
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
        source[point[1] - 7:point[1] + 8, point[0]] = color
        source[point[1], point[0] - 7:point[0] + 8] = color
        #cv2.circle(source, point,4,color,1)

    def retrieve_coronal_scale(self):
        #ml
        filepath = self.animal_path + '/coronal_ml.sc'
        self.coronal_mls = []
        with open(filepath) as fp:
           line = fp.readline()
           while line:
               split = line.split(",")
               split = np.array(split, dtype = int) * self.resize_factor
               self.coronal_mls.append(split)
               line = fp.readline()

        filepath = self.animal_path + '/coronal_dv.sc'
        self.coronal_dvs = []

        with open(filepath) as fp:
           line = fp.readline()
           while line:
               split = line.split(",")
               split = np.array(split, dtype = int) * self.resize_factor
               self.coronal_dvs.append(split)
               line = fp.readline()

    def retrieve_sagittal_scale(self):

        filepath = self.animal_path+'/sagittal_ap.sc'
        self.sagittal_aps = []

        with open(filepath) as fp:
           line = fp.readline()
           while line:
               split = line.split(",")
               split = np.array(split, dtype = int) * self.resize_factor
               self.sagittal_aps.append(split)
               line = fp.readline()

        filepath = self.animal_path + '/sagittal_dv.sc'
        self.sagittal_dvs = []

        with open(filepath) as fp:
           line = fp.readline()
           while line:
               split = line.split(",")
               split = np.array(split, dtype = int) * self.resize_factor
               self.sagittal_dvs.append(split)
               line = fp.readline()

    #    self.sagittal_dvs=np.array(self.sagittal_dvs)
    #    ll=np.concatenate((np.flip(self.sagittal_dvs[1:],axis=0),self.sagittal_dvs))
    #    for l in ll:
    #        print("{},{}".format(l[0],l[1]))


    def set_scale(self) -> None:

        self.coronal_ml = self.coronal_mls[self.coronal_index]
        self.coronal_dv = self.coronal_dvs[self.coronal_index]

        self.sagittal_ap = self.sagittal_aps[self.sagittal_index]
        self.sagittal_dv = self.sagittal_dvs[self.sagittal_index]


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

    def convert_to_mm(self, marker, type:int) -> np.ndarray:

        if type == 0: #ap
            raw_array = [-self.str_to_float(self.coronals[self.coronal_index][0]), (marker[0] - self.coronal_ml[0])/self.coronal_ml[1], (marker[1] - self.coronal_dv[0])/self.coronal_dv[1]]
        else: #ml
            raw_array = [-(marker[0] - self.sagittal_ap[0])/self.sagittal_ap[1], self.str_to_float(self.sagittals[self.sagittal_index]), (marker[1] - self.sagittal_dv[0])/self.sagittal_dv[1]]

        return np.round(np.array(raw_array), 2)


    def distance3d(self, p1, p2) -> float:
        return np.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2 + (p1[2]-p2[2])**2)

    def distance2d(self, p1, p2) -> float:
        return np.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)

    def str_to_float(self, str:str) -> float:
        if str[0] == "-":
            return float(str[:2] + '.' + str[2:])
        else:
            return float(str[:1] + '.' + str[1:])

    def update(self) -> tuple:

        coronal_tuple = self.coronals[self.coronal_index]
        ml = self.sagittals[self.sagittal_index]
        if self.preload == 1:
            coronal_image = self.coronal_images[self.coronal_index].copy()
            sagittal_image = self.sagittal_images[self.sagittal_index].copy()

        else:

            if coronal_tuple[1] != "":
                coronal_str = "b" + coronal_tuple[0] + "a" + coronal_tuple[1]
            else:
                coronal_str = "b" + coronal_tuple[0]

            coronal_image = cv2.imread(self.animal_path+"/{}.jpg".format(coronal_str), cv2.IMREAD_UNCHANGED)
            if self.resize_factor != 1:
                size = coronal_image.shape
                coronal_image = cv2.resize(coronal_image, (int(size[1] * self.resize_factor), int(size[0] * self.resize_factor)), interpolation = cv2.INTER_AREA)

            sagittal_image = cv2.imread(self.animal_path+"/l{}.jpg".format(ml))
            if self.resize_factor != 1:
                size = sagittal_image.shape
                sagittal_image = cv2.resize(sagittal_image, (int(size[1] * self.resize_factor), int(size[0] * self.resize_factor)),interpolation = cv2.INTER_AREA)

        self.coordinate = coronal_tuple[self.reference], ml

        #print(self.animal_path+"/l{}.jpg".format(ml))

        #self.scale=self.get_scale(img)  #center, pixels per mm
        #cv2.imshow("JJ",sagittal_image)
        #self.scale[0] = self.scale[0] - self.scale[1] * 2
        #img[self.scale[0],30] = self.primary_color
        #print(self.scale)

        self.set_scale()

        #self.clear()
        #print("Markers")

        for i, marker in enumerate(self.markers):

            print("     M{}\nap: {}\nml: {}\ndv: {}\n----".format(i,marker[2][0],marker[2][1],marker[2][2]))

            if (i + 1) % 2 == 0:
                angle_front = np.degrees(np.arctan2(-self.markers[i - 1][2][1] + marker[2][1], -self.markers[i-1][2][2] + marker[2][2]))
                angle_sag = np.degrees(np.arctan2(-self.markers[i - 1][2][0]+marker[2][0], -self.markers[i-1][2][2] + marker[2][2]))
                distance = self.distance3d(marker[2], self.markers[i - 1][2])

                if len(self.paths) > 0:
                    if i != self.paths[len(self.paths)-1][0]:
                        self.paths.append([i, self.markers[i - 1], marker, angle_front, angle_sag, distance])
                else:
                    self.paths.append([i,self.markers[i - 1], marker, angle_front, angle_sag, distance])


                print("M{}-M{} angle-front: {} deg\n----".format(i - 1, i, np.round(angle_front), 2))
                print("M{}-M{} angle-sag: {} deg\n----".format(i - 1, i, np.round(angle_sag), 2))
                print("Distance: {} mm\n-----".format(round(distance, 2)))

            if marker[3] == 0: #frontal
                if marker[1] == self.coronal_index:

                    self.place_cross(coronal_image, marker[0],self.primary_color)

                    if (i + 1) % 2 == 0:
                        cv2.line(coronal_image, self.markers[i - 1][0], marker[0], self.primary_color, 1)

                    cv2.putText(coronal_image, "M"+str(i), tuple([mark + 5 for mark in marker[0]]), font,  .5, self.primary_color, 1, cv2.LINE_AA)

                coord_float=self.str_to_float(self.coordinate[1])
                if (i + 1) % 2 == 0:

                    if self.markers[i - 1][2][1] > coord_float > marker[2][1] or self.markers[i - 1][2][1] < coord_float < marker[2][1]:
                        fraction = (coord_float - self.markers[i - 1][2][1])/(marker[2][1] - self.markers[i - 1][2][1])

                        new_marker = self.to_pixel(marker[2], 1)
                        old_marker = self.to_pixel(self.markers[i - 1][2], 1)

                        ml_diff = (new_marker[0] - old_marker[0]) * fraction
                        dv_diff = (new_marker[1] - old_marker[1]) * fraction

                        cv2.line(sagittal_image, old_marker, new_marker, self.second_color, 1)
                        cv2.circle(sagittal_image, old_marker, 2, self.second_color, -1)
                        cv2.circle(sagittal_image, new_marker, 2, self.second_color, -1)

                        start = np.array([old_marker[0] + ml_diff, old_marker[1] + dv_diff], dtype = int)

                        cv2.circle(sagittal_image, tuple(start), 4, self.primary_color, -1)

                size = max(.7 - abs(coord_float - marker[2][1]) * .2, .3)
                new_marker = self.to_pixel(marker[2], 1)
                self.place_cross(sagittal_image, new_marker, self.primary_color)
                cv2.putText(sagittal_image, "M" + str(i), tuple([mark + 5 for mark in new_marker]), font,  size, self.primary_color, 1, cv2.LINE_AA)

            else:

                if marker[1] == self.sagittal_index:
                    self.place_cross(sagittal_image, marker[0], self.primary_color)

                    if (i + 1) % 2 == 0:
                        cv2.line(sagittal_image, self.markers[i - 1][0], marker[0], self.primary_color, 1)

                    cv2.putText(sagittal_image, "M" + str(i), tuple([mark + 5 for mark in marker[0]]), font, .5, self.primary_color, 1, cv2.LINE_AA)

                coord_float = self.str_to_float(self.coordinate[0])
                if (i + 1) % 2 == 0:

                    if self.markers[i - 1][2][0] > coord_float > marker[2][0] or self.markers[i - 1][2][0] < coord_float < marker[2][0]:

                        fraction = (coord_float - self.markers[i - 1][2][0])/(marker[2][0] - self.markers[i - 1][2][0])

                        new_marker = self.to_pixel(marker[2], 0)
                        old_marker = self.to_pixel(self.markers[i - 1][2], 0)
                        ml_diff = (new_marker[0] - old_marker[0]) * fraction
                        dv_diff = (new_marker[1] - old_marker[1]) * fraction

                        cv2.line(coronal_image, old_marker, new_marker, self.second_color, 1)
                        cv2.circle(coronal_image, old_marker, 2, self.second_color, -1)
                        cv2.circle(coronal_image, new_marker, 2, self.second_color, -1)

                        start = np.array([old_marker[0] + ml_diff, old_marker[1] + dv_diff], dtype = int)

                        cv2.circle(coronal_image, tuple(start), 4, self.primary_color, -1)

                size = max(.7 - abs(coord_float - marker[2][0]) * .2, .3)
                new_marker = self.to_pixel(marker[2], 0)
                self.place_cross(coronal_image, new_marker, self.primary_color)
                cv2.putText(coronal_image, "M" + str(i), tuple([mark + 5 for mark in new_marker]), font,  size, self.primary_color, 1, cv2.LINE_AA)

        return coronal_image, sagittal_image

    def to_pixel(self, marker, type):

        if type ==0:
            #sagittal mm -> frontal pixels
            return int(marker[1] * self.coronal_ml[1] + self.coronal_ml[0]), int((marker[2]) * self.coronal_dv[1] + self.coronal_dv[0])
        else:
            return int(marker[0] * self.sagittal_ap[1] + self.sagittal_ap[0]), int((marker[2]) * self.sagittal_dv[1] + self.sagittal_dv[0])


    def clear(self):

        # for windows
        if name == 'nt':
            _ = system('cls')

        # for mac and linux(here, os.name is 'posix')
        else:
            _ = system('clear')

    def copy_paste_xcl(self, startCol, startRow, endCol, endRow, sheet, data_out):

        rangeSelected = []
        #Loops through selected Rows
        for i in range(startRow, endRow + 1,1):
        #Appends the row to a RowSelected list
            rowSelected = []
            for j in range(startCol,endCol+1,1):
                rowSelected.append(sheet.cell(row = i, column = j).value)
            #Adds the RowSelected List and nests inside the rangeSelected
            rangeSelected.append(rowSelected)

        q=0
        for path in data_out:

            #n+=1

            countRow = 0

            #todo: add one marker also

            rangeSelected[5][1]=path[3] #front ang
            rangeSelected[6][1]=path[4] #sag ang
            rangeSelected[7][1]=path[5] #distance

            rangeSelected[13][1]="=B{}-180/PI()*MOD(G3,PI())".format(12+17*q)
            rangeSelected[14][1]="=B{}-180/PI()*MOD(G4,PI())".format(13+17*q)
            rangeSelected[15][1]="=((B{}-B{})^2+(C{}-C{})^2+(D{}-D{})^2)^(1/2)".format(18+17*q,19+17*q,18+17 *q,19+17*q,18+17*q,19+17*q)

            #Marker 1

            rangeSelected[3][0]="m{}".format(path[0]-1)
            rangeSelected[3][1]="=B3 + {}".format(path[1][2][0])#ap
            rangeSelected[3][2]="=C3 + {}".format(path[1][2][1])#ml
            rangeSelected[3][3]="=D3 + {}".format(path[1][2][2])#dv

            #Marker 2

            rangeSelected[4][0]="m{}".format(path[0])
            rangeSelected[4][1]="=B3 + {}".format(path[2][2][0])#ap
            rangeSelected[4][2]="=C3 + {}".format(path[2][2][1])#ml
            rangeSelected[4][3]="=D3 + {}".format(path[2][2][2])#dv

            #AP
            rangeSelected[11][1]="=B3 + G7 * (B{} - B3) - H7 * (C{}-C3)".format(10 + 17*q, 10+17*q)
            rangeSelected[12][1]="=B3 + G7 * (B{} - B3) - H7 * (C{}-C3)".format(11 + 17 *q, 11+17*q)


            rangeSelected[11][0]="m{}".format(path[0] -1)
            rangeSelected[12][0]="m{}".format(path[0])
            #ML
            rangeSelected[11][2]="=H7 * (B{} - B3) +G7 * (C{} - C3)".format(10 + 17 * q, 10 + 17 * q)
            rangeSelected[12][2]="=H7 * (B{} - B3) +G7 * (C{} - C3)".format(11 + 17 * q, 11 + 17 * q)

            #DV
            rangeSelected[11][3]="=D{}".format(10 + 17 * q)
            rangeSelected[12][3]="=D{}".format(11 + 17 * q)

            q+=1

            for i in range(startRow, endRow+1,1):
                countCol = 0
                for j in range(startCol, endCol+1,1):

                    sheet.cell(row = i, column = j).value = rangeSelected[countRow][countCol]
                    countCol += 1
                countRow += 1
            startRow += 17
            endRow += 17


    def save_data(self):
        if len(self.paths) == 0:
            print("No paths marked.")
            return

        now = datetime.now()
        time = now.strftime("%Y%m%d%H%M%S")
        new_save = dir_path+"/data/{}_coordinates_{}.xlsx".format(self.animal, time)
        copyfile(dir_path+"/data/do-not-delete.xlsx", new_save)
        workbook = load_workbook(filename=new_save)
        sheet = workbook.active
        self.copy_paste_xcl(1, 7, 4, 22, sheet, self.paths)
        workbook.save(filename = new_save)
        print("Data saved")

    def keyHandler(self, key):
        if key == ord("x"):

            #self.ap = self.to_decimal(float(self.ap)+.1)
            #self.coordinate = self.ap
            if self.sagittal_index < len(self.sagittals)-1:
                self.sagittal_index += 1
            else:
                print("Done")
        elif key == ord("z"):
            if self.sagittal_index != 0:
                self.sagittal_index -= 1
            else:
                print("Done")

        elif key == ord("a"):

            if self.coronal_index < len(self.coronals)-1:
                self.coronal_index += 1
            else:
                print("Done")

        elif key == ord("s"):
            if self.coronal_index != 0:
                self.coronal_index -= 1
            else:
                print("Done")

        elif key==ord("d"):
            try:
                point=(self.x[self.hover_window],self.y[self.hover_window])
                if self.hover_window==0:
                    self.markers.append([point, self.coronal_index, self.convert_to_mm(point,0), self.hover_window])
                else:
                    self.markers.append([point, self.sagittal_index, self.convert_to_mm(point,1), self.hover_window])
            except AttributeError:
                print("Click image once to gain focus.")

        elif key == ord("f"):
            try:
                if len(self.markers)%2 == 0:
                    self.paths.pop()

                self.markers.pop()
            except:
                pass
        elif key == ord("p"):
            self.save_data()
        elif key == ord("q"):
            return True

        return False

    def iterate(self):

        #todo: du mangler angles og angle korrektion i save-file

        self.coronal_index, self.sagittal_index = self.find_nearest_slices()

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

print("Brain coordinator initiated")

animal = "mouse"
reference = "bregma"

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--animal', metavar='animal', default = "mouse", required=False,
                        help='What animal to coordinate?')

    parser.add_argument('--reference', metavar='reference', default = "bregma", required=False,
                        help='What is your reference point? (bregma/lambda)')

    parser.add_argument('--preload', metavar='preload', default = 0, required=False,
                        help='Preload all slices?')


    args = parser.parse_args()
    animal = args.animal
    preload = args.preload
    reference = args.reference

animal="mouse_allen"
print("Animal: {}".format(animal))
print("Reference: {}".format(reference))

coordinator = Coordinator(animal, reference, preload)
