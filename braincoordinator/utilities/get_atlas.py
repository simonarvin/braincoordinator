import urllib.request
import numpy as np
from pathlib import Path

class Getter:
    def __init__(self, get:str):
        self.get = get
        self.base_url = r"https://raw.githubusercontent.com/simonarvin/brainatlases/master/"
        self.list_url = r'https://raw.githubusercontent.com/simonarvin/brainatlases/master/atlases.ls'
        self.load_list()
        self.print_atlases()

    def load_list(self):
        with urllib.request.urlopen(self.list_url) as f:
            self.lines = f.readlines()

        for i, line in enumerate(self.lines):
            self.lines[i] = line.decode("utf-8").rstrip("\n")

    def print_atlases(self):
        atlases = np.array(self.lines[0].split(","))

        self.atlases = atlases.reshape(-1, 3)
        in_list = self.str_in_list(self.get, self.atlases)
        if len(in_list) != 0:
            index = in_list[0]
            self.download_atlas(index)
        else:
            print("\nAtlases available:")
            for atlas in self.atlases:
                print(atlas[0])

            index = self.request_atlas()
            self.download_atlas(index)

    def str_in_list(self, str, list):
        return np.where(np.any(list==str, axis=1) == True)[0]

    def request_atlas(self):
        request = ""
        while np.any(request == self.atlases) == False:
            print("")
            request = input("What atlas to download?\n")
            if request == "quit" or request == "q":
                print("Quitting")
                return

        return self.str_in_list(request, self.atlases)

    def download_atlas(self, index:int):
        from os.path import dirname
        from os import path
        dir_path = Path(dirname(path.realpath(__file__))).parent

        atlas_info = self.atlases[index][0]
        if isinstance(atlas_info, str):
            atlas_info = self.atlases[index]

        lines = self.lines[int(atlas_info[1]):int(atlas_info[2]) + 1]
        if lines[0] == atlas_info[0]:
            print("Downloading {} atlas..".format(atlas_info[0]))
            atlas_url = "{}{}/".format(self.base_url, lines[0])
            dir = Path("{}/atlas/{}".format(dir_path, lines[0]))

            print("Saving to {}".format(dir))

            dir.mkdir(parents=True, exist_ok=True)

            lines = lines[1:]
            total_files = len(lines)
            for i, line in enumerate(lines):
                file_url = "{}{}".format(atlas_url, line)
                file_name = "{}/{}".format(dir, line)
                with urllib.request.urlopen(file_url) as f:
                    with open(file_name, mode='wb') as localfile:
                        localfile.write(f.read())
                print("Downloading file {}/{}".format(i + 1, total_files))

        print("{} atlas succesfully downloaded.".format(atlas_info[0]))
        print("Now, run braincoordinator --animal {}".format(atlas_info[0]))
