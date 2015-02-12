#!/usr/bin/env python2.6

"""Contains various functions for getting raster lines.
Details about each function are in their docstrings.
Run this module standalone to check functions for proper
outputs and to generate benchmarks."""


def linegen(p1, p2, debug=False):
    """Simple, unoptimized generator function implementation of Bresenham's.
Based largely on Wikipedia's pseudocode circa June 2014. Heavily tested."""

    ########
    # Any other line function in this module that needs to be checked for
    # proper output should be checked against this function.
    ########

    if debug:
        print "linegen called with", p1, p2

    # Special case: vertical line
    if p1[0] == p2[0]:
        if debug:
            print "Vertical line."

        for y in xrange(p1[1], p2[1]):
            yield (p1[0], y)
        return

    # General case
    tx = abs(p1[0] - p2[0])
    ty = abs(p1[1] - p2[1])
    bigslope = tx < ty
    if bigslope:
        tx, ty = ty, tx

    flipx = p1[0] > p2[0]
    flipy = p1[1] > p2[1]

    err = 0
    d_err = float(ty) / float(tx)

    y = 0

    if debug:
        print "bigslope:", bigslope
        print "flipx, flipy:", flipx, flipy
        print "tx, ty:", tx, ty
        print "d_err:", d_err

    for x in xrange(0, tx + 1):
        if bigslope:
            p = [y, x]
        else:
            p = [x, y]

        if flipx:
            p[0] *= -1
        if flipy:
            p[1] *= -1

        p[0] += p1[0]
        p[1] += p1[1]
        yield p

        err += d_err
        if err > 0.5:
            if debug:
                print "Error threshold passed. x =", x, "   err =", err

            y += 1
            err -= 1


def linegenopt(p1, p2):
    """Input and output are same as for linegen. Several unremarkable attempts
at code optimization have been made."""

    # Special case: vertical line
    if p1[0] == p2[0]:
        for y in xrange(p1[1], p2[1]):
            yield (p1[0], y)
        return

    # General case
    tx = abs(p1[0] - p2[0])
    ty = abs(p1[1] - p2[1])
    bigslope = tx < ty
    if bigslope:
        tx, ty = ty, tx

    flipx = p1[0] > p2[0]
    flipy = p1[1] > p2[1]

    err = 0
    d_err = float(ty) / float(tx)

    y = 0
    if bigslope:
        if flipx and flipy:
            for x in xrange(0, tx + 1):
                p = [y, x]

                p[0] *= -1
                p[1] *= -1

                p[0] += p1[0]
                p[1] += p1[1]
                yield p

                err += d_err
                if err > 0.5:
                    y += 1
                    err -= 1
        elif flipx:
            for x in xrange(0, tx + 1):
                p = [y, x]

                p[0] *= -1

                p[0] += p1[0]
                p[1] += p1[1]
                yield p

                err += d_err
                if err > 0.5:
                    y += 1
                    err -= 1
        elif flipy:
            for x in xrange(0, tx + 1):
                p = [y, x]

                p[1] *= -1

                p[0] += p1[0]
                p[1] += p1[1]
                yield p

                err += d_err
                if err > 0.5:
                    y += 1
                    err -= 1
        else:
            for x in xrange(0, tx + 1):
                p = [y, x]

                p[0] += p1[0]
                p[1] += p1[1]
                yield p

                err += d_err
                if err > 0.5:
                    y += 1
                    err -= 1

    else:
        if flipx and flipy:
            for x in xrange(0, tx + 1):
                p = [x, y]

                p[0] *= -1
                p[1] *= -1

                p[0] += p1[0]
                p[1] += p1[1]
                yield p

                err += d_err
                if err > 0.5:
                    y += 1
                    err -= 1
        elif flipx:
            for x in xrange(0, tx + 1):
                p = [x, y]

                p[0] *= -1

                p[0] += p1[0]
                p[1] += p1[1]
                yield p

                err += d_err
                if err > 0.5:
                    y += 1
                    err -= 1
        elif flipy:
            for x in xrange(0, tx + 1):
                p = [x, y]

                p[1] *= -1

                p[0] += p1[0]
                p[1] += p1[1]
                yield p

                err += d_err
                if err > 0.5:
                    y += 1
                    err -= 1
        else:
            for x in xrange(0, tx + 1):
                p = [x, y]

                p[0] += p1[0]
                p[1] += p1[1]
                yield p

                err += d_err
                if err > 0.5:
                    y += 1
                    err -= 1


