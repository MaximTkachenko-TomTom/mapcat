# Context

I work with map data, that is displayer in an Android application. Data comes from the server, processed in the Android app and is drawn on the screen. To understand what data I receive I want to see it on the web page in real time.

# Data

- GeoPoint - (latitude, longitude), a dot on the map.
- PolyLine - list of GeoPoints, connected by a line on the map.
- Polygon - a list of GeoPoints, that is drawn as a closed polygon on the map.

# Requirements

Simple setup, minimum components.

# Idea

Application logs certain commands into logcat, for example
```
add-point red (52.424234, 4.313123)
add-line blue (32.23424, 3.2233234) (22.242344, 1.3234) (33.3242, 1.21231)
remove-point (12.23132, 4.213123)
```

This logcat is piped into a command line program, that pushed them to the web page, that shows the map and draws these points, lines and polygons.

```
adb logcat | mapcat
```
