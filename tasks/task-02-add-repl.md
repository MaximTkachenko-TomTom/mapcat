# REPL

Add a repl functionality to mapcat.

When started without piped input, then it shall behave as a repl:

```
python -m mapcat.main

> add-point ...
< OK add-point ...
> clear
< OK clear

<ctrl+c>
Exit
```

When started with piped input, it shall be readin all lines from it and finish when the pipe is closed:

```
echo "test" | python -m mapcat.main
```
Processes command "test" and finishes.

```
cat commands.txt | python -m mapcat.main
```
Processes all lines in `command.txt` and finishes.

```
adb logcat | python -m mapcat.main
```
Processes all commands from logcat, and effectively runs forever, because `adb logcat` never closes itsoutput.
