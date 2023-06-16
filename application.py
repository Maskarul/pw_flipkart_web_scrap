from flask import Flask, request, jsonify, render_template
from flask_cors import CORS,cross_origin
import requests
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen
import pymongo
import logging

logging.basicConfig(filename="scrapper.log", level=logging.INFO)

application = Flask(__name__)

@application.route("/", methods = ['GET'])
@cross_origin()
def homepage():
    return render_template("index.html")


@application.route('/review', methods = ['GET', 'POST'])
@cross_origin()
def scrapper():
    if request.method == 'POST':    #making sure that the POST method is used to send the data

        try:

            # we are taking the data from the index.html form under id 'content' and getting by which
            # we will have to search in the flipkart.com and assigning it to 'search_string'
            # Before assigning, we we replacing all the spaces in the string present to avoid problem
            # in the contanation in the next line to create the complete search URL(flip_url)

            search_string = request.form['content'].replace(" ", "")
            flip_url = "https://www.flipkart.com/search?q=" + search_string

            # flip_html_dump will contain the whole html dump from the search page.

            flip_html_dump_unreadable = urlopen(flip_url)
            flip_html_dump = flip_html_dump_unreadable.read()
            flip_html_dump_unreadable.close()

            # creating soup object using beautiful soup so that html can be presented in a little 
            # radable format. 

            flip_html_soup = bs(flip_html_dump, "html.parser")

            # "flip_product_link_boxes" is a list of all the product html div element with class with id 
            # "_1AtVbE col-12-12". This div element contains the link to the all the listed products
            # in the flipkart page after the search.

            flip_product_link_boxes = flip_html_soup.findAll("div", {"class": "_1AtVbE col-12-12"})

            # deleting the first 3 div element caue they do not contain the product links.
            # so in our cases they are useless

            del flip_product_link_boxes[0:3]

            product1_box = flip_product_link_boxes[0]

            # so fetching the link from the "href" attribute under 3 level "div" element and a "a"
            # element down and concatanating with flipkart home link to create the link for the first 
            # product in the search page.

            product1_link = "https://www.flipkart.com" + product1_box.div.div.div.a['href']

            product1_html_dump = requests.get(product1_link)
            product1_html_dump.encoding = 'utf-8'
            product1_html_soup = bs(product1_html_dump.text, "html.parser")
            
            # by the below findAll() function, we are going into the html contain of the page of product
            # and trying to find the div element with the class id with "_16PBlm". And this particular
            # element are the comment boxes in the page. So, "product1_commentbox_list" contains
            # all the comment boxes in the product1 page. 

            # each commment box contain the rating, name of the customer who submitted the review,
            # the review marks, and the details review.

            product1_commentbox_list = product1_html_soup.findAll("div", {"class": "_16PBlm"})

            # creating a .csv file to log the data

            filename = search_string + ".csv"
            fw = open(filename, "w")
            headers = "Product, Customer Name, Rating, Heading, Comment \n"
            fw.write(headers)

            # empty review list

            reviews = []

            for product1_comment in product1_commentbox_list:
                try:
                    # here product1_comment.div.div.findAll() returns a list of all the <p> elements
                    # with the class id "_2sc7ZR _2V5EHH". So, by adding [0], we are choosing
                    # the first element of the list and .text returning the text area of the <p>
                    # element

                    name = product1_comment.div.div.findAll("p", {"class": "_2sc7ZR _2V5EHH"})[0].text
                
                except:
                    name = "No Name"
                
                try:
                    rating = product1_comment.div.div.div.div.text
                
                except:
                    rating = "No Rating"

                try:
                    commenthead = product1_comment.div.div.div.p.text

                except:
                    commenthead = "No Comment Heading"

                try:
                    # same logic here itself. findALL() returning a list of <div> element with class ""
                    # which is present under commentbox.div.div
                    comtag = product1_comment.div.div.find_all('div', {'class': ''})
                    #custComment.encode(encoding='utf-8')
                    custComment = comtag[0].div.text
                except Exception as e:
                    print("Exception while creating dictionary: ",e)

                # creating a dictionary with all the fetched details related to the comment box
                # which we will show in the result.html page
                    
                mydict = {"Product": search_string, "Name": name, "Rating" : rating, 
                "Comment Head": commenthead, "Comment" : custComment}

                # adding all the comment box details for each comments in the review list so that 
                # we can add 

                reviews.append(mydict)

            # In the below block, we will put the collected data into the mongodb.
            # connection cusor "client" has been created, then "review_scrap" database created, then
            # under it, "review_scrap_data" collection created. 

            client = pymongo.MongoClient("mongodb+srv://maskarulanam:mongomak987@cluster0.7ul5sdw.mongodb.net/?retryWrites=true&w=majority")
            db = client['review_scrap']
            review_col = db['review_scrap_data']

            # insert_many() function used to insert the "reviews" which is a list of dictionary
            # where each dictionary will have details of a particular product. 

            review_col.insert_many(reviews)

            return render_template('results.html', reviews=reviews[0:(len(reviews)-1)])

        except Exception as e:
            print('The Exception message is: ',e)
            return 'something is wrong'
    # return render_template('results.html')

    else:
        return render_template('index.html')

if __name__=="__main__":
    application.run(host="0.0.0.0")



            











        









        


