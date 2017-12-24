
def GetChoices(platform):

    choices = []
    if platform == '__WXMSW__':
        import ctypes
        import os
        for i in range(65,91):
            vol = chr(i) + ':'
            if os.path.isdir(vol):
                print vol
                choices.append(vol)

    return choices
