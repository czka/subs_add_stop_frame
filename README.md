## Description

I have this bunch of half-broken MicroDVD subtitle files. Their stop-frames are not defined. Like in these example few lines - the curly braces in the second row are missing their content. Only start-frames are there:
 
```
{100}{}Chwila.
{225}{}Ładnie.
{275}{}Przyniosłem ci coś.
```

<snip>

```
{32100}{}Dobrze.
{32275}{}/- Och, Jack!|/- Och, Judy!
{32550}{}Tłumaczenie: Cholek
```

Some video players can cope with that by displaying the line for some pre-defined amount of time, or until the next line begins. Kodi 16.1, on my HTPC, for one can't do that. So I wrote this Python script which takes subsequent line's start-frame, substracts 1 from it and replaces the missing end-frame with the result. For the last line in a file it just adds 99 frames to its start frame. This cuts it for me.

The command line help hopefully explains it all:
 
```
$ ./subs_add_stop_frame.py --help
usage: subs_add_stop_frame.py [--help] [--encoding STRING] --input PATH
                              --output PATH

Add missing MicroDVD subtitle line's stop-frames based on subsequent subtitle
line's start-frame.

Arguments:
  --help             Show this help message and exit.
  --encoding STRING  Input subtitles encoding - one of
                     https://docs.python.org/2/library/codecs.html#standard-
                     encodings. By default the script tries to auto-detect it
                     using `chardet' library, but you may choose to specify it
                     here in case the magic fails.
  --input PATH       Input subtitles file path.
  --output PATH      Output subtitles file path.
```

Now when you run the script on the few example input lines I gave above, they become:
 
```
{100}{224}Chwila.
{225}{274}Ładnie.
{275}{324}Przyniosłem ci coś.
```

<snip>

```
{32100}{32274}Dobrze.
{32275}{32549}/- Och, Jack!|/- Och, Judy!
{32550}{32649}Tłumaczenie: Cholek
```

If you find it useful - enjoy. In case of a bug or something please let me know. Always happy to receive feedback.

