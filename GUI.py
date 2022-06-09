# -*- coding: utf-8 -*-
"""
Created on Fri May 27 21:12:17 2022

@author: Abd El-rhman Fathy
"""

import streamlit as st
import model


st.title("Question Answering")

question = st.text_input("Question",placeholder='Question')

path = st.text_area("Video/directory of videos",placeholder='Video(s)')

get_answer = st.button("Get Answer")

if len(path)!=0:
    if ("\\" in path) and path[len(path)-1] != "\\":
        path = path+"\\"


if get_answer:
    vid, score = model.question_video_answer(path, question)
    st.success("Answer: "+ score['answer'])
    st.success("Time Stamp: "+ str(score['start'])+" - "+ str(score['end']))
    st.success("Accuracy: "+str(score['score']))
    st.success("Video that contains the answer: "+vid)
