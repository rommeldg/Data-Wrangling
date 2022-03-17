#!/usr/bin/env python
# coding: utf-8

# # Wrangling OpenStreetMap Data
# 

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
# 
# 
# 
# 

# ### Import modules that will be use plus chicago openstreetmap  XML extract

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


# In[2]:


def get_element(osm_file, tags=('node', 'way', 'relation')):
    context = ET.iterparse(OSM_FILE, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


# ### nodes and ways 

# In[7]:


# the code below will show the count for nodes, way and other tags

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


# ### K attribute formatting scheme audit

# In[6]:


#Find formatting scheme for K attribute in tags

lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')


def key_type(element, keys):
    """Element keys with all lowercase letters: add to 'lower'
    Element keys with lowercase letters and colon: add to 'lower_colon'
    Element keys with problem characters: add to 'problemchars'
    """
    if element.tag == "tag":
        
        if lower.search(element.attrib['k']):
            keys['lower'] += 1
        
        elif lower_colon.search(element.attrib['k']):
            keys['lower_colon'] += 1
        elif problemchars.search(element.attrib['k']):
            print(element.attrib['k'])
            keys['problemchars'] += 1
        
        else:
            keys['other'] += 1
        
    return keys

def process_map(filename):
    keys = {"lower": 0, "lower_colon": 0, "problemchars": 0, "other": 0}
    for _, element in ET.iterparse(filename):
        keys = key_type(element, keys)

    return keys

keys = process_map(OSM_FILE)

pprint.pprint(keys)


# > * did not find any problem characters in this dataset

# ### Audit street types

# In[9]:


# auditing street types

street_type_re = re.compile(r'\S+\.?$', re.IGNORECASE)
street_types = defaultdict(int)

def audit_street_type(street_types, street_name):
    st = street_type_re.search(street_name)
    if st:
        street_type = st.group()

        street_types[street_type] += 1

def print_sorted_dict(d):
    keys = d.keys()
    keys = sorted(keys, key=lambda s: s.lower())
    for k in keys:
        v = d[k]
        print("%s: %d" % (k, v))

def is_street_name(elem):
    return (elem.tag == "tag") and (elem.attrib['k'] == "addr:street")

def audit():
    for event, elem in ET.iterparse(OSM_FILE):
        if is_street_name(elem):
            audit_street_type(street_types, elem.attrib['v'])    
    print_sorted_dict(street_types)    

if __name__ == '__main__':
    audit()


# > Found a couple of issues regarding the street type audit. First, there are a couple of streets with an abbreviated street type of Ave. I will change them to show Avenue instead. Second, Sangamon is shown as a street type, and it is not.  It is a street name, so I will add street-type Street to it after researching google Maps and verifying the correct type<br /><br />
# >**1. Ave** -> change to Avenue <br /> 
# **2. Sangamon** is a street name -> add street to it <br />
# 

# In[10]:


# cleanup street type

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


# In[11]:


# Fix the following issues found

#st_types = audit_street(SAMPLE_FILE)
st_types = audit_street(OSM_FILE)
pprint.pprint(dict(st_types))


# In[12]:


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


# In[26]:


# street type fix

change_name(st_types) #shows before and after update


# ### Phone Numbers

# In[133]:



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


# In[135]:


num_list = audit_phone(OSM_FILE)

num_list


# In[138]:


# change forward slash to dashes
def update_number(num):
    new_num = num.replace("/","-",3)
    return new_num

def change_numbers(num_list):
    for num in num_list:
        print(num, "=>", update_number(num))
        
change_numbers(num_list)


# ## Postal Codes 
# 
# Cleaning and fixing Chicago postal codes and make sure they all start with "6" and that they are following the standard 5 digits.  
# 
# 

# In[19]:


# Postal Codes
postal_codes = defaultdict(int)

#regular expression for postal codes
postal_code_re = re.compile(r'^[6][0]\d{3}$')

def is_postal_code(elem):
    return (elem.tag == "tag") and (elem.attrib['k'] == "addr:postcode")

def count_postal_code(postal_codes, postal_code):
    """Count number of each unconventional postal code"""
    m = postal_code_re.search(postal_code)
    if not m:
        postal_codes[postal_code] += 1

def audit_zip(file_name):
    osm_file = open(file_name, "r", encoding="utf8").read()
    for event, elem in ET.iterparse(OSM_FILE):
        if is_postal_code(elem):
            count_postal_code(postal_codes, elem.attrib['v'])  
            
    
    return postal_codes


# In[20]:


#fix_pc = audit_zip(SAMPLE_FILE)
fix_pc = audit_zip(OSM_FILE)

pprint.pprint(dict(fix_pc))


# In[21]:



# %load update_postcodes.py
def change_zip(zip_code):
    """Isolate first 5 digits in value attribute"""
    find_zip_re = re.compile(r'(53\d{3})')
    m = find_zip_re.search(zip_code)
    if m:
        new_zip = m.group()
        return new_zip
    else:
        return zip_code
    
def update_postal_codes(fix_pc):
    for zip_code in fix_pc.keys():
        print(zip_code, "=>", change_zip(zip_code))


# In[22]:


update_postal_codes(fix_pc)


# ## Preparing for Database - SQL

# In[23]:


'''
 Note: The schema is stored in a .py file in order to take advantage of the
 int() and float() type coercion functions. Otherwise it could easily stored as
 as JSON or another serialized format.
 '''

schema = {
    'node': {
        'type': 'dict',
        'schema': {
            'id': {'required': True, 'type': 'integer', 'coerce': int},
            'lat': {'required': True, 'type': 'float', 'coerce': float},
            'lon': {'required': True, 'type': 'float', 'coerce': float},
            'user': {'required': True, 'type': 'string'},
            'uid': {'required': True, 'type': 'integer', 'coerce': int},
            'version': {'required': True, 'type': 'string'},
            'changeset': {'required': True, 'type': 'integer', 'coerce': int},
            'timestamp': {'required': True, 'type': 'string'}
        }
    },
    'node_tags': {
        'type': 'list',
        'schema': {
            'type': 'dict',
            'schema': {
                'id': {'required': True, 'type': 'integer', 'coerce': int},
                'key': {'required': True, 'type': 'string'},
                'value': {'required': True, 'type': 'string'},
                'type': {'required': True, 'type': 'string'}
            }
        }
    },
    'way': {
        'type': 'dict',
        'schema': {
            'id': {'required': True, 'type': 'integer', 'coerce': int},
            'user': {'required': True, 'type': 'string'},
            'uid': {'required': True, 'type': 'integer', 'coerce': int},
            'version': {'required': True, 'type': 'string'},
            'changeset': {'required': True, 'type': 'integer', 'coerce': int},
            'timestamp': {'required': True, 'type': 'string'}
        }
    },
    'way_nodes': {
        'type': 'list',
        'schema': {
            'type': 'dict',
            'schema': {
                'id': {'required': True, 'type': 'integer', 'coerce': int},
                'node_id': {'required': True, 'type': 'integer', 'coerce': int},
                'position': {'required': True, 'type': 'integer', 'coerce': int}
            }
        }
    },
    'way_tags': {
        'type': 'list',
        'schema': {
            'type': 'dict',
            'schema': {
                'id': {'required': True, 'type': 'integer', 'coerce': int},
                'key': {'required': True, 'type': 'string'},
                'value': {'required': True, 'type': 'string'},
                'type': {'required': True, 'type': 'string'}
            }
        }
    }
}


# # Defining CSV Files and their respective columns

# In[24]:


OSM_PATH = "chicago.osm"

NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

SCHEMA = schema

NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']


# ### Shaping up the element

# In[25]:


def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    """Clean and shape node or way XML element to Python dict"""

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []  # Handle secondary tags the same way for both node and way elements
    
    count = 0 #way node position
    
    for i in element:
        
        if i.tag == 'tag':
            
            clean_v = None  #cleaned values: street names, postal codes, and phone numbers
            tag_dict = {}
            tag_dict['id'] = element.get('id')
            key_elem = i.get('k')
            value_elem = i.get('v')
            
            if not PROBLEMCHARS.search(key_elem):
                
                #clean street name
                if key_elem == "addr:street":
                    clean_v = update_type(value_elem, mapping) #clean type
                    clean_v = update_direction(clean_v, d_mapping) #clean direction
                             
                                 
                #clean phone numbers    
                if key_elem == "contact:phone":
                    clean_v = update_number(value_elem)
                
                if clean_v != None:
                    clean_v = check_comma(clean_v)
                    tag_dict['value'] = clean_v
                    
                else:
                    tag_dict['value'] = value_elem
                    
                if LOWER_COLON.search(key_elem):
                    key_type = key_elem.split(':')
                    
                    if len(key_type) > 2:
                        tag_dict['key'] = ':'.join(key_type[1:])
                        tag_dict['type'] = key_type[0]
                        
                    else:
                        tag_dict['key'] = key_type[1]
                        tag_dict['type'] = key_type[0]
                        
                else:
                    tag_dict['key'] = key_elem
                    tag_dict['type'] = default_tag_type
            
                
            tags.append(tag_dict)
            
        if i.tag == 'nd':
            node_dict = {}
            node_dict['id'] = element.get('id')
            node_dict['node_id'] = i.get('ref')
            node_dict['position'] = count
            count += 1
            way_nodes.append(node_dict)
        
    
    if element.tag == 'node':
        for i in node_attr_fields:
            node_attribs[i] = element.get(i)
        return {'node': node_attribs, 'node_tags': tags}
        
    elif element.tag == 'way':
        for i in way_attr_fields:
            way_attribs[i] = element.get(i)
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}

    
def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()
            
