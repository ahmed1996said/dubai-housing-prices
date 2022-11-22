
# Dubai housing rental price prediction tool using 150k+ properties from Bayut.com

## 🧑🏽‍💻 Checkout the app!
You can run the app by going to this link: [http://property.ahmedmahrooqi.com/](http://property.ahmedmahrooqi.com/)

BTW, as the famous saying goes: garbage-in garbage-out. I assume that the user has a common sense (for e.g. not selecting a studio apartment with 10 bathrooms!) If you input non-sensible data, you'll get non-sensible predictions. Currently the app doesn't protect from such inputs, but I'm aiming to think about how I can do this in future versions.

## 🔎 Scraping Bayut
The script to scrape Bayut website can be found in ```scrape_bayut.py```. This script scrapes all properties listed in the given Emirate. There is supported functionality to pass in whether you want ```furnished```, ```unfurnished``` or ```all``` properties. However, in my experience, the number of ```furnished``` + ```unfurnished``` properties are not equal to ```all``` properties. Therefore, I resort to scrape ```all```. Some of the data fields that are scraped include:

- ```bedrooms```
- ```bathrooms```
- ```area```
- ```location```
- ```property_type```
- ```property_keyworks```
- ```amenities```
- ```description```


## 🧹 Data cleaning, EDA and Feature Engineering
Data cleaning, EDA and Feature Engineering is done in ```Cleaning, EDA and Feature Engineering.ipynb```. For more information, please checkout this notebook. I tried to include a step-by-step process with relevant comments so you can easily follow my thought process!

##  🏋🏽 Model Training
Model training was performed using ```sklearn``` library. The notebook ```Model.ipynb``` contains all the relevant code for Linear Regression, Lasso Regression, Random Forest and Neural Network models. Just like before, you should be able to follow my thought process by going through the notebook.

## ▶️ Web App
I used  [Flask](https://flask.palletsprojects.com/) to develop the App, and [Bootstrap](https://getbootstrap.com/) for HTML elements and styling. The app is hosted on [Heroku](https://www.heroku.com/).

## ⚠️ Disclaimer
This tool is developed solely for educational purposes and should not be taken as professional advice for property pricing purposes. I strongly discourage you to make any purchase or price-setting decisions based on this tool.



## ❓ Questions, comments, feedback?
Please create a GitHub Issue and I'll get back to you ASAP!
