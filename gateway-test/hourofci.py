#!/usr/bin/env python
# coding: utf-8

# # Hour of CI Widgets Creation

# Creator: Coleman Shepard, shepa135@umn.edu
# 
# This notebook is for the development of widget wrappers to log information from users using the widgets. This is the Python version of the collection methodology for the Hour of CI. 
# 
# [Widget List](https://ipywidgets.readthedocs.io/en/stable/examples/Widget%20List.html)
# 

# ## __init__.py file Contents
# 
# <br>
# 

# In[99]:


from IPython.display import display, clear_output
from ipywidgets import widgets, interact, interactive, fixed, interact_manual, Layout
import time
import datetime
import psycopg2
import numpy as np
import hashlib
import requests
from ipywidgets import Button, HBox, VBox

# Go Button Counting
from string import ascii_lowercase
from collections import Counter
import os
import webbrowser

# Collects user information
import getpass

# Plotting Widgets
get_ipython().run_line_magic('matplotlib', 'notebook')


# Answer_Dict is used for the collection of answers from the user. Submit button retrieves the last entered value. 
Answer_Dict = {"Q1":[None], "Q2":[None], "Q3":[None], "Q4":[None], "Q5":[None], "Q6":[None], "Q7":[None], "Q8":[None], "Q9":[None]}


# Submission count for each questions (attempts in the database)
submission_count = {"Q1":0, "Q2":0, "Q3":0, "Q4":0, "Q5":0, "Q6":0,"Q7":0,"Q8":0,"Q9":0}


# # Constructors to Add to Widgets

# These functions below are components of the wrappers around the Jupyter widgets to provide feedback and log information. 
# 
# <b>Functions</b>
# - Valid (valid)
# - API Call (api_call)
# - Hash Dictionary (hash_dict)
# - Log (logging)
# - Submit Button (button)

# ## Valid

# Uses Valid widget to provide feedback to the user if the answer is right or wrong. 

# In[2]:


def valid(boolVal):
    # If the boolean is True
    if boolVal == True:
        valid_widget = widgets.Valid(
                      value=boolVal,
                      description='Valid!',
                      )
        display(valid_widget)
        print("Congrats!!")
        return True
    
    # If the boolean is false
    elif boolVal == False:
        valid_widget = widgets.Valid(
                      value=boolVal,
                      description='',
                      )
        
        display(valid_widget)
        print("Try Again!")


# Uses the API to evaluate if the answers are correct. This way does not allow the user to retrieve all of the correct information. 

# In[3]:


# Lesson and level could be determined in the first part of each lesson. (i.e. Run these cells )
def api_call(lesson, lesson_level, question, answer):
    
    # Change once in the cloud :) ------------------------
    host = "127.0.0.1"
    port = "5011"
    # If the API Stops working, try switching the port. Sometimes this gets messed up. 
    # ----------------------------------------------------
    
    # Lowercase answer to make it non-case sensitive
    answer = answer.lower()
    
    # Hash answer to send over to the Flask API for validation
    answer = answer.encode('utf-8')
    hash_object = hashlib.sha256(answer)
    hash_answer = hash_object.hexdigest()  

    
    
    url = "http://{}:{}/{}/{}/{}/{}".format(host, port, lesson, lesson_level, question, hash_answer)
    # If you get a JSON Decode error, check to see if the Flask API is up on the right port. T
    # Try changing the port if you are experiencing problems
    response = requests.get(url).json()

    return valid(response)


# ## Logging Function
# 

# In[4]:


def logging(userid, date, time_log, lesson, lesson_level, question, attempts, time_taken, correct):
    ''' 
    This function takes in arguments above, connects to the hourofci database table in postgres, calls a function on the postgres
    side that inserts the information from the table into 
    
    '''
    # Postgres is the definition of beautiful
    logdb_connection = psycopg2.connect(user = "miami",
                                  password = "ggez",
                                  host = "127.0.0.1",
                                  port = "5433",
                                  database = "hourofci")
    # Needed for connection
    cursor = logdb_connection.cursor()
    
    # Specific type casting to align with the database table
    userid = str(userid)
    
    # Question String (Q5, Q2, etc)
    question = question
    
    # Time taken to answer a question
    time_taken = str(time_taken)
    
    # If the submission to the question was correct
    correct = str(correct)
    
    # Removes None from the dictionary (Works fine, but will be searching for a better way)
    if None in Answer_Dict[question]:
        Answer_Dict[question].remove(None)
    
    # Grabs the answers from the specific question from the Answer_Dict
    answers = str(Answer_Dict[question])
    
    # Calls a function in SQL that logs these values
    cursor.callproc('hourofci', (userid, date, time_log, lesson, lesson_level, question, answers, attempts, time_taken, correct))

    # Commit the insert
    logdb_connection.commit()


# ## Submit Button

# The Submit button allows users to submit each answer to validate it. This function contains the validation from above and the logging function to submit any answer to a database. This function needs to be added in each widget instance. Below, you will see examples of these widgets with the submit button included to validate an example answer. The question argument needs to be associated with one of the keys from the <b>Answer_Dict</b>. This ensures the right values are being evaluated for the selected question. 

# In[5]:


def button(question, start_time=time.time()):    
    
    # Resets the answers list from Answer_Dict so we are not collecting redundant information (Keep)
    Answer_Dict[question] = [None]
    
    # For checking the state of the button. Specific for each question.
    global button_state
    button_state = []
    
#     # Get the user start time to evaluate how much time is spent on this module. 
#     start_time = start_time

    
    # Submit Button Creation
    
    button_widget = widgets.Button(
                            value=False,
                            description='Submit',
                            disabled=False,
                            button_style='success', # 'success', 'info', 'warning', 'danger' or ''
                            tooltip='Description',
                            icon='check'
                            )
    
    # Display the button
    display(button_widget)
    

    def on_button_clicked(b):
        
        # Signifies if the button has been pressed to signal to the evaluator that it can run.
        if len(button_state) < 1:
            
            button_state.append(True)
            
        # Checks if the submit button has been clicked.    
        if button_state[0] == True:
            
            # Answer is the last landed on answer in the dictionary. 
            if len(Answer_Dict[question]) > 0:
                answer = str(Answer_Dict[question][-1])
            else:
                print("Try choosing a different answer!")
                return
            
            
            # Submission Count Incrementing 
            submission_count[question] += 1
            
    
    
            # Temp Values --------------------------------------- CHANGE THESE FOR PROD
            lesson = "gateway"
            lesson_level = "beginner"
            #  ------------------------------------------------------------------------
    
            # Question attempts
            attempts = str(submission_count[question])
    
    
            # Call the validation function
            validation = api_call(lesson, lesson_level, question, answer)
            
            validation
           
            
            
            # Default
            correct = "N"
            
            # If validation variable == True, the answer becomes "correct"
            if validation == True:
                correct = "Y"
        
            
            # Date 
            date = datetime.datetime.today().strftime('%Y-%m-%d')
            
            # Time
            time_log = time.strftime("%H:%M:%S", time.gmtime(time.time()))
            
            
            # Total time taken (Calculated everytime submit is pressed)
            time_taken = time.time() - start_time
            print(round(time_taken, 2), "Seconds")
            
            # User ID, but we will have to find a way to calculate it dynamically
            userid = getpass.getuser()
            
            # Log information from logging function
            # Answers variable is located in the logging function

            logging(userid, date, time_log, lesson, lesson_level, question, attempts, time_taken, correct)
            
        
        
   
    # Checks if the button was clicked
    button_widget.on_click(on_button_clicked)


# ## Go Button (Main)
# 
# <br>
# The Go button is similar to the submit button, but it is used to start a task instead of ending it. When Go is clicked, it will start the time and then start another task such as printing out sentences, displaying a graphic, or another task. This will allow us to interactively time the users when they choose to start. 