def validate_element(element, validator, schema=SCHEMA):
    """Raise ValidationError if element does not match schema"""
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.items())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_string = pprint.pformat(errors)
        
        raise Exception(message_string.format(field, error_string))
        
        
class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, bytes) else v) for k, v in row.items()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)
            
            
def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""

    with codecs.open(NODES_PATH, 'w',encoding="utf-8") as nodes_file,          codecs.open(NODE_TAGS_PATH, 'w',encoding="utf-8") as nodes_tags_file,          codecs.open(WAYS_PATH, 'w',encoding="utf-8") as ways_file,          codecs.open(WAY_NODES_PATH, 'w',encoding="utf-8") as way_nodes_file,          codecs.open(WAY_TAGS_PATH, 'w',encoding="utf-8") as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        validator = cerberus.Validator()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                if validate is True:
                    validate_element(el, validator)

                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])


# ### OSM Chicago csv database load

# In[171]:


process_map(OSM_PATH, validate=True)


# In[27]:


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


# ### Statistics 
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

# ## nodes_tags table

# In[28]:


cur.execute(''' DROP TABLE IF EXISTS nodes_tags''')
cur.execute('''
	CREATE TABLE nodes_tags (
    id INTEGER,
    key TEXT,
    value TEXT,
    type TEXT,
    FOREIGN KEY (id) REFERENCES nodes(id)
)''')

