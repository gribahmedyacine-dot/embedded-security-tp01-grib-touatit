"""TP 01 - The CAN bus (Operation Ghost Bus): YOUR working file.

Names: Grib Ahmed Yassine, Touatit Mohammed Walid
Team number: 2

How to work:
  1. Write your team number in the line  TEAM = None  below.
  2. In Part I, some pieces of code are replaced by blanks written ____ .
     Replace each ____ with the right value (the brochure tells you where).
  3. Write the code of each question at the bottom, in the WORK AREA.
  4. Save, then run:   python tp1_start.py
  5. Validate each mission with check(mission_number, your_answer).

Do not modify tp1_common.py.
"""
from tp1_common import MESSAGES, simulate, show, set_team, load_log, check, score

TEAM = 2        # <-- replace None with your team number, for example  TEAM = 7


# ====================================================================== PART I
def frame_bits(dlc, ifs=False):
    """Number of bits of a standard data frame, without stuff bits.
    dlc: number of data bytes (0 to 8). ifs=True adds the inter-frame space."""
    return 44 + 8 * dlc + (3 if ifs else 0)          # blanks 1 and 2


def stuff(bits):
    """Bit stuffing: returns the bits that really go on the bus."""
    out = []          # the bits that go on the bus
    last = None       # value of the previous bit
    run = 0           # how many identical bits in a row so far
    for b in bits:
        out.append(b)
        if b == last:
            run = run + 1
        else:
            run = 1
        last = b
        if run == 5:                                   # blank 3
            ins = "0" if b == "1" else "1"               # blank 4
            out.append(ins)        # insert the opposite bit
            last = ins
            run = 1                                    # blank 5
    return "".join(out)


def arbitrate(ids, width=11):
    """Bitwise arbitration. Returns (winner, losers), where losers gives,
    for each losing identifier, the bit at which it withdrew."""
    words = {i: format(i, "0{}b".format(width)) for i in ids}   # 11-bit strings
    alive = set(ids)      # nodes still transmitting
    losers = {}
    for pos in range(width):
        # level on the bus: dominant if at least one node still alive sends it
        if any(words[i][pos] == "0" for i in alive):     # blank 6
            bus = "0"
        else:
            bus = "1"
        for i in list(alive):
            if words[i][pos] != bus:       # this node sent 1 but reads 0
                losers[i] = pos + 1
                alive.discard(i)
    return alive.pop(), losers


# ================================================================== WORK AREA
if __name__ == "__main__":
    print("TP 01 - Operation Ghost Bus\n")
    if TEAM is None:
        raise SystemExit("Write your team number at the top of the file:  TEAM = ...")
    set_team(TEAM)

    # Write the code of each question below this line.

    # ---------------- Step 1: decode the frames
    print(frame_bits(8))
    print(frame_bits(8, ifs=True))
    duration = frame_bits(8) / 500_000 * 1e6
    print(duration)
    check(1, duration)

    print(stuff("1111110"))
    print(stuff("0000001"))
    r = stuff("1000001111100000")
    print(r)
    check(2, r)

    winner, losers = arbitrate([0x2A5, 0x2A1, 0x3A5])      # lecture example
    print(hex(winner))
    for i in losers:
        print(hex(i), "loses at bit", losers[i])
    winner, losers = arbitrate([0x1B3, 0x1A7, 0x1A5])
    print(hex(winner))
    for i in losers:
        print(hex(i), "loses at bit", losers[i])
    check(3, winner)

    # ---------------- Step 2: simulate the bus
    load, stats = show("Normal bus, 125 kbit/s", MESSAGES, 125_000)
    check(4, round(100 * load, 2))
    wait = stats[0x500]["max_wait"] * 1e6
    print(wait)
    check(5, round(wait))
    show("Normal bus, 500 kbit/s", MESSAGES, 500_000)

    flood = MESSAGES + [dict(name="Flooder", id=0x000, period=0.001, dlc=8)]
    load_f, stats_f = show("Flooding attack", flood, 125_000)
    check(6, round(100 * load_f))
    flood600 = MESSAGES + [dict(name="Flooder", id=0x600, period=0.001, dlc=8)]
    show("Flooder with id 0x600", flood600, 125_000)
    flood4 = MESSAGES + [dict(name="Flooder", id=0x000, period=0.004, dlc=8)]
    show("Flooder 0x000, period 4 ms", flood4, 125_000)

    # ---------------- Step 3: find the saboteur
    log = load_log()
    print(len(log))
    print(log[:3])
    counts = {}
    for time_ms, ident, nbytes in log:
        counts[ident] = counts.get(ident, 0) + 1
    for ident in sorted(counts):
        print(hex(ident), counts[ident])
    periods_ms = {m["id"]: m["period"] * 1000 for m in MESSAGES}
    print("id      expected observed diff")
    for ident in sorted(counts):
        exp = round(3000 / periods_ms[ident])
        print("{:<7} {:>8} {:>8} {:>+5}".format(hex(ident), exp, counts[ident], counts[ident] - exp))
    SPOOFED = max(counts, key=lambda k: counts[k] - round(3000 / periods_ms[k]))
    FAKE = counts[SPOOFED] - round(3000 / periods_ms[SPOOFED])
    print("intruder id:", hex(SPOOFED), "fake frames:", FAKE)
    check(7, hex(SPOOFED))
    check(8, FAKE)

    PERIOD = periods_ms[SPOOFED]
    times = [t for t, ident, n in log if ident == SPOOFED]
    alerts = [b for a, b in zip(times, times[1:]) if b - a < PERIOD / 2]
    print(len(alerts))
    print(alerts[:8])

    score()
