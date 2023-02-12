Author: Mark Xu

# Python based DICOM file reader
A functioning demo of a DICOM file reader as part of an image analysis group project from the USYD course BMET3921 Biomedical Design and Technology. The program reads a folder of CT scans in the form of DICOM files, computes pixel array of the images, and stores the images in memory for subsequent processing and analysis (analysis not part of this demo). 

## Run instructions
For Windows, run main.exe in dist/main/
For others, run main.py and install Python packages as per the comments

## Creation:

**Programming language** Python
**Important packages** PyDicom, numpy, PySimpleGUi

Python was chosen as the language to implement this demo for its familiarity, widely available packages, and simplicity. The demo was completed in 5 days, averaging around 1.5 hours per day spent. Around half the time spent on creating this program was on figuring how utilise parallel processing to speed up the importing process, as the default behaviour of the program is too slow for a proper demonstration. 

PyInstaller was used to compile an executable for Windows, demonstrating the feasibility of creating an hassle-free program with widely available tools like Python for medical professionals. 

## Optimizations
Added parallel processing using Python's multiprocessing package to speed up the process of extracting pixel array from DICOM files. Multiprocessing decreased the importing time of large folders by more than 2.5 times. 

## What I got out of this:

Throughout the creation of this demo, I haved learned the basices of handling the processing and storage of uncompressed image files. I also gained an understanding of the fundamentals of parallel processing in Python. 