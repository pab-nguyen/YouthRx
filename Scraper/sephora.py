from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from fake_useragent import UserAgent

import time
import random
import re
import os
import csv
import math

### This script is for scraping the sephora product pages - getting
### information on each product:

### name & brand: the name and brand of the product

### The family/genus/species of the product,
### representing the hierarchy of categorization: "family" is the  main
### category (Makeup, Hair, Skincare, Men, or  Fragrance), the "genus" is the
### category within the family, and the "species" is the subcategory within
### the genus.

### price: The full price (USD) of the product, for its default size and/or
### color
### weight & volume: the weight (oz) and volume (mL) of the product, for its
### default size

### num_loves: the number of "loves" the product has received

### num_reviews: the number of reviews the product has
### if the number of reviews is greater than 1000, the nearest floor 100 is
### given at the top of the page. If the number of reviews is greater than
### 10,000, it is given as the nearest floor 1000. For example, if the actual
### number of reviews is 1200, the top of the page will say "1.2K". If the
### number of reviews is 21897, the top of the page will say "21K".
### Similarly, products with millions of reviews were rounded to the nearest
### 10th of a million

### ave_rating: the average rating of the product
### at the top of the page, the value given for the ave_rating is rounded to
### the nearest 0.5. The highest rating is 5 (5 stars)

### details: all the text under the "details" tab
### ingredients: all the text under the "ingredients" tab

##############################################################################
## Setting up the Selenium webdriver and also grabbing the product urls
## which are the result of get_product_urls.py and the Scrapy spider
## and get_chemical_urls.py

ua = UserAgent()
userAgent = ua.random

opts = Options()
user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36'
opts.add_argument("--disable-notifications")
opts.add_argument(f'user-agent={userAgent}')
# opts.add_argument("--headless")
#opts.add_argument('--disable-gpu')
#opts.add_argument('--no-sandbox')
#opts.add_experimental_option("excludeSwitches", ["enable-automation"])
#opts.add_experimental_option('useAutomationExtension', False)

driver = webdriver.Chrome(options=opts)

driver.delete_all_cookies()

product_urls = open('sephora_product_urls.txt', 'r').readlines()
# product_urls = open('../sephora_chemical_urls.txt', 'r').readlines()

##############################################################################
## This script is designed so that should the program fail for whatever
## reason -- usually because of accidentally quitting the browser window or
## the browser crashing, or a loss of connection, etc -- the current data will
## save so that the driver can be restarted where it left off.

## If the script has not been run before, a "products.csv" file will be
## created with the data written to it. If the script has been run before but
## quit unexpectedly, the index of where it left off will be saved in
## "index.txt", and upon rerunning the script, the products.csv file will be
## openned and appended to, starting from the index in index.txt.

columns = ['name', 'brand', 'family', 'genus', 'species', 'price','ave_rating', 'volume', 'num_loves', 'num_reviews', 'weight', 'details','ingredients','url']
## for writing the first row of the csv using DictWriter
column_dict = dict(zip(columns, columns))

if os.path.isfile(f'index.txt') and os.path.isfile(f'products.csv'):
    index = int(open('index.txt').read())
    csv_file = open(f'products.csv', 'a', encoding='utf-8', newline='')
    writer = csv.DictWriter(csv_file, fieldnames=columns)
    product_urls = product_urls[index:]
else:
    index = 0
    csv_file = open(f'products.csv', 'w', encoding='utf-8', newline='')
    writer = csv.DictWriter(csv_file, fieldnames=columns)
    writer.writerow(column_dict)

##############################################################################

## I chose not to scrape things that were not chemical based (do not have
## ingredients lists) and I also decided not to do anything travel-size or
## mini size to avoid redundant products and skewed price ranges
unwanted_products = ['Mini Size', 'Value & Gift Sets', 'Facial Rollers',
                     'Brushes & Applicators', 'False Eyelashes', 'Rollerballs & Travel Size',
                     'Candles & Home Scents', 'Beauty Supplements', 'High Tech Tools',
                     'Lip Sets', 'Face Sets', 'Eye Sets', 'Makeup Bags & Travel Accessories',
                     'Tweezers & Eyebrow Tools', 'Blotting Papers', 'Hair Tools']

