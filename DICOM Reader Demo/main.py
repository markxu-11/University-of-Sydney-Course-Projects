import PySimpleGUI as sg
from PIL import Image
import pydicom
from pydicom.dataset import FileDataset
import numpy as np
from multiprocessing import Process, Manager
import multiprocessing
from multiprocessing.managers import ListProxy
import os
from io import BytesIO
from math import ceil

# Package required currently
# Install by running command in terminal
# pip install pysimplegui
# pip install pydicom
# pip install numpy
# pip install Pillow
# pip install pylibjpeg pylibjpeg-libjpeg pydicom

# For compiling python script to application file - only run if making application
# Replace "filename.py" with filename of this file
# pip install pyinstaller
# pyinstaller --hiddenimport=pydicom.encoders.gdcm --hiddenimport=pydicom.encoders.pylibjpeg "filename.py"

def hardcoded_sort(ls: list[str]) -> list[str]:
    return sorted(ls, key=lambda n: int(n[1:]))

def read_dcmlist(folder_path: str, filenames: list[str]) -> list[FileDataset]:
    return [pydicom.dcmread(os.path.join(folder_path, f)) for f in filenames]

def get_pixel_arrays(datasets: list[FileDataset]) -> list[np.ndarray]:
    return [d.pixel_array for d in datasets]

def gpam_helper(datasets: list[FileDataset], target_list: ListProxy, 
                    start: int, end: int):
    """Helper function of get_pixel_arrays_multithread

    Args:
        datasets (list[FileDataset]): list of FileDataset from pydicom
        target_list (ListProxy): Python's ListProxy
        start (int): start index
        end (int): end index
    """    
    target_list[start:end] = [d.pixel_array for d in datasets]

def get_pixel_arrays_multithread(
    datasets: list[FileDataset], threads: int=None) -> ListProxy:
    """Get pixel array from pydicom FileDataset

    Args:
        datasets (list[FileDataset]): list of FileDataset from pydicom
        threads (int, optional): Sets number of processes. Defaults to None.

    Returns:
        ListProxy: ListProxy of pixel arrays
    """    
    if not threads:
        threads = int(multiprocessing.cpu_count() / 2)
    
    s = len(datasets)
    interval = ceil(s / threads)
    start = 0
    end = start + interval

    manager = Manager()
    proxy_pixel_array = manager.list([0] * s)
    processes = []

    while start < s:
        p = Process(target=gpam_helper, args=(datasets[start:end], proxy_pixel_array, start, end))
        p.start()
        processes.append(p)
        start += interval
        end += interval

    for p in processes:
        p.join()
    return proxy_pixel_array

