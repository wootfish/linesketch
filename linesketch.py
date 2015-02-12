#!/usr/bin/env python2.6
from PIL import Image
import getopt
import random
import sys
import os
import time
from multiprocessing import Process, Queue
from linegenlib import linegenopt as linegen


def findbestline(imagelist, ssize, linelenexp=0.135, maxweight=255, trialpts=5):
    assert trialpts >= 2

    linetup = (0, 0, 0, 0, 0, 0)
    for j in xrange(0, ssize):
        p1 = (0, 0, -1)
        p2 = (0, 0, -1)

        w, h = len(imagelist) - 1, len(imagelist[0]) - 1

        for i in xrange(0, trialpts):
            x_ = random.randint(0, len(imagelist) - 1)
            y_ = random.randint(0, len(imagelist[0]) - 1)
            if imagelist[x_][y_] > p1[2]:
                p2 = p1
                p1 = (x_, y_, imagelist[x_][y_])

        x1, y1 = p1[:2]
        x2, y2 = p2[:2]

        n = 0
        weight = 255
        points = 1
        for x, y in linegen((x1, y1), (x2, y2)):
            points += 1
            n += imagelist[x][y]

            if imagelist[x][y] < weight:
                weight = imagelist[x][y]

        assert n >= 0
        assert weight >= 0

        if points < 3:
            continue

        fitness = weight * (points**linelenexp)

        if fitness > linetup[0]:
            linetup = (fitness, weight, x1, y1, x2, y2)

    return linetup


def main(inputname, outfolder, writebw=True, writecol=True, quiet=False,
         samplesize=175, linelenexp=0.135, processes=8, iters=150,
         updinterv=50, debug=False, bwsep=False):
    imraw = Image.open(inputname)
    raww, rawh = imraw.size

    screenw = 1366
    screenh = 768

    if raww >= screenw or rawh >= screenh:
        screenar = screenw/float(screenh)
        rawar = raww/float(rawh)

        if rawar < screenar:  # source image closer to square than screen is
            width = int(screenh*rawar)
            height = int(screenh)
        else:
            width = int(screenw)
            height = int(screenw/rawar)

        im = imraw.resize((width, height), Image.ANTIALIAS)
    else:
        im = imraw
        width, height = raww, rawh

    if debug:
        print width, height

    inputfilename = inputname.split("/")[-1].split(".")[0]
    sourcegray = [[sum(im.getpixel((x, y)))/3 for y in xrange(0, height)]
                  for x in xrange(0, width)]

    sourcergb = [[im.getpixel((x, y)) for y in xrange(0, height)]
                 for x in xrange(0, width)]

    imlist = [[0 for j in xrange(0, height)] for k in xrange(0, width)]

    if debug:
        print "All data lists ready."

    tupqueue = Queue()
    i = 0
    timer = time.clock()
    avgt = timer

    if bwsep:
        outnamebw = outfolder + "/b&w/" + inputfilename + "_s%s_bw_i%s.png"
        outnamecolor = outfolder + "/col/" + inputfilename + "_s%s_color_i%s.png"
    else:
        outnamebw = outfolder + "/" + inputfilename + "_s%s_bw_i%s.png"
        outnamecolor = outfolder + "/" + inputfilename + "_s%s_color_i%s.png"

    while True:
        curried = lambda q: q.put(findbestline(sourcegray, samplesize, linelenexp))
        processesrunning = 8
        p1 = Process(target=curried, args=(tupqueue,))
        p2 = Process(target=curried, args=(tupqueue,))
        p3 = Process(target=curried, args=(tupqueue,))
        p4 = Process(target=curried, args=(tupqueue,))
        p5 = Process(target=curried, args=(tupqueue,))
        p6 = Process(target=curried, args=(tupqueue,))
        p7 = Process(target=curried, args=(tupqueue,))
        p8 = Process(target=curried, args=(tupqueue,))
        p1.start()
        p2.start()
        p3.start()
        p4.start()
        p5.start()
        p6.start()
        p7.start()
        p8.start()

        l = []
        for k in xrange(0, processesrunning):
            l.append(tupqueue.get(block=True))

        p1.join()
        p2.join()
        p3.join()
        p4.join()
        p5.join()
        p6.join()
        p7.join()
        p8.join()

        threshold = int(max(l)[0]*0.95)
        l = [t for t in l if t[0] > threshold]
        seen = set()  # used to prevent visiting a grid point multiple times & subtracting too much from it

        for tup in l:
            if debug:
                print "Drawing line along", tup[2:]

            w = int(tup[1] * 0.7)
            start, end = ((tup[2], tup[3]), (tup[4], tup[5]))

            for x, y in linegen(start, end):
                if (x, y) in seen:
                    continue
                seen.add((x, y))

                assert w <= sourcegray[x][y]
                sourcegray[x][y] -= w
                imlist[x][y] += w

            if not quiet and i % updinterv == 0:
                timer_ = timer
                timer = time.time()
                if timer - timer_ < 2*avgt:
                    if i == 200:
                        avgt = timer - timer_
                    else:
                        avgt = (4*avgt + (timer - timer_)) / 5

                print i, "\t", w, "\t", tup[0]

            if i % iters == 0:
                if writebw:
                    if not quiet:
                        print "\nWriting %s!" % (outnamebw % (samplesize, i),)
                    writetofile(imlist, outnamebw % (samplesize, i))

                if writecol:
                    if not quiet:
                        print "Writing %s!" % (outnamecolor % (samplesize, i),)
                    writecolortofile(imlist, sourcergb, outnamecolor % (samplesize, i))

                if not quiet:
                    print "\n\ni\tweight\tfitness"
            i += 1