## The xpath for the "continue shopping" button on the pop-up modal dialog
continue_shopping_xpath = '//button[@aria-label="Continue shopping"]'
try:
    for i, url in enumerate(product_urls):
        # keep track of how many pages have been scraped
        print(i + index)
        product_dict = {}
        driver.implicitly_wait(10)
        driver.get(url)
        if i == 0:
            try:
                button = driver.find_element_by_xpath(continue_shopping_xpath)
                button.click()
            except:
                time.sleep(1)
        # product_type is the text containing family/genus/species
        product_type = driver.find_elements_by_xpath('//nav[@aria-label="Br' + \
                                                     'eadcrumbs"]//a')
        # if len(product_type) <  3, it is gift card or gift set of some sort
        print("1")
        driver.save_screenshot("screenshot.png")

        if len(product_type) < 3: continue

        print("2")
        # separate the family, genus and species
        product_type = [val.text for val in product_type]
        # remove products that are in the unwanted_products categories
        if (product_type[1] in unwanted_products) or \
                (product_type[2] in unwanted_products):
            continue
        print("3")
        # get the product name and brand, which is usually up high on the
        # page, but sometimes is more in the center of the page
        product = driver.find_elements_by_xpath('//span[@data-at="product_name"]')
        brand = driver.find_elements_by_xpath('//a[@data-at="brand_name"]')
        if len(product) == 0:
            product = driver.find_elements_by_xpath('//h1[@data-comp="Displ' + \
                                                    'ayName Flex Box"]//span')

        ## add the various values to the product dictionary
        product_dict['url'] = driver.current_url
        product_dict['family'] = product_type[0]
        product_dict['genus'] = product_type[1]
        product_dict['species'] = product_type[2]
        product_dict['name'] = product[0].text
        product_dict['brand'] = brand[0].text
        ## Likewise, the price can be found in two different locations
        product_dict['price'] = driver.find_element_by_xpath('//p[@data-comp="Price "]/span/span[1]/b').text

        ## The size of the product and item number are often listed together
        ## as "XX.XX( fl) oz/XX mL ITEM # XXXXXXXXXX"
        ## sometimes, that xpath only contains the element number, in which
        ##	case the weight & volume are in a different location. Sometimes no
        ## weight/volume are listed
        try:
            size = driver.find_element_by_xpath('//div[@data-comp="SwatchDescription "]').text
        except:
            size=''

        ## once the size variable is found, separate the weight (in oz) from
        ## the volume (in mL)
        ## the weight can also be in fluid oz, but oz and fl oz are treated
        ## the same here
        weight = re.findall("((\d+\.?\d*)( fl)? ?oz)", size)
        if weight:
            product_dict['weight'] = weight[0][1]
        volume = re.findall("(\d+) ?mL", size)
        if volume:
            product_dict['volume'] = volume[0]
        ## get the number of "loves" from the top of the page
        product_dict['num_loves'] = driver.find_element_by_xpath('//div[@data-comp="LovesCount "]/span').text
        ## the number of reviews is only listed if there are reviews
        try:
            product_dict['num_reviews'] = driver.find_element_by_xpath('//span[@data-at="number_of_reviews"]').text.split()[0]
        except:
            product_dict['num_reviews'] = '0'
        # if there are reviews, then get the average review
        if product_dict['num_reviews'] != '0':
            product_dict['ave_rating'] = driver.find_element_by_xpath('//div[@data-comp="StarRating "]').get_attribute('aria-label').split()[0]
        time.sleep(2)

        ## get ingredients and details
        try:
            driver.find_element_by_xpath('//button[@data-at="ingredients"]').click()
            product_dict['ingredients'] = driver.find_element_by_xpath('//div[@id="ingredients"]/div/div').get_attribute("innerHTML")
        except:
            pass

        try:
            driver.find_element_by_xpath('//button[@class="css-5fs8cb eanm77i0"]').click()
            product_dict['details'] = driver.find_element_by_xpath('//div[@class="css-u2scbn eanm77i0"]/div').get_attribute("innerHTML")
        except:
            pass


        ## The number of reviews written at the top of the page tends to be
        ## rounded, as described above. The average rating at the top of the
        ## page also tends to be rounded to the nearest 0.5. However, the
        ## actual average rating and number of reviews is written at the
        ## bottom of the page above the reviews. The driver will attempt to
        ## get the actual number of reviews and the actual average rating, but
        ## if the page length is atypical, the driver might not see those
        ## elements. If the driver does not see them, then it just moves on
        ## with the rounded values from the top of the page. If it does see
        ## them, then it will replace the rounded values from the top of the
        ## page with the actual values from the bottom of the page.
        ## This part of the script could maybe be written better, but in the
        ## interest of time and efficiency, I chose to move on.
        driver.execute_script("arguments[0].scrollIntoView();", driver.find_element_by_xpath('//div[@id="ratings-reviews-container"]'))

        if product_dict['num_reviews'] != '0':
            try:
                ave_rating = driver.find_element_by_xpath('//span[@class="css-1ac1x0l eanm77i0"]').get_attribute("innerHTML")
                product_dict['ave_rating'] = ave_rating

            except:
                pass
            try:
                num_reviews = driver.find_element_by_xpath('//div[contains(@data-comp,"ReviewsStats")]//span[@class="css-nv7myq eanm77i0"]').text.split()[0]
                product_dict['num_reviews'] = num_reviews
            except:
                pass
        ## write everything into the csv
        writer.writerow(product_dict)
        time.sleep(2)
        print("end")
except Exception as e:
    ## if there is an error with the page, print the url and error message so
    ## the page can be manually inspected
    print(url)
    print(e)
    ## write the index so the script knows where where it left off
    open('index.txt', 'w').write('%d' % (i + index))
    csv_file.close()
    driver.quit()
    time.sleep(5)
    quit()

driver.quit()
quit()