conn.commit()

with open('nodes_tags.csv', 'r',encoding="utf-8") as fin:
	dr = csv.DictReader(fin) # comma is the default delimiter
	to_db = [(i['id'], i['key'], i['value'], i['type']) for i in dr]

# 6. insert the formatted data

cur.executemany('INSERT OR IGNORE INTO nodes_tags(id, key, value,type) VALUES (?, ?, ?, ?);', to_db)
# commit the changes
conn.commit()


# ## nodes table

# In[29]:


cur.execute(''' DROP TABLE IF EXISTS nodes''')
cur.execute('''
	CREATE TABLE nodes (
    id INTEGER PRIMARY KEY NOT NULL,
    lat REAL,
    lon REAL,
    user TEXT,
    uid INTEGER,
    version INTEGER,
    changeset INTEGER,
    timestamp TEXT
)''')

conn.commit()

with open('nodes.csv','r', encoding="utf-8") as f: 
    dr = csv.DictReader(f)
    to_db = [(i['id'], i['lat'], i['lon'], i['user'], i['uid'], i['version'], i['changeset'], i['timestamp']) for i in dr]
    
# insert the formatted data

cur.executemany("INSERT INTO nodes (id, lat, lon, user, uid, version, changeset, timestamp) VALUES (?,?,?,?,?,?,?,?);", to_db)
conn.commit()
f.close()


