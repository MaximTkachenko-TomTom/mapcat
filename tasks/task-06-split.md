# Split components

Now `mapcat` serves the webpage, and each invocation hosts a new page. We'll break this connection into independent parts.

# Parts

## Web page

The web page shall be runing independently from `mapcat` python program. It will be hosted separately. It must have open socket for commands, and allow clients to connect and disconnect. Page must have an UI indication - green circle in the corner - when at least one client is connected, which turns red when no clients are conected.

## Mapcat Python client

The `mapcat` program shall not serve the page any more, but connect to socket in existing running page.

