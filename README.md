# Question Answering model
## what does it simply do?

The model is to answer a given question by readding the subtitle of one video or multiple videos within one directory.
The language used in this task is ```Python```.

## Feature
- Answer question by reading the subtitle of a video

## approach
The task was devided into two main parts:
- Reading the subtitle from a given video and clean it.
- extracting the answer from the read subtile.

### 1. Reading subtitle from a given video
- The function responsible for that is ```read_subtitle``` that takes list of video paths and return list of subtitles with their associated time stamp.
- The approach was to read two or three frames per second from the video to get frames that contain all the subtitles in the video and also decrease the number of processed frames so it doesn't process every frame in the video.
The library used in this was ```cv2```.
- Eevery frame that was chosen to be processed was first cut into the third to get the part of it that contains the desired subtitle and avoid reading noises or other words in the frame.
- After cutting the frame the text extraction was then handled by the library ```pytesseract``` which is OCR library.
- then sequnce of processing steps were applied to filter the read subtitle. e.g; determine when the subtitle change, remove strange characters, checking if the sentence is...etc.
- The result is then filtered to get only sentences relevant to the question using ```get_context``` function.

### 2. extracting the answer from the read subtile
- After getting the context related to the question the subtitle then is combined into one string.
- The question answering model is imported from ```transformers.pipline```.
- Both The question and the combined context are fed to the model and the result is accumlated.
- based on the index of the start and the end of the answer the time stamp is searched for.



## Functions implemented in the task
| Function | input | output 
| :---: | :---: | :---: |
| ```time_to_string``` | time in seconds | time in the form mm:ss |
| ```is_in_english``` | qoute  | True/False  |
|```read_subtitle``` |list of paths | subtitle wth timestamp |
|```get_context``` | question and subtitle | related subtitle|
|``` is_video_file ```| file name | True/False|
|```answer``` |question and related subtitle | answer |
|```question_video_answer``` | question and path/directory | best answer|

###### Note: the model is written in the file ```model.py```.

## GUI
The GUI is very simple created using ```streamlit``` in the file ``` GUI.py```.


## Results
to test the results a video of length five seconds was created that has five different subtitles and five questions was asked to the model three were answered correctly and the other two weren't this most probably because of the misslocating of the related subtitles or the font of them was a bit small.


# To run the task
### install required libraries
```bash
pip install requirements.txt
```
### install Tessaract-OCR
please download and install Tesseract-OCR through the following link https://github.com/UB-Mannheim/tesseract/wiki
and make sure that the installation directory is a folder named "Tesseract-OCR" in the same directory of the task files.

for example the directory in my pc is "C:\Users\Abd El-rhman Fathy\Desktop\Task\Tesseract-OCR"
where all task files are in folder "Task"

### How to run
1. open your shell/terminal
2. navigate to the directory containing project files
3. run the following command 
``` bash
streamlit run GUI.py
```

### Comments:
- the model take time running a progress bar will give the intution of how long to wait.
- multiple videos is to be put in the same directory first.

### Time Spent on Every section
- searching : total 6 hrs
- Text extraction : 3 hrs
- Text Filtering and cleaning: 3 hrs
- answering section : 4 hrs
- debugging : 4 hrs
- README.md : 2 hrs
- creating demo video : 1 hr
- creating illustration video : 1 hr