# ## ways table

# In[30]:


cur.execute(''' DROP TABLE IF EXISTS ways''')
conn.commit()
cur.execute('''
CREATE TABLE ways (
    id INTEGER PRIMARY KEY NOT NULL,
    user TEXT,
    uid INTEGER,
    version TEXT,
    changeset INTEGER,
    timestamp TEXT
)''')

conn.commit()

with open('ways.csv','r', encoding="utf-8") as f: 
    dr = csv.DictReader(f)
    to_db = [(i['id'],i['user'],i['uid'],i['version'],i['changeset'],i['timestamp']) for i in dr]

# insert the formatted data        
    
cur.executemany("INSERT INTO ways (id, user, uid, version, changeset, timestamp) VALUES (?,?,?,?,?,?);", to_db)
conn.commit()
f.close()


# ## ways tag

# In[31]:


cur.execute(''' DROP TABLE IF EXISTS ways_tags''')
conn.commit()
cur.execute('''
CREATE TABLE ways_tags (
    id INTEGER NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    type TEXT,
    FOREIGN KEY (id) REFERENCES ways(id)
)''')

conn.commit()


with open('ways_tags.csv','r', encoding="utf-8") as f: 
    dr = csv.DictReader(f)
    to_db = [(i['id'],i['key'],i['value'],i['type']) for i in dr]

# insert the formatted data 

cur.executemany("INSERT INTO ways_tags (id, key, value, type) VALUES (?,?,?,?);", to_db)
conn.commit()
f.close()


# ## ways_nodes table

# In[32]:


cur.execute(''' DROP TABLE IF EXISTS ways_nodes''')
conn.commit()
cur.execute('''
CREATE TABLE ways_nodes (
    id INTEGER NOT NULL,
    node_id INTEGER NOT NULL,
    position INTEGER NOT NULL,
    FOREIGN KEY (id) REFERENCES ways(id),
    FOREIGN KEY (node_id) REFERENCES nodes(id)
)''')

conn.commit()


with open('ways_nodes.csv','r', encoding="utf-8") as f: 
    dr = csv.DictReader(f)
    to_db = [(i['id'],i['node_id'],i['position']) for i in dr]
    
# insert the formatted data 
    
cur.executemany("INSERT INTO ways_nodes (id, node_id, position) VALUES (?,?,?);", to_db)
conn.commit()
f.close()


# **Number of Unique Users**

# In[38]:


# Number of unique users

query = "SELECT COUNT(DISTINCT(u.uid))FROM (SELECT uid FROM Nodes UNION ALL SELECT uid FROM Ways) as u;"
cur.execute(query)
rows=cur.fetchall()

pprint.pprint(rows)


# **Number of Nodes**

# In[39]:


# Number of nodes

query = "SELECT count(DISTINCT(id)) FROM nodes;"
cur.execute(query)
rows=cur.fetchall()

pprint.pprint(rows)


# **Number of Ways**

# In[40]:


# Number of ways

query = "SELECT count(DISTINCT(id)) FROM ways;"
cur.execute(query)
rows=cur.fetchall()

pprint.pprint(rows)


# **Number of Chosen Type of Nodes**

# In[41]:


# number of chosen type of nodes

query = "SELECT type , count(*) as num  FROM nodes_tags group by type order by num desc;"
cur.execute(query)
rows=cur.fetchall()

pprint.pprint(rows)


# **Number of Cafes establishments** 

# In[46]:


# number of chosen type of nodes "cafe"