def linegenfudged(p1, p2):
    """
Does not generate a line precisely from p1 to p2: rather, a point near p2 is
picked which allows for a constant number of steps along the longer axis for
every single step along the short axis. This is almost always a different point
from p2, and this function should not be used when precise lines are needed.
However, this function is astronomically faster than linegen or linegenopt, and
there is a guarantee that it will always choose the same line, so in situations
where speed is a higher priority than accuracy, this function may be a good
choice."""

    dx = abs(p1[0] - p2[0])
    dy = abs(p1[1] - p2[1])

    ylonger = dy > dx
    xstep = 1 if p1[0] < p2[0] else -1
    ystep = 1 if p1[1] < p2[1] else -1

    if ylonger:
        ygap = int(round((dy+1)/float(dx+1)))
        y = p1[1]
        ymax = p1[1]
        if p2[1] > p1[1]:
            ymax = p2[1]
        for x in xrange(p1[0], p2[0], xstep):
            for i in xrange(0, ygap):
                y += ystep
                if y < 0 or y > ymax:
                    return
                yield (x, y)
    else:
        xgap = int(round((dx+1)/float(dy+1)))
        x = p1[0]
        xmax = p1[0]
        if p2[0] > p1[0]:
            xmax = p2[0]
        for y in xrange(p1[1], p2[1], ystep):
            for i in xrange(0, xgap):
                x += xstep
                if x < 0 or x > xmax:
                    return
                yield (x, y)


def vline(p1, p2):
    """vline and hline are extremely simple and not too interesting, but they
can create some remarkable effects in e.g. linesketch.py if you swap a
vanilla line generator out with one of them."""
    if p1[1] > p2[1]:
        p1, p2 = p2, p1
    for y in xrange(p1[1], p2[1]+1):
        yield (p1[0], y)


def hline(p1, p2):
    """vline and hline are extremely simple and not too interesting, but they
can create some remarkable effects in e.g. linesketch.py if you swap a
vanilla line generator out with one of them."""
    if p1[0] > p2[0]:
        p1, p2 = p2, p1
    for y in xrange(p1[0], p2[0]+1):
        yield (x, p1[1])


def stresstestlinefunc(f, w=80, h=80):
    """This function is a tool involved in benchmarking the module's functions."""

    for x1 in xrange(1, w, 3):
        for y1 in xrange(1, h, 3):
            for x2 in xrange(1, w, 3):
                for y2 in xrange(1, h, 3):
                    for p in f((x1, y1), (x2, y2)):
                        pass


def main():
    print "Starting tests."

    import random
    import time

    flag = True
    for i in xrange(5000):
        domain = 1000
        x1 = random.randrange(0, domain)
        x2 = random.randrange(0, domain)
        y1 = random.randrange(0, domain)
        y2 = random.randrange(0, domain)

        l1 = [p for p in linegen((x1, y1), (x2, y2))]
        l2 = [p for p in linegenopt((x1, y1), (x2, y2))]

        if l1 != l2:
            print "Mismatch between linegen and linegenopt!"
            print "(x1, y1) (x2, y2):   (%s, %s) (%s, %s)" % (x1, y1, x2, y2)
            flag = False

    if not flag:
        print "At least one test failed."
    else:
        print "Tests passed."
        print "Continuing to benchmarking."

        funcs = (linegen, linegenopt, linegenfudged)

        flist = {}
        for func in funcs:
            flist[func] = []
        # flist = {func: [] for func in funcs}

        samples = 7

        for i in xrange(samples):
            print "i:", i

            for func in funcs:
                print "\nf: ", ("%s" % (func,)).split(" ")[1]
                t1 = time.time()
                stresstestlinefunc(func, w=70)
                t2 = time.time()
                print round(t2-t1, 5)
                flist[func].append(t2-t1)

        for func in funcs:
            print "\n Function: ", ("%s" % (func,)).split(" ")[1]
            flist[func].sort()
            print "Mean time:", sum(flist[func])/len(flist[func])
            print "Median time:", flist[func][samples/2]


if __name__ == "__main__":
    main()
