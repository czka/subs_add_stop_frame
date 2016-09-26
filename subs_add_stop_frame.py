#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# Copyright (c) 2016, Maciej Sieczka. All rights reserved.

import sys
import os

try:
    from chardet.universaldetector import UniversalDetector
except ImportError:
    sys.stderr.write("%s: error: Can't find `chardet' library. Maybe you just "
                     "need to install it using your OS package manager, or "
                     "`pip2'. More hints in the traceback below.\n"
                     % os.path.basename(sys.argv[0]))
    raise

import argparse
import io
import codecs
import re


class Subtitles:
    def __init__(self, infile, outfile, encoding=None):
        self.infile = infile
        self.outfile = outfile
        self.encoding = encoding

    def validate_encoding(self):
        codecs.lookup(self.encoding)

    def detect_encoding(self):
        with open(self.infile, 'rb') as infile:
            detector = UniversalDetector()
            for line in infile:
                detector.feed(line)
                if detector.done:
                    break
            detector.close()
            self.encoding = detector.result['encoding']

    def interpolate_stop_frames(self):
        with io.open(file=self.infile, mode='r', encoding=self.encoding) as infile,\
             io.open(file=self.outfile, mode='w', encoding=self.encoding) as outfile:
            # rstrip() should do, but why not strip it both sides, just in case?
            # I say strip it good, it won't hurt.
            l1 = infile.readline().strip()
            while infile:
                if l1:
                    l2 = infile.readline().strip()
                    if l2:
                        # The end frame is subsequent's subtitle's start frame
                        # minus 1.
                        t2 = int(re.search(r"^\{([0-9]+)\}", l2).group(1))
                        outfile.write(l1.replace('}{}','}{'+str(t2-1)+'}',1)+'\n')
                        l1 = l2
                    else:
                        # For the last subtitle there's no subsequent one, so
                        # let's add an arbitrary, say, 99 frames.
                        outfile.write(l1.replace('}{}','}{'+str(t2+99)+'}',1)+'\n')
                        break


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Add missing MicroDVD subtitle line's stop-frames based on "
                    "subsequent subtitle line's start-frame.", add_help=False)

    # A bit of a hack to customize ArgumentParser.print_help() output.
    #
    # Goals:
    #
    # - Get rid of default "positional arguments" and "optional arguments"
    #   print_help() sections. Not only it's artificial that those positional
    #   ones are automatically required, but also leads to absurdities like
    #   required arguments in the "optional" section :).
    # - On a command line I prefer named arguments (ie. the "optional" in
    #   argparse lingo) over positional. They are self-explanatory and self-
    #   documenting. Assuming eg. that a 2nd file on the command line is the
    #   output is only a convention (compare `ogr2ogr' manual for instance).
    #   And, after all, there are people on our planet who read right-to-left
    #   ;).
    # - Capitalize --help description.
    # - Preserve as much of great argparse functionality as possible.
    #
    # Means:
    #
    # - Use add_help=False.
    # - Use add_argument_group. All arguments land in a single section. Their
    #   required/optional status can be told from "usage" print_help() output
    #   by the presence or lack of "[]" brackets surrounding them.
    # - Specify custom help argument.
    # - Use parse_known_args(), early, to pick up -h/--help if it's there.
    #   parse_args() would produce an error if the command line was
    #   invalid/incomplete and would not let display the complete command help
    #   message due to add_help=False.
    # - Now we can add the remaining, named arguments to parser. argparse calls
    #   these "optional", so required=True is... required.
    # - Help True/False flag is now in Namespace's 1st tuple item, the rest of
    #   the command line is in 2nd Namespace's tuple item. print_help() will
    #   consider both tuple items nicely, just as if they were added in one
    #   batch, without parse_known_args() in the middle.
    # - Run print_help() if the help flag is set in the 1st tuple and exit.
    # - Finally, a proper parse_args() run if help was not requested, and on to
    #   main code execution.

    group = parser.add_argument_group("Arguments")
    group.add_argument("--help", action='store_true',
                       help="Show this help message and exit.")
    args = parser.parse_known_args()
    group.add_argument("--encoding", metavar='STRING', type=str,
                       help="Input subtitles encoding - one of "
                            "https://docs.python.org/2/library/codecs.html#"
                            "standard-encodings. By default the script tries "
                            "to auto-detect it using `chardet' library, but "
                            "you may choose to specify it here in case the "
                            "magic fails.", default=None)
    group.add_argument("--input",  metavar='PATH', dest='infile', type=str,
                       help="Input subtitles file path.", required=True)
    group.add_argument("--output", metavar='PATH', dest='outfile', type=str,
                       help="Output subtitles file path.", required=True)

    if args[0].help:
        parser.exit(parser.print_help())
    else:
        args = parser.parse_args()
        subs = Subtitles(args.infile, args.outfile, args.encoding)
        if args.encoding:
            try:
                subs.validate_encoding()
            except LookupError:
                parser.error("Encoding '%s' is not supported." % args.encoding)
        else:
            subs.detect_encoding()
        subs.interpolate_stop_frames()
