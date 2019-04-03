import os.path

def clearLayout(layout):
  while layout.count():
    child = layout.takeAt(0)
    if child.widget():
      child.widget().deleteLater()

def get_ressources_file(file_name):
    ressources = os.path.join("gui", "ressources")
    return os.path.join(ressources, file_name)
