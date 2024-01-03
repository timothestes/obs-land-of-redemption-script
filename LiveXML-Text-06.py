# modified by discorny from url-text by Jim

import obspython as obs
import xml.etree.ElementTree as ET
from os.path import exists, isfile
import csv
import unicodedata
from urllib import request

# define variables
url = ""
weburl = ""
csvurl = ""
interval = 100
search_all = False
namespace = ""


# create function to update text
def update_text():
    global weburl, url, csvurl, search_all, namespace

    if weburl:
        try:
            with request.urlopen(weburl) as response:
                xml_data = response.read().decode('utf-8')
                tree = ET.ElementTree(ET.fromstring(xml_data))
                apply_xml_to_sources(tree, search_all)
        except Exception as e:
            print(f"Failed to fetch XML data from the provided URL: {e}")
    elif isfile(url):
        tree = ET.parse(url)
        apply_xml_to_sources(tree, search_all)
    else:
        pass

def apply_xml_to_sources(tree, search_all):
    global csvurl, namespace

    root = tree.getroot()
    if search_all:
        elements = root.iter()
    else:
        elements = root

    for child in elements:
        # Adjustments needed to match the local file logic
        # Modify according to your XML structure and OBS source naming conventions
        childelement = child.tag
        source = obs.obs_get_source_by_name("%" + child.tag + "%")

        if source:
            text = child.text.strip() if child.text else ""
            
            if isfile(csvurl) and text:
                with open(csvurl, 'r') as read_obj:
                    csv_reader = csv.reader(read_obj)
                    list_of_csv = list(csv_reader)
                    for x in list_of_csv:
                        if x[0] == childelement and x[1] == text:
                            text = x[2]
                            break  # Stop searching if found
            settings = obs.obs_data_create()
            obs.obs_data_set_string(settings, "text", text)
            obs.obs_source_update(source, settings)
            obs.obs_data_release(settings)
            obs.obs_source_release(source)

# creates function for the refresh button that updates runs the updates_text function
# why the button couldn't just run update_text() instead idk
# maybe it makes it something that can run from the properties
def refresh_pressed(props, prop):
    update_text()


# ----------------------------------------
# just a description for obs properties
def script_description():
    return "Looks for text sources with names that match XML tags from Sportzcast LiveXML in %tag% format.\n\nE.g, To get <clock> data, create a new text source named %clock%\n\nTags are case-sensitive\nThe script prioritizes the Web URL. If there is a Web URL entered, the Local XML path is ignored.\nYou may run in to issues when using the Web URL if your update interval is shorter than the web server allows.\nIf you aren't seeing your data, try ticking the \"Search Whole XML File\" box. \n\nBy Jim (modified by discorny)"


def script_update(settings):
    # TIL do i need to tell python what variables to bring in to each function?
    #answer: yes
    global url
    global csvurl
    global interval
    global search_all
    global namespace
    global weburl  # Add the global declaration for the web URL variable

    weburl = obs.obs_data_get_string(settings, "weburl_input")  # Retrieve the web URL from settings

    url = obs.obs_data_get_string(settings, "url")

    csvurl = obs.obs_data_get_string(settings, "csvurl")

    interval = obs.obs_data_get_int(settings, "interval")

    search_all = obs.obs_data_get_bool(settings, "searchall")

    namespace = obs.obs_data_get_string(settings, "namespace")


    obs.timer_remove(update_text)

    if weburl != "":
        obs.timer_add(update_text, interval)
    elif url != "":
        obs.timer_add(update_text, interval)


# sets defaults in obs
def script_defaults(settings):
    global interval
    global search_all
    # sets the default inverval to 10ms
    obs.obs_data_set_default_int(settings, "interval", interval)
    obs.obs_data_set_default_bool(settings, "searchall", search_all)



# creates properties that can be set in the script gui
def script_properties():

    # i think obs has a structure for properties and this creates a var with that structure
    props = obs.obs_properties_create()

    # creates a path type property, adds it to the props var, sets "url" as identifier,
    # displays "File Path", text type, only *.xml files, no default location
    obs.obs_properties_add_text(props, "weburl_input", "Web URL:", obs.OBS_TEXT_DEFAULT)  # Add a text property for the web URL

    obs.obs_properties_add_path(props, "url", "Local XML Path:", obs.OBS_TEXT_DEFAULT, "*.xml", "")

    obs.obs_properties_add_path(props, "csvurl", "Value change CSV:", obs.OBS_TEXT_DEFAULT, "*.csv", "")

    obs.obs_properties_add_text(props, "namespace", "Namespace:", obs.OBS_TEXT_DEFAULT)

    obs.obs_properties_add_bool(props, "searchall", "Search Whole XML File")

    # creates int property, adds to pros var, sets indentifier to "interval",
    # displays "Update..." in GUI, min 1, max 9999, steps 1
    obs.obs_properties_add_int(props, "interval", "Update Interval (ms)", 1, 9999, 1)

    # creates button, adds to props, indentifier "button", displays "Refresh", runs refresh_pressed()
    obs.obs_properties_add_button(props, "button", "Refresh", refresh_pressed)
    # returns value of props when called
    return props
