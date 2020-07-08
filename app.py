from flask import Flask, render_template, redirect
from flask_pymongo import PyMongo
import pymongo
from config import username, password
import scrape_mars


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
    mars_data = scrape_mars.scrape()
    mars.update({},mars_data, upsert = True)
    return redirect("/",code=302)

@app.route("/images")
def images():
    mars_data = db.mars.find_one()
    return render_template("image.html", mars  = mars_data)



if __name__ == "__main__":
    app.run(debug=True)