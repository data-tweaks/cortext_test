import os
import toml

from config import *
from snowflake.snowpark.session import Session 
from snowflake.cortex import Complete

import streamlit as st
import pandas as pd  
import numpy as np
import io 
from PIL import Image


def snowpark_session_create(): 
 
    config = toml.load("app/config/connections.toml")
    connConfig = config["aiGround"]

    connection_params = {
        "user" : st.secrets["user"],   
        "password": st.secrets["password"],
        "account" : st.secrets["account"],
        "warehouse" : connConfig.get("warehouse"),
        "database" : connConfig.get("database"),
        "schema" : connConfig.get("schema")
    }

    session = Session.builder.configs(connection_params).create()
    return session 

def config_app_UI(): 

    page_element="""
    <style>
    [data-testid="stAppViewContainer"]{
    background-image: url("https://data-tweaks.com/wp-content/uploads/2025/05/myAIAppBanner4.png") ;  
    background-size: cover;
    }
    </style>
    """
    st.markdown(page_element, unsafe_allow_html=True)

    st.write("\n\n") 
    st.write("\n\n") 
    st.divider()
    st.header(f"  **:grey[WHAT CAN YOU DO WITH CURIOSITY AND IMAGE PROCESSING APP?]** ")
    st.write("1- **:grey[Analyse images]**") 
    st.write("2- **:grey[Compare images]**") 
    st.write("3- **:grey[Ask questions if you are curious about something!]**") 
    st.write("\n\n") 


def initSession(): 
    if "curiosity" not in st.session_state:
        st.session_state.curiosity = False
    if "prompt" not in st.session_state:
        st.session_state.prompt = ""
    if "analyzeImg" not in st.session_state:
        st.session_state.analyzeImg = False
    if "compareImg" not in st.session_state:
        st.session_state.compareImg = False
    if "clearSess" not in st.session_state:
        st.session_state.clearSess = False       
    if "demo_session" not in st.session_state:
        st.session_state.demo_session = None
    if "image_input" not in st.session_state:
        st.session_state.image_input = []
    if "compimg1_input" not in st.session_state:
        st.session_state.image_input = []
    if "compImg2_input" not in st.session_state:
        st.session_state.image_input = []    
    if "anlyzImg1_input" not in st.session_state:
        st.session_state.image_input = []    

def clearSession(): 
    st.session_state.curiosity = False
    st.session_state.prompt = ""
    st.session_state.analyzeImg = False
    st.session_state.compareImg = False
    st.session_state.clearSess = False       
    st.session_state.demo_session = None
    st.session_state.image_input = []
    st.session_state.image_input = []
    st.session_state.image_input = []    
    st.session_state.image_input = []    


def execute_cortex_complete_api(prompt , session):    
    response_txt = Complete(
                    'llama3.1-8b',
                    prompt,
                    session=session
                    )

    if response_txt is not None: 
        return response_txt
    else:   
        return f"Sorry, I don't know the answer of your question." 


def compare_images_via_cortex_SQL(session, img1_bytes, img2_bytes):
    response = session.sql(
          f"""
                SELECT SNOWFLAKE.CORTEX.COMPLETE('claude-3-5-sonnet',
                PROMPT('Compare this image {{0}} to this image {{1}} and describe the ideal audience for each in two concise bullets no longer than 10 words',
                TO_FILE('@IMAGE_REP', '{img1_bytes}'),
                TO_FILE('@IMAGE_REP', '{img2_bytes}')
                   ));
           """ 
    ).collect()

    if response is not None: 
        return response[0][0]
    else:   
        return "please choose another image, this image is not suitable for processesing. " 
 

def compare_images_via_cortex_SQL(session, img1_bytes, img2_bytes):
    session.sql(
          f"""  ALTER SESSION SET USE_CACHED_RESULT = FALSE;   """  ).collect()
    response = session.sql(
          f"""
                SELECT SNOWFLAKE.CORTEX.COMPLETE('claude-3-5-sonnet',
                PROMPT('Compare this image {{0}} to this image {{1}} and describe the ideal audience for each in two concise bullets no longer than 10 words',
                TO_FILE('@IMAGE_REP', '{img1_bytes}'),
                TO_FILE('@IMAGE_REP', '{img2_bytes}')
                   ));
           """ 
    ).collect()

    if response is not None: 
        return response[0][0]
    else:   
        return "Please choose another image, this image is not suitable for processesing. " 


def analyze_images_via_cortex_SQL(session , imgName):
    response = session.sql(   
          f"""  select snowflake.cortex.complete 
                (
                    'pixtral-large' , 
                    ' Put image filename in an attribute called "Image." 
                    Put classification in an attribute called "Name"  
                    Put a short title in title case og image {imgName} in an attribute called "Title"
                    Put a short description expalining it to a 5 year old child in an attribute called "description"
                    ' , 
                    to_file('@image_analyse' , '{imgName}' )
                ) as image_classification 
                from directory(@image_analyse)
           """ 
    ).collect()

    if response is not None: 
        return response[0][0]
    else: 
        return "Please choose another image, this image is not suitable for processesing. " 


def purgeAnalyzeStage(session):
    response = session.sql( f"""  remove @image_analyse  """).collect()


