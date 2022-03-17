#!/usr/bin/env python
# coding: utf-8

# # Wrangling OpenStreetMap Data

# ## Chicago, IL, United States
# 
# <img src="MyChicago.jpg" align='left' width="90%"/>
# 
# <br clear="all" />
# 
# 
# "**The Windy City**," "**Second City**," "**City of Big Shoulders**" are some of the monikers describing Chicago.  It is the largest American city in the midwest and home to **2.7 million** people as of the **2020 census**. It has been my home for more than 20 years, and I love living in this city.  Chicago has a lot to offer, from theaters, bars, popular sports team, restaurants, outdoor activities, and many more. In addition, it is on the southwest corner of **Lake Michigan**, which makes living in this city more fun than many other cities in America, especially during summertime.
# 
# ### Content:
# This project is an exploratory data analysis as part of the **Udacity Data Analyst Nanodegree** through **Western Governors University**. I will be using the XML dataset for Chicago that I have extracted from OpenStreetMap https://www.openstreetmap.org/relation/122604. OpenStreetMap is a collaborative project attempting to create geographic map of the world. 
# 
# I am using **Jupyter Notebook** and writing the codes in **Python**. This project calls for this dataset to be audited, cleaned, convert to **CSV** and uploaded to a database(SQL).  Once uploaded in a database, I will write SQL statements to explore the dataset and discover some fun facts about Chicago. 

# In[1]:


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


# **Count of nodes and ways**

# In[2]:


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


# ### Dataset Issues
# 
# 
# **1.** After my initial analysis, I saw a couple of problems with the street types audit.  One had Sangamon showing as a street type, which is incorrect.  Sangamon is a street name in Chicago.  I cleaned this issue by adding the correct street type suffix for it. </br> </br>
# I also found a couple of street with an abbreviated version of Avenue to Ave.  I updated them to show the full spelling instead. </br> </br>
# Other than this, there was not much issue found from the Chicago Open Street Map data.

# **Street Types Audit**

# In[5]:


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


# In[6]:


st_types = audit_street(OSM_FILE)
pprint.pprint(dict(st_types))


# In[7]:


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


# **Street Type Fix**

# In[8]:


change_name(st_types)


# **2.** The second issue that I found from the phone number audit was a phone number showing a forward slash "/" instead of a dash "-".  It was corrected by changinf the  " / " to " - ".

# **Phone Numbers Audit**

# In[9]:


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


# In[11]:


num_list = audit_phone(OSM_FILE)

num_list


# **Phone Number Fix**

# In[12]:


# change forward slash to dashes
def update_number(num):
    new_num = num.replace("/","-",3)
    return new_num

def change_numbers(num_list):
    for num in num_list:
        print(num, "=>", update_number(num))
        
change_numbers(num_list)


# **3.**  The other two audits, **Postal Codes** and "**K**" attribute formatting scheme, did not show any issues.  Postal codes audit return with {'il':1} and was corrected to {'il':il}.  "**K**" attribute formatting scheme audit did not show any problemchars.

# ### Chicago OSM CSV Database Load
# 
# Loaded nodes.csv, nodes.csv, ways.csv, ways_nodes.csv, ways_tags.csv to SQLITE and it created database "chicago.db".   

# In[6]:


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


# ### Dataset Statistics 
# 
# ```
# chicago.osm ............. 92 MB 
# chicago.db .............. 48 MB
# nodes.csv  .............. 29 MB
# nodes_tags.csv ..........  2 MB 
# ways.csv ................  3 MB
# ways_nodes.csv .......... 10 MB
# ways_tags.csv ...........  9 MB
# ```

# ### Number of unique users

# In[8]:


# Number of unique users

query = "SELECT COUNT(DISTINCT(u.uid))FROM (SELECT uid FROM Nodes UNION ALL SELECT uid FROM Ways) as u;"
cur.execute(query)
rows=cur.fetchall()

pprint.pprint(rows)


# ### Number of Nodes

# In[7]:


# Number of nodes

query = "SELECT count(DISTINCT(id)) FROM nodes;"
cur.execute(query)
rows=cur.fetchall()

pprint.pprint(rows)


# ### Number of ways

# In[9]:


# Number of ways

query = "SELECT count(DISTINCT(id)) FROM ways;"
cur.execute(query)
rows=cur.fetchall()

pprint.pprint(rows)


# **Number of Chosen Type of Nodes**

# In[24]:


# number of chosen type of nodes

query = "SELECT type , count(*) as num  FROM nodes_tags group by type order by num desc LIMIT 10;"
cur.execute(query)
rows=cur.fetchall()

pprint.pprint(rows)


# **Number of Cafes establishments** 

# In[11]:


# number of chosen type of nodes "cafe"

query = "SELECT value, count(*) FROM (select key,value from nodes_tags UNION ALL select key,value from ways_tags)  where value like '%cafe%';"
cur.execute(query)
rows=cur.fetchall()

