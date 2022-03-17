# Wrangling OpenStreetMap Data

## Chicago, IL, United States

<img src="MyChicago.jpg" align='left' width="90%"/>

<br clear="all" />


"**The Windy City**," "**Second City**," "**City of Big Shoulders**" are some of the monikers describing Chicago.  It is the largest American city in the midwest and home to **2.7 million** people as of the **2020 census**. It has been my home for more than 20 years, and I love living in this city.  Chicago has a lot to offer, from theaters, bars, popular sports team, restaurants, outdoor activities, and many more. In addition, it is on the southwest corner of **Lake Michigan**, which makes living in this city more fun than many other cities in America, especially during summertime.

### Content:
This project is an exploratory data analysis as part of the **Udacity Data Analyst Nanodegree** through **Western Governors University**. I will be using the XML dataset for Chicago that I have extracted from OpenStreetMap https://www.openstreetmap.org/relation/122604. OpenStreetMap is a collaborative project attempting to create geographic map of the world. 

I am using **Jupyter Notebook** and writing the codes in **Python**. This project calls for this dataset to be audited, cleaned, convert to **CSV** and uploaded to a database(SQL).  Once uploaded in a database, I will write SQL statements to explore the dataset and discover some fun facts about Chicago. 


```python
# OSM Chicago XML file extract

import xml.etree.ElementTree as ET
import pprint
from collections import defaultdict
import codecs
import csv
import cerberus
import re
import sqlite3
import schema

OSM_FILE = "chicago.osm"
```

**Count of nodes and ways**


```python
def count_tags(filename):
    """Count top level tags"""
    tag_count = {}
    osm_file = open(filename, "r", encoding="utf8")
    for each, elem in ET.iterparse(OSM_FILE):
        if elem.tag in tag_count:
            tag_count[elem.tag] += 1
        else:
            tag_count[elem.tag] = 1
    return tag_count

sample_tags = count_tags(OSM_FILE)
sample_tags
```




    {'note': 1,
     'meta': 1,
     'bounds': 1,
     'tag': 357231,
     'node': 338481,
     'nd': 446712,
     'way': 56061,
     'member': 123260,
     'relation': 1974,
     'osm': 1}



### Dataset Issues


**1.** After my initial analysis, I saw a couple of problems with the street types audit.  One had Sangamon showing as a street type, which is incorrect.  Sangamon is a street name in Chicago.  I cleaned this issue by adding the correct street type suffix for it. </br> </br>
I also found a couple of street with an abbreviated version of Avenue to Ave.  I updated them to show the full spelling instead. </br> </br>
Other than this, there was not much issue found from the Chicago Open Street Map data.

**Street Types Audit**


```python
expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road", "Park", "Access", "Market", 
            "Trail", "Parkway", "Commons", "Way", "Circle", "Trace", "Plaza", "Terrace", "Walk", "Riverwalk", "voltage=138000",
           "West", "South"]


def audit_street_type(street_types, street_name):
    """Check street type in data against expected types"""
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)

            
def audit_street(osmfile):
    OSM_FILE = open(osmfile, "r", encoding="utf8")
    street_types = defaultdict(set)
    for event, elem in ET.iterparse(OSM_FILE, events=("start",)):

        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])
    OSM_FILE.close()
    return street_types          

```


```python
st_types = audit_street(OSM_FILE)
pprint.pprint(dict(st_types))
```

    {'Ave': {'S Wentworth Ave', 'S Michigan Ave'}, 'Sangamon': {'North Sangamon'}}
    


```python
mapping = { "Ave": "Avenue",
            "Sangamon": "Sangamon Street",
           }
           
def update_type(name, mapping):
    """Replace abbreviated street type with full version using mapping"""
    name = name
    split_name = name.split(' ')
    
    for i in split_name:
        if i in mapping.keys():
            name = name.replace(i,mapping[i])

    return name

def change_name(st_types):
    """iterate through street types and use helper function update_name to update data"""
    for st_type, ways in st_types.items():
            for name in ways:
                better_name = update_type(name, mapping)
                print(name, "=>", better_name)
```

**Street Type Fix**


