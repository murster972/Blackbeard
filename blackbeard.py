#!/usr/bin/env python3
import os, sys, time
import subprocess
import argparse

#NOTE: image from http://www.tompitts.co.uk/wp-content/uploads/Blackbeards-logo.jpg

#NOTE: sepearet into seperate files?

#TODO: Add option to allow resume a copy, e.g. get length of dest and copy from next byte onwards
#      Have program check copied data is valid first using hashes, e.g. create hash of dest file
#      and source file matching length of dest file bytes, then compare.

#TODO: Try and improve speed
#TODO: Add eta

#TODO: Add blackbeard ascii art

' An version of the linux util cp, allows users to copy files from multiple sources to destinations '
class Blackbeard:
    def __init__(self, source, dest, buff_size):
        #size of byte chunks to copy to file each iteration
        self.buff_size = buff_size if buff_size else 20000

        copied = 0

        for s, d in zip(source, dest):
            print("Copying file...\nSource: {}\nDest: {}".format(s, d))
            try:
                self._copy_data(s, d)
            except KeyboardInterrupt:
                self._print_err("\n[*] Didn't copy all files")
            copied += 1

        print("[*] %d files copied successfully" % copied)

    ''' Copies data from one file to another

        :param s: source file name
        :param d: destination file name '''
    def _copy_data(self, source, dest):
        with open(source, "rb", buffering=0) as s, open(dest, "wb", buffering=0) as d:
            #gets size of source file in bytes and GigaBytes(gb)
            s_size = os.stat(source).st_size
            s_size_gb = s_size / 1000000000

            #TODO: Change to match terminal window width
            #columns in progress bar
            prog_bar_length = 25

            #TODO: move elapsed time to seperate thread so it doesn't get hung
            #      when writing to file or flushing scren etc.
            elapsed_time = 0
            remaining_data = s_size

            data = True

            #copies source data to dest file
            while data:
                start = time.time()

                data = s.read(self.buff_size)
                d.write(data)

                #gets cur-length of dest file
                l = d.seek(0, 2)
                l_gb = l / 1000000000

                remaining_data = s_size - l

                perct = l / s_size * 100
                perct_sized = int(perct / (100 / prog_bar_length))
                spaces = int(prog_bar_length - perct_sized)
                bar = "{}{}".format("█" * perct_sized, " " * spaces)

                elapsed_time += time.time() - start

                #converts time to minutes if more than 60s
                e_time = "%.2fs" % elapsed_time

                if elapsed_time > 60:
                    mins = elapsed_time - (elapsed_time % 60)
                    secs = elapsed_time - mins
                    e_time = "%dm %.2fs" % (mins / 60, secs)

                #returns cursors to start of screen (\r), prints progress bar and info
                #then clears screen
                sys.stdout.write("\r[%s] %.2f%% - %.2fGB of %.2fGB - elapsed %s" % (bar, perct, l_gb, s_size_gb, e_time))
                sys.stdout.flush()
            print("\n")

    ''' Prints error message and exits

        :param m: msg to print '''
    def _print_err(self, m):
        print(m)
        sys.exit(-1)

''' Checks permissions and exsitence of source and destination file

    :param s: source file name
    :param d: dest file name
    :param force: True or False if overwrite all
    :output bool: True if valid copy False if not, e.g. bad permissions, no overwrite, etc. '''
def check_files(s, d, force):
    is_s = os.path.isfile(s)

    #checks source exists
    if not is_s:
        print("[-] ERROR: Source file '%s' doesn't exist" % s)

    #checks user can read source
    if not is_s or check_perms(s, "rb"):
        return 0

    #checks if user wishes to overwrite file when --force isn't passed
    if os.path.isfile(d) and not force:
        opt = input("[*] File '%s' exists, overwrite? [y/n/all]: " % d).lower()

        if opt not in  ["y", "yes", "all"]:
            print("[*] Won't copy '%s' to '%s'" % (s, d))
            return 0
        elif opt == "all":
            print("[*] Will force copy all files")
            args["force"] = True
        else:
            #checks user can overwrite file
            if check_perms(s, "rb"):
                return 0

    #checks user can overwrite existing files
    if os.path.isfile(d) and force:
        check_perms(d, "wb")

    #checks user can can write to dest dir
    target_dir = d.split("/")
    target_dir = "/".join(target_dir[:-1]) if len(target_dir) > 1 else os.getcwd()

    if check_perms(d, "wb", target_dir):
        return 0

    return 1