# In[37]:


# Data Structure to shove (function,argument) tuple into into to be activated on a click. It's a bit weird, but it works. 
array_to_pass = []



# Question Array
question_array = []

# Function to be put into the array_to_pass (Simple Example)
def default_action(action):
    print(action)
    

    
def goBtn(question, funct, action):
    # Resets the array at the beginning to make sure other questions don't break it
    array_to_pass = []
    question_array = []
    
    # Appends the function and argument to the  
    array_to_pass.append(action)
    question_array.append(question)

    # Create a new button
    button = widgets.Button(description="Go!", 
                           button_style='info',)
    

    
    # Display button
    display(button)

    # Action for the event listener
    def on_button_clicked(b):
        
        # Start time needs to be passed to the Submit button. 
        start_time = time.time()
        # Access the last item in the array for access to the latest function. 
        print(array_to_pass[-1])
        
        
        # Append start time to time_taken_array for later retrieval 
        BoundedIntText(question_array[-1])
        
    
        
    
    # Event Listener Called on CLick
    button.on_click(on_button_clicked)
    
#     return start_time

# Pass a function with an 
# goBtn(default_action,ggez)


# ## Go Button  (Part 1)

# In[45]:


ggez = "Geospatial science and technologies are super powerful when enabled with cyberinfrastructure."

def goBtn_part1():
    goBtn("Q4",default_action, ggez)

# goBtn_part1()


# ## Go Button (Part 2)

# In[8]:


paragraph = "A young farm boy, who dreams of adventure, lives in a galaxy torn by rebellion and war. He is pushed into the conflict after his aunt and uncle are killed by the Empire for the droids he possesses. After joining a smuggler for cheap transportation, the boy and his mentor are captured by the Empire on their way to rescue a princess and, in the ensuing struggle, the mentor sacrifices himself. The boy and the smuggler save the princess and think they have escaped, only to learn the Empire has followed them to the Rebel base, intending to destroy the planet. Aided by his companions and the last lesson of his fallen mentor, the boy must exploit the hidden weakness of the Empire’s destructive weapon to preserve the Rebellion."

def goBtn_part2():
    goBtn("Q5", default_action, paragraph)

# goBtn_part2()


# ## Go Button (Part 3)

# In[9]:


def goBtn_part3():
    total = 0
    print("e's in the screenplays")
    print("-----------------------------------------------")
    # Creates a list of files in the directory.
    for file in os.listdir("screenplays"):
        # Open each Text file
        
        with open("screenplays\\" + file) as f:
            # Counts total letters in each text file
            letters = Counter(letter for line in f 
                      for letter in line.lower() 
                      if letter in ascii_lowercase)
            
            # Create a readable name for each movie.
            if file == "airbud_1997.txt":
                screenplay = "AirBud"
            elif file == "goofymovie.txt":
                screenplay = "Goofy Movie"
            elif file == "spiderman3.txt":
                screenplay = "Spider-Man 3"
            elif file == "tmnt3.txt":
                screenplay = "Teenage Mutant Ninja Turtles III"
            elif file == "sleeplessinseattle.txt":
                screenplay = "Sleepless in Seattle"
            elif file == "pokemon.txt":
                screenplay = "Pokémon: The First Movie"
            elif file == "kingkong.txt":
                screenplay = "King Kong"
            elif file == "casablanca.txt":
                screenplay = "Casablanca"
            total+=letters["e"]
            # Print Results
            print("There are", letters["e"], "e's in the", screenplay, "screenplay.")
    print("-----------------------------------------------")
    print("There are", total, "letter e's in the screenplays.")
            
# goBtn_part3()


# ## Go Button (Part 4)

# In[10]:


def goBtn_part4_1():
    goBtn("Q2", default_action,action="")
    
# goBtn_part4_1()


# In[11]:


def goBtn_part5():
    print("Zero e's found..")
    
# goBtn_part4()