def main(): 
    font = ("Arial", 11)
    g_width = 600
    g_height = 600

    def graph_array(graph_elem: sg.Graph, array: np.ndarray, intensity_factor: int=1):
        temp = array
        temp *= np.uint16(intensity_factor)
        im = Image.fromarray(temp)
        output = BytesIO()
        im.save(output, format="PNG")
        data = output.getvalue()
        graph_elem.erase()
        graph_elem.draw_image(data=data, location=(0, g_height))

    def make_main_window():
        import_frame = sg.Frame("Import", [
            [sg.Column([
                [sg.Text("Input Path", justification="c", size=(11, 1)), 
                 sg.Input(key="-INPATH-"), sg.FolderBrowse()], 
                [sg.Text("Range\n(default: all)", justification="c", size=(11, 2)), 
                 sg.Text("Start"), sg.Input(size=(4, 1), key="-START-"), 
                 sg.Text("End"), sg.Input(size=(4, 1), key="-END-"), 
                 sg.Button("Import")],
            ]), ],
        ])

        preview_frame = sg.Frame("Preview", layout=[
            [sg.Graph(canvas_size=(g_width, g_height), 
             graph_bottom_left=(0, 0), graph_top_right=(g_width, g_height),
             background_color="black", visible=False, key="-VIEWER-")],
            [sg.Button("Preview")],
            [sg.B("<<<"), sg.B("<<"), sg.B("<"), sg.B(">"), sg.B(">>"), sg.B(">>>"), 
             sg.Text("", size=(15, 1), key="-IMGNUM-")],
            [sg.Text("Brightness"), sg.Slider(range=(1, 30), orientation="h", 
             enable_events=True, key="-BRIGHTNESS-")],
        ], key="-PREVIEWFRAME-")

        layout = [
            [import_frame],
            [preview_frame],
        ]
        return sg.Window("DICOM Reader Demo", layout, font=font, finalize=True)


    window = make_main_window()

    # variables
    dcm_files: list[FileDataset] = None
    dcm_pixel_arrays: list[np.ndarray] = None # <--- Output of the first stage
    importing = False
    cur_idx: int = 0
    brightness: int = 1
    # event loop
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, "Exit"):
            break

        # importing
        if event == "Import" and not importing:
            path = values["-INPATH-"]

            try: 
                fnames = hardcoded_sort(os.listdir(path)) # remove hardcoded sort
            except FileNotFoundError:
                importing = False
                sg.popup("Invalid path")
                continue

            importing = True
            print("Importing...")
            start = None
            end = None
            if len(values["-START-"]) != 0:
                start = int(values["-START-"])
            if len(values["-END-"]) != 0:
                end = int(values["-END-"])
            window.perform_long_operation(
                lambda: read_dcmlist(path, fnames[start:end]), "-IMPORTFINISH-")

        if event == "-IMPORTFINISH-":
            # get the value after import is finished
            dcm_files = values["-IMPORTFINISH-"]          
            print("Converting to pixel array...")
            window.perform_long_operation(
                lambda: get_pixel_arrays_multithread(dcm_files), "-GETARRAYFINISH-")
        
        # loading preview
        if event == "Preview" and not importing:
            window["-VIEWER-"].update(visible=True)
            brightness = values["-BRIGHTNESS-"]
            img_arr = dcm_pixel_arrays[cur_idx]
            graph_array(window["-VIEWER-"], img_arr, brightness)
            window["-IMGNUM-"].update(f"{cur_idx + 1} / {len(dcm_pixel_arrays)}")

        if event == "-GETARRAYFINISH-":
            dcm_pixel_arrays = values["-GETARRAYFINISH-"]
            
            # set value
            brightness = values["-BRIGHTNESS-"]
            img_arr = dcm_pixel_arrays[cur_idx]
            graph_array(window["-VIEWER-"], img_arr, brightness)
            window["-IMGNUM-"].update(f"{cur_idx + 1} / {len(dcm_pixel_arrays)}")

            print("Import Finished")
            importing = False

        if event in ("<<<", "<<", "<", ">", ">>", ">>>") and dcm_pixel_arrays:
            max_idx = len(dcm_pixel_arrays) - 1
            if event == "<<<":
                cur_idx = cur_idx - 100 if cur_idx > 100 else 0
            elif event == "<<":
                cur_idx = cur_idx - 10 if cur_idx > 10 else 0
            elif event == "<":
                cur_idx = cur_idx - 1 if cur_idx > 1 else 0
            elif event == ">":
                cur_idx = cur_idx + 1 if cur_idx + 1 < max_idx else max_idx
            elif event == ">>":
                cur_idx = cur_idx + 10 if cur_idx + 10 < max_idx else max_idx
            elif event == ">>>":
                cur_idx = cur_idx + 100 if cur_idx + 100 < max_idx else max_idx
            
            brightness = values["-BRIGHTNESS-"]
            img_arr = dcm_pixel_arrays[cur_idx]
            graph_array(window["-VIEWER-"], img_arr, brightness)
            window["-IMGNUM-"].update(f"{cur_idx + 1} / {len(dcm_pixel_arrays)}")

        
        if event == "-BRIGHTNESS-" and dcm_pixel_arrays:
            brightness = values["-BRIGHTNESS-"]
            img_arr = dcm_pixel_arrays[cur_idx]
            graph_array(window["-VIEWER-"], img_arr, brightness)
            window["-IMGNUM-"].update(f"{cur_idx + 1} / {len(dcm_pixel_arrays)}")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()