```python
change_name(st_types)
```

    North Sangamon => North Sangamon Street
    S Wentworth Ave => S Wentworth Avenue
    S Michigan Ave => S Michigan Avenue
    

**2.** The second issue that I found from the phone number audit was a phone number showing a forward slash "/" instead of a dash "-".  It was corrected by changinf the  " / " to " - ".

**Phone Numbers Audit**


```python
phone_re = re.compile(r'\+1[\s-]\d{3}[\s-]\d{3}[\s-]\d{4}$')

def is_phone_number(elem):
    return (elem.tag == "tag") and (elem.attrib['k'] == "contact:phone")

def find_phone_numbers(phone_number):
    """Find phone numbers that need fixing"""
    m = phone_re.search(phone_number)
    if not m:
        return phone_number


def audit_phone(file_name):
    with open(file_name, "r") as osm_file:
        num_list = []
        for event, elem in ET.iterparse(OSM_FILE):
            if is_phone_number(elem):
                contact_num = find_phone_numbers(elem.attrib['v'])
                if contact_num != None:
                    num_list.append(contact_num)
        return num_list
```


```python
num_list = audit_phone(OSM_FILE)

num_list
```




    ['(800) 680-2068', '+1/312-861-1037']



**Phone Number Fix**


```python
# change forward slash to dashes
def update_number(num):
    new_num = num.replace("/","-",3)
    return new_num

def change_numbers(num_list):
    for num in num_list:
        print(num, "=>", update_number(num))
        
change_numbers(num_list)
```

    (800) 680-2068 => (800) 680-2068
    +1/312-861-1037 => +1-312-861-1037
    

**3.**  The other two audits, postal codes and "**K**" attribute formatting scheme, did not show any issues.  Postal codes audit return with {'il':1} and was corrected to {'il':il}.  "**K**" attribute formatting scheme audit did not show any problemchars.

### Chicago OSM CSV Database Load

Loaded nodes.csv, nodes.csv, ways.csv, ways_nodes.csv, ways_tags.csv to SQLITE and it created database "chicago.db".   


```python
import sqlite3
import pprint

chicago_map = 'chicago.db'

conn = sqlite3.connect(chicago_map)

cur = conn.cursor()

cur.execute("select count(*) as count from ways;")
rows = cur.fetchall()
#rows = c.fetchone()

print(rows)

print
for row in rows:
  print()

#conn.close
```

    [(56061,)]
    
    

### Dataset Statistics 

```
chicago.osm ............. 92 MB 
chicago.db .............. 48 MB
nodes.csv  .............. 29 MB
nodes_tags.csv ..........  2 MB 
ways.csv ................  3 MB
ways_nodes.csv .......... 10 MB
ways_tags.csv ...........  9 MB
```

### Number of unique users


```python
# Number of unique users

query = "SELECT COUNT(DISTINCT(u.uid))FROM (SELECT uid FROM Nodes UNION ALL SELECT uid FROM Ways) as u;"
cur.execute(query)
rows=cur.fetchall()

pprint.pprint(rows)
```

    [(930,)]
    

### Number of Nodes


```python
# Number of nodes

query = "SELECT count(DISTINCT(id)) FROM nodes;"
cur.execute(query)
rows=cur.fetchall()

pprint.pprint(rows)
```

    [(338481,)]
    

### Number of ways


```python
# Number of ways

query = "SELECT count(DISTINCT(id)) FROM ways;"
cur.execute(query)
rows=cur.fetchall()

pprint.pprint(rows)
```

    [(56061,)]
    

**Number of Chosen Type of Nodes**


```python
# number of chosen type of nodes

query = "SELECT type , count(*) as num  FROM nodes_tags group by type order by num desc LIMIT 10;"
cur.execute(query)
rows=cur.fetchall()

pprint.pprint(rows)
```

    [('regular', 51534),
     ('addr', 9487),
     ('network', 2550),
     ('brand', 1734),
     ('seamark', 793),
     ('gnis', 563),
     ('operator', 491),
     ('payment', 260),
     ('name', 239),
     ('flag', 170)]
    

**Number of Cafes establishments** 


