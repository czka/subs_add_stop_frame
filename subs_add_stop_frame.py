#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# Copyright (c) 2016, Maciej Sieczka. All rights reserved.

import sys
import os
import argparse
import io
import codecs
import re

try:
    from chardet.universaldetector import UniversalDetector
except ImportError:
    sys.stderr.write("%s: error: Can't find `chardet' library. Maybe you just "
                     "need to install it using your OS package manager, or "
                     "`pip2'. More hints in the traceback below.\n"
                     % os.path.basename(sys.argv[0]))
    raise


class SubsAddStopFrameError(Exception):
    """Base class for subs_add_stop_frame exceptions."""
    def __init__(self, errmsg=None):
        # I'm doing my best to follow the instructions on
        # https://wiki.python.org/moin/WritingExceptionClasses here, but trying
        # not to enforce any particular message on the exception caller. Let me
        # know if you know how to do it better.
        Exception.__init__(self, errmsg)


class LineMalformedError(SubsAddStopFrameError):
    """Bogus subtitle line format. Should be:
    `{<number>}{<number> or none}<some text> or none'."""


class StopFrameTooLowError(SubsAddStopFrameError):
    """Stop frame can't be lower than start frame."""


class StartFrameTooLowError(SubsAddStopFrameError):
    """Start frame can't be lower than previous stop-frame or start-frame."""


class Subtitles:
    def __init__(self, infile, outfile, encoding=None):
        self.infile = infile
        self.outfile = outfile
        self.encoding = encoding

    def validate_encoding(self):
        codecs.lookup(self.encoding)

    def validate_sanity(self):
        """Validates basic input MicroDVD format conformance and runs sanity
        checks against input frame numbers."""
        with open(self.infile, 'rb') as infile:
            prev_start_frame = prev_stop_frame = ''
            prev_line_count = curr_line_count = 0

            for line in infile:
                curr_line = line.strip()
                curr_line_count += 1

                if curr_line:
                    if re.match(r"\{[0-9]+\}\{[0-9]*\}", curr_line):
                        curr_start_frame, curr_stop_frame = \
                            re.match(r"\{([0-9]+)\}\{([0-9]*)\}",
                                     curr_line).groups()

                        if prev_start_frame and int(prev_start_frame) >= \
                                int(curr_start_frame):
                            errmsg = 'Start-frame %s in input line %s should '\
                                     'be greater than start-frame %s in input '\
                                     'line %s.' % (curr_start_frame,
                                                   curr_line_count,
                                                   prev_start_frame,
                                                   prev_line_count)
                            raise StartFrameTooLowError(errmsg)

                        if prev_stop_frame and int(prev_stop_frame) >= \
                                int(curr_start_frame):
                            errmsg = 'Start-frame %s in input line %s should '\
                                     'be greater than stop-frame %s in input '\
                                     'line %s.' % (curr_start_frame,
                                                   curr_line_count,
                                                   prev_stop_frame,
                                                   prev_line_count)
                            raise StartFrameTooLowError(errmsg)

                        if curr_stop_frame and int(curr_start_frame) >= \
                                int(curr_stop_frame):
                            errmsg = 'Stop-frame %s in input line %s should be'\
                                     ' greater than its start-frame %s.' % \
                                     (curr_stop_frame, curr_line_count,
                                      curr_start_frame)
                            raise StopFrameTooLowError(errmsg)
                    else:
                        errmsg = 'Input line %s is malformed.' % curr_line_count
                        raise LineMalformedError(errmsg)

                    prev_start_frame = curr_start_frame
                    prev_stop_frame = curr_stop_frame
                    prev_line_count = curr_line_count

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
        """Adds stop-frame if missing, as subsequent start-frame minus 1. This
        method assumes that the input was validated according to
        validate_sanity() method."""
        with io.open(file=self.infile, mode='r', encoding=self.encoding) as \
                infile, io.open(file=self.outfile, mode='w',
                                encoding=self.encoding) as outfile:

            prev_start_frame = prev_stop_frame = ''
            for line in infile:
                # rstrip() should do, but why not strip it both sides, just in
                # case? I say strip it good, it won't hurt.
                curr_line = line.strip()

                if curr_line:
                    curr_start_frame, curr_stop_frame, curr_text = \
                        re.match(r"\{([0-9]+)\}\{([0-9]*)\}(.*)",
                                 curr_line).groups()

                    if prev_start_frame:
                        if not prev_stop_frame:
                            prev_stop_frame = int(curr_start_frame) - 1

                        outfile.write('{%s}{%s}%s\n' % (prev_start_frame,
                                                        prev_stop_frame,
                                                        prev_text))
                    prev_start_frame = curr_start_frame
                    prev_stop_frame = curr_stop_frame
                    prev_text = curr_text
            else:
                # For the last subtitle line there's no subsequent one, so
                # if it lacks its stop-frame, let's make it its start-frame +
                # an arbitrary, say, 99 frames.
                if not curr_stop_frame:
                    curr_stop_frame = int(curr_start_frame) + 99
                outfile.write('{%s}{%s}%s\n' % (curr_start_frame,
                                                curr_stop_frame, curr_text))


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
    # - Use parse_known_args(), early, to pick up `--help' if it's there.
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
        subs.validate_sanity()
        subs.interpolate_stop_frames()
