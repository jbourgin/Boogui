from tkinter import Tk     # from tkinter import Tk for Python 3.x
from tkinter.filedialog import askopenfilenames

Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
files = askopenfilenames(title="Ouvrir les fichiers pour comparaison", filetypes=[("CSV files", ".csv")])
if len(files) != 2:
    raise Exception("Vous avez choisi {0} fichiers. Il en faut deux.".format(len(files)))

with open(files[0], 'r') as t1, open(files[1], 'r') as t2:
    fileone = t1.readlines()
    filetwo = t2.readlines()

for count, line in enumerate(fileone):
    if line != filetwo[count]:
        print("Difference at line {0}".format(count))
        print(filename)
        print(line)
        print(filename2)
        print(filetwo[count])
