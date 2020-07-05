from flask import Flask, render_template, redirect
from flask_pymongo import PyMongo
import scrape_mars
import pymongo
from config import username, password
from bs4 import BeautifulSoup as bs
import re
import pandas as pd
from splinter import Browser
from splinter.exceptions import ElementDoesNotExist
import time


#===============================================================================================
#==========================================Scrape function======================================
#===============================================================================================
# initialize a browser
def init_browser():
    """open a chrome browser
    """
    executable_path = {'executable_path': '/usr/local/bin/chromedriver'}

    return Browser('chrome', **executable_path, headless=False)

# scrape data
def scrape():
    """scrape data from website and save into a dict
    """
    # define websites we want to scrape
    news_url = "https://mars.nasa.gov/news/"
    image_url = "https://www.jpl.nasa.gov/spaceimages/?search=&category=Mars"
    weather_url = "https://twitter.com/marswxreport?lang=en"
    fact_url = "https://space-facts.com/mars/"
    hemisphere_urls = "https://astrogeology.usgs.gov/search/results?q=hemisphere+enhanced&k1=target&v1=Mars"

    #=================================== scrape latest news =================================
    # open default browser
    browser = init_browser()
    browser.visit(news_url)
    time.sleep(1.5)
    # create soup object
    html = browser.html
    soup = bs(html, "html5lib")
    
    # -------------------------
    news_title = soup.find("ul","item_list").find_all("div","content_title")[0].text
    news_p = soup.find("ul","item_list").find_all("div","article_teaser_body")[0].text

    #================================== scrape images =======================================
    browser.visit(image_url)
    time.sleep(1)
    # create soup object
    html = browser.html
    soup = bs(html, "html5lib")
    
    # -------------------------
    image_section = soup.find("section","grid_gallery").find_all("li","slide")[0]
    part_url = "https://www.jpl.nasa.gov"
    try:
        featured_image = image_section.find('img', {'src':re.compile('.jpg')})["src"]
        featured_image = part_url+featured_image
    except: 
        print("error in scraping featured image")

    #================================== scrape temperature ==================================
    browser.visit(weather_url)
    time.sleep(1.5)
    # create soup object
    html = browser.html
    soup = bs(html, "html5lib")
    
    # -------------------------
    twitters = soup.find_all("div","css-1dbjc4n")
    mars_weather = []
    for twit in twitters:
        try:
            if twit.span:
                tweet = twit.find("span","css-901oao").text
                if tweet[0:11] == "InSight sol" and (tweet not in mars_weather) :
                    mars_weather.append(tweet)
                    break
        except:
            None
    
    #================================== scrape fact table =================================
    fact_table = pd.read_html(fact_url)[0]
    fact_table = fact_table.rename(columns = {0:"Metric",1:"Value"})
    fact_table_html = fact_table.to_html(index = False)

    #================================== scrape Mars Hemispheres ==============================
    browser.visit(hemisphere_urls)
    time.sleep(1)

    # scrape soup object
    html = browser.html
    soup = bs(html, "html5lib")
    
    # -------------------------
    titles = soup.find_all("div","description")
    
    # -------------------------
    title_list = []
    image_url = []
    hemisphere_image_urls =[]
    for title in titles:
        try:
            title_list.append(title.h3.text)

            # click the title link
            browser.links.find_by_partial_text(title.h3.text).click()

            # scrape image url
            new_html = browser.html
            new_soup = bs(new_html, "html5lib")
            # try to get image url
            try:
                img_url = new_soup.find("div","downloads").find("li").a["href"]
                image_url.append(img_url)
            except:
                print("----Image error----")

            # go back 
            browser.back()


        except:
            print("----error----")
            
    # -------------------------
    for i in range(len(title_list)):
        dict_list = {"title":title_list[i],"img_url":image_url[i]}
        hemisphere_image_urls.append(dict_list)

    
    #============================== store scraped info to a dict ============================
        summary_dict = dict(news_title = news_title,
                            news_p = news_p,
                            featured_image = featured_image,
                            mars_weather =mars_weather[0],
                            fact_table = fact_table_html,
                            hemisphere_image_urls = hemisphere_image_urls)

    browser.quit()

    return summary_dict
#===============================================================================================
#===============================================================================================
#===============================================================================================
#===============================================================================================




app = Flask(__name__)

# set up mongo connection and define document
# mongo = PyMongo(app, uri="mongodb://localhost:27017/mars_db")
conn = f"mongodb+srv://{username}:{password}@cluster0.s7ibi.mongodb.net/mars_db?retryWrites=true&w=majority"
client = pymongo.MongoClient(conn)
db = client.mars_db

@app.route("/")
def home():
    mars_data = db.mars.find_one()
    return render_template("index.html", mars  = mars_data)


@app.route("/scrape")
def scraper():
    mars = db.mars
    mars_data = scrape()
    mars.update({},mars_data, upsert = True)
    return redirect("/",code=302)

@app.route("/images")
def images():
    mars_data = db.mars.find_one()
    return render_template("image.html", mars  = mars_data)



if __name__ == "__main__":
    app.run(debug=True)