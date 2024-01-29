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
lackey_username = ""
display_usernames = False


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


def count_cards(
    players_zone3_cards: dict,
    lackey_username: str = "",
    display_usernames: bool = False,
) -> list[str]:
    """
    Counts the number of cards for each player. Sorts the scores with the user's score first if a lackey username is provided.

    Args:
        players_zone3_cards (dict): A dictionary containing players and their corresponding cards.
        lackey_username (str): The username of the user, used for sorting. Optional.

    Returns:
        list[str]: A list containing the number of cards for each player, sorted with the user's score first if username is provided.
    """
    # Only perform sorting if lackey_username is provided and non-empty
    if lackey_username:
        # Convert lackey_username to uppercase for case-insensitive comparison
        lackey_username_upper = lackey_username.upper()

        # Sort players with the user's score first
        sorted_players = sorted(
            players_zone3_cards.keys(),
            key=lambda player: (
                player.upper() != lackey_username_upper,
                player.upper(),
            ),
        )
    else:
        # If no username is provided, use the original order
        sorted_players = players_zone3_cards.keys()

    output = []
    for player in sorted_players:
        n_souls = len(players_zone3_cards[player])
        if display_usernames:
            n_souls = f"{player}: {n_souls}"
        output.append(str(n_souls))
    return output


def update_text():
    """
    Updates the text source in OBS based on the parsed XML file.
    """
    global url
    global source_name
    global lackey_username
    global display_usernames

    if isfile(url):
        try:
            tree = ET.parse(url)
            apply_xml_to_source(tree, source_name, lackey_username, display_usernames)

        except Exception as e:
            print(f"Error: {e}")


def apply_xml_to_source(
    tree, source_name: str, lackey_username: str, display_usernames: bool
):
    zone_3_output = parse_file(tree)
    n_souls = count_cards(zone_3_output, lackey_username, display_usernames)
    source = obs.obs_get_source_by_name(source_name)

    if n_souls and source:
        if display_usernames:
            text_to_put = "\n".join(n_souls)
        else:
            text_to_put = str("- ".join(n_souls))
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
    global url, interval, source_name, lackey_username, display_usernames

    url = obs.obs_data_get_string(settings, "url")
    interval = obs.obs_data_get_int(settings, "interval")
    source_name = obs.obs_data_get_string(settings, "text_source_name")
    lackey_username = obs.obs_data_get_string(settings, "lackey_username")
    display_usernames = obs.obs_data_get_bool(settings, "display_usernames")

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
    obs.obs_properties_add_bool(
        props,
        name="display_usernames",
        description="Show Lackey Usernames",
    )
    obs.obs_properties_add_text(
        props, "text_source_name", "Source name to update:", obs.OBS_TEXT_DEFAULT
    )
    obs.obs_properties_add_text(
        props,
        "lackey_username",
        "Your Lackey Username (used to help show the score consistently, optional)",
        obs.OBS_TEXT_DEFAULT,
    )
    obs.obs_properties_add_int(props, "interval", "Update Interval (ms)", 1, 9999, 1)
    obs.obs_properties_add_button(props, "button", "Refresh", refresh_pressed)
    return props