pprint.pprint(rows)


# **Top 10 Contributing Users**

# In[12]:


#Top 10 contributing users

query = "select u.user, count(*) as num from (select user from nodes UNION ALL select user from ways) as u group by user order by num desc limit 10;"
cur.execute(query)
rows=cur.fetchall()
print('Top 10 contributing users and their contribution:\n')
pprint.pprint(rows)


# **Top 10 types of Cuisines**

# In[13]:


# Top 20 cuisines in Chicago
query="select value,count(*) as num from (select key,value from nodes_tags UNION ALL select key,value from ways_tags) as u where u.key like '%cuisine%' group by value order by num desc limit 10;"
cur.execute(query)
rows=cur.fetchall()

pprint.pprint(rows)


# **Top 15 Chicago Websites**

# In[14]:


# Top 15 website links in Chicago

query = "select u.value, count(*) as num from (select value from nodes_tags UNION ALL select value from ways_tags) as u WHERE value LIKE '%www.%' group by u.value order by num desc limit 15;"
cur.execute(query)
rows=cur.fetchall()

pprint.pprint(rows)


# **List of amenities Chicago has to offer**

# In[16]:


# Amenities

query="select value, count(*) as num from nodes_tags where key='amenity' group by value order by num desc limit 10;"
cur.execute(query)
rows=cur.fetchall()

pprint.pprint(rows)


# ### Jewel - Osco
# 
# I normally shop at Jewel-Osco, a popular grocery store in Chicago.  I am curious to see how many Jewel-Osco stores are there within the area of Chicago I extracted in openstreetmap.

# In[17]:


# How many Jewel-Osco are there
query = "select u.value, count(*) as num from (select value from nodes_tags UNION ALL select value from ways_tags) as u WHERE value like 'Jewel-Osco%' group by u.value order by num desc;"
cur.execute(query)
rows=cur.fetchall()

pprint.pprint(rows)


# ### Museums
# ```I like to list the different museums in Chicago that makes Chicago one of the best cities to live in around the world.  Chicago has some of the best museums to offer such as the Field museum and The Museum of Science in Industry.```

# In[18]:


query = "select u.value, count(*) as num from (select value from nodes_tags UNION ALL select value from ways_tags) as u WHERE value like '%museum%' and value not like 'en%' and value not like 'http++' group by u.value order by num desc limit 10;"
cur.execute(query)
rows=cur.fetchall()

pprint.pprint(rows)


# **Religion in Chicago and Christian Denomination**

# In[19]:


# Religion
query="select value, count(*) as num from (select key,value from nodes_tags UNION ALL select key,value from ways_tags) where key='religion' group by value order by num desc;"
cur.execute(query)
rows=cur.fetchall()

pprint.pprint(rows)


# In[20]:


# Christian Denomination
query="SELECT b.value, COUNT(*) as num FROM ways_tags JOIN (SELECT DISTINCT(id) FROM ways_tags WHERE value='place_of_worship') a ON ways_tags.id=a.id JOIN (SELECT DISTINCT(id), value FROM ways_tags WHERE key = 'denomination') b ON a.id = b.id WHERE ways_tags.key='religion' AND ways_tags.value = 'christian' GROUP BY b.value ORDER BY num DESC;"
cur.execute(query)
rows=cur.fetchall()

pprint.pprint(rows)


# ### Areas for future Data Improvement

# In[21]:


query="SELECT value FROM (SELECT key,value FROM nodes_tags UNION ALL SELECT key,value FROM ways_tags) WHERE key='phone' LIMIT 5;"
cur.execute(query)
rows=cur.fetchall()

pprint.pprint(rows)


# The code for cleaning the phone numbers from the dataset was successful.  It successfully changed "/" (forward slash) to dashes. However, the issue is that so many phone numbers do not have the correct format. </br>
#  
# ```+1-312-372-0072, +1-312-427-3170, (312) 920-9100, (312)-1116, 888-642-6674, +13122650580, +1 (312) 475-1390, 7732482570, 8 800 775-52-93, 8889496289, 312-642-3000, 800 DL MOODY```

# ### Benefits 
# 
# The Benefits of improving the phone numbers dataset would not just look clean and conform to standards, but by following the international standards for phone numbers, any developers or users extracting these phone data can leverage them on auto-dialing programs and others.   
# 
# ### Anticipated Issue
# 
# There are a few variations of phone numbers, and it might be challenging to catch all of these variations and be able to 100% clean this data.
# 

# ## Conclusion
# 
# As mentioned, I only took a smaller section of Chicago from OpenStreetMap, and expanding the extract would add more challenges to cleaning these data. While auditing the street type, I only found a few issues with them, which means that the community is constantly improved. Setting up standards and hoping the user community follows them can only help this project's long-term goal of creating a geographic map of the world.