def main(): 
    
    #configure the app 
    config_app_UI() 
    initSession()
    snowpark_session_create()
       
    procContainer = st.container(border = True)
    clearButton,  cortexButtons =  procContainer.columns(2)
    analyseImgCol , compareImgCol , curiosityCol =  procContainer.columns(3)

    #clear the session for a clean page 
    if clearButton.button("**:grey[CLEAR SESSION]**"):
        st.session_state.clearSess = True
        clearSession() 

    ###################################################################################
    # CURIOSITY
    ###################################################################################

    # set the session for curiosity function 
    if cortexButtons.button("  **:grey[ASK ME ANYTHING]** "):
        st.session_state.curiosity = True

    if st.session_state.curiosity:
        st.session_state.prompt = procContainer.text_input("Ask me:")
            
        if st.session_state.prompt.strip():
            procContainer.write(f" **You asked :** {st.session_state.prompt}")
            # Create Snowflake session only once
            if not st.session_state.demo_session:
                st.session_state.demo_session = snowpark_session_create()

            # Return answer for the question     
            answer = execute_cortex_complete_api(st.session_state.prompt , st.session_state.demo_session )  
            procContainer.divider()
            procContainer.write(answer)


    ###########################################################################################
    # COMPARING IMAGES 
    ###########################################################################################

    # set the session for comparing images 
    if cortexButtons.button(" **:grey[COMPARE IMAGES]** ")  :
        st.session_state.compareImg = True

    if st.session_state.compareImg : 
        procContainer.header("**:grey[UPLOAD 2 IMAGES TO COMPARE!]**")
        procContainer.write("\n\n")
       
        # create the session if it is not created 
        if not st.session_state.demo_session:
            st.session_state.demo_session = snowpark_session_create()

        img1Name = ""
        img2Name = ""

        leftImage , rightImage = procContainer.columns(2)
 
        # upload a file in jpg, jpeg or png mode 
        st.session_state.Compimg1_input = leftImage.file_uploader('**:grey[Upload the first image in PNG format]**', type= ['jpg', 'jpeg', 'png'])         
        if st.session_state.Compimg1_input is not None:
            img1Name = st.session_state.Compimg1_input.name
            img1Type = st.session_state.Compimg1_input.type
            leftImage.write(img1Type)
            image1 = Image.open(st.session_state.Compimg1_input)
            leftImage.write("Went through")
            buffer = io.BytesIO()
            leftImage.write("Went through 2")
            image1.save(buffer, format= img1Type)
            leftImage.write("Went through 3")
            buffer.seek(0)
            leftImage.write("Went through 4")
            with open(f"/tmp/{img1Name}", "wb") as f:
                f.write(buffer.read())     
            leftImage.write("Went through 5")    
   
        # upload a file in jpg, jpeg or png mode 
        st.session_state.CompImg2_input = rightImage.file_uploader('**:grey[Upload the second image in PNG format]**',type= ['jpg', 'jpeg', 'png']) 
        # if file is uploaded then open the image 
        if st.session_state.CompImg2_input is not None:
            img2Name = st.session_state.CompImg2_input.name
            img2Type = st.session_state.CompImg2_input.type
            image2 = Image.open(st.session_state.CompImg2_input)
            buffer = io.BytesIO()
            image2.save(buffer, format= img2Type)
            buffer.seek(0)
            with open(f"/tmp/{img2Name}", "wb") as f:
                f.write(buffer.read())

        # put the images to the stage 
        if st.session_state.CompImg2_input  is not None and  st.session_state.Compimg1_input is not None:  
            leftImage.write(image1)
            leftImage.write(f" **:grey[Image 1 :]** {img1Name} ")
            leftImage.write("Went through 6 ")
            st.session_state.demo_session.file.put(f"/tmp/{img1Name}", "@IMAGE_REP", auto_compress=True)
            leftImage.write("Went through 7")      
            rightImage.write(image2)
            rightImage.write(f" **:grey[Image 2 :]** {img2Name} ")
            st.session_state.demo_session.file.put(f"/tmp/{img2Name}", "@IMAGE_REP", auto_compress=True)

        # compare the images 
        if img2Name != "" and img1Name != "": 
            answer = compare_images_via_cortex_SQL( st.session_state.demo_session ,  img1Name ,img2Name )  
            procContainer.write(answer) 


    ###########################################################################################
    # ANALYZE IMAGES 
    ###########################################################################################

    # set the session for analyzing images 
    if cortexButtons.button(" **:grey[ANALYZE IMAGES]** ") :
        st.session_state.analyzeImg = True

    if st.session_state.analyzeImg : 
        if not st.session_state.demo_session:
            st.session_state.demo_session = snowpark_session_create()

        # remove the existing images from the stage 
        purgeAnalyzeStage(st.session_state.demo_session)
        image = ""

        # upload images 
        st.session_state.anlyzImg1_input = procContainer.file_uploader('**:grey[Upload image in PNG format]**', type= ['jpg', 'jpeg', 'png']) 
        if st.session_state.anlyzImg1_input is not None:
            imgName = st.session_state.anlyzImg1_input.name
            image = Image.open(st.session_state.anlyzImg1_input)
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            buffer.seek(0)         
            with open(f"/tmp/{imgName}", "wb") as f:
                f.write(buffer.read())

        if st.session_state.anlyzImg1_input  is not None :  
            procContainer.write(image)
            procContainer.write(f" **:grey[Image :]** {imgName} ")
            st.session_state.demo_session.file.put(f"/tmp/{imgName}", "@IMAGE_ANALYSE", auto_compress=False)   

        if image != "":
            st.session_state.demo_session.sql(  f""" ALTER SESSION SET USE_CACHED_RESULT = FALSE;  """ ).collect()
            answer = analyze_images_via_cortex_SQL(st.session_state.demo_session , imgName)
            procContainer.write(answer) 


# run main
main()