''' gets files from source directory and checks if user is able to copy to dest directory

    :param source: source directory
    :param dest: destination directory
    :param force: True or False if overwrite all

    :output files: list of list [files to copy, destination files]'''
def get_dir_files(source, dest, force):
    files_to_copy = []
    dest_of_files = []

    for i in os.walk(source):
        f = i[-1]
        dir_ = i[0]
        dir_ += "/" if dir_[-1] != "/" else ""
        d_ = dest
        d_ += "/" if d_[-1] != "/" else ""

        #loops through each file in dir and adds to list of files if user is able to copy
        for x in f:
            if check_files(dir_ + x, d_ + x, force):
                files_to_copy.append(dir_ + x)
                dest_of_files.append(d_ + x)

    return (files_to_copy, dest_of_files)

''' Checks if user has permission to read/write file

    reasin for not using os.access explained here https://docs.python.org/3/library/os.html#os.stat

    :param f: name of file to check
    :param wr: operation, e.g. rb, wb, etc. '''
def check_perms(f, wr, dir_=None):
    try:
        f = open(f, wr).close()
    except PermissionError:
        op = "read from file" if wr[0] == "r" else "write to file"
        struct = "File" if not dir_ else "Directory"
        f_ = f if not dir_ else dir_
        print("[-] ERROR: %s %s won't be copied, User doesn't have permission to %s" % (struct, f_, op))
        return 1

