# Support long polylines

## Problem

Android's Log breaks long line into multiple log messages, which breaks mapcat commands. This is not a problem for adding single points, but polylines and polygons may consist of many points, which result in long log lines.

Also, the log messages may be printed out of order.
