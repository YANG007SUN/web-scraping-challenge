from bs4 import BeautifulSoup as bs
import re
import pandas as pd
from splinter import Browser
from splinter.exceptions import ElementDoesNotExist
import time
from selenium import webdriver
import os

# initialize a browser
def init_browser():
    """open a chrome browser
    """

    chrome_options = webdriver.ChromeOptions()
    chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    return webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chrome_options)

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
    browser.get(news_url)
    time.sleep(1.5)
    # create soup object
    html = browser.page_source
    soup = bs(html, "html5lib")
    
    # -------------------------
    news_title = soup.find("ul","item_list").find_all("div","content_title")[0].text
    news_p = soup.find("ul","item_list").find_all("div","article_teaser_body")[0].text

    #================================== scrape images =======================================
    browser.get(image_url)
    time.sleep(1)
    # create soup object
    html = browser.page_source
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
    browser.get(weather_url)
    time.sleep(1.5)
    # create soup object
    html = browser.page_source
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
    browser.get(hemisphere_urls)
    time.sleep(1)

    # scrape soup object
    html = browser.page_source
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



    