```python
# number of chosen type of nodes "cafe"

query = "SELECT value, count(*) FROM (select key,value from nodes_tags UNION ALL select key,value from ways_tags)  where value like '%cafe%';"
cur.execute(query)
rows=cur.fetchall()

pprint.pprint(rows)

```

    [('cafe', 470)]
    

**Top 10 Contributing Users**


```python
#Top 10 contributing users

query = "select u.user, count(*) as num from (select user from nodes UNION ALL select user from ways) as u group by user order by num desc limit 10;"
cur.execute(query)
rows=cur.fetchall()
print('Top 10 contributing users and their contribution:\n')
pprint.pprint(rows)
```

    Top 10 contributing users and their contribution:
    
    [('chicago-buildings', 176966),
     ('nickvet419', 78415),
     ('Umbugbene', 18502),
     ('Zol87', 15053),
     ('jimjoe45', 13523),
     ('lectrician1', 6201),
     ('Chicago Park District GIS', 6176),
     ('Arcureil', 6006),
     ('NE2', 5309),
     ('Steven Vance', 5281)]
    

**Top 10 types of Cuisines**


```python
# Top 20 cuisines in Chicago
query="select value,count(*) as num from (select key,value from nodes_tags UNION ALL select key,value from ways_tags) as u where u.key like '%cuisine%' group by value order by num desc limit 10;"
cur.execute(query)
rows=cur.fetchall()

pprint.pprint(rows)
```

    [('sandwich', 93),
     ('coffee_shop', 91),
     ('american', 74),
     ('pizza', 55),
     ('burger', 49),
     ('mexican', 42),
     ('chinese', 35),
     ('italian', 34),
     ('donut;coffee_shop', 31),
     ('asian', 13)]
    

**Top 15 Chicago Websites**


```python
# Top 15 website links in Chicago

query = "select u.value, count(*) as num from (select value from nodes_tags UNION ALL select value from ways_tags) as u WHERE value LIKE '%www.%' group by u.value order by num desc limit 15;"
cur.execute(query)
rows=cur.fetchall()

pprint.pprint(rows)
```

    [('http://www.railwayoperationsimulator.com/wp-content/uploads/2012/01/Chicago-Union-Station.jpg',
      29),
     ('http://www.cityofchicago.org/city/en/depts/cdot/provdrs/ped/svcs/pedway.html',
      16),
     ('http://www.navypierflyover.com/', 10),
     ('http://www.mcdonalds.com/', 9),
     ('https://www.peets.com/', 6),
     ('https://www.cornerbakerycafe.com/', 6),
     ('https://www.transitchicago.com/fares/where-to-buy/', 5),
     ('http://www.pret.com/www.pret.com/en-us/', 5),
     ('TIGER/Line® 2008 Place Shapefiles (http://www.census.gov/geo/www/tiger/)',
      5),
     ('https://www.lappetito.com/', 4),
     ('https://www.hannahsbretzel.com/', 4),
     ('https://www.argotea.com/', 4),
     ('http://www.cafecitochicago.com/', 4),
     ('https://www.stansdonuts.com/', 3),
     ('https://www.ramensan.com/', 3)]
    

**List of amenities Chicago has to offer**


```python
# Amenities

query="select value, count(*) as num from nodes_tags where key='amenity' group by value order by num desc limit 10;"
cur.execute(query)
rows=cur.fetchall()

pprint.pprint(rows)
```

    [('restaurant', 745),
     ('bench', 288),
     ('cafe', 262),
     ('bar', 246),
     ('fast_food', 239),
     ('bicycle_rental', 187),
     ('parking_entrance', 93),
     ('bank', 63),
     ('bicycle_parking', 59),
     ('drinking_water', 52)]
    

### Jewel - Osco

I normally shop at Jewel-Osco, a popular grocery store in Chicago.  I am curious to see how many Jewel-Osco stores are there within the area of Chicago I extracted in openstreetmap.


```python
# How many Jewel-Osco are there
query = "select u.value, count(*) as num from (select value from nodes_tags UNION ALL select value from ways_tags) as u WHERE value like 'Jewel-Osco%' group by u.value order by num desc;"
cur.execute(query)
rows=cur.fetchall()

pprint.pprint(rows)
```

    [('Jewel-Osco', 14)]
    

