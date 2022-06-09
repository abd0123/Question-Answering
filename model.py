
# Libraries

# Note Streamlit in this file is only for progrss bar and please wait message
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'Tesseract-OCR\tesseract'
import cv2 as cv
import enchant
from enchant.checker import SpellChecker
from difflib import SequenceMatcher
import re
from nltk.stem.porter import PorterStemmer
from transformers import pipeline
import os
import streamlit as st

"""
function to convert time from seconds to mm:ss
"""
def time_to_string(time):
    minutes = time//60
    time %= 60
    
    #determine the double accuracy of the output
    formatted_string = "{:.2f}".format(time)
    
    return str(int(minutes))+":"+formatted_string


"""
fuction to check if a sentence is English 
used to filter the extracted text from videos
"""
def is_in_english(quote):
    # get the US English dictionary and check the qoute
    d = SpellChecker("en_US")
    d.set_text(quote)
    
    # get words with wrong spelling
    errors = [err.word for err in d]
    
    # maximum number of errors is 50% of the whole qoute
    max_error_count = 0.5*len(quote.split())
    
    # Empty qoute are not considered
    min_text_length = 1
    
    return False if ((len(errors) > max_error_count) or len(quote.split()) < min_text_length) else True


"""
read subtibles take list of videos paths 
and return list of lists of subtitles
"""
def read_subtitle(paths):
    out = []
    
    h = 1
    #loop for each video in paths
    for path in paths:
        
        #progress bar for each video
        st.text("Video"+str(h))
        h+=1;
        my_bar = st.progress(0)
        
        #subtitles of the video
        result = []
        video = cv.VideoCapture(path)
        c = 0
        fps = video.get(cv.CAP_PROP_FPS)
        frame_count = int(video. get(cv. CAP_PROP_FRAME_COUNT))
        total =frame_count/fps;
        print(fps)
        print(frame_count)
        """
        read video frame by frame and process tow frames per second
        to resduce processing time and a subtitle generally lasts mores than
        one second 
        """
        success, image = video.read()
        
        # keeps tracks of each subtitle start time
        start = 0
        
        while success:
            
            # 1 second mid point
            x = int(fps//2)
            if x==0:
                x+=1
            
            # processing mid points frames
            if c%x==0:
                # cut the frame by third to get only subtitle section
                imglnegth = len(image)
                image = image[2*imglnegth//3:imglnegth, :]
                cv.imwrite("temp.jpg", image)
                
                #read subtitle from frame
                subtitle = pytesseract.image_to_string(r'temp.jpg')
                
                #clean missread subtitles
                subtitle = re.sub(r"""[^a-zA-Z0-9 ']""", '', subtitle)
                
                if len(result)==0: # first subtitle in a video
                    result.append([subtitle, start, 0])
                else:
                    
                    """
                     check if the read subtitle is english and
                     check if this subtitle doesnt match the previous one 
                     (different subtitles) to avoid duplicates
                    """
                    if is_in_english(subtitle) and SequenceMatcher(None, result[len(result)-1][0], subtitle).ratio() < 0.6:
                        start = c/fps
                        result.append([subtitle, time_to_string(start), 0])
                        result[len(result)-2][2] = time_to_string(start)
                    elif is_in_english(subtitle):
                        
                        # if it is english and have fewer errors than the previous 
                        # it shou replace it
                        d = SpellChecker("en_US")
                        d.set_text(subtitle)
                        errors = [err.word for err in d]
                        x = len(errors)
                        d = SpellChecker("en_US")
                        d.set_text(result[len(result)-1][0])
                        errors = [err.word for err in d]
                        y = len(errors)
                        if y>x:
                            result[len(result)-1][0] = subtitle
            
            #update vars and progress bar
            success, image = video.read()
            c+=1;
            
            #update progress bar
            my_bar.progress(c/frame_count)
        
        """ one video finished"""
        
        # set the end time of the last subtitle
        result[len(result)-1][2] = time_to_string(total)
        
        # replace the wrong detected words with suggestions
        dictionary = enchant.Dict("en_US")
        for i in range(len(result)):
            sentence = result[i][0]
            sentence = sentence.split()
            for j in range(len(sentence)):
                word = sentence[j]
                if dictionary.check(word) != True and len(dictionary.suggest(word)) != 0:
                    sentence[j] = dictionary.suggest(word)[0]
            sentence = ' '.join(sentence)
            result[i][0] = sentence
        out.append(result)
    print(out)
    return out

"""
only get the subtitles that are related to the question
"""

def get_context(question, subtitles):
    out = []
    
    #turn every word in the question to its stem 
    question = question.lower()     #Lower Case
    question = question.split()     #list of words
    ps = PorterStemmer()            #stemmer
    question = [ps.stem(word) for word in question]
    question = ' '.join(question)
    
    # loop over the subtitle of each video
    for video in subtitles:
        curr = []
        
        # steming and checking the relation between the 
        # subtitle and question
        for result in video:
            sentence = result[0]
            sentence = sentence.lower()
            sentence = sentence.split()
            
            #count the semilarities
            c = 0
            for word in sentence:
                if ps.stem(word) in question:
                    c+=1
            # add if not zero similaries
            if c!=0:
                curr.append(result)

        out.append(curr);
    return out

def answer(question, subtitles):
    # initialize question answering model
    qa_model = pipeline("question-answering")
    
    # get relative context to the question
    context = get_context(question, subtitles)
    
    out = []
    
    # all context is combined in subtitle
    subtitle = ""
    
    # i is index of the video
    for i in range(len(context)):
        for result in context[i]:
            sentence = result[0]
            subtitle += " "
            
            # keep track of the starting index
            start = len(subtitle)
            
            #concatenate the context into one string
            subtitle += sentence
            
            # keep track of the ending index
            end = len(subtitle)-1
            out.append([start, end, i])
    
    #get the answer in the form
    # "{'score': 0.8, 'answer': answer, 'start': start_idx, 'end': end_idx}"
    score = qa_model(question = question, context = subtitle)
    
    #start index
    start = score['start']
    
    #end index
    end = score['end']
    
    #time stamp
    stamp = [-1,-1]
    
    #video index
    vid = -1
    
    j = 0
    for i in range(len(out)):
        rang = out[i]
        
        previous = rang[2]
        # check if the start is in this range
        if start >= rang[0] and start <= rang[1]:
            
            # start time 
            stamp[0] = context[rang[2]][j][1]
            
            # video index
            vid = rang[2]

        # check if the end is in this range
        if end >= rang[0] and end <= rang[1]:
            
            #end time
            stamp[1] = context[rang[2]][j][2]
        
        j += 1
        if i < len(out)-1:
            if out[i+1][2] != previous:
                j -= len(context[previous])

    if stamp[1]==-1:
        stamp[1] = context[vid][len(context[vid])-1][2]
    
    # override the start and end indices with time stamp
    score['start'] =  stamp[0]
    score['end'] = stamp[1]
    return vid, score


"""
check if the file is video stackoverflow
"""
def is_video_file(filename):
    video_file_extensions = ('.264', '.3g2', '.3gp', '.3gp2', '.3gpp', '.3gpp2', '.3mm', '.3p2', '.60d', '.787', '.89', '.aaf', '.aec', '.aep', '.aepx',
'.aet', '.aetx', '.ajp', '.ale', '.am', '.amc', '.amv', '.amx', '.anim', '.aqt', '.arcut', '.arf', '.asf', '.asx', '.avb','.avc', '.avd', '.avi', '.avp', '.avs', '.avs', '.avv', '.axm', '.bdm', '.bdmv', '.bdt2', '.bdt3', '.bik', '.bin', '.bix',
'.bmk', '.bnp', '.box', '.bs4', '.bsf', '.bvr', '.byu', '.camproj', '.camrec', '.camv', '.ced', '.cel', '.cine', '.cip','.clpi', '.cmmp', '.cmmtpl', '.cmproj', '.cmrec', '.cpi', '.cst', '.cvc', '.cx3', '.d2v', '.d3v', '.dat', '.dav', '.dce',
'.dck', '.dcr', '.dcr', '.ddat', '.dif', '.dir', '.divx', '.dlx', '.dmb', '.dmsd', '.dmsd3d', '.dmsm', '.dmsm3d', '.dmss','.dmx', '.dnc', '.dpa', '.dpg', '.dream', '.dsy', '.dv', '.dv-avi', '.dv4', '.dvdmedia', '.dvr', '.dvr-ms', '.dvx', '.dxr',
'.dzm', '.dzp', '.dzt', '.edl', '.evo', '.eye', '.ezt', '.f4p', '.f4v', '.fbr', '.fbr', '.fbz', '.fcp', '.fcproject','.ffd', '.flc', '.flh', '.fli', '.flv', '.flx', '.gfp', '.gl', '.gom', '.grasp', '.gts', '.gvi', '.gvp', '.h264', '.hdmov',
'.hkm', '.ifo', '.imovieproj', '.imovieproject', '.ircp', '.irf', '.ism', '.ismc', '.ismv', '.iva', '.ivf', '.ivr', '.ivs','.izz', '.izzy', '.jss', '.jts', '.jtv', '.k3g', '.kmv', '.ktn', '.lrec', '.lsf', '.lsx', '.m15', '.m1pg', '.m1v', '.m21',
'.m21', '.m2a', '.m2p', '.m2t', '.m2ts', '.m2v', '.m4e', '.m4u', '.m4v', '.m75', '.mani', '.meta', '.mgv', '.mj2', '.mjp','.mjpg', '.mk3d', '.mkv', '.mmv', '.mnv', '.mob', '.mod', '.modd', '.moff', '.moi', '.moov', '.mov', '.movie', '.mp21',
'.mp21', '.mp2v', '.mp4', '.mp4v', '.mpe', '.mpeg', '.mpeg1', '.mpeg4', '.mpf', '.mpg', '.mpg2', '.mpgindex', '.mpl','.mpl', '.mpls', '.mpsub', '.mpv', '.mpv2', '.mqv', '.msdvd', '.mse', '.msh', '.mswmm', '.mts', '.mtv', '.mvb', '.mvc',
'.mvd', '.mve', '.mvex', '.mvp', '.mvp', '.mvy', '.mxf', '.mxv', '.mys', '.ncor', '.nsv', '.nut', '.nuv', '.nvc', '.ogm','.ogv', '.ogx', '.osp', '.otrkey', '.pac', '.par', '.pds', '.pgi', '.photoshow', '.piv', '.pjs', '.playlist', '.plproj',
'.pmf', '.pmv', '.pns', '.ppj', '.prel', '.pro', '.prproj', '.prtl', '.psb', '.psh', '.pssd', '.pva', '.pvr', '.pxv','.qt', '.qtch', '.qtindex', '.qtl', '.qtm', '.qtz', '.r3d', '.rcd', '.rcproject', '.rdb', '.rec', '.rm', '.rmd', '.rmd',
'.rmp', '.rms', '.rmv', '.rmvb', '.roq', '.rp', '.rsx', '.rts', '.rts', '.rum', '.rv', '.rvid', '.rvl', '.sbk', '.sbt','.scc', '.scm', '.scm', '.scn', '.screenflow', '.sec', '.sedprj', '.seq', '.sfd', '.sfvidcap', '.siv', '.smi', '.smi',
'.smil', '.smk', '.sml', '.smv', '.spl', '.sqz', '.srt', '.ssf', '.ssm', '.stl', '.str', '.stx', '.svi', '.swf', '.swi','.swt', '.tda3mt', '.tdx', '.thp', '.tivo', '.tix', '.tod', '.tp', '.tp0', '.tpd', '.tpr', '.trp', '.ts', '.tsp', '.ttxt',
'.tvs', '.usf', '.usm', '.vc1', '.vcpf', '.vcr', '.vcv', '.vdo', '.vdr', '.vdx', '.veg','.vem', '.vep', '.vf', '.vft','.vfw', '.vfz', '.vgz', '.vid', '.video', '.viewlet', '.viv', '.vivo', '.vlab', '.vob', '.vp3', '.vp6', '.vp7', '.vpj',
'.vro', '.vs4', '.vse', '.vsp', '.w32', '.wcp', '.webm', '.wlmp', '.wm', '.wmd', '.wmmp', '.wmv', '.wmx', '.wot', '.wp3','.wpl', '.wtv', '.wve', '.wvx', '.xej', '.xel', '.xesc', '.xfl', '.xlmv', '.xmv', '.xvid', '.y4m', '.yog', '.yuv', '.zeg',
'.zm1', '.zm2', '.zm3', '.zmv'  )
    if filename.endswith((video_file_extensions)):
        return True
    else: 
        return False

def question_video_answer(path, question):
    paths = []
    
    # videos in different paths (not required case)
    if type(path) == list:
        paths = path
    
    # multiple videos in directory
    elif os.path.isdir(path):
        arr = os.listdir(path)
        for f in arr:
            if is_video_file(f):
                paths.append(path+f)
    
    # one video
    elif os.path.isfile(path):
        paths = [path]
    
    #maxmize the answer from the multiple videos
    vid_idx = 0
    best_acc = {'score':0, 'answer': "no answer found", 'start':'00:00', 'end':'00:00'}
    for p in paths:
        #read subtitles
        subtitles = read_subtitle([p])
        st.text("Please Wait few seconds")
        
        #answer
        i , ans = answer(question, subtitles)
        
        #max
        if ans['score'] > best_acc['score']:
            best_acc = ans
            vid_idx = i

    return paths[vid_idx], best_acc;