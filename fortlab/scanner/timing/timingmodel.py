"""Microapp compiler inspector"""

import os, shutil

from collections import Mapping

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

        nprocs = 1
        fwds = {"data": mpipaths}
        group_opts = ["--multiproc", "%d" % nprocs, "--assigned-input",
               "data:@data", "--clone", "%d" % len(mpipaths), "--forwarding", "accumulate"]
        #group_opts = ["--assigned-input", "data:@data", "--clone", "%d" % len(mpipaths), "--forwarding", "accumulate"]
        app_args = ["_tcollect", "@data"]

        register_appclass(_TCollect)

        #ret, fwds = self.manager.run_command(cmd, forward=fwds)
        ret, fwds = self.run_subgroup(group_args=group_opts, app_args=app_args, forward=fwds)
        assert ret == 0, "_tcollect returned non-zero code."

        unregister_appclass(_TCollect)

        for grp, pathouts in fwds.items():
            for pathout in pathouts:
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

#        etimemin_limit = Config.model['types']['etime']['minval']
#        etimemax_limit = Config.model['types']['etime']['maxval']
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

        import pdb; pdb.set_trace()

#        else:
#            try:
#                etime_sections = [ Config.path['etime'], 'summary']
#
#                self.addmodel(Config.path['etime'], etime_sections)
#
#                # elapsedtime section
#                etime = []
#                #fd.write('; <MPI rank> < OpenMP Thread> <invocation order> =  <file number>:<line number><num of invocations> ...\n')
#
#                for ranknum, threadnums in etimes.items():
#                    for threadnum, invokenums in threadnums.items():
#                        for invokenum, evalues  in invokenums.items():
#                            etime.append( ( '%s %s %s'%(ranknum, threadnum, invokenum), ', '.join(evalues) ) )
#                self.addsection(Config.path['etime'], Config.path['etime'], etime)
#
#                summary = []
#                summary.append( ('minimum_elapsedtime', str(etimemin)) )
#                summary.append( ('maximum_elapsedtime', str(etimemax)) )
#                summary.append( ('number_elapsedtimes', str(netimes)) )
#                summary.append( ('resolution_elapsedtime', str(etimeresol)) )
#                self.addsection(Config.path['etime'], 'summary', summary )
#            except Exception as e:
#                kgutils.logger.error(str(e))
#
#
#    out, err, retcode = kgutils.run_shcmd('make recover', cwd=etime_realpath)
#
#    if Config.state_switch['clean']:
#        kgutils.run_shcmd(Config.state_switch['clean'])