def main():
    #parses cmd-line args
    parser = argparse.ArgumentParser(description='Version of linux cp command. Copy files or directorys. use --help to see parameters.')

    parser.add_argument('source', type=lambda x: x.split(", "), help='FILE NAME or "F1, F2, ..."', metavar='SOURCE')
    parser.add_argument('dest', type=lambda x: x.split(", "), help='FILE NAME or "F1, F2, ..."', metavar="DESTINATION")
    parser.add_argument('--force', '-f', nargs="?", const=True, help="force copy, overwrite existing files")
    parser.add_argument('--buff_size', '-bs', type=int, help="Integer representing buffer sized used when reading/writing file data. 20000 by default.")
    parser.add_argument('--is_dir', '-dir', nargs="?", const=True, help="When passed assumes all source and dest are dirs, will copy all files from soure dir to dest dir in same heirachical structure.")
    parser.add_argument('--continue', '-c', nargs="?", const=True, help="Look for partiallay copied files and continue copying from were they stopped.")
    parser.add_argument('--Arrr!', '--Yarrr!', '--Arg!', nargs="?", const=True, help="...")

    args = {arg[0]:arg[1] for arg in parser.parse_args()._get_kwargs()}

    if args["Arrr!"]:
        print("""████████████████████████████████████████████████████████████████████████████████
██████████████████████▀````▀████████████████████████╨```╙▀██████████████████████
████████████████████▀` ▄╦   `▀████████████████████M ╔▄▄▄▄ ╙▀████████████████████
██████████████████▀`,╗▀`      `▀████████████████▀ ╔▓█▀▀▀██▄ ╙███████████████████
████████████████▌` ╗▀`          ╙▀████████████▀ ,▄█▀     ╙██▄ ╙█████████████████
███████████████" ▄▓╨              ╙▀▀▀▀▀▀▀▀▀▀`,▄█▀`        ▀██▄ ╙███████████████
█████████████" ╔▓╨                ,▄▄▄▄▄▄▄▄▄▄▄██"        ╓▄▓███▓, ▀█████████████
███████████╨ ╓▓▀                ╙╨╨▀▀▀▀▀▀▀▀▀▀▀╙         "╙╙╙╙╙╙╙╙   ▀███████████
█████████▀ ╔▓▀`                                                      `▀█████████
███████▀ ,╬▀`                                                          `▀███████
█████▀`,▄▀"                                                              ╙▀█████
███▀`,▄▓"                                                                  ╙████
██^  ╙"                .    .     .   .   .      .      .                    ╙██
█▌                j█████████████████████████████████████████▌                 ██
██▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓██▀╙"``▄██████▀╓▓██████▀"`` ╔▓██████▀╠████▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓██
███████████████▌``╫╨   ,╔▓█████▀╓▄███╨└█▌    ╔▓██████▀╔▓██▀"╣Ñ`╠████████████████
███████████████▌ ╫▌   ▄▓█████▀╔▓███╨   ▓M  ╔▓██████▀╔▓██▀`  j▓Hj████████████████
███████████████▌ ╫▌ ▄██████▀▄▓███▀`   j█▌▄▓██████▀▄▓██▀`    ▐█Mj████████████████
███████████████▌ ╫███████▌▓████╨      ╣████████▓▓███▌"      ╣█Mj████████████████
███████████████▓,`▀█████▓████╨       ╫███████▓▓███▌"       ╔▓" ╢████████████████
█████████████████▓,╙██▓████╨       ,╣▀███████████"        ╔╫,▄██████████████████
███████████████████▌`▀███╨     ,╓▄▓M`╫████H╙▀██▌        ╓╬╨╟████████████████████
███████████████████▌   ███▓▓▓████▀,  ╙▀▀▀▀`  ╙▀████▓▓▓██▌  ║████████████████████
███████████████████▌   ╢███████▓▓██▄▄▄▄▄▄▄▄▄▄██▓████████▌  ║████████████████████
███████████████████▌   ║███████████▀▀╨```╙▀▀▀███████████M  ║████████████████████
███████████████████▌   ╙███████▌`              ╙████████`  ║████████████████████
███████████████████▌     `╨███╨   ,▄▄▓████▓▄µ   `▀██▌"     ║████████████████████
███████████████████▌       "╨   ╚▓████████████M   ╙╨       ║████████████████████
███████████████████▌             ╙████▀▀▀▀███▌             ║████████████████████
███████████████████▌              ╙▀╨     `▀▀              ║████████████████████
███████████████████▌                                       ║████████████████████
███████████████████▌                                       ║████████████████████
████████████████▀▀█▌                                       ║██▀█████████████████
████████████████ "█▀ ]▄,                                ╔▄ ╙█▀ ╠████████████████
████████████████▄▄▄▄╥╫██▄                             ╔▓██▄▄▄▄▄╣████████████████
█████████████████████████▌                           j██████████████████████████
█████████████████████████▌ ╫▄                     ╔▓ j██████████████████████████
██████████████████████╨╟█▌ ╫██▄                ,▄███`j██"║██████████████████████
█████████████████████▌ "▀" ╫███▌               ╫████` ╨╨ j██████████████████████
██████████████████████▄▄▄▄▄▓███▌ Φ▄        ,▄N ╫████▄▄▄▄▄▄██████████████████████
███████████████████████████████▌ ▓██▓▄▄▄▄▄▄██▌ ╫████████████████████████████████
███████████████████████████████▌ ▓███████████▌ ╫████████████████████████████████
███████████████████████████▌`║█▌ ▓███████████▌ ╫█▌`▓████████████████████████████
███████████████████████████▌ `╙` ▓███████████▌ "╙` ▓████████████████████████████
████████████████████████████▓▓▓▓▓█████████████▓▓▓▓▓█████████████████████████████
████████████████████████████████████████████████████████████████████████████████""")
        input("Enter to continue...")

    if len(args["source"]) != len(args["dest"]):
        Blackbeard._print_err("[-] ERROR: Must pass the same ammount of source and destination files.")

    #files
    if not args["is_dir"]:
        #checks source files exist, user has perm to read/write source/dest
        #and checks if shoudl overwrite existing dest
        for ind in range(len(args["source"]), 0, -1):
            s = args["source"][ind - 1]
            d = args["dest"][ind - 1]

            if not check_files(s, d, force=args["force"]):
                del args["source"][ind - 1]
                del args["dest"][ind - 1]

        Blackbeard(args["source"], args["dest"], args["buff_size"])
    #dirs
    else:
        #checks dir exists, and gets files from it
        for ind in range(len(args["source"]), 0, -1):
            s = args["source"][ind - 1]
            d = args["dest"][ind - 1]

            #checks if source and dest exist and are valid dirs
            valid = [True, True]

            if not os.path.isdir(s): valid[0] = False
            if not os.path.isdir(d): valid[1] = False

            if not valid[0] or not valid[1]:
                d1 = "" if valid[0] else s
                d2 = "" if valid[1] else d
                print("[*] ERROR: Won't copy, Invalid directory/s:\n\t%s\n\t%s" % (d1, d2))
                continue

            #gets files from source and dest
            source, dest = get_dir_files(s, d, args["force"])

            print("[*] INFO: Copying Files from directory '%s' to '%s'" % (s, d))
            Blackbeard(source, dest, args["buff_size"])

if __name__ == '__main__':
    main()