### Museums
```I like to list the different museums in Chicago that makes Chicago one of the best cities to live in around the world.  Chicago has some of the best museums to offer such as the Field museum and The Museum of Science in Industry.```


```python
query = "select u.value, count(*) as num from (select value from nodes_tags UNION ALL select value from ways_tags) as u WHERE value like '%museum%' and value not like 'en%' and value not like 'http++' group by u.value order by num desc limit 10;"
cur.execute(query)
rows=cur.fetchall()

pprint.pprint(rows)
```

    [('museum', 25),
     ('Museum Campus/11th Street', 5),
     ('Field Museum', 4),
     ('South Museum Campus Drive', 2),
     ('Museum Park Tower 1', 2),
     ('Chicago History Museum', 2),
     ('https://www.fieldmuseum.org/', 1),
     ('https://www.chicagochildrensmuseum.org/', 1),
     ('https://www.ccamuseum.org/', 1),
     ('https://www.21cmuseumhotels.com/chicago', 1)]
    

**Religion in Chicago and Christian Denomination**


```python
# Religion
query="select value, count(*) as num from (select key,value from nodes_tags UNION ALL select key,value from ways_tags) where key='religion' group by value order by num desc;"
cur.execute(query)
rows=cur.fetchall()

pprint.pprint(rows)
```

    [('christian', 91),
     ('jewish', 4),
     ('buddhist', 3),
     ('muslim', 2),
     ('ascended_master_teachings', 1)]
    


```python
# Christian Denomination
query="SELECT b.value, COUNT(*) as num FROM ways_tags JOIN (SELECT DISTINCT(id) FROM ways_tags WHERE value='place_of_worship') a ON ways_tags.id=a.id JOIN (SELECT DISTINCT(id), value FROM ways_tags WHERE key = 'denomination') b ON a.id = b.id WHERE ways_tags.key='religion' AND ways_tags.value = 'christian' GROUP BY b.value ORDER BY num DESC;"
cur.execute(query)
rows=cur.fetchall()

pprint.pprint(rows)
```

    [('roman_catholic', 14),
     ('presbyterian', 4),
     ('lutheran', 4),
     ('baptist', 4),
     ('methodist', 3),
     ('catholic', 3),
     ('anglican', 3),
     ('african_methodist_episcopal', 3),
     ('apostolic', 2),
     ('pentecostal', 1),
     ('orthodox', 1),
     ('jehovahs_witness', 1),
     ('evangelical', 1),
     ('christian science', 1),
     ('Church of God', 1),
     ('Baptist', 1)]
    

### Areas for future Data Improvement


```python
query="SELECT value FROM (SELECT key,value FROM nodes_tags UNION ALL SELECT key,value FROM ways_tags) WHERE key='phone' LIMIT 5;"
cur.execute(query)
rows=cur.fetchall()

pprint.pprint(rows)
```

    [('+1-312-372-0072',),
     ('+1 (312) 588-0064',),
     ('+1-312-236-1777',),
     ('+1-312-266-1616',),
     ('+1-312-222-1525',)]
    

The code for cleaning the phone numbers from the dataset was successful.  It successfully changed "/" (forward slash) to dashes. However, the issue is that so many phone numbers do not have the correct format. </br>
 
```+1-312-372-0072, +1-312-427-3170, (312) 920-9100, (312)-1116, 888-642-6674, +13122650580, +1 (312) 475-1390, 7732482570, 8 800 775-52-93, 8889496289, 312-642-3000, 800 DL MOODY```

### Benefits 

The Benefits of improving the phone numbers dataset would not just look clean and conform to standards, but by following the international standards for phone numbers, any developers or users extracting these phone data can leverage them on auto-dialing programs and others.   

### Anticipated Issue

There are a few variations of phone numbers, and it might be challenging to catch all of these variations and be able to 100% clean this data.


## Conclusion

As mentioned, I only took a smaller section of Chicago from OpenStreetMap, and expanding the extract would add more challenges to cleaning these data. While auditing the street type, I only found a few issues with them, which means that the community is constantly improved. Setting up standards and hoping the user community follows them can only help this project's long-term goal of creating a geographic map of the world.