########################
#
#        #nprocs = min( len(mpipaths), multiprocessing.cpu_count()*1)
#        nprocs = 1
#
#        if nprocs == 0:
#            kgutils.logger.warn('No elapsedtime data files are found.')
#        else:
#            workload = [ chunk for chunk in chunks(mpipaths, int(math.ceil(len(mpipaths)/nprocs))) ]
#            inqs = []
#            outqs = []
#            for _ in range(nprocs):
#                inqs.append(multiprocessing.Queue())
#                outqs.append(multiprocessing.Queue())
#
#            procs = []
#            for idx in range(nprocs):
#                proc = multiprocessing.Process(target=readdatafiles, args=(inqs[idx], outqs[idx]))
#                procs.append(proc)
#                proc.start()
#
#            for inq, chunk in zip(inqs,workload):
#                inq.put(chunk)
#
#            for outq in outqs:
#                etime, emeta = outq.get()
#                update(etimes, etime)
#                etimemin = min(etimemin, emeta[0])
#                etimemax = max(etimemax, emeta[1])
#                netimes += emeta[2]
#                etimeresol = max(etimeresol, emeta[3])
#                nexcluded_under += emeta[4]
#                nexcluded_over += emeta[5]
#            for idx in range(nprocs):
#                procs[idx].join()
#
#
#            if len(etimes) == 0:
#                if not _DEBUG:
#                    shutil.rmtree(datadir)
#                kgutils.logger.warn('Elapsedtime data is not collected.')
#            else:
#                try:
#                    etime_sections = [ Config.path['etime'], 'summary']
#
#                    self.addmodel(Config.path['etime'], etime_sections)
#
#                    # elapsedtime section
#                    etime = []
#                    #fd.write('; <MPI rank> < OpenMP Thread> <invocation order> =  <file number>:<line number><num of invocations> ...\n')
#
#                    for ranknum, threadnums in etimes.items():
#                        for threadnum, invokenums in threadnums.items():
#                            for invokenum, evalues  in invokenums.items():
#                                etime.append( ( '%s %s %s'%(ranknum, threadnum, invokenum), ', '.join(evalues) ) )
#                    self.addsection(Config.path['etime'], Config.path['etime'], etime)
#
#                    summary = []
#                    summary.append( ('minimum_elapsedtime', str(etimemin)) )
#                    summary.append( ('maximum_elapsedtime', str(etimemax)) )
#                    summary.append( ('number_elapsedtimes', str(netimes)) )
#                    summary.append( ('resolution_elapsedtime', str(etimeresol)) )
#                    self.addsection(Config.path['etime'], 'summary', summary )
#
#                except Exception as e:
#                    kgutils.logger.error(str(e))
#
#        else:
#            if not _DEBUG:
#                shutil.rmtree(datadir)
#            kgutils.logger.info('failed to generate elapsedtime information')
#
#        out, err, retcode = kgutils.run_shcmd('make recover', cwd=etime_realpath)
#
#        if Config.state_switch['clean']:
#            kgutils.run_shcmd(Config.state_switch['clean'])
#    else: # check if coverage should be invoked
#        kgutils.logger.info('Reusing Elapsedtime file: %s/%s'%(Config.path['outdir'], Config.modelfile))
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#
#    # check if elapsedtime data exists in model file
#    if not os.path.exists('%s/%s'%(Config.path['outdir'], Config.modelfile)):
#        kgutils.logger.warn('No elapsedtime file is found.')
#    else:
#        # read ini file
#        kgutils.logger.info('Reading %s/%s'%(Config.path['outdir'], Config.modelfile))
#
#        cfg = configparser.ConfigParser()
#        cfg.optionxform = str
#        cfg.read('%s/%s'%(Config.path['outdir'], Config.modelfile))
#
#        try:
#
#            etimemin = float(cfg.get('elapsedtime.summary', 'minimum_elapsedtime').strip())
#            etimemax = float(cfg.get('elapsedtime.summary', 'maximum_elapsedtime').strip())
#            netimes = int(cfg.get('elapsedtime.summary', 'number_elapsedtimes').strip())
#            etimediff = etimemax - etimemin
#            etimeres = float(cfg.get('elapsedtime.summary', 'resolution_elapsedtime').strip())
#
#            # <MPI rank> < OpenMP Thread> <invocation order> =  <file number>:<line number>:<num etimes> ... 
#            if etimediff == 0:
#                nbins = 1
#            else:
#                nbins = max(min(Config.model['types']['etime']['nbins'], netimes), 2)
#
#            kgutils.logger.info('nbins = %d'%nbins)
#            kgutils.logger.info('etimemin = %f'%etimemin)
#            kgutils.logger.info('etimemax = %f'%etimemax)
#            kgutils.logger.info('etimediff = %f'%etimediff)
#            kgutils.logger.info('netimes = %d'%netimes)
#
#            if nbins > 1:
#                etimebins = [ {} for _ in range(nbins) ]
#                etimecounts = [ 0 for _ in range(nbins) ]
#            else:
#                etimebins = [ {} ]
#                etimecounts = [ 0 ]
#
#            idx = 0
#            for opt in cfg.options('elapsedtime.elapsedtime'):
#                ranknum, threadnum, invokenum = tuple( num for num in opt.split() )
#                start, stop = cfg.get('elapsedtime.elapsedtime', opt).split(',')
#                estart = float(start)
#                eend = float(stop)
#                etimeval = eend - estart
#                if nbins > 1:
#                    binnum = int(math.floor((etimeval - etimemin) / etimediff * (nbins - 1)))
#                else:
#                    binnum = 0
#                etimecounts[binnum] += 1
#            kgutils.logger.info('etimediff = %f'%etimediff)
#            kgutils.logger.info('netimes = %d'%netimes)
#
#            if nbins > 1:
#                etimebins = [ {} for _ in range(nbins) ]
#                etimecounts = [ 0 for _ in range(nbins) ]
#            else:
#                etimebins = [ {} ]
#                etimecounts = [ 0 ]
#
#            idx = 0
#            for opt in cfg.options('elapsedtime.elapsedtime'):
#                ranknum, threadnum, invokenum = tuple( num for num in opt.split() )
#                start, stop = cfg.get('elapsedtime.elapsedtime', opt).split(',')
#                estart = float(start)
#                eend = float(stop)
#                etimeval = eend - estart
#                if nbins > 1:
#                    binnum = int(math.floor((etimeval - etimemin) / etimediff * (nbins - 1)))
#                else:
#                    binnum = 0
#                etimecounts[binnum] += 1
#        triples = []
#        for binnum, etimebin in enumerate(etimebins):
#            bin_triples = []
#            range_begin = binnum*(etimemax-etimemin)/nbins + etimemin if binnum > 0  else etimemin
#            range_end = (binnum+1)*(etimemax-etimemin)/nbins + etimemin if binnum < (nbins-1)  else None
#
#            bunit = 'sec'
#            if range_begin < 1.E-6:
#                bunit = 'usec'
#                range_begin *= 1.E6
#
#            if range_end is None:
#                print 'From bin # %d [ %f (%s) ~ ] %f %% of %d'%(binnum, \
#                    range_begin, bunit, countdist[binnum] * 100, totalcount)
#            else:
#                eunit = 'sec'
#                if range_end < 1.E-6:
#                    eunit = 'usec'
#                    range_end *= 1.E6
#
#                print 'From bin # %d [ %f (%s) ~ %f (%s) ] %f %% of %d'%(binnum, \
#                    range_begin, bunit, range_end, eunit, countdist[binnum] * 100, totalcount)
#
#            for invokenum in sorted(etimebin.keys()):
#                if len(bin_triples) >= datacollect[binnum]: break
#                # select datacollect[binum] under this data tree, rank/thread/invoke
#                bininvokes = etimebin[invokenum].keys()
#                random.shuffle(bininvokes)
#                for ranknum in bininvokes:
#                    if len(bin_triples) >= datacollect[binnum]: break
#                    binranks = etimebin[invokenum][ranknum].keys()
#                    random.shuffle(binranks)
#                    for threadnum in binranks:
#                        bin_triples.append( (ranknum, threadnum, invokenum) )
#                        print '        invocation triple: %s:%s:%s'%(ranknum, threadnum, invokenum)
#            triples.extend(bin_triples)
#
#        print 'Number of bins: %d'%nbins
#        print 'Minimun elapsed time: %f'%etimemin
#        print 'Maximum elapsed time: %f'%etimemax
#        #print 'Selected invocation triples:'
#        #print ','.join([ ':'.join([ str(n) for n in t ]) for t in triples])
#
#        for ranknum, threadnum, invokenum in triples:
#            Config.invocation['triples'].append( ( (str(ranknum), str(ranknum)), (str(threadnum), str(threadnum)), \
#                (str(invokenum), str(invokenum)) ) )
#
