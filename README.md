# Q5M2_submit
reproducibility materials Q5M2 geo-visualization

## Data pre-processing
sql.txt: a few processing steps in sql to filter inactive user and get the user's "nationality". Resulting data is exported to csv files. 
make_data.py: get country level user count and flow between countries. <br>
**Notice: networkx 1.10 is required to run the script proporly**


## Dash app
available at https://dashsamplemmmmmm.herokuapp.com/  first loading will take some time due to Heroku server status <br>
requirements.txt for installationg of libraries <br> 
app.py for the actual app <br>
**Notice: the versions of the libraries are super important**


## Flourish mash-up
available at https://gisedu.itc.utwente.nl/student/s6039677/flourish.html  <br>
flourish.html (main file containing all the flourish export div's) <br> 
data_for_flourish.py (making data ready for flourish)


## Source
Flourish: https://flourish.studio/ <br>
Dash/Plotly: https://dash.plot.ly/
