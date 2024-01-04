import xml.etree.ElementTree as ET
from os.path import isfile

import obspython as obs

# my python was located here: (useful for enabling python on OBS)
# /opt/homebrew/Cellar/python@3.11/3.11.5/Frameworks

# define variables
url = ""
weburl = ""
csvurl = ""
interval = 100
search_all = False
namespace = ""
source_name = ""


def parse_file(tree: ET.ElementTree) -> dict:
    root = tree.getroot()

    players_zone3_cards = {}

    for player in root.findall("player"):
        player_name = player.find("name").text
        zone3_cards = player.find(".//zone3")

        # Extracting card information from each card in zone3
        if zone3_cards is not None:
            cards_info = [
                {"id": card.find("id").text, "owner": card.find("owner").text}
                for card in zone3_cards.findall("card")
            ]
            players_zone3_cards[player_name] = cards_info
        else:
            players_zone3_cards[player_name] = []

    return players_zone3_cards


def count_cards(players_zone3_cards: dict) -> list[str]:
    output = []
    for player in players_zone3_cards:
        n_souls = len(players_zone3_cards[player])
        output.append(str(n_souls))
        # print(f"{player} has {n_souls} souls")
    return output


def update_text():
    global url
    global source_name

    if isfile(url):
        tree = ET.parse(url)
        apply_xml_to_source(tree, source_name)
    else:
        pass


def apply_xml_to_source(tree, source_name: str):
    zone_3_output = parse_file(tree)
    n_souls = count_cards(zone_3_output)
    source = obs.obs_get_source_by_name(source_name)
    # if not source:
    # print("could not find the source!")

    if n_souls and source:
        text_to_put = f"Soul Count: {'-'.join(n_souls)}"
        settings = obs.obs_data_create()
        obs.obs_data_set_string(settings, "text", text_to_put)
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
    return "Looks for the SavedGame.txt file (usually found at /Applications/LackeyCCG/plugins/Redemption/saved/SavedGame.txt for Mac) and counts the number of Lost Souls in each players land of redemption and updates "


def script_update(settings):
    # TIL do i need to tell python what variables to bring in to each function?
    # answer: yes
    global url
    global interval
    global source_name

    url = obs.obs_data_get_string(settings, "url")

    interval = obs.obs_data_get_int(settings, "interval")

    source_name = obs.obs_data_get_string(settings, "text_source_name")

    obs.timer_remove(update_text)

    if url != "":
        obs.timer_add(update_text, interval)


# sets defaults in obs
def script_defaults(settings):
    global interval
    # sets the default inverval to 10ms
    obs.obs_data_set_default_int(settings, "interval", interval)


# creates properties that can be set in the script gui
def script_properties():
    # i think obs has a structure for properties and this creates a var with that structure
    props = obs.obs_properties_create()

    obs.obs_properties_add_path(
        props,
        "url",
        "Lackey Redemption SavedGame.txt file path:",
        obs.OBS_TEXT_DEFAULT,
        "*.txt",
        "",
    )

    obs.obs_properties_add_text(
        props,
        "text_source_name",
        "Source name that you want to update:",
        obs.OBS_TEXT_DEFAULT,
    )

    # creates int property, adds to pros var, sets indentifier to "interval",
    # displays "Update..." in GUI, min 1, max 9999, steps 1
    obs.obs_properties_add_int(props, "interval", "Update Interval (ms)", 1, 9999, 1)

    # creates button, adds to props, indentifier "button", displays "Refresh", runs refresh_pressed()
    obs.obs_properties_add_button(props, "button", "Refresh", refresh_pressed)

    # returns value of props when called
    return props