query = "SELECT value, count(*) FROM (select key,value from nodes_tags UNION ALL select key,value from ways_tags)  where value like '%cafe%';"
cur.execute(query)
rows=cur.fetchall()

pprint.pprint(rows)


# **Top 10 Contributing Users**

# In[68]:


#Top 10 contributing users

query = "select u.user, count(*) as num from (select user from nodes UNION ALL select user from ways) as u group by user order by num desc limit 10;"
cur.execute(query)
rows=cur.fetchall()
print('Top 10 contributing users and their contribution:\n')
pprint.pprint(rows)


# **Top 20 types of Cuisines**

# In[67]:


# Top 20 cuisines in Chicago
query="select value,count(*) as num from (select key,value from nodes_tags UNION ALL select key,value from ways_tags) as u where u.key like '%cuisine%' group by value order by num desc limit 20;"
cur.execute(query)
rows=cur.fetchall()

pprint.pprint(rows)


# **Top 15 Chicago Websites**

# In[140]:


# Top 15 website links in Chicago

query = "select u.value, count(*) as num from (select value from nodes_tags UNION ALL select value from ways_tags) as u WHERE value LIKE '%www.%' group by u.value order by num desc limit 100;"
cur.execute(query)
rows=cur.fetchall()

pprint.pprint(rows)


# **List of amenities Chicago has to offer**

# In[51]:


# Amenities

query="select value, count(*) as num from nodes_tags where key='amenity' group by value order by num desc limit 20;"
cur.execute(query)
rows=cur.fetchall()

pprint.pprint(rows)


# ### Jewel - Osco
# 
# I normally shop at Jewel-Osco, a popular grocery store in Chicago.  I am curious to see how many Jewel-Osco stores are there within the area of Chicago I extracted in openstreetmap.

# In[90]:


# How many Jewel-Osco are there
query = "select u.value, count(*) as num from (select value from nodes_tags UNION ALL select value from ways_tags) as u WHERE value like 'Jewel-Osco%' group by u.value order by num desc;"
cur.execute(query)
rows=cur.fetchall()

pprint.pprint(rows)


# ### Museums
# ```I like to list the different museums in Chicago that makes Chicago one of the best cities to live in around the world.  Chicago has some of the best museums to offer such as the Field museum and The Museum of Science in Industry.```

# In[108]:


query = "select u.value, count(*) as num from (select value from nodes_tags UNION ALL select value from ways_tags) as u WHERE value like '%museum%' and value not like 'en%' and value not like 'http++' group by u.value order by num desc;"
cur.execute(query)
rows=cur.fetchall()

pprint.pprint(rows)


# **Religion in Chicago and Christian Denomination**

# In[110]:


# Religion
query="select value, count(*) as num from (select key,value from nodes_tags UNION ALL select key,value from ways_tags) where key='religion' group by value order by num desc;"
cur.execute(query)
rows=cur.fetchall()

pprint.pprint(rows)


# In[119]:


# Christian Denomination
query="SELECT b.value, COUNT(*) as num FROM ways_tags JOIN (SELECT DISTINCT(id) FROM ways_tags WHERE value='place_of_worship') a ON ways_tags.id=a.id JOIN (SELECT DISTINCT(id), value FROM ways_tags WHERE key = 'denomination') b ON a.id = b.id WHERE ways_tags.key='religion' AND ways_tags.value = 'christian' GROUP BY b.value ORDER BY num DESC;"
cur.execute(query)
rows=cur.fetchall()

pprint.pprint(rows)


# ### Areas for future Data Improvement

# In[139]:


query="SELECT value FROM (SELECT key,value FROM nodes_tags UNION ALL SELECT key,value FROM ways_tags) WHERE key='phone';"
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
# 
# 
# 
# 
# 

# ## Conclusion
# 
# As mentioned, I only took a smaller section of Chicago from OpenStreetMap, and expanding the extract would add more challenges to cleaning these data. While auditing the street type, I only found a few issues with them, which means that the community is constantly improved. Setting up standards and hoping the user community follows them can only help this project's long-term goal of creating a geographic map of the world.
