"""Microapp compiler inspector"""

import os, shutil, multiprocessing

try:
    from collections import Mapping
except:
    from collections.abc import Mapping



from microapp import App, register_appclass, unregister_appclass

def _update(d, u):
    for k, v in u.items():
        if isinstance(v, Mapping):
            r = _update(d.get(k, {}), v)
            d[k] = r
        else:
            if k in d:
                if isinstance( u[k], int ):
                    d[k] += u[k]
                else:
                    d[k] = u[k]
            else:
                d[k] = u[k]
    return d


class FortranTimingCollector(App):

    _name_ = "timingcollect"
    _version_ = "0.1.0"

    def __init__(self, mgr):

        self.add_argument("datadir", help="raw data directory")
        self.add_argument("-o", "--output", type=str, help="output path.")

        self.register_forward("data", help="timing raw data")

    def perform(self, args):

        datadir = args.datadir["_"]

        # collect data
        etimes = {} # mpirank:omptid:invoke=[(fileid, linenum, numvisits), ... ]
        etimemin = 1.0E100
        etimemax = 0.0
        netimes = 0
        etimeresol = 0.0
        nexcluded_under = 0
        nexcluded_over = 0

        mpipaths = []
        for item in os.listdir(datadir):
            try:
                mpirank, ompthread = item.split('.')
                if mpirank.isdigit() and ompthread.isdigit():
                    mpipaths.append((datadir, mpirank, ompthread))
            except:
                pass

        nprocs = max(int(multiprocessing.cpu_count()/2), 1)

        fwds = {"data": mpipaths}
        group_opts = ["--multiproc", "%d" % nprocs, "--assigned-input",
               "data:@data", "--clone", "%d" % len(mpipaths), "--data-join", "accumulate"]
        app_args = ["_tcollect", "@data"]

        register_appclass(_TCollect)

        ret, fwds = self.run_subgroup(group_args=group_opts, app_args=app_args, forward=fwds)
        assert ret == 0, "_tcollect returned non-zero code."

        unregister_appclass(_TCollect)

        # how many groups per app
        for grp, pathouts in fwds.items():
            # how many exits per group
            for pathout in pathouts:
                # how many edges per exit
                for etime, emeta in pathout["data"]: # using group command
                #etime, emeta = pathout["data"]

                    _update(etimes, etime)

                    etimemin = min(etimemin, emeta[0])
                    etimemax = max(etimemax, emeta[1])
                    netimes += emeta[2]
                    etimeresol = max(etimeresol, emeta[3])
                    nexcluded_under += emeta[4]
                    nexcluded_over += emeta[5]

        if len(etimes) == 0:
            shutil.rmtree(datadir)

        etimes["_summary_"] = {
                "elapsedtime_min": etimemin,
                "elapsedtime_max": etimemax,
                "number_eitmes": netimes,
                "elapsedtime_res": etimeresol,
                "number_underflow": nexcluded_under,
                "number_overflow": nexcluded_over
            }

        self.add_forward(data=etimes)

        
class _TCollect(App):

    _name_ = "_tcollect"
    _version_ = "0.1.0"

    def __init__(self, mgr):

        self.add_argument("data", help="input data")
        self.add_argument("-o", "--output", type=str, help="output path.")

        self.register_forward("data", help="timing data")

    def perform(self, args):

        # collect data
        etimes = {} # mpirank:omptid:invoke=[(fileid, linenum, numvisits), ... ]
        emeta = [ 1.0E100, 0.0, 0, 0.0, 0, 0 ] #  min, max, number, resolution, under limit, over limit

        etimemin_limit = None
        etimemax_limit = None

        etimeroot, mpirank, ompthread = args.data["_"]

        try:
            if mpirank not in etimes: etimes[mpirank] = {}
            if ompthread not in etimes[mpirank]: etimes[mpirank][ompthread] = {}

            with open(os.path.join(etimeroot, '%s.%s'%(mpirank, ompthread)), 'r') as f:
                for line in f:
                    invoke, start, stop, resolution = line.split()
                    estart = float(start)
                    estop = float(stop)
                    ediff = estop - estart
                    if etimemin_limit is not None and ediff < etimemin_limit:
                        emeta[4] += 1
                    elif etimemax_limit is not None and ediff > etimemax_limit:
                        emeta[5] += 1
                    else:
                        etimes[mpirank][ompthread][invoke] = ( start, stop )

                        if ediff < emeta[0]:
                            emeta[0] = ediff
                        if ediff > emeta[1]:
                            emeta[1] = ediff
                        emeta[2] += 1
                        eresol = float(resolution)
                        if eresol > emeta[3]:
                            emeta[3] = eresol

        except Exception as e:
            pass
            # TODO log error message
        finally:
            pass

        self.add_forward(data=(etimes, emeta))


class FortranTimingCombiner(App):

    _name_ = "timingcombine"
    _version_ = "0.1.0"

    def __init__(self, mgr):

        self.add_argument("data", help="timing data")
        self.add_argument("-o", "--output", type=str, help="output path.")

        self.register_forward("data", help="timing model data")

    def perform(self, args):
        raise("timingcombine is not implemented yet.")
