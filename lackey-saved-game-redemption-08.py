import xml.etree.ElementTree as ET
from os.path import isfile

import obspython as obs

# Define global variables
url = ""
weburl = ""
csvurl = ""
interval = 100
search_all = False
namespace = ""
source_name = ""


def parse_file(tree: ET.ElementTree) -> dict:
    """
    Parses an XML file to extract card information for each player.

    Args:
    tree (ET.ElementTree): The XML tree to be parsed.

    Returns:
    dict: A dictionary containing players and their corresponding cards.
    """
    root = tree.getroot()
    players_zone3_cards = {}

    for player in root.findall("player"):
        player_name = player.find("name").text
        zone3_cards = player.find(".//zone3")

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
    """
    Counts the number of cards for each player.

    Args:
    players_zone3_cards (dict): A dictionary containing players and their corresponding cards.

    Returns:
    list[str]: A list containing the number of cards for each player.
    """
    output = []
    for player in players_zone3_cards:
        n_souls = len(players_zone3_cards[player])
        output.append(str(n_souls))
    return output


def update_text():
    """
    Updates the text source in OBS based on the parsed XML file.
    """
    global url
    global source_name

    if isfile(url):
        try:
            tree = ET.parse(url)
            apply_xml_to_source(tree, source_name)
        except Exception as e:
            print(f"Error: {e}")


def apply_xml_to_source(tree, source_name: str):
    """
    Applies the extracted XML data to the OBS source.

    Args:
    tree (ET.ElementTree): The XML tree containing the data.
    source_name (str): The name of the OBS source to be updated.
    """
    zone_3_output = parse_file(tree)
    n_souls = count_cards(zone_3_output)
    source = obs.obs_get_source_by_name(source_name)

    if n_souls and source:
        text_to_put = f"Soul Count: {'-'.join(n_souls)}"
        settings = obs.obs_data_create()
        obs.obs_data_set_string(settings, "text", text_to_put)
        obs.obs_source_update(source, settings)
        obs.obs_data_release(settings)
        obs.obs_source_release(source)


def refresh_pressed(props, prop):
    """
    Refresh button action that updates the text source in OBS.

    Args:
    props: OBS properties (not used).
    prop: OBS property (not used).
    """
    update_text()


def script_description():
    """
    Returns a description of the script for OBS.

    Returns:
    str: Description of the script.
    """
    return "Counts the number of Lost Souls in each player's land of redemption and updates OBS source."


def script_update(settings):
    """
    Updates script settings.

    Args:
    settings: OBS data settings.
    """
    global url, interval, source_name

    url = obs.obs_data_get_string(settings, "url")
    interval = obs.obs_data_get_int(settings, "interval")
    source_name = obs.obs_data_get_string(settings, "text_source_name")

    obs.timer_remove(update_text)
    if url:
        obs.timer_add(update_text, interval)


def script_defaults(settings):
    """
    Sets default settings for the script.

    Args:
    settings: OBS data settings.
    """
    global interval
    obs.obs_data_set_default_int(settings, "interval", interval)


def script_properties():
    """
    Creates properties for the script settings in the OBS interface.

    Returns:
    OBS properties: The created OBS properties.
    """
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
        props, "text_source_name", "Source name to update:", obs.OBS_TEXT_DEFAULT
    )
    obs.obs_properties_add_int(props, "interval", "Update Interval (ms)", 1, 9999, 1)
    obs.obs_properties_add_button(props, "button", "Refresh", refresh_pressed)
    return props
