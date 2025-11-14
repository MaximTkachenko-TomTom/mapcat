# Tags

When adding features to the map, I need to be able to add a `tag` to them, so that later I can remove multiple features bu tag.

# Commands

## Add commands
Update existing `add-*` commands to accept optional `tag`:

```
add-point (53.342,24.23) id=point_1 tag=traffic_light
```

Tags are not necessary unique.

## Remove command

Update `remove` command to accept either `id` or `tag`

```
remove id=point_1 // exists
remove tag=traffic_light // new
```