# ## Next Buttons

# In[12]:


def nextPage(url):
    # This can be a jupyter notebook, but the host and port need to be referenced in the path
    webbrowser.open(url, new=0, autoraise=True)


# ### Gateway Lessons

# In[98]:


def cyberLiteracy():
    # Honestly is a function to hide the passing in of an argument to make it look cleaner
    # This one references a gateway lesson notebook
    button_1 = Button(description="Next", layout=Layout(width='350px', height='120px', margin='5% 25% 5% 25%'))
    button_1.style.button_color = '#59b4e2'
    
    display(button_1)
    
    def on_clicked(b):
        nextPage('http://localhost:8890/notebooks/Gateway_Lesson/Lesson%20Notebooks/Cyber%20Literacy%20for%20GIScience.ipynb')
    
    button_1.on_click(on_clicked)

# cyberLiteracy()


# In[97]:


def theSearch():
    # Gateway search page
    button_1 = Button(description="Next", layout=Layout(width='350px', height='120px', margin='5% 25% 5% 25%'))
    button_1.style.button_color = '#59b4e2'
    
    display(button_1)
    
    def on_clicked(b):
        nextPage('http://localhost:8890/notebooks/Gateway_Lesson/Lesson%20Notebooks/The%20Search.ipynb')
    
    button_1.on_click(on_clicked)
    
# theSearch()


# In[17]:


def spatialThinking():
    # Next Lesson (Spatial Thinking)
    nextPage('http://localhost:8890/notebooks/Gateway_Lesson/Lesson%20Notebooks/CI%20In%20Life.ipynb') 


# In[19]:


def bigData():
    # Next Lesson (Big Data)
    nextPage('http://localhost:8890/notebooks/Gateway_Lesson/Lesson%20Notebooks/CI%20In%20Life.ipynb')


# In[84]:


def nextLesson(x,y):
    # Button Instances
    button_1 = Button(description=x, layout=Layout(width='350px', height='100px', margin='100px 150px 100px 80px'))
    button_2 = Button(description=y, layout=Layout(width='350px', height='100px', margin='100px 150px 100px 80px'))
    
    # Change the button color
    button_1.style.button_color = '#59b4e2'
    button_2.style.button_color = '#59b4e2'

    # Display boxes for the buttons
    left_box = VBox([button_1])
    right_box = VBox([button_2])
    display(HBox([left_box, right_box]))

    
    def spatial_thinking(b):
        nextPage('https://sites.google.com/umn.edu/hourofci/home')
#         spatialThinking()


    def big_data(b):
        nextPage('https://sites.google.com/umn.edu/hourofci/home')
#         bigData()
        
    # Fix the functionality of this function. Try to make it useful for every single tutorial.. 
        


    button_1.on_click(spatial_thinking)
    button_2.on_click(big_data)

# nextLesson('Spatial Thinking', 'Big Data')


# # Jupyter Widgets

# This section gives an overview of the importable widgets that include the logging and validation functions for Hour of CI.

# ## Widget Construction Breakdown
# 
# <br>

# This is the basic break down of how the widgets are constructed. These comments will hopefully illustrate the break down of the widget wrapper consturction.

# In[12]:


# Def of some function
    # Widget instance with specified parameters
    # Display function
    # Def of another function to monitor value changes
    # Observe function
    # Button


# ## IntSlider

# In[70]:


def IntSlider(question):
    start_time = time.time()
    int_range = widgets.IntSlider()
    display(int_range)
    value = 10
    
    
    def on_value_change(change):
        
        # Appends the answer to the Answer_Dict to push over to the database.
        Answer_Dict[question].append(change["new"])


    int_range.observe(on_value_change, names='value')
    
    # Button Evaluator with arguments (desired_answer, frmt) | Fmrt is the format to evaluate like single item, list, dict, etc
    button(question, start_time)  

# IntSlider(question = "Q2")


# ## Text

# In[14]:


