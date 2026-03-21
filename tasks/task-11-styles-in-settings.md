# Styles in settings

Settings must include following styles:
- OSM Default
- Driving light
    - url: https://api.tomtom.com/maps/orbis/assets/styles/0.0.*/style?key=<api_key>&map=basic_street-light-driving&hillshade=hillshade_light&navigationAndRoute=navigation_and_route_light&poi=poi_light&range=range_light&apiVersion=1&renderer=premium

# Adding a style

When new style is added, it appears at the bottom of the list. Title is "Custom 1", "Custom 2", etc... On hover full url is be shown. List is persistent across page reloads.

# Current style

- By default the OSM Default style is seledted.
- When a style that requires a TomTom API key is selected for the 1st time, the prompt to enter a key is shown. If key is not entered - OSM Default is used.
- List always shows the currently selected style.