def writetofile(tupimg, filename):
    width = len(tupimg)
    height = len(tupimg[0])
    im = Image.new('RGB', (width, height))

    for x in xrange(0, len(tupimg)):
        for y in xrange(0, len(tupimg[x])):
            c = tupimg[x][y]

            im.putpixel((x, y), (c, c, c))
    im.save(filename)


def writecolortofile(tupimg, colorimg, fname):
    width = len(tupimg)
    height = len(tupimg[0])
    im = Image.new('RGB', (width, height))

    for x in xrange(0, len(tupimg)):
        for y in xrange(0, len(tupimg[x])):
            ratio = float(3*tupimg[x][y]) / (sum(colorimg[x][y]) + 1)

            im.putpixel((x, y), (int(colorimg[x][y][0]*ratio),
                                 int(colorimg[x][y][1]*ratio),
                                 int(colorimg[x][y][2]*ratio)))
    im.save(fname)


def usage():
    print """Arguments format:
    ./linesketch2.py [ FLAGS ] input outfolder\n
    Input can be either a file or a folder.

    ==Flags==
    -h: Show this help and exit
    -r: Write all output to outfolder (don't create subfolders)
    -c: Only write color output
    -b: Only write black & white output
    -a: Save black and white outputs to seperate subfolders
    -q: Run quiet
    -d: Debug mode (run /very/ verbose). Overrides -q
    -i [iterations]: How many lines should be added between each filesave
    -u [interval]: How often an update should be written to stdout (e.g. every 25 or 100 lines)
    -s [samplesize]: How many lines each subprocess should look at
    -e [exponent]: Default value is 0.135. larger->longer lines, smaller->shorter
    -p [processes]: Number of processes to spawn per image [[UNIMPLEMENTED]]"""


def isimg(fname):
    """Returns whether fname has a supported image file extension."""
    return fname.split(".")[-1] in ("jpg", "png", "bmp", "gif")

if __name__ == "__main__":
    #if len(sys.argv) < 3:
#        usage()
#        sys.exit()

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hrcbdqai:u:s:e:", ["help"])
    except getopt.GetoptError, errorcode:
        print "There was a problem with parsing the command line arguments."
        print "Error:", errorcode
        usage()
        sys.exit()

    #print "opts:", opts
    #print "args:", args

    if len(args) < 2:
        print "Please provide input, outfolder, and optionally any flags,"
        print "in the following format:"
        usage()
        sys.exit()

    inputs = [args[0]]
    outfolder = args[1]

    try:
        inputs = [args[0]+"/"+f for f in os.listdir(args[0]) if isimg(f)]
    except OSError, errorcode:
        if errorcode[0] == 2:
            print "File or folder named '%s' doesn't exist. Exiting." % (args[0],)
            sys.exit()

        assert errorcode[0] == 20  # 20: 'not a folder', e.g. 'is a file'

    kwargs = {}
    makesubs = True
    bwsep = False
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print "Help:\n"
            usage()
            sys.exit()
        elif opt == "-r":
            makesubs = False
        elif opt == "-c":
            kwargs["opt"] = False
        elif opt == "-b":
            kwargs["writecol"] = False
        elif opt == "-a":
            bwsep=True
            kwargs["bwsep"] = True
        elif opt == "-q":
            kwargs["quiet"] = True
        elif opt == "-d":
            kwargs["quiet"] = False
            kwargs["debug"] = True
        elif opt == "-i":
            kwargs["iters"] = int(arg)
        elif opt == "-u":
            kwargs["updinterv"] = int(arg)
        elif opt == "-s":
            kwargs["samplesize"] = int(arg)
        elif opt == "-e":
            kwargs["linelenexp"] = float(arg)
        elif opt == "-p":
            raise NotImplementedError("Process count control has not yet been implemented.")
            #kwargs["processes"] = int(arg)

    if "debug" in kwargs:
        print "Command line parameter parsing complete."
        print "opts:", opts
        print "args:", args
        print ""
        print "inputs:", inputs
        print "kwargs:", kwargs
        print "Moving on to spawning processes.\n"

    for inputfile in inputs:
        if makesubs:
            fname = inputfile.split("/")[-1].split(".")[0]
            dname = outfolder + "/" + fname
            try:
                os.mkdir(dname)
            except OSError, errcode:
                assert errcode[0] == 17  # 17: File [or directory] already exists

            if bwsep:
                for subdir in ("b&w", "col"):
                    try:
                        os.mkdir(dname+"/"+subdir)
                    except OSError, errcode:
                        assert errcode[0] == 17
        else:
            dname = outfolder
            if bwsep:
                for subdir in ("b&w", "col"):
                    try:
                        os.mkdir(dname+"/"+subdir)
                    except OSError, errcode:
                        assert errcode[0] == 17


        tfunc = lambda: main(inputfile, dname, **kwargs)

        if "debug" in kwargs:
            print "==Root process==: Function curried. input: %s output: %s" % (inputfile, dname)
            print "==Root process==: Starting new process."

        Process(target=tfunc).start()