def Text(question, placeholder = 'Type Something', description = "Question"):
    start_time = time.time()
    
    # Widget State
    text = widgets.Text(
        value='',
        placeholder= placeholder,
        description = description,
        disabled=False
    )
    display(text)

    
    # Python Observer
    def on_value_change(change):
        
        # Appends to the dictionary answer
        Answer_Dict[question].append(change["new"])
    

            
    # Call the observer function
    text.observe(on_value_change, names='value')
    
    # Button Evaluator with arguments (desired_answer, frmt) | Fmrt is the format to evaluate like single item, list, dict, etc
    button(question, start_time)    
        
    
# Text(question = "Q2")


# ## FloatSlider

# In[15]:


def FloatSlider(question):
    start_time = time.time()
    float_slider_widget = widgets.FloatSlider(
                                                value=5.0,
                                                min=0,
                                                max=10.0,
                                                step=0.1,
                                                description='Slider:',
                                                disabled=False,
                                                continuous_update=False,
                                                orientation='horizontal',
                                                readout=True,
                                                readout_format='.1f',
                                            )
    
    # Display widget
    display(float_slider_widget)
    

    def on_value_change(change): 
        # Appends to the dictionary answer
        Answer_Dict[question].append(change["new"])

    float_slider_widget.observe(on_value_change, names='value')
    
    # Button Evaluator with arguments (desired_answer, frmt) | Fmrt is the format to evaluate like single item, list, dict, etc
    button(question, start_time)  

# FloatSlider("Q2")


# ## FloatLogSlider

# In[16]:


def FloatLogSlider(question):
    start_time = time.time()
    float_log_slider_widget = widgets.FloatLogSlider(
                                                        value=5,
                                                        base=10,
                                                        min=-10, # max exponent of base
                                                        max=10, # min exponent of base
                                                        step=0.2, # exponent step
                                                        description='Log Slider'
                                                    )
    
    
    display(float_log_slider_widget)
    

    def on_value_change(change):
        # Appends to the dictionary answer
        Answer_Dict[question].append(change["new"])

    float_log_slider_widget.observe(on_value_change, names='value')
    
    # Button Evaluator with arguments (desired_answer, frmt) | Fmrt is the format to evaluate like single item, list, dict, etc
    button(question, start_time)

# FloatLogSlider("Q1")


# ## BoundedIntText

# In[17]:


def BoundedIntText(question):
    start_time = time.time()
    widget = widgets.BoundedIntText(
                            value=5,
                            min=0,
                            max=1000,
                            step=1,
                            description='Text:',
                            disabled=False
                          )
    display(widget)
    
    def on_value_change(change):
        # Appends to the dictionary answer
        Answer_Dict[question].append(change["new"])
        
    widget.observe(on_value_change, names='value')
    
    button(question, start_time)

# BoundedIntText("Q2", start_time=time.time())


# ## BoundedFloatText

# In[18]:


def BoundedFloatText(question):
    start_time = time.time()
    widget = widgets.BoundedFloatText(
                            value=5.0,
                            min=0,
                            max=15.0,
                            step=1,
                            description='Text:',
                            disabled=False
                          )
    display(widget)
    
    def on_value_change(change):
        # Appends to the dictionary answer
        Answer_Dict[question].append(change["new"])
        
    widget.observe(on_value_change, names='value')
    
    button(question, start_time)

# BoundedFloatText("Q1")


# ## Dropdown

# In[19]:


def Dropdown(question, options=['...','1', '2', '3','4', '5', '6', '7', '8', '9', '10']):
    start_time = time.time()
    widget =  widgets.Dropdown(
                                options=options,
                                value= options[0],
                                description='Answer: ',
                                disabled=False,
                            )
    display(widget)
    
    def on_value_change(change):
        # Appends to the dictionary answer
        Answer_Dict[question].append(change["new"])
        
    widget.observe(on_value_change, names='value')
    
    button(question, start_time)

# Dropdown("Q1")


# ## Radio Buttons

