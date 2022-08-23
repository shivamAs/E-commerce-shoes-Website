import json
import requests
from random import randint
import numpy as np

total = 50 #initially random number just to start loop
offset= 0

iteminfo = []
allsizes = ["38", "39", "40", "41", "42", "43", "44", "45"]

categoryset = {}
brandset = {}


allowed_brands = [ "Topper", "Fila", "Adidas", "Reebok", "Puma", "Isabella", "Savage", "Footy", "New Balance", "John Foos", "Nazarena", "Rave", "Other" ]
allowed_brands_lower = [ "topper", "fila", "adidas", "reebok", "puma", "isabella", "savage", "footy", "new balance", "john foos", "nazarena", "rave", "other" ]
topper_cap = 40
other_cap = 40

def add_category(item, cat):
    item['category'] = cat  
    if (cat in categoryset):
        categoryset[cat] = categoryset[cat] + 1
    else: 
        categoryset[cat] = 1
        
def add_brand(item, brand):
    item['brand'] = brand
    
    
topper_count = 0
other_count = 0
while offset < total:
    r = requests.get('https://api.mercadolibre.com/sites/MLA/search?seller_id=257128833&category=MLA22389&offset='+str(offset))
    data = r.json()
    total = data['paging']['total']
    print(str(offset) + " of " + str(total))
    offset = offset + len(data['results'])

    for item in data['results']:
        newitem = {}
        newitem['title'] = item['title']
        newitem['price'] = item['price']
        newitem['stock'] = randint(5, 50)
        itemreq = requests.get('https://api.mercadolibre.com/items/'+item['id']+'?attributes=attributes,pictures')
        itemattributes = itemreq.json()
        for attr in itemattributes['attributes']:
            if attr['id'] == 'BRAND':
                add_brand(newitem, attr['value_name'])
            if attr['id'] == 'STYLE': 
                add_category(newitem, attr['value_name'])
                                    
                
                
        #add fields if not present        
        if 'category' not in newitem:
            add_category(newitem, "Other")
        if 'brand' not in newitem:
            add_brand(newitem, "Other")            
        
        #normalize the string
        found = False
        for index, item in enumerate(allowed_brands_lower):
            if (item == newitem["brand"].lower()):
                newitem["brand"] = allowed_brands[index]
                found = True
                break               
        if not found:
            newitem["brand"] = "Other"
                        
        #check for cap limits               
        shouldadd = True        
        if (newitem["brand"] == "Other"):
            other_count = other_count + 1
            if (other_count > other_cap):
                shouldadd = False
        if (newitem["brand"] == "Topper"):
            topper_count = topper_count + 1 
            if (topper_count > topper_cap):
                shouldadd = False
        
        
                
        if (shouldadd):
            #log stats
            if (newitem["brand"] in brandset):
                brandset[newitem["brand"]] = brandset[newitem["brand"]] + 1
            else: 
                brandset[newitem["brand"]] = 1
                
            #get picture and download
            picture_id = itemattributes['pictures'][0]['id']
            picture_name = picture_id
            picrequest = requests.get('https://api.mercadolibre.com/pictures/' + picture_id)
            picdata = picrequest.json()
            for pic in picdata['variations']:
                if pic['size'] == '400x400':
                    picture_url = pic['url']
                    break           
                            
            
            img_data = requests.get(picture_url).content
            with open(picture_name + '.jpg', 'wb') as handler:
                handler.write(img_data)
                
            newitem['picture'] = picture_name
            
            #add some random sizes   
            newitem['sizes'] = np.random.choice(allsizes, randint(1,8), False)
            
            #append item
            iteminfo.append(newitem)            

        
        
print("////////////// Completado /////////////////////")
print("---Categories---")
for a in categoryset:
    print(a, ": ", categoryset[a])
print("---Brands---")
for b in brandset:
    print(b, ": ", brandset[b])

        
import pymysql

db = pymysql.connect(host='localhost',user='root',password='nico',database='eshop')

cursor = db.cursor()

for article in iteminfo:
    cursor.execute("INSERT INTO `article` (`title`, `stock`, `price`, `picture`) VALUES (%s, %s, %s, %s)", (article['title'], str(article['stock']), str(article['price']), article['picture']))
    articleid = cursor.lastrowid
    cursor.execute("INSERT INTO `brand` (`name`, `article_id`) VALUES (%s, %s)", (article['brand'], articleid))
    cursor.execute("INSERT INTO `category` (`name`, `article_id`) VALUES (%s, %s)", (article['category'], articleid))
    for size in article['sizes']:
        cursor.execute("INSERT INTO `size` (`value`, `article_id`) VALUES (%s, %s)", (size, articleid))

db.close()