# In[20]:


def RadioButtons(question, options = ['1', '2', '3','4', '5']):
    start_time = time.time()
    widget =  widgets.RadioButtons(
                                    options=options,
                                    description='Answer:',
                                    disabled=False
                                )
    display(widget)
    
    def on_value_change(change):
        # Appends to the dictionary answer
        Answer_Dict[question].append(change["new"])
        
    widget.observe(on_value_change, names='value')
    
    button(question, start_time)

# RadioButtons("Q1", start_time=time.time())


# In[21]:


def RBtn_1():
    option = [
        'Online payment system.',
        'Locating the nearest coffee shop with a mobile app.',
        "Logging onto Netflix with your parent's account.",
        'Watching a movie on Netflix.',
        'Browsing social media during the movie.',
        'Giving someone directions in person.'
    ]
    st_time = time.time()
    RadioButtons("Q1", options=option)

    
# RBtn_1()


# In[22]:


def RBtn_2():
    option = [
        'Video conference call through your computer.',
        'Ordering food via mobile app.',
        'Listening to your favorite music through a mobile app.',
        'Completing an online tutorial successfully.',
        'Using an ATM.',
        'Paying for a meal with cash.'
        
    ]
    RadioButtons("Q2", options=option)

    
# RBtn_2()


# In[23]:


def RBtn_3():
    option = [
        'Purchasing a train ticket online',
        'Purchasing a city bus ticket in person',
        'Updating software on your computer',
        'Purchasing groceries with a credit card',
        
    ]
    RadioButtons("Q3", options=option)

    
# RBtn_3()


# ## Select

# In[24]:


def Select(question, options = ['Linux', 'Windows', 'OSX']):
    start_time = time.time()
    widget =  widgets.Select( 
                                options=options,
                                value='OSX',
                                # rows=10,
                                description='OS:',
                                disabled=False
                            )
    display(widget)
    
    def on_value_change(change):
        # Appends to the dictionary answer
        Answer_Dict[question].append(change["new"])
        
    widget.observe(on_value_change, names='value')
    
    button(question, start_time)

# Select("Q1")


# ## Toggle Buttons

# In[22]:


def ToggleButtons(question, options = ['Slow', 'Regular', 'Fast']):
    start_time = time.time()
    widget =  widgets.ToggleButtons(
                                    options=options,
                                    description='Speed:',
                                    disabled=False,
                                    button_style='', # 'success', 'info', 'warning', 'danger' or ''
                                    tooltips=['Description of slow', 'Description of regular', 'Description of fast'],
                                #     icons=['check'] * 3
                                )
    display(widget)
    
    def on_value_change(change):
        # Appends to the dictionary answer
        Answer_Dict[question].append(change["new"])
        
    widget.observe(on_value_change, names='value')
    
    button(question, start_time)

# ToggleButtons("Q1")


# ## Select Multiple

# In[26]:


def SelectMultiple(question, options = ['1', '2', '3','4', '5']):
    start_time = time.time()
    widget =  widgets.SelectMultiple(
                                        options=options,
                                        value=['1'],
                                        description='Answers',
                                        disabled=False
                                    )
    display(widget)
    
    def on_value_change(change):
        # Appends to the dictionary answer
        Answer_Dict[question].append(change["new"])
        
    widget.observe(on_value_change, names='value')
    
    button(question, start_time)

# SelectMultiple("Q1")


# ## Plot Example for Eric
# 

# In[27]:


def graph_widget(question):
    x = np.linspace(0, 2 * np.pi)
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    line, = ax.plot(x, np.sin(x))

    def update(w = 1.0):
        # Appends to the dictionary answer
        Answer_Dict[question].append(w)
        line.set_ydata(np.sin(w * x))
        fig.canvas.draw()

    # Button Evaluator with arguments (desired_answer, frmt) | Fmrt is the format to evaluate like single item, list, dict, etc
    button(question)    

    interact(update);
    
# graph_function(question='Q1')

